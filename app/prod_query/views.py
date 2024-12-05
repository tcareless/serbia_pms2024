from django.http import HttpResponse
from django.shortcuts import render
from django.db import connections
# import mysql.connector

from datetime import datetime, date, timedelta
import time

from .forms import MachineInquiryForm
from .forms import CycleQueryForm
from .forms import WeeklyProdDate
from .forms import WeeklyProdUpdate
from .models import Weekly_Production_Goal
from query_tracking.models import record_execution_time
from django.shortcuts import redirect

import logging
logger = logging.getLogger('prod-query')


def sub_index(request):
    return redirect('prod_query:prod-query_index')



# part is the part number [##-####] as a string
# end_of_period is the timestamp of the last second of the period (used to search for currently effective goal)
# returns a tupple with the part number and the goal

def weekly_prod_goal(part, end_of_period):
    goals = Weekly_Production_Goal.objects.filter(part_number=part).order_by('-year', '-week').all()
    for goal in goals:
        goal_date = date.fromisocalendar(year=goal.year, week=goal.week, day=7)
        goal_ts = datetime.combine(goal_date, datetime.min.time()).timestamp()-7200
        if goal_ts <= end_of_period:
            return goal.goal
    return 0



def adjust_target_to_effective_date(target_date):
    (temp_year,temp_week,temp_day) = target_date.isocalendar()
    effective_date = date.fromisocalendar(year=temp_year, week=temp_week, day=7)
    effective_date -= timedelta(days = 7)
    return effective_date
    

#  Report total production by part from end of line machines
def weekly_prod(request):

    # Part, shift start in 24 hour time, list of machines used
    parameters = [
        ("50-9341", 22, ['1533']),
        ("50-0455", 22, ['1816']),
        ("50-1467", 22, ['742', '650L', '650R', '769']),  # 650L and 650R replaced with 742 5/28/2024
        ("50-3050", 22, ['769']),
        ("50-8670", 23, ['1724', '1725', '1750']),
        ("50-0450", 23, ['1724', '1725', '1750']),
        ("50-5401", 23, ['1724', '1725', '1750']),
        ("50-0447", 23, ['1724', '1725', '1750']),
        ("50-5404", 23, ['1724', '1725', '1750']),
        ("50-0519", 23, ['1724', '1725', '1750']),
        ("50-4865", 23, ['1617']),
        ("50-5081", 23, ['1617']),
        ("50-4748", 23, ['797']),
        ("50-3214", 23, ['1725']),
        ("50-5214", 23, ['1725']),
    ]
    # Add new part information here.
    # Increase number of rows in template script file

    context = {}
    tic = time.time()
    target = datetime.today().date()        #this is wrong, doesn't allow setting goal setting for previous weeks
    (temp_year,temp_week,temp_day) = datetime.today().date().isocalendar()
    effective_date = date.fromisocalendar(year=temp_year, week=temp_week, day=7)
    effective_date -= timedelta(days = 7)
    context['form'] = WeeklyProdDate(initial={'date': target})
    context['update_form'] = WeeklyProdUpdate(initial={'effective_date': effective_date})

    if request.method == 'POST':

        if 'update' in request.POST:
            form = WeeklyProdUpdate(request.POST)
            if form.is_valid():
                effective_date = form.cleaned_data.get('effective_date')
                goal = form.cleaned_data.get('goal')
                part_number = form.cleaned_data.get('part_number')

                #check for weekly goal, if there overwrite it, else make new weekly goal
                
                effective_year = effective_date.year
                effective_week = effective_date.isocalendar().week

                new_weekly_goal, created = Weekly_Production_Goal.objects.get_or_create(
                    part_number=part_number,
                    year=effective_year, 
                    week=effective_week,
                    defaults={'goal': goal},)

                new_weekly_goal.goal = goal
                new_weekly_goal.save()

        form = WeeklyProdDate(request.POST)
        if form.is_valid():
            # Previous week
            if 'prev' in request.POST:
                target = form.cleaned_data.get('date') - timedelta(days=7)
                new_effective_date = adjust_target_to_effective_date(target)
                context['update_form'] = WeeklyProdUpdate(initial={'effective_date': new_effective_date})
            # Specific week
            if 'specific' in request.POST:
                target = form.cleaned_data.get('date')
                new_effective_date = adjust_target_to_effective_date(target)
                context['update_form'] = WeeklyProdUpdate(initial={'effective_date': new_effective_date})
            # Current week
            context['form'] = WeeklyProdDate(initial={'date': target})

    cursor = connections['prodrpt-md'].cursor()

    # Date headers for table
    days_past_sunday = target.isoweekday() % 7
    sunday = target - timedelta(days=days_past_sunday)
    dates = []
    for i in range(1, 8):
        dates.append(sunday + timedelta(days=i))

    seconds_in_shift = 28800
    rows = []
    for part, shift_start_hour, source_machine_list in parameters:

        # Time stamps for each shift
        shift_start = datetime(target.year, target.month, target.day,
                               shift_start_hour, 0, 0)-timedelta(days=days_past_sunday)
        shift_starts = []
        start = datetime.timestamp(shift_start)
        for i in range(0, 21):
            shift_starts.append(start)
            start = start + seconds_in_shift
        last_shift_end = shift_starts[20] + seconds_in_shift

        # Goal
        end_of_period = last_shift_end
        goal = weekly_prod_goal(part,end_of_period)

        # One query for each machine used by part
        # sql "in" is very slow
        values_from_query = 21
        row = [0] * values_from_query
        for machine in source_machine_list:
            # Prepares select for query
            sum_string = ''
            for i in range(0, values_from_query):
                sum_string += f"IFNULL(SUM(\n"
                sum_string += f"CASE\n"
                sum_string += f"WHEN TimeStamp >= {shift_starts[i]}\n"
                sum_string += f"AND TimeStamp <= {shift_starts[i] + seconds_in_shift} THEN 1\n"
                sum_string += f"ELSE 0\n"
                sum_string += f"END\n"
                sum_string += f"), 0) as quantitycol{i+1},"
            sum_string = sum_string[:-1]
            sum_string = "SELECT\n" + sum_string

            # Prepares remainder of query
            sql_quantities = f"\nFROM\n"
            sql_quantities += f"GFxPRoduction\n"
            sql_quantities += f"WHERE\n"
            sql_quantities += f"TimeStamp >= {shift_starts[0]}\n"
            sql_quantities += f"AND TimeStamp < {last_shift_end}\n"
            sql_quantities += f"AND Machine = '{machine}'\n"
            sql_quantities += f"AND Part = '{part}'"

            # Executes query
            sql_quantities = sum_string + sql_quantities
            cursor.execute(sql_quantities)
            # The return value is a tuple with a single value, which this unpacks
            (res,) = cursor.fetchall()
            for i in range(0, values_from_query):
                row[i] += res[i]

        # Calculates:
        # The total parts actually produced
        # The predicted total by end of week
        #   based off of percent of time left in week
        #   sets the percent to 100% if the week is in the past
        # The difference between the predicted total and the goal
        # This processing occurs once per row
        week_total = sum(row)
        time_left = last_shift_end - datetime.timestamp(datetime.now())
        if time_left < 0:
            predicted = round(int(week_total))
        else:
            proportion = time_left / 604800
            predicted = round(int(week_total)/(1-proportion))
        difference = round(predicted-int(goal))

        # Goal is inserted after the loop processing is completed, simplifying the indexes
        row.insert(0, part)
        row.append(week_total)
        row.append(predicted)
        row.append(goal)  # add in goal for reference
        row.append(difference)
        rows.append(row)

    context['dates'] = dates
    context['rows'] = rows
    context['page_title'] = "Weekly Production"

    print(time.time()-tic)

    return render(request, 'prod_query/weekly-prod.html', context)


def prod_query_index_view(request):
    context = {}
    context["main_heading"] = "Prod Query Index"
    context["title"] = "Prod Query Index - pmsdata12"
    return render(request, f'prod_query/index_prod_query.html', context)

# Updated strokes_per_min_graph view
def strokes_per_min_graph(request):
    default_numGraphPoints = 300
    context = {}
    if request.method == 'GET':
        form = CycleQueryForm()
        context['form'] = form
        context['numGraphPoints'] = default_numGraphPoints
    elif request.method == 'POST':
        form = CycleQueryForm(request.POST)
        if form.is_valid():
            machine = form.cleaned_data['machine']
            start_date = form.cleaned_data['start_date']
            start_time = form.cleaned_data['start_time']
            end_date = form.cleaned_data['end_date']
            end_time = form.cleaned_data['end_time']
            numGraphPoints = int(request.POST.get('numGraphPoints', default_numGraphPoints))

            # Ensure numGraphPoints is within the allowed range
            if numGraphPoints < 50:
                numGraphPoints = 50
            elif numGraphPoints > 1000:
                numGraphPoints = 1000

            # Combine date and time into datetime objects
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)

            # Convert datetimes to Unix timestamps
            start_timestamp = int(time.mktime(start_datetime.timetuple()))
            end_timestamp = int(time.mktime(end_datetime.timetuple()))

            # Calculate the total duration in minutes
            total_minutes = (end_datetime - start_datetime).total_seconds() / 60

            # Calculate the interval to display numGraphPoints points
            interval = max(int(total_minutes / numGraphPoints), 1)

            labels, counts = fetch_chart_data(machine, start_timestamp, end_timestamp, interval=interval, group_by_shift=False)
            context['chartdata'] = {
                'labels': labels,
                'dataset': {
                    'label': 'Quantity',
                    'data': counts,
                    'borderWidth': 1
                }
            }
        context['form'] = form
        context['numGraphPoints'] = numGraphPoints

    return render(request, 'prod_query/strokes_per_minute.html', context)


