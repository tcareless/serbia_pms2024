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

            context['production'] = results
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










