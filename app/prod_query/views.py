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



# Define lines object
lines = [
    {
        "line": "AB1V Reaction",
        "scrap_line": "AB1V Reaction",
        "operations": [
            {
                "op": "10",
                "machines": [
                    {"number": "1703R", "target": 1925},
                    {"number": "1704R", "target": 1925},
                    {"number": "616", "target": 1050},
                    {"number": "623", "target": 1050},
                    {"number": "617", "target": 1050},
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "659", "target": 4200},
                    {"number": "626", "target": 2800},
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "1712", "target": 7000},
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "1716L", "target": 7000},
                ],
            },
            {
                "op": "90",
                "machines": [
                    {"number": "1723", "target": 7000, "part_numbers": ["50-0450", "50-8670"]
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
                    {"number": "1740L", "target": 3500},
                    {"number": "1740R", "target": 3500},
                ],
            },
            {
                "op": "40",
                "machines": [
                    {"number": "1701L", "target": 3500},
                    {"number": "1701R", "target": 3500},
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "733", "target": 7000},
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "775", "target": 3500},
                    {"number": "1702", "target": 3500},
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "581", "target": 3500},
                    {"number": "788", "target": 3500},
                ],
            },
            {
                "op": "80",
                "machines": [
                    {"number": "1714", "target": 7000},
                ],
            },
            {
                "op": "90",
                "machines": [
                    {"number": "1717L", "target": 7000},
                ],
            },
            {
                "op": "100",
                "machines": [
                    {"number": "1706", "target": 7000},
                ],
            },
            {
                "op": "110",
                "machines": [
                    {"number": "1723", "target": 7000, "part_numbers": ["50-0447", "50-5401"]
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
                    {"number": "1705L", "target": 3500},
                    {"number": "1746R", "target": 3500},
                ],
            },
            {
                "op": "25",
                "machines": [
                    {"number": "621", "target": 3500},
                    {"number": "629", "target": 3500},
                ],
            },
            {
                "op": "30",
                "machines": [
                    {"number": "785", "target": 700},
                    {"number": "1748", "target": 3150},
                    {"number": "1718", "target": 3150},
                ],
            },
            {
                "op": "35",
                "machines": [
                    {"number": "669", "target": 7000},
                ],
            },
            {
                "op": "40",
                "machines": [
                    {"number": "1726", "target": 7000},
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "1722", "target": 7000},
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "1713", "target": 7000},
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "1716R", "target": 7000},
                ],
            },
            {
                "op": "90",
                "machines": [
                    {"number": "1723", "target": 7000, "part_numbers": ["50-0519", "50-5404"]
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
                    {"number": "1504", "target": 5625},  
                    {"number": "1506", "target": 5625},  
                    {"number": "1519", "target": 5625},  
                    {"number": "1520", "target": 5625},
                    {"number": "1518", "target": 5625},  
                    {"number": "1521", "target": 5625},  
                    {"number": "1522", "target": 5625}, 
                    {"number": "1523", "target": 5625}, 
                ],
            },
            {
                "op": "30",
                "machines": [
                    {"number": "1502", "target": 11250}, 
                    {"number": "1507", "target": 11250},  
                    {"number": "1539", "target": 11250}, 
                    {"number": "1540", "target": 11250}, 
                ],
            },
            {
                "op": "40",
                "machines": [
                    {"number": "1501", "target": 11250},  
                    {"number": "1515", "target": 11250},  
                    {"number": "1524", "target": 11250}, 
                    {"number": "1525", "target": 11250}, 
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "1508", "target": 13500},  
                    {"number": "1532", "target": 15750},  
                    {"number": "1538", "target": 15750}, 
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "1509", "target": 22500},  
                    {"number": "1541", "target": 22500}, 
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "1514", "target": 22500}, 
                    {"number": "1531", "target": 22500}, 
                ],
            },
            {
                "op": "80",
                "machines": [
                    {"number": "1510", "target": 22500},  
                    {"number": "1527", "target": 22500}, 
                ],
            },
            {
                "op": "90",
                "machines": [
                    {"number": "1513", "target": 45000}, 
                ],
            },
            {
                "op": "100",
                "machines": [
                    {"number": "1503", "target": 22500},  
                    {"number": "1530", "target": 22500}, 
                ],
            },
            {
                "op": "110",
                "machines": [
                    {"number": "1511", "target": 22500},
                    {"number": "1528", "target": 22500},  
                ],
            },
            {
                "op": "120",
                "machines": [
                    {"number": "1533", "target": 45000}, 
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
                    {"number": "1800", "target": 5918},
                    {"number": "1801", "target": 5918},
                    {"number": "1802", "target": 5072},
                ],
            },
            {
                "op": "30",
                "machines": [
                    {"number": "1529", "target": 4227},
                    {"number": "776", "target": 4227},
                    {"number": "1824", "target": 4227},
                    {"number": "1543", "target": 4227},
                ],
            },
            {
                "op": "40",
                "machines": [
                    {"number": "1804", "target": 8454},
                    {"number": "1805", "target": 8454},
                ],
            },
            {
                "op": "50",
                "machines": [
                    {"number": "1806", "target": 16908},
                ],
            },
            {
                "op": "60",
                "machines": [
                    {"number": "1808", "target": 16908},
                ],
            },
            {
                "op": "70",
                "machines": [
                    {"number": "1810", "target": 16908},
                ],
            },
            {
                "op": "80",
                "machines": [
                    {"number": "1815", "target": 16908},
                ],
            },
            {
                "op": "90",
                "machines": [
                    {"number": "1542", "target": 16908},
                ],
            },
            {
                "op": "100",
                "machines": [
                    {"number": "1812", "target": 1908},
                ],
            },
                        {
                "op": "110",
                "machines": [
                    {"number": "1813", "target": 16908},
                ],
            },
                        {
                "op": "120",
                "machines": [
                    {"number": "1816", "target": 16908},
                ],
            },
        ],
    },
    # {
    #     "line": "10R140",
    #     "scrap_line": "10R140",
    #     "operations": [
    #         {
    #             "op": "10",
    #             "machines": [
    #                 {"number": "1708", "target": 5918},
    #             ],
    #         },
    #         {
    #             "op": "20",
    #             "machines": [
    #                 {"number": "1709", "target": 4227},
    #             ],
    #         },
    #         {
    #             "op": "30",
    #             "machines": [
    #                 {"number": "1710", "target": 8454},
    #             ],
    #         },
    #         {
    #             "op": "40",
    #             "machines": [
    #                 {"number": "1711", "target": 16908},
    #             ],
    #         },
    #         {
    #             "op": "50",
    #             "machines": [
    #                 {"number": "1715", "target": 16908},
    #             ],
    #         },
    #         {
    #             "op": "60",
    #             "machines": [
    #                 {"number": "1716", "target": 16908},
    #             ],
    #         },
    #         {
    #             "op": "70",
    #             "machines": [
    #                 {"number": "1706", "target": 16908},
    #             ],
    #         },
    #         {
    #             "op": "80",
    #             "machines": [
    #                 {"number": "1720", "target": 16908},
    #             ],
    #         },
    #         {
    #             "op": "90",
    #             "machines": [
    #                 {"number": "748", "target": 1908},
    #                 {"number": "677", "target": 1908},
    #             ],
    #         },
    #                     {
    #             "op": "100",
    #             "machines": [
    #                 {"number": "1723", "target": 1908, "part_numbers": ["50-0519", "50-5404"]},
    #             ],
    #         },
    #                     {
    #             "op": "110",
    #             "machines": [
    #                 {"number": "1752", "target": 1908},
    #             ],
    #         },
    #     ],
    # },
    {
        "line": "Presses",
        "scrap_line": "NA",
        "operations": [
            {
                "op": "compact",
                "machines": [
                    {"number": "272", "target": 18000,},
                    {"number": "273", "target": 18000,},
                    {"number": "277", "target": 18000,},
                    {"number": "278", "target": 18000,},
                    {"number": "262", "target": 18000,},
                    {"number": "240", "target": 18000,},
                    {"number": "280", "target": 18000,},
                    {"number": "242", "target": 18000,},
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
from django.db.models import Max
from .models import OAMachineTargets


@csrf_exempt
def gfx_downtime_and_produced_view(request):
    if request.method == "POST":
        start_time = time.time()  # Record the start time
        
        try:
            # Parse input data
            machines = json.loads(request.POST.get('machines', '[]'))
            line_name = request.POST.get('line')  # Line name sent in POST request
            start_date_str = request.POST.get('start_date')

            if not machines:
                return JsonResponse({'error': 'No machine numbers provided'}, status=400)
            if not start_date_str:
                return JsonResponse({'error': 'Start date is required.'}, status=400)
            if not line_name:
                return JsonResponse({'error': 'Line is required.'}, status=400)

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

            # Fetch machine targets and parts
            machine_targets = {}
            machine_parts = {}  # Modify as needed to fetch part numbers dynamically

            # Query the database for targets
            for machine in machines:
                most_recent_target = (
                    OAMachineTargets.objects.filter(
                        machine_id=machine,
                        line=line_name,
                        effective_date_unix__lte=start_timestamp
                    )
                    .order_by('-effective_date_unix')
                    .first()
                )

                if most_recent_target:
                    machine_targets[machine] = most_recent_target.target
                else:
                    machine_targets[machine] = 0  # Default to 0 if no target found

            # Debugging: Print the machine targets
            print("Machine Targets:", machine_targets)

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


# JSON map for machine numbers to pr_downtime1 machines (assetnums)
MACHINE_MAP = {
    "1703R": "1703",
    "1704R": "1704",
    "machine3": "prdowntime_machine3",
    # Add more mappings as needed
}

from .useful_functions import fetch_prdowntime1_entries

def pr_downtime_view(request):
    try:
        default_numGraphPoints = 250  # Set default number of graph points
        
        # Extract parameters from the request
        assetnum = request.GET.get('assetnum')
        called4helptime = request.GET.get('called4helptime')
        completedtime = request.GET.get('completedtime')

        # Validate input
        if not all([assetnum, called4helptime, completedtime]):
            return JsonResponse({"error": "Missing required parameters"}, status=400)

        # Map assetnum to the TKB machine, or use assetnum directly
        mapped_assetnum = MACHINE_MAP.get(assetnum, assetnum)

        # Parse incoming time strings into datetime objects
        est = pytz.timezone('US/Eastern')
        try:
            called4helptime_dt = datetime.strptime(called4helptime, "%Y-%m-%d %H:%M:%S %Z").astimezone(est)
            completedtime_dt = datetime.strptime(completedtime, "%Y-%m-%d %H:%M:%S %Z").astimezone(est)
        except Exception as e:
            return JsonResponse({"error": f"Invalid date format: {e}"}, status=400)

        # Convert datetimes to Unix timestamps
        start_timestamp = int(time.mktime(called4helptime_dt.timetuple()))
        end_timestamp = int(time.mktime(completedtime_dt.timetuple()))

        # Calculate the total duration in minutes
        total_minutes = (completedtime_dt - called4helptime_dt).total_seconds() / 60

        # Calculate the interval to display default_numGraphPoints points
        interval = max(int(total_minutes / default_numGraphPoints), 1)

        # Fetch downtime data
        data = fetch_prdowntime1_entries(mapped_assetnum, called4helptime_dt.isoformat(), completedtime_dt.isoformat())

        # Fetch chart data for Strokes Per Minute
        labels, counts = fetch_chart_data(
            machine=mapped_assetnum,
            start=start_timestamp,
            end=end_timestamp,
            interval=interval,
            group_by_shift=False
        )
        
        # Prepare chart data for JSON serialization
        chart_labels = [dt.isoformat() if isinstance(dt, datetime) else dt for dt in labels]

        # Serialize downtime data
        serialized_data = [
            {
                "problem": entry[0],
                "called4helptime": entry[1].isoformat() if entry[1] else None,
                "completedtime": entry[2].isoformat() if entry[2] else None,
            }
            for entry in data
        ]

        return JsonResponse({
            "data": serialized_data,
            "chart_data": {
                "labels": chart_labels,
                "counts": counts
            }
        }, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)





# ======================================
# ========= Total Scrap ================
# ======================================


from django.http import JsonResponse

def total_scrap_view(request):
    try:
        # Extract and validate GET parameters
        scrap_line = request.GET.get('scrap_line')
        start_date_str = request.GET.get('start_date')

        if not scrap_line:
            return JsonResponse({'error': "Scrap line is required."}, status=400)

        if not start_date_str:
            return JsonResponse({'error': "Start date is required."}, status=400)

        try:
            # Handle ISO format with UTC 'Z'
            if start_date_str.endswith('Z'):
                start_date_str = start_date_str.replace('Z', '+00:00')
            
            start_date = datetime.fromisoformat(start_date_str)
            end_date = start_date + timedelta(days=5)
        except Exception:
            return JsonResponse({'error': "Invalid start date format."}, status=400)

        query = """
            SELECT Id, scrap_part, scrap_operation, scrap_category, scrap_amount, scrap_line, 
                   total_cost, date, date_current
            FROM tkb_scrap
            WHERE scrap_line = %s
            AND date_current BETWEEN %s AND %s
            ORDER BY date_current ASC;
        """

        # Use the Django database connection
        with connections['prodrpt-md'].cursor() as cursor:
            cursor.execute(query, [scrap_line, start_date, end_date])
            rows = cursor.fetchall()

        # Calculate total scrap amount and prepare results
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

        return JsonResponse({'total_scrap_amount': total_scrap_amount, 'scrap_data': results})

    except Exception as e:
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


def save_machine_target(machine_id, effective_date, target, line=None):
    """
    Save or update a machine target record in the database.

    :param machine_id: ID of the machine
    :param effective_date: Effective date in "YYYY-MM-DD" format
    :param target: Target value to save
    :param line: Line value to save
    :return: Saved or updated OAMachineTargets instance
    """
    try:
        # Convert effective_date to Unix timestamp
        date_obj = datetime.strptime(effective_date, "%Y-%m-%d")
        unix_timestamp = int(time.mktime(date_obj.timetuple()))
    except ValueError as e:
        raise ValueError(f"Invalid effective date format: {effective_date}") from e

    # Check if an entry already exists for the machine, line, and effective date
    record, created = OAMachineTargets.objects.update_or_create(
        machine_id=machine_id,
        line=line,  # Include the line in the filter criteria
        effective_date_unix=unix_timestamp,
        defaults={"target": target},
    )
    return record, created


@csrf_exempt
def update_target(request):
    """
    Handle updating the target for a machine on a specific effective date.
    """
    print("Received update_target request.")
    if request.method == "POST":
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            print("Data received from frontend:", data)
            
            # Retrieve the variables
            machine_id = data.get("machine_id")
            effective_date = data.get("effective_date")
            target = data.get("target")
            line = data.get("line")
            
            print(f"Machine ID: {machine_id}")
            print(f"Effective Date: {effective_date}")
            print(f"Target: {target}")
            print(f"Line: {line}")
            
            # Validate inputs
            if not machine_id or not effective_date or not target:
                print("Missing required parameters.")
                return JsonResponse({"error": "Missing required parameters."}, status=400)
            
            # Save or update the machine target
            record, created = save_machine_target(machine_id, effective_date, target, line)
            
            print("Record saved or updated:", record)
            print("Was the record newly created?", created)
            
            # Prepare the response
            response_data = {
                "message": "Target updated successfully.",
                "created": created,
                "record": {
                    "machine_id": record.machine_id,
                    "effective_date": record.effective_date_unix,
                    "target": record.target,
                    "line": record.line,  # Include line in the response
                },
            }
            return JsonResponse(response_data, status=200)
        
        except json.JSONDecodeError:
            print("Invalid JSON data received.")
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            print("Unexpected error:", str(e))
            return JsonResponse({"error": str(e)}, status=500)
    
    print("Invalid request method.")
    return JsonResponse({"error": "Invalid request method."}, status=405)



# =======================================================================
# =======================================================================
# =========================== OA Display V3 =============================
# =======================================================================
# =======================================================================


from django.shortcuts import render
from django.http import HttpResponse
import calendar
from datetime import datetime, timedelta


def get_month_start_and_end(selected_date):
    today = datetime.now()
    first_day_of_month = selected_date.replace(day=1)
    if first_day_of_month.weekday() == 6:
        start_date = first_day_of_month.replace(hour=23, minute=0, second=0)
    else:
        start_date = (first_day_of_month - timedelta(days=1)).replace(hour=23, minute=0, second=0)
    if selected_date.year == today.year and selected_date.month == today.month:
        end_date = today.replace(second=0, microsecond=0)
    else:
        end_date = selected_date.replace(
            day=calendar.monthrange(selected_date.year, selected_date.month)[1]
        ).replace(hour=23, minute=0, second=0)

    return start_date, end_date


def get_sunday_to_friday_ranges(first_day, last_day):
    ranges = []
    first_friday = first_day
    while first_friday.weekday() != 4:
        first_friday += timedelta(days=1)
    first_friday = first_friday.replace(hour=23, minute=0, second=0)
    if first_day < first_friday:
        ranges.append((first_day, first_friday))
    current_start = first_friday + timedelta(days=2) 
    current_start = current_start.replace(hour=23, minute=0, second=0)
    while current_start + timedelta(days=5) <= last_day:
        current_end = current_start + timedelta(days=5)
        current_end = current_end.replace(hour=23, minute=0, second=0)
        ranges.append((current_start, current_end))
        current_start += timedelta(days=7)
    if last_day.weekday() != 6:
        if ranges and ranges[-1][1] < last_day:
            last_sunday = last_day
            while last_sunday.weekday() != 6:
                last_sunday -= timedelta(days=1)
            last_sunday = last_sunday.replace(hour=23, minute=0, second=0)
            if last_sunday > ranges[-1][1]:
                ranges.append((last_sunday, last_day))
    return ranges


def fetch_downtime_by_date_ranges(machine, date_ranges, downtime_threshold=5, machine_parts=None):
    downtime_results = []
    try:
        with connections['prodrpt-md'].cursor() as cursor:
            for start, end in date_ranges:
                start_timestamp = int(start.timestamp())
                end_timestamp = int(end.timestamp())
                downtime = calculate_downtime(
                    machine=machine,
                    cursor=cursor,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    downtime_threshold=downtime_threshold,
                    machine_parts=machine_parts
                )
                potential_minutes = calculate_potential_minutes(start, end)
                downtime_results.append({
                    'start': start,
                    'end': end,
                    'downtime': downtime,
                    'potential_minutes': potential_minutes
                })
        return downtime_results
    except Exception as e:
        print(f"Error in fetch_downtime_by_date_ranges: {e}")  # Log the error to the console
        raise RuntimeError(f"Error fetching downtime data: {str(e)}")  # Re-raise the exception


def calculate_potential_minutes(start, end):
    return int((end - start).total_seconds() / 60)


def calculate_percentage_week(potential_minutes):
    full_week_minutes = 7200
    if potential_minutes == full_week_minutes:
        return f"{potential_minutes} (Full Week)"
    percentage = round((potential_minutes / full_week_minutes) * 100)
    return f"{potential_minutes} ({percentage}%)"


def fetch_production_by_date_ranges(machine, machine_parts, date_ranges):
    total_production = 0
    try:
        with connections['prodrpt-md'].cursor() as cursor:
            for start, end in date_ranges:
                start_timestamp = int(start.timestamp())
                end_timestamp = int(end.timestamp())
                total_production += calculate_total_produced(
                    machine=machine,
                    machine_parts=machine_parts,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    cursor=cursor
                )
        return total_production
    except Exception as e:
        print(f"Error in fetch_production_by_date_ranges: {e}")  # Log the error to the console
        raise RuntimeError(f"Error fetching production data: {str(e)}")  # Re-raise the exception


def calculate_percentage_downtime(downtime, potential_minutes):
    if potential_minutes == 0:
        return "0%"
    percentage = (downtime / potential_minutes) * 100
    return f"{int(round(percentage))}%"  # Round and convert to an integer


def get_machine_part_numbers(machine_id, line_name, lines):
    for line in lines:
        if line['line'] == line_name:  # Match the correct line
            for operation in line['operations']:
                for machine in operation['machines']:
                    if machine['number'] == machine_id:
                        # Return part numbers if they exist, otherwise None
                        return machine.get('part_numbers', None)
    return None  # Return None if no match is found


def get_month_details(selected_date, machine, line_name, lines):
    first_day, last_day = get_month_start_and_end(selected_date)
    ranges = get_sunday_to_friday_ranges(first_day, last_day)

    # Fetch downtime data
    downtime_results = fetch_downtime_by_date_ranges(
        machine=machine,
        date_ranges=ranges
    )
    for result in downtime_results:
        result['potential_minutes'] = calculate_percentage_week(result['potential_minutes'])
        result['percentage_downtime'] = calculate_percentage_downtime(
            downtime=result['downtime'],
            potential_minutes=int(result['potential_minutes'].split()[0])
        )
    
    # Fetch part numbers for the machine within the specified line
    part_numbers = get_machine_part_numbers(machine, line_name, lines)

    # Fetch production data, including part numbers if available
    with connections['prodrpt-md'].cursor() as cursor:
        for result in downtime_results:
            result['produced'] = calculate_total_produced(
                machine=machine,
                machine_parts=part_numbers,  # Pass part numbers dynamically
                start_timestamp=int(result['start'].timestamp()),
                end_timestamp=int(result['end'].timestamp()),
                cursor=cursor
            )
    return {
        'first_day': first_day,
        'last_day': last_day,
        'ranges': downtime_results
    }


def get_machine_target(machine_id, selected_date_unix, line_name):
    target_entry = OAMachineTargets.objects.filter(
        machine_id=machine_id,
        effective_date_unix__lte=selected_date_unix,
        line=line_name  # Ensure the target matches the specific line
    ).order_by('-effective_date_unix').first()
    return target_entry.target if target_entry else None


def calculate_adjusted_target(target, percentage_downtime):
    """
    Calculate the adjusted target based on:
    Adjusted Target = Target - (Target * (Downtime%))

    :param target: Original target value (int)
    :param percentage_downtime: Downtime percentage as a string (e.g., "24%")
    :return: Adjusted target (int)
    """
    try:
        downtime_fraction = float(percentage_downtime.strip('%')) / 100.0
        adjusted_target = target - (target * downtime_fraction)
        adjusted_target = round(adjusted_target)
        # Debug print:
        return adjusted_target
    except Exception as e:
        print(f"Error in calculate_adjusted_target: {e}")
        # If there's an error, return original target (fallback)
        return target


def calculate_totals(grouped_results):
    for date_block, operations in grouped_results.items():
        for operation, operation_data in operations.items():
            machines = operation_data.get('machines', [])
            if not isinstance(machines, list):
                continue

            total_target = 0
            total_adjusted_target = 0
            total_produced = 0
            total_downtime = 0
            total_potential_minutes = 0
            downtime_percentages = []
            a_values = []
            p_values = []

            for machine in machines:
                target = machine.get('target', 0)
                adjusted_target = machine.get('adjusted_target', 0)
                produced = machine.get('produced', 0)
                downtime = machine.get('downtime', 0)
                potential_minutes_str = machine.get('potential_minutes', "0 (0%)")
                percentage_downtime_str = machine.get('percentage_downtime', "0%")
                p_str = machine.get('p_value', "0%").strip('%')

                try:
                    percentage_downtime_val = float(percentage_downtime_str.strip('%'))
                    downtime_percentages.append(percentage_downtime_val)

                    total_target += target
                    total_adjusted_target += adjusted_target
                    total_produced += produced
                    total_downtime += downtime

                    pm_value = int(potential_minutes_str.split()[0])
                    total_potential_minutes += pm_value

                    p_val = int(p_str) if p_str.isdigit() else 0
                    if p_val > 0:
                        p_values.append(p_val)

                    # Calculate A value for this machine
                    a_value = calculate_A(pm_value, downtime)
                    machine['a_value'] = a_value  # Store A value back to the machine dict
                    
                    a_values.append(int(a_value.strip('%')))
                except ValueError as ve:
                    print(f"[DEBUG] Error processing machine data in calculate_totals: {ve}")

            average_downtime = round(sum(downtime_percentages) / len(downtime_percentages)) if downtime_percentages else 0
            average_a = round(sum(a_values) / len(a_values)) if a_values else 0
            average_p = round(sum(p_values) / len(p_values)) if p_values else 0

            # Add the operation's aggregated totals to operation_data
            operation_data['totals'] = {
                'total_target': total_target,
                'total_adjusted_target': total_adjusted_target,
                'total_produced': total_produced,
                'total_downtime': total_downtime,
                'total_potential_minutes': total_potential_minutes,
                'average_downtime_percentage': f"{average_downtime}%",
                'average_a_value': f"{average_a}%",
                'average_p_value': f"{average_p}%"
            }

            # Print P and A values for the operation totals
            print(f"Operation Totals - Date Block: {date_block}, Operation: {operation}, Average P: {average_p}%, Average A: {average_a}%")

    return grouped_results


def calculate_line_totals(grouped_results):
    for date_block, operations in grouped_results.items():
        line_totals = {
            'total_target': 0,
            # Remove direct summation of adjusted targets; we'll recalculate this below
            'total_produced': 0,
            'total_downtime': 0,
            'total_potential_minutes': 0,
            'downtime_percentages': [],
            'p_values': [],
            'a_values': [],
            'total_scrap_amount': 0
        }
        for operation, operation_data in operations.items():
            operation_totals = operation_data.get('totals', {})
            line_totals['total_target'] += operation_totals.get('total_target', 0)
            # Do NOT sum total_adjusted_target directly
            line_totals['total_produced'] += operation_totals.get('total_produced', 0)
            line_totals['total_downtime'] += operation_totals.get('total_downtime', 0)
            line_totals['total_potential_minutes'] += operation_totals.get('total_potential_minutes', 0)

            # Extract P and A values
            average_p_value = operation_totals.get('average_p_value', "0%").strip('%')
            try:
                line_totals['p_values'].append(int(average_p_value))
            except ValueError:
                pass

            average_a_value = operation_totals.get('average_a_value', "0%").strip('%')
            try:
                line_totals['a_values'].append(int(average_a_value))
            except ValueError:
                pass

            downtime_percentage = operation_totals.get('average_downtime_percentage', "0%")
            try:
                line_totals['downtime_percentages'].append(float(downtime_percentage.strip('%')))
            except ValueError:
                pass

            # Scrap totals (line_totals from operations dict)
            if 'line_totals' in operations:
                line_totals['total_scrap_amount'] = operations['line_totals'].get('total_scrap_amount', 0)

        # Calculate averages
        average_downtime = int(round(
            sum(line_totals['downtime_percentages']) / len(line_totals['downtime_percentages'])
        )) if line_totals['downtime_percentages'] else 0

        average_p = round(sum(line_totals['p_values']) / len(line_totals['p_values'])) if line_totals['p_values'] else 0
        average_a = round(sum(line_totals['a_values']) / len(line_totals['a_values'])) if line_totals['a_values'] else 0

        # Print P and A values for the line totals
        print(f"Line Totals - Date Block: {date_block}, Average P: {average_p}%, Average A: {average_a}%")

        # Recalculate adjusted target at the line level using the aggregated downtime
        percentage_downtime_str = f"{average_downtime}%"
        total_adjusted_target = calculate_adjusted_target(line_totals['total_target'], percentage_downtime_str)

        # Ensure `line_totals` key exists
        if 'line_totals' not in operations:
            operations['line_totals'] = {}

        operations['line_totals'].update({
            'total_target': line_totals['total_target'],
            'total_adjusted_target': total_adjusted_target,  # Use recalculated adjusted target
            'total_produced': line_totals['total_produced'],
            'total_downtime': line_totals['total_downtime'],
            'total_potential_minutes': line_totals['total_potential_minutes'],
            'average_downtime_percentage': percentage_downtime_str,
            'average_p_value': f"{average_p}%",
            'average_a_value': f"{average_a}%",
            'total_scrap_amount': line_totals['total_scrap_amount'],
            # q_value will be calculated later in get_line_details after all operations are done
        })
    return grouped_results


def calculate_monthly_totals(grouped_results):
    monthly_totals = {
        'total_target': 0,
        # Remove direct summation of adjusted targets here as well
        'total_produced': 0,
        'total_downtime': 0,
        'total_potential_minutes': 0,
        'downtime_percentages': [],
        'a_values': [],  # Track A values for monthly totals
        'p_values': [],  # Track P values for monthly totals
        'total_scrap_amount': 0,
        'q_values': []
    }

    for date_block, operations in grouped_results.items():
        if 'line_totals' in operations:
            line_totals = operations['line_totals']
            monthly_totals['total_target'] += line_totals['total_target']
            # Do NOT sum total_adjusted_target from line level, recalculate after
            monthly_totals['total_produced'] += line_totals['total_produced']
            monthly_totals['total_downtime'] += line_totals['total_downtime']
            monthly_totals['total_potential_minutes'] += line_totals['total_potential_minutes']
            monthly_totals['total_scrap_amount'] += line_totals.get('total_scrap_amount', 0)

            # Collect Q values
            q_value = line_totals.get('q_value', "0%").strip('%')
            try:
                monthly_totals['q_values'].append(float(q_value))
            except ValueError:
                pass

            # Track average P values
            try:
                p_value = float(line_totals.get('average_p_value', "0%").strip('%'))
                monthly_totals['p_values'].append(p_value)
            except ValueError:
                pass

            # Track average A values
            try:
                a_value = float(line_totals.get('average_a_value', "0%").strip('%'))
                monthly_totals['a_values'].append(a_value)
            except ValueError:
                pass

            # Track downtime percentages
            try:
                downtime_percentage = float(line_totals.get('average_downtime_percentage', "0%").strip('%'))
                monthly_totals['downtime_percentages'].append(downtime_percentage)
            except ValueError:
                pass

    # Calculate averages
    average_downtime = round(sum(monthly_totals['downtime_percentages']) / len(monthly_totals['downtime_percentages'])) if monthly_totals['downtime_percentages'] else 0
    monthly_totals['average_downtime_percentage'] = f"{average_downtime}%"

    if monthly_totals['p_values']:
        average_p = round(sum(monthly_totals['p_values']) / len(monthly_totals['p_values']))
    else:
        average_p = 0
    monthly_totals['average_p_value'] = f"{average_p}%"

    if monthly_totals['a_values']:
        average_a = round(sum(monthly_totals['a_values']) / len(monthly_totals['a_values']))
    else:
        average_a = 0
    monthly_totals['average_a_value'] = f"{average_a}%"

    # Calculate average Q
    if monthly_totals['q_values']:
        average_q = round(sum(monthly_totals['q_values']) / len(monthly_totals['q_values']), 2)
    else:
        average_q = 0
    monthly_totals['average_q_value'] = f"{average_q}%"

    # Recalculate the monthly adjusted target using the monthly average downtime
    percentage_downtime_str = f"{average_downtime}%"
    monthly_adjusted_target = calculate_adjusted_target(monthly_totals['total_target'], percentage_downtime_str)

    # Update monthly_totals to include recalculated adjusted target
    monthly_totals['total_adjusted_target'] = monthly_adjusted_target

    return monthly_totals


def total_scrap_for_line(scrap_line, start_date, end_date):
    try:
        query = """
            SELECT Id, scrap_part, scrap_operation, scrap_category, scrap_amount, scrap_line, 
                   total_cost, date, date_current
            FROM tkb_scrap
            WHERE scrap_line = %s
            AND date_current BETWEEN %s AND %s
            ORDER BY date_current ASC;
        """
        with connections['prodrpt-md'].cursor() as cursor:
            cursor.execute(query, [scrap_line, start_date, end_date])
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
        return {
            'total_scrap_amount': total_scrap_amount,
            'scrap_data': results
        }
    except Exception as e:
        print(f"Error in total_scrap_for_line: {e}")  # Log the error to the console
        raise RuntimeError(f"Error fetching scrap data: {str(e)}")  # Re-raise the exception


def calculate_p(total_produced, total_adjusted_target, downtime_percentage):
    if total_produced == 0 and downtime_percentage.strip('%') == "100":
        return 100  # Special case: 100% downtime means P should be 100%
    if total_adjusted_target == 0:
        return 0  # Avoid division by zero
    return round((total_produced / total_adjusted_target) * 100)  # Convert to percentage



def calculate_A(total_potential_minutes, downtime_minutes):
    if total_potential_minutes == 0:
        return "0%"  # Avoid division by zero
    a_value = round(((total_potential_minutes - downtime_minutes) / total_potential_minutes) * 100)
    return f"{a_value}%"  # Return percentage as a string


def calculate_Q(total_produced_last_op, scrap_total):
    if total_produced_last_op + scrap_total == 0:
        return "0%"
    q_value = round((total_produced_last_op / (total_produced_last_op + scrap_total) * 100), 2)
    return f"{q_value}%"


def get_total_produced_last_op_for_block(operations):
    try:
        valid_operations = [op for op in operations.keys() if op != 'line_totals']
        if valid_operations:
            try:
                # Sort using numeric values if possible, fallback to string sorting
                last_op = sorted(valid_operations, key=lambda x: int(x) if x.isdigit() else x)[-1]
            except ValueError as ve:
                print(f"ValueError during sorting operations: {ve}")
                last_op = sorted(valid_operations, key=str)[-1]  # Fallback to string sorting

            produced = 0
            if 'totals' in operations[last_op]:
                produced = operations[last_op]['totals'].get('total_produced', 0)
            return produced
        return 0
    except Exception as e:
        print(f"Error in get_total_produced_last_op_for_block: {e}")
        return 0


def get_line_details(selected_date, selected_line, lines):
    """
    Fetch detailed data for a line on a given date, including adjusted targets
    based on the percentage downtime.
    """
    try:
        selected_date_unix = int(selected_date.timestamp())
        line_data = next((line for line in lines if line['line'] == selected_line), None)
        if not line_data:
            raise ValueError(f"Invalid line selected: {selected_line}")

        grouped_results = {}
        for operation in line_data['operations']:
            for machine in operation['machines']:
                machine_number = machine['number']
                machine_target = get_machine_target(machine_number, selected_date_unix, selected_line)
                if machine_target is None:
                    continue

                machine_details = get_month_details(selected_date, machine_number, selected_line, lines)
                for block in machine_details['ranges']:
                    date_block = (block['start'], block['end'])
                    if date_block not in grouped_results:
                        grouped_results[date_block] = {}
                    if operation['op'] not in grouped_results[date_block]:
                        grouped_results[date_block][operation['op']] = {'machines': []}

                    # Calculate adjusted target using percentage_downtime from block
                    # block['percentage_downtime'] should be something like "24%"
                    adjusted_target = calculate_adjusted_target(
                        target=machine_target,
                        percentage_downtime=block['percentage_downtime']
                    )

                    p_value = f"{calculate_p(block['produced'], adjusted_target, block['percentage_downtime'])}%"
                    machine_data = {
                        'machine_number': machine_number,
                        'target': machine_target,
                        'adjusted_target': adjusted_target,
                        'produced': block['produced'],
                        'downtime': block['downtime'],
                        'potential_minutes': block['potential_minutes'],
                        'percentage_downtime': block['percentage_downtime'],
                        'p_value': p_value
                    }
                    grouped_results[date_block][operation['op']]['machines'].append(machine_data)

        grouped_results = calculate_totals(grouped_results)

        # Add scrap info and line totals
        for date_block, operations in grouped_results.items():
            start_date, end_date = date_block
            scrap_data = total_scrap_for_line(scrap_line=selected_line, start_date=start_date, end_date=end_date)
            total_scrap_amount = scrap_data['total_scrap_amount']
            if 'line_totals' not in operations:
                operations['line_totals'] = {}
            operations['line_totals']['total_scrap_amount'] = total_scrap_amount

        grouped_results = calculate_line_totals(grouped_results)
        for date_block, operations in grouped_results.items():
            if 'line_totals' in operations:
                scrap_total = operations['line_totals'].get('total_scrap_amount', 0)
                total_produced_last_op = get_total_produced_last_op_for_block(operations)
                operations['line_totals']['q_value'] = calculate_Q(total_produced_last_op, scrap_total)

        monthly_totals = calculate_monthly_totals(grouped_results)
        return {
            'line_name': selected_line,
            'grouped_results': grouped_results,
            'monthly_totals': monthly_totals
        }
    except Exception as e:
        print(f"Error in get_line_details: {e}")
        raise


def get_all_lines(lines):
    return [line['line'] for line in lines]


def get_month_and_year(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return date.strftime('%B %Y')  # Format to "Month Year"
    except ValueError:
        return None  # Return None if the date is invalid


def oa_byline2(request):
    context = {'lines': get_all_lines(lines)}  # Load all available lines
    if request.method == 'POST':
        selected_date_str = request.POST.get('date')
        selected_line = request.POST.get('line')
        
        # Add selected date and line to the context for persistence
        context['selected_date'] = selected_date_str
        context['selected_line'] = selected_line

        try:
            # Parse the selected date
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d')
            today = datetime.now()

            if selected_date > today:
                context['error'] = "The selected date is in the future. Please select a valid date."
            else:
                # Call the function to get line details for the selected date and line
                line_details = get_line_details(selected_date, selected_line, lines)
                context.update(line_details)
                context['selected_date'] = selected_date  # Add selected date in datetime format
                # Get the month and year for the title
                month_year = get_month_and_year(selected_date_str)
                if month_year:
                    context['month_year'] = month_year
        except ValueError:
            # Handle invalid date errors
            context['error'] = "Invalid date or error processing the date."

    return render(request, 'prod_query/oa_display_v3.html', context)