def cycle_times(request):
    context = {}
    toc = time.time()
    if request.method == 'GET':
        form = CycleQueryForm()

    if request.method == 'POST':
        form = CycleQueryForm(request.POST)
        if form.is_valid():
            target_date = form.cleaned_data.get('target_date')
            times = form.cleaned_data.get('times')
            machine = form.cleaned_data.get('machine')

            shift_start, shift_end = shift_start_end_from_form_times(target_date, times)

            tic = time.time()

            sql = f'SELECT * FROM `GFxPRoduction` '
            sql += f'WHERE `Machine`=\'{machine}\' '
            sql += f'AND `TimeStamp` BETWEEN \'{int(shift_start.timestamp())}\' AND \'{int(shift_end.timestamp())}\' '
            sql += f'ORDER BY TimeStamp;'
            cursor = connections['prodrpt-md'].cursor()
            cursor.execute(sql)
            lastrow = -1
            times = {}

            count = 0
            # get the first row and save the first cycle time            
            row = cursor.fetchone()
            if row:
                lastrow = row[4]

            while row:
                cycle = round(row[4]-lastrow)
                if cycle > 0 :
                    times[cycle] = times.get(cycle, 0) + 1
                    lastrow = row[4]
                    count += 1
                row = cursor.fetchone()

            res = sorted(times.items())
            if (len(res) == 0):
                context['form'] = form
                return render(request, 'prod_query/cycle_query.html', context)

            # Uses a range loop to rehydrate the frequency table without holding the full results in memory
            # Sums values above the lower trim index and stops once it reaches the upper trim index
            PERCENT_EXCLUDED = 0.05
            remove = round(count * PERCENT_EXCLUDED)
            low_trimindex = remove
            high_trimindex = count - remove
            it = iter(res)
            trimsum = 0
            track = 0
            val = next(it)
            for i in range(high_trimindex):
                if (track >= val[1]):
                    val = next(it)
                    track = 0
                if (i > low_trimindex):
                    trimsum += val[0]
                track += 1
            trimAve = trimsum / high_trimindex
            context['trimmed'] = f'{trimAve:.3f}'
            context['excluded'] = f'{PERCENT_EXCLUDED:.2%}'

            # Sums all cycle times that are DOWNTIME_FACTOR times larger than the trimmed average
            DOWNTIME_FACTOR = 3
            threshold = int(trimAve * DOWNTIME_FACTOR)
            downtime = 0
            microstoppage = 0
            for r in res:
                if (r[0] > trimAve and r[0] < threshold):
                    microstoppage += (r[0] - trimAve) * r[1]
                if (r[0] > threshold):
                    downtime += r[0] * r[1]
            context['microstoppage'] = f'{microstoppage / 60:.1f}'
            context['downtime'] = f'{downtime / 60:.1f}'
            context['factor'] = DOWNTIME_FACTOR

            record_execution_time("cycle_times", sql, toc-tic)
            context['time'] = f'Elapsed: {toc-tic:.3f}'

            context['result'] = res
            context['machine'] = machine

            labels, counts = strokes_per_minute_chart_data(machine, shift_start.timestamp(), shift_end.timestamp(), 5 )
            context['chartdata'] = {
                'labels': labels,
                'dataset': {'label': 'Quantity',
                        'data': counts,
                        'borderWidth': 1}
            }



    context['form'] = form
    context['title'] = 'Production'



    return render(request, 'prod_query/cycle_query.html', context)

# Combined fetch data function that both views can use
def fetch_chart_data(machine, start, end, interval=5, group_by_shift=False):
    """
    Fetch chart data for a specific machine between start and end times.
    
    Parameters:
    - machine: str, identifier of the machine
    - start: int, start of the period (Unix timestamp)
    - end: int, end of the period (Unix timestamp)
    - interval: int, time interval in minutes for strokes per minute data (default is 5)
    - group_by_shift: bool, whether to group data by shift (default is False)
    
    Returns:
    - labels: list of timestamps or dates
    - data: list of counts or lists of counts for each shift
    """
    
    # Construct the SQL query based on whether data should be grouped by shift or by time intervals
    if group_by_shift:
        sql = f'SELECT DATE(FROM_UNIXTIME(TimeStamp)) as event_date, '
        sql += f'CASE '
        sql += f'WHEN HOUR(FROM_UNIXTIME(TimeStamp)) >= 7 AND HOUR(FROM_UNIXTIME(TimeStamp)) < 15 THEN "Day" '
        sql += f'WHEN HOUR(FROM_UNIXTIME(TimeStamp)) >= 15 AND HOUR(FROM_UNIXTIME(TimeStamp)) < 23 THEN "Afternoon" '
        sql += f'ELSE "Night" '
        sql += f'END AS Shift, '
        sql += f'count(*) '
        sql += f'FROM GFxPRoduction '
        sql += f'WHERE TimeStamp BETWEEN {start} AND {end} '
        sql += f'AND Machine = "{machine}" '
        sql += f'GROUP BY event_date, Shift '
        sql += f'ORDER BY event_date, Shift;'
    else:
        sql = f'SELECT DATE_ADD('
        sql += f'FROM_UNIXTIME({start}), '
        sql += f'Interval CEILING(TIMESTAMPDIFF(MINUTE, FROM_UNIXTIME({start}), '
        sql += f'FROM_UNIXTIME(TimeStamp))/{interval})*{interval} minute) as event_datetime_interval, '
        sql += f'count(*) '
        sql += f'FROM GFxPRoduction '
        sql += f'WHERE TimeStamp BETWEEN {start} AND {end} AND Machine = "{machine}" '
        sql += f'GROUP BY event_datetime_interval '
        sql += f'ORDER BY event_datetime_interval;'

    # Execute the SQL query and fetch the results
    with connections['prodrpt-md'].cursor() as c:
        c.execute(sql)
        data = c.fetchall()

    labels = []
    counts = []
    
    if group_by_shift:
        # Initialize lists for each shift
        day_counts = []
        afternoon_counts = []
        night_counts = []

        # Create an iterator for the fetched data
        data_iter = iter(data)
        row = next(data_iter, None)

        interval = 24 * 60 * 60  # Interval of 1 day

        # Iterate over each day in the specified period
        for timestamp in range(start, end, interval):
            dt = datetime.fromtimestamp(timestamp).date()

            # Initialize counts for each shift
            day_count = 0
            afternoon_count = 0
            night_count = 0

            # Accumulate counts for each shift within the current date interval
            while row and row[0] == dt:
                if row[1] == 'Day':
                    day_count = row[2]
                elif row[1] == 'Afternoon':
                    afternoon_count = row[2]
                elif row[1] == 'Night':
                    night_count = row[2]
                row = next(data_iter, None)

            # Append the results for the current date to the lists
            labels.append(dt)
            day_counts.append(day_count)
            afternoon_counts.append(afternoon_count)
            night_counts.append(night_count)
            counts.append(day_count + afternoon_count + night_count)

        return labels, day_counts, afternoon_counts, night_counts, counts
    else:
        # Create an iterator for the fetched data
        data_iter = iter(data)
        row = next(data_iter, None)
        
        # Iterate over each time interval in the specified period
        for time in range(int(start), int(end), interval * 60):
            dt = datetime.fromtimestamp(time)

            # Initialize count for the current interval
            if not row:
                row = (dt, 0)
            if row and row[0] > dt:
                labels.append(dt)
                counts.append(0)
                continue
            while row and row[0] < dt:
                row = next(data_iter, None)
            if row and row[0] == dt:
                labels.append(dt)
                counts.append(row[1] / interval)
                row = next(data_iter, None)

        return labels, counts


def prod_query(request):
    context = {}
    if request.method == 'GET':
        form = MachineInquiryForm()

    if request.method == 'POST':
        tic = time.time()

        form = MachineInquiryForm(request.POST)
        results = []

        if form.is_valid():
            # print('form valid')

            inquiry_date = form.cleaned_data.get('inquiry_date')

            times = form.cleaned_data.get('times')

            machines = form.cleaned_data.get('machines')

            machine_list = []
            for machine in machines:
                machine = machine.strip()
                machine_list.append(machine)
                machine_list.append(f'{machine}REJ')
                machine_list.append(f'{machine}AS')

            # build list of parts with quotes and commas for sql IN clause
            parts = form.cleaned_data.get('parts')

            part_list = ''
            for part in parts:
                part_list += f'"{part.strip()}", '
            part_list = part_list[:-2]

            shift_start, shift_end = shift_start_end_from_form_times(inquiry_date, times)

            shift_start_ts = datetime.timestamp(shift_start)

            if int(times) <= 6:  # 8 hour query
                sql = 'SELECT Machine, Part, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp <= ' + \
                    str(shift_start_ts + 3600) + \
                    ' THEN 1 ELSE 0 END) as hour1, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 3600) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 7200) + \
                    ' THEN 1 ELSE 0 END) as hour2, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 7200) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 10800) + \
                    ' THEN 1 ELSE 0 END) as hour3, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 10800) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 14400) + \
                    ' THEN 1 ELSE 0 END) as hour4, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 14400) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 18000) + \
                    ' THEN 1 ELSE 0 END) as hour5, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 18000) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 21600) + \
                    ' THEN 1 ELSE 0 END) as hour6, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 21600) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 25200) + \
                    ' THEN 1 ELSE 0 END) as hour7, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts +
                                                           25200) + ' THEN 1 ELSE 0 END) AS hour8 '
                sql += 'FROM GFxPRoduction '
                sql += 'WHERE TimeStamp >= ' + \
                    str(shift_start_ts) + ' AND TimeStamp < ' + \
                    str(shift_start_ts + 28800) + ' '
                if machine:
                    sql += 'AND Machine = %s '
                if len(part_list):
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Part '
                sql += 'ORDER BY Part ASC;'

            elif int(times) <= 8:  # 24 hour by shift query
                sql = 'SELECT Machine, Part, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp <= ' + \
                    str(shift_start_ts + 28800) + \
                    ' THEN 1 ELSE 0 END) as shift1, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 28800) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 57600) + \
                    ' THEN 1 ELSE 0 END) as shift2, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts +
                                                           57600) + ' THEN 1 ELSE 0 END) AS shift3 '
                sql += 'FROM GFxPRoduction '
                sql += 'WHERE TimeStamp >= ' + \
                    str(shift_start_ts) + ' AND TimeStamp < ' + \
                    str(shift_start_ts + 86400) + ' '
                if machine:
                    sql += 'AND Machine = %s '
                if len(part_list):
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Part '
                sql += 'ORDER BY Part ASC;'

            else:  # week at a time query
                sql = 'SELECT Machine, Part, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp <= ' + \
                    str(shift_start_ts + 86400) + \
                    ' THEN 1 ELSE 0 END) as mon, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 86400) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 172800) + \
                    ' THEN 1 ELSE 0 END) as tue, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 172800) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 259200) + \
                    ' THEN 1 ELSE 0 END) as wed, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 259200) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 345600) + \
                    ' THEN 1 ELSE 0 END) as thur, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 345600) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 432000) + \
                    ' THEN 1 ELSE 0 END) as fri, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 432000) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 518400) + \
                    ' THEN 1 ELSE 0 END) as sat, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + \
                    str(shift_start_ts + 518400) + \
                    ' THEN 1 ELSE 0 END) AS sun '
                sql += 'FROM GFxPRoduction '
                sql += 'WHERE TimeStamp >= ' + \
                    str(shift_start_ts) + ' AND TimeStamp < ' + \
                    str(shift_start_ts + 604800) + ' '
                if machine:
                    sql += 'AND Machine = %s '
                if len(part_list):
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Part '
                sql += 'ORDER BY Part ASC;'

            cursor = connections['prodrpt-md'].cursor()
            try:
                for machine in machine_list:
                    cursor.execute(sql, [machine])
                    result = cursor.fetchall()
                    for row in result:
                        machine = row[0]
                        if machine.endswith('REJ'):
                            machine = machine[:-3]
                        row = list(row)
                        row.append(sum(row[2:]))
                        row.insert(0, machine)
                        results.append(row)

            except Exception as e:
                print("Oops!", e, "occurred.")
            finally:
                cursor.close()

            # Calculate totals
            if results:
                num_columns = len(results[0]) - 2  # Exclude 'Machine' and 'Part' columns
                totals = [0] * num_columns
                for row in results:
                    for i, value in enumerate(row[2:], start=0):  # Start from 0 to align with the column indexes
                        if isinstance(value, (int, float)):
                            totals[i] += value
                        else:
                            try:
                                totals[i] += int(value)
                            except ValueError:
                                continue

            context['production'] = results
            context['totals'] = totals
            context['start'] = shift_start
            context['end'] = shift_end
            context['ts'] = int(shift_start_ts)
            context['times'] = int(times)

            toc = time.time()
            context['elapsed_time'] = toc-tic
            logger.info(sql)
            logger.info(
                f'[{toc-tic:.3f}] machines="{machines}" parts="{parts}" times="{times}" date="{inquiry_date}" {datetime.isoformat(shift_start)} {shift_start_ts:.0f}')

    context['form'] = form

    return render(request, 'prod_query/prod_query.html', context)



def shift_start_end_from_form_times(inquiry_date, times):
    if times == '1':  # 10pm - 6am
        shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day, 22, 0, 0)-timedelta(days=1)
        shift_end = shift_start + timedelta(hours=8)
    elif times == '2':  # 11pm - 7am
        shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day, 23, 0, 0)-timedelta(days=1)
        shift_end = shift_start + timedelta(hours=8)
    elif times == '3':  # 6am - 2pm
        shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day, 6, 0, 0)
        shift_end = shift_start + timedelta(hours=8)
    elif times == '4':  # 7am - 3pm
        shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day, 7, 0, 0)
        shift_end = shift_start + timedelta(hours=8)
    elif times == '5':  # 2pm - 10pm
        shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day, 14, 0, 0)
        shift_end = shift_start + timedelta(hours=8)
    elif times == '6':  # 3pm - 11pm
        shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day, 15, 0, 0)
        shift_end = shift_start + timedelta(hours=8)

    elif times == '7':  # 6am - 6am
        shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day, 6, 0, 0)
        shift_end = shift_start + timedelta(days=1)
    elif times == '8':  # 7am - 7am
        shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day, 7, 0, 0)
        shift_end = shift_start + timedelta(days=1)

    elif times == '9':  # 11pm to 11pm week
        days_past_sunday = inquiry_date.isoweekday() % 7
        shift_start = datetime(inquiry_date.year, inquiry_date.month,
                                       inquiry_date.day, 22, 0, 0)-timedelta(days=days_past_sunday)
        shift_end = shift_start + timedelta(days=7)
    elif times == '10':  # 10pm to 10pmn week
        days_past_sunday = inquiry_date.isoweekday() % 7
        shift_start = datetime(inquiry_date.year, inquiry_date.month,
                                       inquiry_date.day, 23, 0, 0)-timedelta(days=days_past_sunday)
        shift_end = shift_start + timedelta(days=7)
    return shift_start,shift_end


def reject_query(request):
    context = {}
    tic = time.time()

    available_results = []
    available_sql = 'SELECT DISTINCT(CONCAT(Machine,Part)) AS cc, Part, Machine FROM 01_vw_production_rejects ORDER BY Part, Machine;'
    cursor = connections['prodrpt-md'].cursor()
    try:
        cursor.execute(available_sql)
        result = cursor.fetchall()
        for row in result:
            row = list(row[1:])
            available_results.append(row)
    except Exception as e:
        print("Oops!", e, "occurred.")
    finally:
        cursor.close()
    context['available'] = available_results

    if request.method == 'GET':
        form = MachineInquiryForm()

    if request.method == 'POST':
        tic = time.time()

        form = MachineInquiryForm(request.POST)
        results = []

        if form.is_valid():

            inquiry_date = form.cleaned_data.get('inquiry_date')
            times = form.cleaned_data.get('times')

            # build list of machines with quotes and commas
            machines = form.cleaned_data.get('machines')

            machine_list = ''
            for machine in machines:
                machine_list += f'"{machine.strip()}", '
            machine_list = machine_list[:-2]

            parts = form.cleaned_data.get('parts')

            part_list = ''
            for part in parts:
                part_list += f'"{part.strip()}", '
            part_list = part_list[:-2]

            shift_start, shift_end = shift_start_end_from_form_times(inquiry_date, times)

            shift_start_ts = datetime.timestamp(shift_start)

            if int(times) <= 6:  # 8 hour query
                sql = 'SELECT Machine, Part, Reason, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp <= ' + \
                    str(shift_start_ts + 3600) + \
                    ' THEN 1 ELSE 0 END) as hour1, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 3600) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 7200) + \
                    ' THEN 1 ELSE 0 END) as hour2, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 7200) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 10800) + \
                    ' THEN 1 ELSE 0 END) as hour3, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 10800) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 14400) + \
                    ' THEN 1 ELSE 0 END) as hour4, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 14400) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 18000) + \
                    ' THEN 1 ELSE 0 END) as hour5, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 18000) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 21600) + \
                    ' THEN 1 ELSE 0 END) as hour6, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 21600) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 25200) + \
                    ' THEN 1 ELSE 0 END) as hour7, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts +
                                                           25200) + ' THEN 1 ELSE 0 END) AS hour8 '
                sql += 'FROM `01_vw_production_rejects` '
                sql += 'WHERE TimeStamp >= ' + \
                    str(shift_start_ts) + ' AND TimeStamp < ' + \
                    str(shift_start_ts + 28800) + ' '
                if len(machine_list):
                    sql += 'AND Machine IN (' + machine_list + ') '
                if len(part_list):
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Machine, Reason, Part '
                sql += 'ORDER BY Part ASC, Machine ASC, Reason ASC;'

            elif int(times) <= 8:  # 24 hour by shift query
                sql = 'SELECT Machine, Part, Reason, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp <= ' + \
                    str(shift_start_ts + 28800) + \
                    ' THEN 1 ELSE 0 END) as shift1, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 28800) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 57600) + \
                    ' THEN 1 ELSE 0 END) as shift2, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts +
                                                           57600) + ' THEN 1 ELSE 0 END) AS shift3 '
                sql += 'FROM `01_vw_production_rejects` '
                sql += 'WHERE TimeStamp >= ' + \
                    str(shift_start_ts) + ' AND TimeStamp < ' + \
                    str(shift_start_ts + 86400) + ' '
                if len(machine_list):
                    sql += 'AND Machine IN (' + machine_list + ') '
                if len(part_list):
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Machine, Reason, Part '
                sql += 'ORDER BY Part ASC, Machine ASC, Reason ASC;'

            else:  # week at a time query
                sql = 'SELECT Machine, Part, Reason, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp <= ' + \
                    str(shift_start_ts + 86400) + \
                    ' THEN 1 ELSE 0 END) as mon, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 86400) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 172800) + \
                    ' THEN 1 ELSE 0 END) as tue, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 172800) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 259200) + \
                    ' THEN 1 ELSE 0 END) as wed, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 259200) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 345600) + \
                    ' THEN 1 ELSE 0 END) as thur, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 345600) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 432000) + \
                    ' THEN 1 ELSE 0 END) as fri, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 432000) + \
                    ' AND TimeStamp < ' + \
                    str(shift_start_ts + 518400) + \
                    ' THEN 1 ELSE 0 END) as sat, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + \
                    str(shift_start_ts + 518400) + \
                    ' THEN 1 ELSE 0 END) AS sun '
                sql += 'FROM `01_vw_production_rejects` '
                sql += 'WHERE TimeStamp >= ' + \
                    str(shift_start_ts) + ' AND TimeStamp < ' + \
                    str(shift_start_ts + 604800) + ' '
                if len(machine_list):
                    sql += 'AND Machine IN (' + machine_list + ') '
                if len(part_list):
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Machine, Reason, Part '
                sql += 'ORDER BY Part ASC, Machine ASC, Reason ASC;'

            cursor = connections['prodrpt-md'].cursor()
            print(sql)
            try:
                cursor.execute(sql)
                result = cursor.fetchall()

                for row in result:
                    row = list(row)
                    row.append(sum(row[3:]))
                    results.append(row)

            except Exception as e:
                print("Oops!", e, "occurred.")
            finally:
                cursor.close()

            context['production'] = results
            context['start'] = shift_start
            context['end'] = shift_end
            context['ts'] = shift_start_ts
            context['times'] = int(times)

            toc = time.time()
            context['elapsed_time'] = toc-tic
            logger.info(sql)
            logger.info(
                f'[{toc-tic:.3f}] machines="{machines}" parts="{parts}" times="{times}" date="{inquiry_date}" {datetime.isoformat(shift_start)} {shift_start_ts:.0f}')

    context['form'] = form
    context['title'] = 'Production'

    return render(request, 'prod_query/reject_query.html', context)


def machine_detail(request, machine, start_timestamp, times):

    tic = time.time()
    part_list = request.GET.get('parts')
    context = {}
    context['title'] = f'{machine} Detail'
    context['machine'] = machine
    context['reject_data'] = get_reject_data(
        machine, start_timestamp, times, part_list)
    context['production_data'] = get_production_data(
        machine, start_timestamp, times, part_list)
    context['ts'] = int(start_timestamp)
    context['times'] = int(times)
    context['elapsed'] = time.time() - tic

    if (times <= 6):
        window_length = 60*60*8
    elif (times <= 8):
        window_length = 60*60*24
    else:
        window_length = 60*60*24*7

    context['pagerprev'] = start_timestamp - window_length
    context['pagernext'] = start_timestamp + window_length
    context['start_dt'] = datetime.fromtimestamp(
        int(start_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    context['end_dt'] = datetime.fromtimestamp(
        int(start_timestamp + window_length)).strftime('%Y-%m-%d %H:%M:%S')
    
    # print(context['elapsed'])

    return render(request, 'prod_query/machine_detail.html', context)


def get_reject_data(machine, start_timestamp, times, part_list):
    if int(times) <= 6:  # 8 hour query
        sql = 'SELECT Part, Reason, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp) + ' AND TimeStamp <= ' + \
            str(start_timestamp + 3600) + ' THEN 1 ELSE 0 END) as hour1, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 3600) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 7200) + ' THEN 1 ELSE 0 END) as hour2, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 7200) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 10800) + ' THEN 1 ELSE 0 END) as hour3, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 10800) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 14400) + ' THEN 1 ELSE 0 END) as hour4, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 14400) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 18000) + ' THEN 1 ELSE 0 END) as hour5, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 18000) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 21600) + ' THEN 1 ELSE 0 END) as hour6, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 21600) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 25200) + ' THEN 1 ELSE 0 END) as hour7, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp +
                                                   25200) + ' THEN 1 ELSE 0 END) AS hour8 '
        sql += 'FROM `01_vw_production_rejects` '
        sql += 'WHERE TimeStamp >= ' + \
            str(start_timestamp) + ' AND TimeStamp < ' + \
            str(start_timestamp + 28800) + ' '
        sql += 'AND Machine = "' + machine + 'REJ" '
        if (part_list):
            sql += 'AND Part IN (' + part_list + ') '
        sql += 'GROUP BY Part, Reason '
        sql += 'ORDER BY Part ASC, Reason ASC;'

    elif int(times) <= 8:  # 24 hour by shift query
        sql = 'SELECT Part, Reason, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp) + ' AND TimeStamp <= ' + \
            str(start_timestamp + 28800) + ' THEN 1 ELSE 0 END) as shift1, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 28800) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 57600) + ' THEN 1 ELSE 0 END) as shift2, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp +
                                                   57600) + ' THEN 1 ELSE 0 END) AS shift3 '
        sql += 'FROM `01_vw_production_rejects` '
        sql += 'WHERE TimeStamp >= ' + \
            str(start_timestamp) + ' AND TimeStamp < ' + \
            str(start_timestamp + 86400) + ' '
        sql += 'AND Machine = "' + machine + 'REJ" '
        if (part_list):
            sql += 'AND Part IN (' + part_list + ') '
        sql += 'GROUP BY Part, Reason '
        sql += 'ORDER BY Part ASC, Reason ASC;'

    else:  # week at a time query
        sql = 'SELECT Part, Reason, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp) + ' AND TimeStamp <= ' + \
            str(start_timestamp + 86400) + ' THEN 1 ELSE 0 END) as mon, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 86400) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 172800) + ' THEN 1 ELSE 0 END) as tue, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 172800) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 259200) + ' THEN 1 ELSE 0 END) as wed, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 259200) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 345600) + ' THEN 1 ELSE 0 END) as thur, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 345600) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 432000) + ' THEN 1 ELSE 0 END) as fri, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 432000) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 518400) + ' THEN 1 ELSE 0 END) as sat, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + \
            str(start_timestamp + 518400) + ' THEN 1 ELSE 0 END) AS sun '
        sql += 'FROM `01_vw_production_rejects` '
        sql += 'WHERE TimeStamp >= ' + \
            str(start_timestamp) + ' AND TimeStamp < ' + \
            str(start_timestamp + 604800) + ' '
        sql += 'AND Machine = "' + machine + 'REJ" '
        if (part_list):
            sql += 'AND Part IN (' + part_list + ') '
        sql += 'GROUP BY Part, Reason '
        sql += 'ORDER BY Part ASC, Reason ASC;'

    cursor = connections['prodrpt-md'].cursor()
    # print(sql)
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        results = []
        for row in result:
            row = list(row)
            row.append(sum(row[2:]))
            results.append(row)

        if len(results):
            result_length = len(results[0])
            totals = [0] * result_length

            for row in results:
                for idx in range(2, result_length):
                    totals[idx] += row[idx]
            totals[0] = 'Totals'
            totals[1] = ''
            results.append(totals)

    except Exception as e:
        print("Oops!", e, "occurred.")
    finally:
        cursor.close()
    return results


def get_production_data(machine, start_timestamp, times, part_list):

    if int(times) <= 6:  # 8 hour query
        sql = 'SELECT Part, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp) + ' AND TimeStamp <= ' + \
            str(start_timestamp + 3600) + ' THEN 1 ELSE 0 END) as hour1, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 3600) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 7200) + ' THEN 1 ELSE 0 END) as hour2, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 7200) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 10800) + ' THEN 1 ELSE 0 END) as hour3, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 10800) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 14400) + ' THEN 1 ELSE 0 END) as hour4, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 14400) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 18000) + ' THEN 1 ELSE 0 END) as hour5, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 18000) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 21600) + ' THEN 1 ELSE 0 END) as hour6, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 21600) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 25200) + ' THEN 1 ELSE 0 END) as hour7, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp +
                                                   25200) + ' THEN 1 ELSE 0 END) AS hour8 '
        sql += 'FROM GFxPRoduction '
        sql += 'WHERE TimeStamp >= ' + \
            str(start_timestamp) + ' AND TimeStamp < ' + \
            str(start_timestamp + 28800) + ' '
        sql += 'AND Machine = "' + machine + '" '
        if (part_list):
            sql += 'AND Part IN (' + part_list + ') '
        sql += 'GROUP BY Part '
        sql += 'ORDER BY Part ASC;'

    elif int(times) <= 8:  # 24 hour by shift query
        sql = 'SELECT Part, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp) + ' AND TimeStamp <= ' + \
            str(start_timestamp + 28800) + ' THEN 1 ELSE 0 END) as shift1, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 28800) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 57600) + ' THEN 1 ELSE 0 END) as shift2, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp +
                                                   57600) + ' THEN 1 ELSE 0 END) AS shift3 '
        sql += 'FROM GFxPRoduction '
        sql += 'WHERE TimeStamp >= ' + \
            str(start_timestamp) + ' AND TimeStamp < ' + \
            str(start_timestamp + 86400) + ' '
        sql += 'AND Machine = "' + machine + '" '
        if (part_list):
            sql += 'AND Part IN (' + part_list + ') '
        sql += 'GROUP BY Part '
        sql += 'ORDER BY Part ASC;'

    else:  # week at a time query
        sql = 'SELECT Part, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp) + ' AND TimeStamp <= ' + \
            str(start_timestamp + 86400) + ' THEN 1 ELSE 0 END) as mon, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 86400) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 172800) + ' THEN 1 ELSE 0 END) as tue, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 172800) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 259200) + ' THEN 1 ELSE 0 END) as wed, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 259200) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 345600) + ' THEN 1 ELSE 0 END) as thur, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 345600) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 432000) + ' THEN 1 ELSE 0 END) as fri, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + str(start_timestamp + 432000) + \
            ' AND TimeStamp < ' + \
            str(start_timestamp + 518400) + ' THEN 1 ELSE 0 END) as sat, '
        sql += 'SUM(CASE WHEN TimeStamp >= ' + \
            str(start_timestamp + 518400) + ' THEN 1 ELSE 0 END) AS sun '
        sql += 'FROM GFxPRoduction '
        sql += 'WHERE TimeStamp >= ' + \
            str(start_timestamp) + ' AND TimeStamp < ' + \
            str(start_timestamp + 604800) + ' '
        sql += 'AND Machine = "' + machine + '" '
        if (part_list):
            sql += 'AND Part IN (' + part_list + ') '
        sql += 'GROUP BY Part '
        sql += 'ORDER BY Part ASC;'

    results = []
    cursor = connections['prodrpt-md'].cursor()
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
            row = list(row)
            row.append(sum(row[1:]))
            results.append(row)

    except Exception as e:
        print("Oops!", e, "occurred.")
    finally:
        cursor.close()

    return results



# #views.py
from .forms import ShiftTotalsForm
import time
import numpy as np

def fetch_shift_totals_by_day_and_shift(machine_number, start_date, end_date):
    """
    Fetch production totals by day and shift for a specific machine.
    
    Parameters:
    - machine_number: str, identifier of the machine
    - start_date: datetime, start of the period to fetch data for
    - end_date: datetime, end of the period to fetch data for
    
    Returns:
    - labels: list of dates
    - day_counts: list of counts for day shift
    - afternoon_counts: list of counts for afternoon shift
    - night_counts: list of counts for night shift
    - total_counts: list of total counts per day
    """

    # Convert datetime objects to Unix timestamps
    start_stamp = int(time.mktime(start_date.timetuple()))
    end_stamp = int(time.mktime(end_date.timetuple()))

    # SQL query to fetch production counts grouped by date and shift
    sql  = f'SELECT DATE(FROM_UNIXTIME(TimeStamp)) as event_date, '
    sql += f'CASE '
    sql += f'WHEN HOUR(FROM_UNIXTIME(TimeStamp)) >= 7 AND HOUR(FROM_UNIXTIME(TimeStamp)) < 15 THEN "Day" '
    sql += f'WHEN HOUR(FROM_UNIXTIME(TimeStamp)) >= 15 AND HOUR(FROM_UNIXTIME(TimeStamp)) < 23 THEN "Afternoon" '
    sql += f'ELSE "Night" '
    sql += f'END AS Shift, '
    sql += f'count(*) '
    sql += f'FROM GFxPRoduction '
    sql += f'WHERE TimeStamp BETWEEN {start_stamp} AND {end_stamp} '
    sql += f'AND Machine = "{machine_number}" '
    sql += f'GROUP BY event_date, Shift '
    sql += f'ORDER BY event_date, Shift;'

    # Execute the SQL query using the specified database connection
    with connections['prodrpt-md'].cursor() as c:
        c.execute(sql)
        data = c.fetchall()

    # Initialize lists to store results
    labels = []
    day_counts = []
    afternoon_counts = []
    night_counts = []
    total_counts = []

    # Create an iterator for the fetched data
    data_iter = iter(data)
    row = next(data_iter, None)

    interval = 24 * 60 * 60 # Interval of 1 day

    # Iterate over each day in the specified period
    for timestamp in range(start_stamp, end_stamp, interval):  # Interval of 1 day
        dt = datetime.fromtimestamp(timestamp).date()  # Convert timestamp to date

        # Initialize counts for each shift
        day_count = 0
        afternoon_count = 0
        night_count = 0

        # Accumulate counts for each shift within the current date interval
        while row and row[0] == dt:
            if row[1] == 'Day':
                day_count = row[2]
            elif row[1] == 'Afternoon':
                afternoon_count = row[2]
            elif row[1] == 'Night':
                night_count = row[2]
            row = next(data_iter, None)

        # Append the results for the current date to the lists
        labels.append(dt)
        day_counts.append(day_count)
        afternoon_counts.append(afternoon_count)
        night_counts.append(night_count)
        total_counts.append(day_count + afternoon_count + night_count)

    return labels, day_counts, afternoon_counts, night_counts, total_counts


def moving_average(data, window_size):
    """
    Calculate the moving average of a list of numbers.
    
    Parameters:
    - data: list of numbers
    - window_size: int, size of the moving average window
    
    Returns:
    - list of moving average values
    """
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid').tolist()



# Updated shift_totals_view view
def shift_totals_view(request):
    context = {'form': ShiftTotalsForm()}
    if request.method == 'POST':
        form = ShiftTotalsForm(request.POST)
        if form.is_valid():
            machine_numbers = form.cleaned_data['machine_number'].split(',')
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            chartdata = []
            for machine_number in machine_numbers:
                machine_number = machine_number.strip()
                labels, day_counts, afternoon_counts, night_counts, total_counts = fetch_chart_data(
                    machine_number, int(time.mktime(start_date.timetuple())), int(time.mktime(end_date.timetuple())), group_by_shift=True)

                window_size = 7
                moving_avg = moving_average(total_counts, window_size)
                avg_labels = labels[window_size - 1:]

                chartdata.append({
                    'machine_number': machine_number,
                    'labels': labels,
                    'datasets': [
                        {'label': 'Day Shift', 'data': day_counts, 'borderWidth': 1, 'borderColor': 'rgba(255, 99, 132, 1)'},
                        {'label': 'Afternoon Shift', 'data': afternoon_counts, 'borderWidth': 1, 'borderColor': 'rgba(54, 162, 235, 1)'},
                        {'label': 'Night Shift', 'data': night_counts, 'borderWidth': 1, 'borderColor': 'rgba(75, 192, 192, 1)'},
                        {'label': 'Total', 'data': total_counts, 'borderWidth': 2, 'borderColor': 'rgba(0, 0, 0, 1)', 'borderDash': [5, 5]}
                    ],
                    'moving_avg': {
                        'labels': avg_labels,
                        'data': moving_avg
                    }
                })

            context.update({
                'form': form,
                'chartdata': chartdata
            })
        else:
            print("Form is invalid")
    return render(request, 'prod_query/shift_totals.html', context)











# ===================================================================
# ===================================================================
# ==================  SC Production Tool ============================
# ===================================================================
# ===================================================================


from django.shortcuts import render
from datetime import datetime
from collections import defaultdict
import MySQLdb

def get_sc_production_data(request):
    context = {}

    if request.method == 'POST':
        asset_num = request.POST.get('asset_num')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        db = MySQLdb.connect(
            host="10.4.1.224",
            user="stuser",
            passwd="stp383",
            db="prodrptdb"
        )
        
        cursor = db.cursor()

        query = f"""
            SELECT pdate, actual_produced, shift
            FROM sc_production1
            WHERE asset_num = {asset_num}
            AND pdate BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY pdate ASC;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()

        cursor.close()
        db.close()

        # Initialize dictionary to store shift totals and grand totals by day
        daily_data = defaultdict(lambda: {'7am-3pm': 0, '3pm-11pm': 0, '11pm-7am': 0, 'grand_total': 0})

        for row in rows:
            pdate, actual_produced, shift = row
            daily_data[pdate][shift] += actual_produced
            daily_data[pdate]['grand_total'] += actual_produced

        # Prepare data for Chart.js
        labels = [day.strftime('%Y-%m-%d') for day in daily_data.keys()]
        data_by_shift = {
            '7am-3pm': [daily_data[day]['7am-3pm'] for day in daily_data],
            '3pm-11pm': [daily_data[day]['3pm-11pm'] for day in daily_data],
            '11pm-7am': [daily_data[day]['11pm-7am'] for day in daily_data],
            'grand_total': [daily_data[day]['grand_total'] for day in daily_data]
        }

        context.update({
            'labels': labels,
            'data_by_shift': data_by_shift,
            'asset_num': asset_num,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'show_chart': True  # Flag to show the chart
        })

    return render(request, 'prod_query/sc_production.html', context)



# ===================================================================
# ===================================================================
# ==================  SC Production ToolV2 ==========================
# ===================================================================
# ===================================================================


from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timedelta
import MySQLdb

def get_sc_production_data_v2(request):
    if request.method == 'POST':
        asset_num = request.POST.get('asset_num')
        selected_date = request.POST.get('selected_date')

        # Convert the selected date and find the Sunday of that week
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d')
        start_of_week = selected_date - timedelta(days=selected_date.weekday() + 1)  # Find the previous Sunday

        # The production starts from Sunday at 11pm-7am shift (so the actual production start time is 11pm Sunday)
        start_date = start_of_week + timedelta(hours=23)  # Sunday at 11pm
        end_date = start_date + timedelta(days=6, hours=23)  # End date is Saturday at 11pm

        # Connect to the database
        db = MySQLdb.connect(
            host="10.4.1.224",
            user="stuser",
            passwd="stp383",
            db="prodrptdb"
        )
        
        cursor = db.cursor()

        # Query to get the production data for the entire week starting from Sunday 11pm
        query = f"""
            SELECT pdate, actual_produced, shift
            FROM sc_production1
            WHERE asset_num = {asset_num}
            AND pdate BETWEEN '{start_date.strftime('%Y-%m-%d %H:%M:%S')}' AND '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY pdate ASC;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()

        cursor.close()
        db.close()

        # Prepare the labels and data for Chart.js
        shift_intervals = ['7am-3pm', '3pm-11pm', '11pm-7am']
        labels = []  # To store shift + date labels (e.g., '2024-10-09 7am-3pm')
        totals = []  # To store the actual production totals for each shift

        # Initialize the dictionary for shift totals
        current_day = start_date.date()  # Only consider the date part for day changes
        daily_data = {shift: 0 for shift in shift_intervals}  # Store totals for each shift per day

        for row in rows:
            pdate, actual_produced, shift = row

            # No need for .date() since pdate is already a date object
            row_date = pdate

            # Check if the day changes, if yes, append the totals for the previous day
            if row_date != current_day:
                for shift_interval in shift_intervals:
                    if not (current_day == start_of_week.date() and shift_interval in ['7am-3pm', '3pm-11pm']):
                        labels.append(f"{current_day.strftime('%Y-%m-%d')} {shift_interval}")
                        totals.append(daily_data[shift_interval])
                
                current_day = row_date  # Move to the new day
                daily_data = {shift: 0 for shift in shift_intervals}  # Reset for the new day

            # Add the production data to the correct shift
            daily_data[shift] += actual_produced

        # Append data for the final day
        for shift_interval in shift_intervals:
            if not (current_day == start_of_week.date() and shift_interval in ['7am-3pm', '3pm-11pm']):
                labels.append(f"{current_day.strftime('%Y-%m-%d')} {shift_interval}")
                totals.append(daily_data[shift_interval])

        # Return the data as JSON
        return JsonResponse({
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'labels': labels,
            'totals': totals
        })

    # If it's a GET request, render the form page
    return render(request, 'prod_query/sc_production_v2.html')





# ========================================================
# ========================================================
# =================== OA Display =========================
# ========================================================
# ========================================================


# List of scrap lines
SCRAP_LINES = [
    "AB1V Reaction",
    "AB1V Input",
    "Magna",
    "10R140",
    "10R60",
    "GFX",
    "Compact",
    "AB1V Reaction Gas",
    "AB1V Overdrive Gas",
    "10R80",
    "50-4748",
    "AB1V Input Gas",



]

def get_scrap_lines(request):
    return JsonResponse({'scrap_lines': SCRAP_LINES})

# Define lines object
lines = [
    {
        "line": "AB1V Reaction",
        "scrap_line": "AB1V Reaction",
        "operations": [
            {
                "op": "10",
                "machines": [
                    {"number": "1703R", "target": 1925, "pr_downtime_machine": "1703"},
                    {"number": "1704R", "target": 1925, "pr_downtime_machine": "1703"},
                    {"number": "616", "target": 1050, "pr_downtime_machine": "1703"},
                    {"number": "623", "target": 1050, "pr_downtime_machine": "1703"},
                    {"number": "617", "target": 1050, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "659", "target": 4200, "pr_downtime_machine": "1703"},
                    {"number": "626", "target": 2800, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "1712", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "1716L", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "90",
                "machines": [
                    {
                        "number": "1723",
                        "target": 7000,
                        "pr_downtime_machine": "1703",
                        "part_numbers": ["50-0450", "50-8670"]
                    }
                ]
            }

        ],
    },
        {
        "line": "AB1V Input",
        "scrap_line": "AB1V Input",
        "operations": [
            {
                "op": "10",
                "machines": [
                    {"number": "1740L", "target": 3500, "pr_downtime_machine": "1703"},
                    {"number": "1740R", "target": 3500, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "40",
                "machines": [
                    {"number": "1701L", "target": 3500, "pr_downtime_machine": "1703"},
                    {"number": "1701R", "target": 3500, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "733", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "775", "target": 3500, "pr_downtime_machine": "1703"},
                    {"number": "1702", "target": 3500, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "581", "target": 3500, "pr_downtime_machine": "1703"},
                    {"number": "788", "target": 3500, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "80",
                "machines": [
                    {"number": "1714", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "90",
                "machines": [
                    {"number": "1717L", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "100",
                "machines": [
                    {"number": "1706", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "110",
                "machines": [
                    {
                        "number": "1723",
                        "target": 7000,
                        "pr_downtime_machine": "1703",
                        "part_numbers": ["50-0447", "50-5401"]
                    }
                ]
            }

        ],
    },
        {
        "line": "AB1V Overdrive",
        "scrap_line": "AB1V Overdrive Gas",
        "operations": [
            {
                "op": "20",
                "machines": [
                    {"number": "1705L", "target": 3500, "pr_downtime_machine": "1703"},
                    {"number": "1746R", "target": 3500, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "25",
                "machines": [
                    {"number": "621", "target": 3500, "pr_downtime_machine": "1703"},
                    {"number": "629", "target": 3500, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "30",
                "machines": [
                    {"number": "785", "target": 700, "pr_downtime_machine": "1703"},
                    {"number": "1748", "target": 3150, "pr_downtime_machine": "1703"},
                    {"number": "1718", "target": 3150, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "35",
                "machines": [
                    {"number": "669", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "40",
                "machines": [
                    {"number": "1726", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "1722", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "1713", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "1716R", "target": 7000, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "90",
                "machines": [
                    {
                        "number": "1723",
                        "target": 7000,
                        "pr_downtime_machine": "1703",
                        "part_numbers": ["50-0519", "50-5404"]
                    }
                ]
            }

        ],
    },
       {
        "line": "10R80",
        "scrap_line": "10R80",
        "operations": [
            {
                "op": "10",
                "machines": [
                    {"number": "1504", "target": 5625, "pr_downtime_machine": "1703"},  
                    {"number": "1506", "target": 5625, "pr_downtime_machine": "1703"},  
                    {"number": "1519", "target": 5625, "pr_downtime_machine": "1703"},  
                    {"number": "1520", "target": 5625, "pr_downtime_machine": "1703"},
                    {"number": "1518", "target": 5625, "pr_downtime_machine": "1703"},  
                    {"number": "1521", "target": 5625, "pr_downtime_machine": "1703"},  
                    {"number": "1522", "target": 5625, "pr_downtime_machine": "1703"}, 
                    {"number": "1523", "target": 5625, "pr_downtime_machine": "1703"}, 
                ],
            },
            {
                "op": "30",
                "machines": [
                    {"number": "1502", "target": 11250, "pr_downtime_machine": "1703"}, 
                    {"number": "1507", "target": 11250, "pr_downtime_machine": "1703"},  
                    {"number": "1539", "target": 11250, "pr_downtime_machine": "1703"}, 
                    {"number": "1540", "target": 11250, "pr_downtime_machine": "1703"}, 
                ],
            },
            {
                "op": "40",
                "machines": [
                    {"number": "1501", "target": 11250, "pr_downtime_machine": "1703"},  
                    {"number": "1515", "target": 11250, "pr_downtime_machine": "1703"},  
                    {"number": "1524", "target": 11250, "pr_downtime_machine": "1703"}, 
                    {"number": "1525", "target": 11250, "pr_downtime_machine": "1703"}, 
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "1508", "target": 13500, "pr_downtime_machine": "1703"},  
                    {"number": "1532", "target": 15750, "pr_downtime_machine": "1703"},  
                    {"number": "1538", "target": 15750, "pr_downtime_machine": "1703"}, 
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "1509", "target": 22500, "pr_downtime_machine": "1703"},  
                    {"number": "1541", "target": 22500, "pr_downtime_machine": "1703"}, 
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "1514", "target": 22500, "pr_downtime_machine": "1703"}, 
                    {"number": "1531", "target": 22500, "pr_downtime_machine": "1703"}, 
                ],
            },
            {
                "op": "80",
                "machines": [
                    {"number": "1510", "target": 22500, "pr_downtime_machine": "1703"},  
                    {"number": "1527", "target": 22500, "pr_downtime_machine": "1703"}, 
                ],
            },
            {
                "op": "90",
                "machines": [
                    {"number": "1513", "target": 45000, "pr_downtime_machine": "1703"}, 
                ],
            },
            {
                "op": "100",
                "machines": [
                    {"number": "1503", "target": 22500, "pr_downtime_machine": "1703"},  
                    {"number": "1530", "target": 22500, "pr_downtime_machine": "1703"}, 
                ],
            },
            {
                "op": "110",
                "machines": [
                    {"number": "1511", "target": 22500, "pr_downtime_machine": "1703"},
                    {"number": "1528", "target": 22500, "pr_downtime_machine": "1703"},  
                ],
            },
            {
                "op": "120",
                "machines": [
                    {"number": "1533", "target": 45000, "pr_downtime_machine": "1703"}, 
                ],
            },
        ],
    },
 {
        "line": "10R60",
        "scrap_line": "10R60",
        "operations": [
            {
                "op": "10",
                "machines": [
                    {"number": "1800", "target": 5918, "pr_downtime_machine": "1703"},
                    {"number": "1801", "target": 5918, "pr_downtime_machine": "1703"},
                    {"number": "1802", "target": 5072, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "30",
                "machines": [
                    {"number": "1529", "target": 4227, "pr_downtime_machine": "1703"},
                    {"number": "776", "target": 4227, "pr_downtime_machine": "1703"},
                    {"number": "1824", "target": 4227, "pr_downtime_machine": "1703"},
                    {"number": "1543", "target": 4227, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "40",
                "machines": [
                    {"number": "1804", "target": 8454, "pr_downtime_machine": "1703"},
                    {"number": "1805", "target": 8454, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "1806", "target": 16908, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "1808", "target": 16908, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "1810", "target": 16908, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "80",
                "machines": [
                    {"number": "1815", "target": 16908, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "90",
                "machines": [
                    {"number": "1542", "target": 16908, "pr_downtime_machine": "1703"},
                ],
            },
            {
                "op": "100",
                "machines": [
                    {"number": "1812", "target": 1908, "pr_downtime_machine": "1703"},
                ],
            },
                        {
                "op": "110",
                "machines": [
                    {"number": "1813", "target": 16908, "pr_downtime_machine": "1703"},
                ],
            },
                        {
                "op": "120",
                "machines": [
                    {"number": "1816", "target": 16908, "pr_downtime_machine": "1703"},
                ],
            },
        ],
    },
    {
        "line": "Presses",
        "scrap_line": "NA",
        "operations": [
            {
                "op": "compact",
                "machines": [
                    {"number": "272", "target": 18000, "pr_downtime_machine": "1703"},
                    {"number": "273", "target": 18000, "pr_downtime_machine": "1703"},
                    {"number": "277", "target": 18000, "pr_downtime_machine": "1703"},
                    {"number": "278", "target": 18000, "pr_downtime_machine": "1703"},
                    {"number": "262", "target": 18000, "pr_downtime_machine": "1703"},
                    {"number": "240", "target": 18000, "pr_downtime_machine": "1703"},
                    {"number": "280", "target": 18000, "pr_downtime_machine": "1703"},
                    {"number": "242", "target": 18000, "pr_downtime_machine": "1703"},
                ],
            },
        ],
    },

]


# Updated Mapping of machine numbers to downtime thresholds
MACHINE_THRESHOLDS = {
    '1703R': 5, '1703L': 5, '1704R': 5, '1704L': 5,
    '616': 5, '623': 5, '617': 5, '659': 5,
    '626': 5, '1712': 5, '1716L': 5, '1716R': 5, '1723': 5,
    '1800': 5, '1801': 5, '1802': 5, '534': 5,
    '1529': 5, '776': 5, '1824': 5, '1543': 5,
    '1804': 5, '1805': 5, '1806': 5, '1808': 5,
    '1810': 5, '1815': 5, '1542': 5, '1812': 5,
    '1813': 5, '1816': 5, '810': 5,
    '1740L': 5, '1740R': 5, '1701L': 5, '1701R': 5,
    '733': 5, '775': 5, '1702': 5, '581': 5,
    '788': 5, '1714': 5, '1717L': 5, '1706': 5,
    '1724': 5, '1725': 5, '1750': 5,
    '1705': 5, '1746': 5, '621': 5, '629': 5,
    '785': 5, '1748': 5, '1718': 5, '669': 5,
    '1726': 5, '1722': 5, '1713': 5, '1719': 5,
    '1504': 5, '1506': 5, '1519': 5, '1520': 5,
    '1502': 5, '1507': 5, '1501': 5, '1515': 5,
    '1508': 5, '1532': 5, '1509': 5, '1514': 5,
    '1510': 5, '1513': 5, '1503': 5, '1511': 5,
    '1533': 5, '1518': 5, '1521': 5, '1522': 5,
    '1523': 5, '1539': 5, '1540': 5, '1524': 5,
    '1525': 5, '1538': 5, '1541': 5, '1531': 5,
    '1527': 5, '1530': 5, '1528': 5, '1546': 5,
    '1547': 5, '1548': 5, '1549': 5, '594': 5,
    '1551': 5, '1552': 5, '751': 5, '1554': 5,
    '272': 5, '273': 5, '277': 5, '278': 5,
    '262': 5, '240': 5, '280': 5, '242': 5,
    '1705L': 5, '1705R': 5, '1746L': 5, '1746R': 5,
}


# View for rendering the template
def oa_display(request):
    return render(request, 'prod_query/oa_display.html')

# View for providing machine data
def get_machine_data(request):
    # Prepare machine targets and line-to-machine mapping dynamically
    machine_targets = {}
    line_mapping = {}

    for line in lines:
        line_name = line["line"]
        line_mapping[line_name] = []
        for operation in line["operations"]:
            for machine in operation["machines"]:
                machine_number = machine["number"]
                target = machine["target"]
                machine_targets[machine_number] = target
                line_mapping[line_name].append(machine_number)

    return JsonResponse({
        'machine_targets': machine_targets,
        'line_mapping': line_mapping
    })




# ======================================
# ========= GFX Downtime Delta =========
# ======================================

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import time  # Import the time module
from .useful_functions import *
from django.utils import timezone  # Import Django's timezone utilities
import pytz  # If using pytz for timezone handling


@csrf_exempt
def gfx_downtime_and_produced_view(request):
    if request.method == "POST":
        start_time = time.time()  # Record the start time

        try:
            # Parse input data
            machines = json.loads(request.POST.get('machines', '[]'))
            start_date_str = request.POST.get('start_date')

            if not machines:
                return JsonResponse({'error': 'No machine numbers provided'}, status=400)
            if not start_date_str:
                return JsonResponse({'error': 'Start date is required.'}, status=400)

            # Parse and validate start date
            try:
                if start_date_str.endswith('Z'):
                    start_date_str = start_date_str.replace('Z', '+00:00')
                start_date = datetime.fromisoformat(start_date_str)

                # Make start_date timezone-aware (assuming input is UTC if 'Z' was present)
                if start_date.tzinfo is None:
                    start_date = timezone.make_aware(start_date, timezone=timezone.utc)

                # Convert start_date to EST
                est_timezone = pytz.timezone('America/New_York')
                start_date_est = start_date.astimezone(est_timezone)

                # Adjust end_date: if current week, end_date = min(start_date + 5 days, now)
                end_date_candidate = start_date_est + timedelta(days=5)
                now_est = timezone.now().astimezone(est_timezone)  # Current time in EST
                end_date_est = min(end_date_candidate, now_est)
            except ValueError:
                print(f"Invalid start date format: {start_date_str}")
                return JsonResponse({'error': 'Invalid start date format.'}, status=400)

            # Convert to timestamps in EST
            start_timestamp = int(start_date_est.timestamp())
            end_timestamp = int(end_date_est.timestamp())

            # Calculate total potential minutes
            total_potential_minutes_per_machine = (end_timestamp - start_timestamp) / 60  # in minutes

            # Machine metadata (targets and parts)
            machine_targets = {}
            machine_parts = {}
            for line in lines:
                for operation in line['operations']:
                    for machine in operation['machines']:
                        machine_number = machine['number']
                        machine_targets[machine_number] = machine['target']
                        
                        # Associate parts directly to the machine
                        machine_parts[machine_number] = machine_parts.get(machine_number, [])
                        if line.get('parts'):
                            machine_parts[machine_number].extend(line['parts'])


            downtime_results = []
            produced_results = []
            total_downtime = 0
            total_produced = 0

            # Use Django's database connection
            with connections['prodrpt-md'].cursor() as cursor:
                for machine in machines:
                    downtime_threshold = MACHINE_THRESHOLDS.get(machine, 0)

                    # Call the downtime function
                    machine_downtime = calculate_downtime(
                        machine, cursor,
                        start_timestamp, end_timestamp,
                        downtime_threshold, machine_parts.get(machine, None)
                    )
                    downtime_results.append({'machine': machine, 'downtime': machine_downtime})
                    total_downtime += machine_downtime

                    # Call the total produced function
                    machine_total_produced = calculate_total_produced(
                        machine, machine_parts.get(machine, []),
                        start_timestamp, end_timestamp, cursor
                    )
                    produced_results.append({'machine': machine, 'produced': machine_total_produced})
                    total_produced += machine_total_produced

            # Prepare adjusted targets per machine
            adjusted_machine_targets = {}
            scaling_factor = total_potential_minutes_per_machine / 7200  # 7200 is the full week's minutes
            for machine in machines:
                original_target = machine_targets.get(machine, 0)
                adjusted_original_target = original_target * scaling_factor
                adjusted_machine_targets[machine] = {
                    'original_target': original_target,
                    'adjusted_original_target': adjusted_original_target
                }

            # Final response
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Processing complete. Total elapsed time: {elapsed_time:.2f} seconds.")

            return JsonResponse({
                'downtime_results': downtime_results,
                'total_downtime': total_downtime,
                'produced_results': produced_results,
                'total_produced': total_produced,
                'total_potential_minutes_per_machine': total_potential_minutes_per_machine,
                'elapsed_time': f"{elapsed_time:.2f} seconds",
                'machine_targets': adjusted_machine_targets,
                'start_date': start_date_est.strftime('%Y-%m-%d %H:%M:%S %Z'),  # Formatted EST start date
                'end_date': end_date_est.strftime('%Y-%m-%d %H:%M:%S %Z')       # Formatted EST end date
            })

        except Exception as e:
            print(f"Unhandled error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Send machine details via POST'}, status=200)

# ======================================
# ========= PR Downtime  ===============
# ======================================

from .useful_functions import fetch_downtime_entries

# JSON map for machine numbers to pr_downtime1 machines (assetnums)
MACHINE_MAP = {
    "machine1": "prdowntime_machine1",
    "machine2": "prdowntime_machine2",
    "machine3": "prdowntime_machine3",
    # Add more mappings as needed
}

from .useful_functions import fetch_downtime_entries
from django.http import JsonResponse

def pr_downtime_view(request):
    """
    Handles the view logic for downtime entries.

    :param request: The HTTP request containing 'assetnum', 'called4helptime', and 'completedtime'.
    :return: JSON response with the matching downtime entries.
    """
    try:
        # Extract parameters from the request
        assetnum = request.GET.get('assetnum')
        called4helptime = request.GET.get('called4helptime')
        completedtime = request.GET.get('completedtime')

        # Validate input
        if not all([assetnum, called4helptime, completedtime]):
            return JsonResponse({"error": "Missing required parameters"}, status=400)

        # Map assetnum to the TKB machine
        mapped_assetnum = MACHINE_MAP.get(assetnum)
        if not mapped_assetnum:
            return JsonResponse({"error": f"No mapping found for asset number {assetnum}"}, status=404)

        # Fetch the data using the helper function
        data = fetch_downtime_entries(mapped_assetnum, called4helptime, completedtime)

        # Return the data as a JSON response
        return JsonResponse({"data": data}, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)







# basically I need this view to take in assetnum the startdateiso (called4helptime) and endofweek(completedtime) iso as parameters and those now become the time window pointers for this 
# query. The pr_downtime1 table has the downtime entry REASONS written by the operators or supervisors for that machine during the window, 


# Here's the thing though, we need to also include entries that started before the window and bleed into the window and we also need to include entries that 
# start in the window and bleed out of the window. 


# It needs to return a list of entries including the problem, called4help and completedtime columns. 


# For the db connection I have made this fucntion 
# get_db_connection(): that is living inside settings.py which can be found here 
# /home/tcareless/pms2024/app/pms/settings.py
# and we are here, so you can use relative paths to find that function inside settings.py and import the function to get the connection. 
# /home/tcareless/pms2024/app/prod_query/views.py



# ALSO The data fetching should all be done in its own function that is CALLED by the pr_downtime_view so please make sure that is true as well.


# This is the structure of the table Table: pr_downtime1
# Select data Show structure Alter table New item

# Column	Type	Comment
# machinenum	varchar(111)	
# problem	varchar(554) NULL	
# called4helptime	datetime	
# priority	varchar(40) [99]	
# whoisonit	varchar(554) NULL	
# down	varchar(99)	category: yes_down, no, c/o,  planned_down, etc.
# closed	tinyint(1) NULL	
# completedtime	datetime NULL	
# remedy	varchar(554) NULL	
# createdtime	timestamp NULL [CURRENT_TIMESTAMP]	
# updatedtime	datetime NULL	time when person takes the call
# idnumber	int(8) Auto Increment	
# whoisonit_full	varchar(100) NULL	
# side	varchar(100) NULL [0]	
# assetnum	varchar(100) NULL	
# changeovertime	datetime NULL [0000-00-00 00:00:00]	
# category	char(100)	
# asset_duplicates	int(20) [1]	
# IP_Address	char(60)	
# Indexes
# PRIMARY	idnumber
# INDEX	closed
# INDEX	machinenum
# INDEX	assetnum
# INDEX	completedtime
# Alter indexes

# Foreign keys
# Add foreign key

# Triggers
# BEFORE	INSERT	assetnumpopulate_prdt1	Alter
# BEFORE	UPDATE	closed_trigger	Alter
# Add trigger




# and the html file frontend will send the 3 variables to the view

# ======================================
# ========= Total Scrap ================
# ======================================

def get_db_connection():
    return MySQLdb.connect(
        host="10.4.1.224",
        user="stuser",
        passwd="stp383",
        db="prodrptdb"
    )

from django.http import JsonResponse

def total_scrap_view(request):
    try:
        scrap_line = request.GET.get('scrap_line')
        start_date_str = request.GET.get('start_date')


        if not scrap_line:
            return JsonResponse({'error': "Scrap line is required."}, status=400)

        if not start_date_str:
            return JsonResponse({'error': "Start date is required."}, status=400)

        try:
            # Replace 'Z' with '+00:00' to handle UTC format
            if start_date_str.endswith('Z'):
                start_date_str = start_date_str.replace('Z', '+00:00')
            
            # Parse the start date
            start_date = datetime.fromisoformat(start_date_str)
            end_date = start_date + timedelta(days=5)
        except Exception as e:
            return JsonResponse({'error': "Invalid start date format."}, status=400)

        query = """
            SELECT Id, scrap_part, scrap_operation, scrap_category, scrap_amount, scrap_line, 
                   total_cost, date, date_current
            FROM tkb_scrap
            WHERE scrap_line = %s
            AND date_current BETWEEN %s AND %s
            ORDER BY date_current ASC;
        """

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(query, (scrap_line, start_date, end_date))
        rows = cursor.fetchall()

        total_scrap_amount = sum(row[4] for row in rows)
        results = [
            {
                'Id': row[0],
                'Scrap Part': row[1],
                'Scrap Operation': row[2],
                'Scrap Category': row[3],
                'Scrap Amount': row[4],
                'Scrap Line': row[5],
                'Total Cost': row[6],
                'Date': row[7],
                'Date Current': row[8],
            }
            for row in rows
        ]

        cursor.close()
        db.close()
        return JsonResponse({'total_scrap_amount': total_scrap_amount, 'scrap_data': results})

    except Exception as e:
        print("Unhandled exception:", str(e))  # Debug log
        return JsonResponse({'error': str(e)}, status=500)

# =======================================
# ========= OA Calculation ==============
# =======================================


def calculate_oa_metrics(data):
    """
    Calculate OA, P, A, and Q metrics from the provided data.

    :param data: Dictionary containing input data for calculation
    :return: Dictionary with OA, P, A, Q metrics or raises an exception for invalid input
    """
    try:
        # Extract variables
        total_downtime = int(data.get('totalDowntime', 0))
        total_produced = int(data.get('totalProduced', 0))
        total_target = int(data.get('totalTarget', 0))
        total_potential = int(data.get('totalPotentialMinutes', 0))
        total_scrap = int(data.get('totalScrap', 0))

        # Validate inputs
        if total_target <= 0:
            raise ValueError('Total target must be greater than 0')
        if total_potential <= 0:
            raise ValueError('Total potential must be greater than 0')

        # Calculate P, A, Q
        P = total_produced / total_target
        A = (total_potential - total_downtime) / total_potential
        Q = total_produced / (total_produced + total_scrap) if (total_produced + total_scrap) > 0 else 0

        # Calculate OA
        OA = P * A * Q

        return {'OA': OA, 'P': P, 'A': A, 'Q': Q}

    except KeyError as e:
        raise ValueError(f"Missing key in input data: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid input: {e}")


@csrf_exempt
def calculate_oa(request):
    if request.method == 'POST':
        try:
            # Parse input data
            raw_body = request.body
            logger.info("Raw request body: %s", raw_body)
            data = json.loads(raw_body)
            logger.info("Parsed request data: %s", data)

            # Call utility function to calculate OA metrics
            metrics = calculate_oa_metrics(data)

            # Log results
            logger.info("Calculated OA Metrics: %s", metrics)

            return JsonResponse(metrics)

        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", e)
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except ValueError as e:
            logger.error("Validation error: %s", e)
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)









# =======================================================================
# =======================================================================
# =========================== OA Display V2 =============================
# =======================================================================
# =======================================================================


def oa_display_v2(request):
    """
    Render the OA Display V2 page with the lines data for the dropdown.
    """
    return render(request, 'prod_query/oa_display_v2.html', {'lines': lines})
