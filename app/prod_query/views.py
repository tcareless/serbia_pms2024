from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.db import connections
import mysql.connector

from datetime import datetime, date, timedelta
import time

from .forms import MachineInquiryForm
from .forms import CycleQueryForm
from .forms import WeeklyProdDate
from .forms import WeeklyProdUpdate
from .models import Weekly_Production_Goal
from query_tracking.models import record_execution_time

import logging
logger = logging.getLogger('prod-query')

# part is the part number [##-####] as a string
# end_of_period is the timestamp of the last second of the period (used to search for currently effective goal)
# returns a tupple with the part number and the goal

def weekly_prod_goal(part, end_of_period):
    #with the 7 days adjustment, goals set for previous weeks now work as well as current week
    (temp_year,temp_week,temp_day) = datetime.fromtimestamp(end_of_period).isocalendar()
    adjusted_period_end = date.fromisocalendar(year=temp_year, week=temp_week, day=7)
    adjusted_period_end -= timedelta(days = 7)
    
    adjusted_week = adjusted_period_end.isocalendar().week
    adjusted_year = adjusted_period_end.year

    goal = Weekly_Production_Goal.objects.filter(part_number=part).filter(
        year__lte=adjusted_year).filter(week__lte=adjusted_week).order_by('-year', '-week').first()
    return goal.goal
    

def weekly_prod_goal_for_addons(part, end_of_period):
    #with the 7 days adjustment, goals set for previous weeks now work as well as current week
    (temp_year,temp_week,temp_day) = datetime.fromtimestamp(end_of_period).isocalendar()
    adjusted_period_end = date.fromisocalendar(year=temp_year, week=temp_week, day=7)
    #adjusted_period_end -= timedelta(days = 7)
    
    adjusted_week = adjusted_period_end.isocalendar().week
    adjusted_year = adjusted_period_end.year

    goal = Weekly_Production_Goal.objects.filter(part_number=part).filter(
        year__lte=adjusted_year).filter(week__lte=adjusted_week).order_by('-year', '-week').first()
    return goal.goal


def adjust_target_to_effective_date(target_date):
    (temp_year,temp_week,temp_day) = target_date.isocalendar()
    effective_date = date.fromisocalendar(year=temp_year, week=temp_week, day=7)
    effective_date -= timedelta(days = 7)
    return effective_date
    



def weekly_prod(request, year=None, week_number=None):

    tic = time.time()
    context = {}

    target = datetime.today().date()
    (temp_year,temp_week,temp_day) = target.isocalendar()

    if year and week_number:
        effective_date = date.fromisocalendar(year=year+2000, week=week_number, day=7)  #2000 is because year is just 23, 11 etc
        effective_date -= timedelta(days = 7) # adjust by one week back becuase above gives last day of the week

        days_past_sunday = 7
        sunday = effective_date

        shift_year = effective_date.year
        shift_month = effective_date.month
        shift_day = effective_date.day
        extra_days = timedelta(days=0)

        
        

    else:
        
        
        effective_date = date.fromisocalendar(year=temp_year, week=temp_week, day=7)

        days_past_sunday = target.isoweekday() % 7
        sunday = target - timedelta(days=days_past_sunday)

        shift_year = target.year
        shift_month = target.month
        shift_day = target.day
        extra_days = timedelta(days=days_past_sunday)

        

        effective_date -= timedelta(days = 7) # adjust by one week back becuase above gives last day of the week
    
    if temp_week == 1 or week_number == 1:
        prev_week_date = date.fromisocalendar(year=temp_year, week=52, day=temp_day)
    elif week_number != 1 and week_number:
        prev_week_date = date.fromisocalendar(year=year+2000, week=week_number-1, day=temp_day)
    else:
        prev_week_date = date.fromisocalendar(year=temp_year, week=temp_week-1, day=temp_day)

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
                new_effective_date = adjust_target_to_effective_date(prev_week_date)
                context['update_form'] = WeeklyProdUpdate(initial={'effective_date': effective_date})
                return redirect(f"/prod-query/weekly-prod/{prev_week_date.year-2000}/{prev_week_date.isocalendar().week}")
            # Specific week
            if 'specific' in request.POST:
                target = form.cleaned_data.get('date')
                new_effective_date = adjust_target_to_effective_date(target)
                context['update_form'] = WeeklyProdUpdate(initial={'effective_date': new_effective_date})
            # Current week
            context['form'] = WeeklyProdDate(initial={'date': target})

    cursor = connections['prodrpt-md'].cursor()

    # Part, shift start in 24 hour time, list of machines used
    parameters = [
        ("50-9341", 22, ['1533']),
        ("50-0455", 22, ['1812']),
        ("50-1467", 22, ['650L', '650R', '769']),
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

    

    # Date headers for table
    
    dates = []
    for i in range(1, 8):
        dates.append(sunday + timedelta(days=i))

    seconds_in_shift = 28800
    shift_starts = []
    rows = []
    for part, shift_start_hour, source_machine_list in parameters:

        # Time stamps for each shift
        
        shift_start = datetime(shift_year, shift_month, shift_day,
                               shift_start_hour, 0, 0)-extra_days
            
        start = datetime.timestamp(shift_start)
        for i in range(0, 21):
            shift_starts.append(start)
            start = start + seconds_in_shift
        last_shift_end = shift_starts[20] + seconds_in_shift

        # Goal
        end_of_period = last_shift_end
        
        goal = weekly_prod_goal(part, end_of_period)
        

        # sql_goals = f'SELECT DISTINCT * FROM tkb_weekly_goals WHERE part = "{line[0]}" AND TimeStamp < {last_shift_end} ORDER BY `Id` DESC LIMIT 1'
        # cursor.execute(sql_goals)
        # # The return value is a tuple:
        # # 1 is the part name
        # # 2 is the goal
        # goal = cursor.fetchone()

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

            if times == '1':  # 10pm - 6am
                shift_start = datetime(
                    target_date.year, target_date.month, target_date.day, 22, 0, 0)-timedelta(days=1)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '2':  # 11pm - 7am
                shift_start = datetime(
                    target_date.year, target_date.month, target_date.day, 23, 0, 0)-timedelta(days=1)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '3':  # 6am - 2pm
                shift_start = datetime(
                    target_date.year, target_date.month, target_date.day, 6, 0, 0)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '4':  # 7am - 3pm
                shift_start = datetime(
                    target_date.year, target_date.month, target_date.day, 7, 0, 0)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '5':  # 2pm - 10pm
                shift_start = datetime(
                    target_date.year, target_date.month, target_date.day, 14, 0, 0)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '6':  # 3pm - 11pm
                shift_start = datetime(
                    target_date.year, target_date.month, target_date.day, 15, 0, 0)
                shift_end = shift_start + timedelta(hours=8)

            elif times == '7':  # 6am - 6am
                shift_start = datetime(
                    target_date.year, target_date.month, target_date.day, 6, 0, 0)
                shift_end = shift_start + timedelta(days=1)
            elif times == '8':  # 7am - 7am
                shift_start = datetime(
                    target_date.year, target_date.month, target_date.day, 7, 0, 0)
                shift_end = shift_start + timedelta(days=1)

            db_params = {'host': '10.4.1.245',
                         'database': 'django_pms',
                         'port': 6601,
                         'user': 'muser',
                         'password': 'wsj.231.kql'}

            connection = mysql.connector.connect(**db_params)
            tic = time.time()

            sql = f'SELECT * FROM `GFxPRoduction` '
            sql += f'WHERE `Machine`=\'{machine}\' '
            sql += f'AND `TimeStamp` BETWEEN \'{str(shift_start.timestamp()).split(".", 1)[0]}\' AND \'{str(shift_end.timestamp()).split(".", 1)[0]}\' '
            sql += f'ORDER BY Id;'
            cursor = connection.cursor(dictionary=True)
            cursor.execute(sql)
            lastrow = -1
            times = {}

            count = 0
            row = cursor.fetchone()
            while row:
                if lastrow == -1:
                    lastrow = row["TimeStamp"]
                    continue
                cycle = int(f'{row["TimeStamp"]-lastrow:0>5.0f}')
                times[cycle] = times.get(cycle, 0) + 1
                lastrow = row["TimeStamp"]
                count += 1
                row = cursor.fetchone()

            res = sorted(times.items())
            if (len(res) == 0):
                context['form'] = form
                return render(request, 'prod_query/cycle_query.html', context)

            # Uses a range loop to rehydrate the frequency table without holding the full results in memory
            # Sums values above the lower trim index and stops once it reaches the upper trim index
            PERCENT_EXCLUDED = 0.01
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

    context['form'] = form

    return render(request, 'prod_query/cycle_query.html', context)


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

            # build list of machines with quotes and commas
            machines = form.cleaned_data.get('machines')

            machine_list = ''
            for machine in machines:
                machine_list += f'"{machine.strip()}", "{machine.strip()}REJ", "{machine.strip()}AS", '
            machine_list = machine_list[:-2]

            parts = form.cleaned_data.get('parts')

            part_list = ''
            for part in parts:
                part_list += f'"{part.strip()}", '
            part_list = part_list[:-2]

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
                if len(machine_list):
                    sql += 'AND Machine IN (' + machine_list + ') '
                if len(part_list):
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Machine, Part '
                sql += 'ORDER BY Part ASC, Machine ASC;'

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
                if len(machine_list):
                    sql += 'AND Machine IN (' + machine_list + ') '
                if len(part_list):
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Machine, Part '
                sql += 'ORDER BY Part ASC, Machine ASC;'

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
                if len(machine_list):
                    sql += 'AND Machine IN (' + machine_list + ') '
                if len(part_list):
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Machine, Part '
                sql += 'ORDER BY Part ASC, Machine ASC;'

            cursor = connections['prodrpt-md'].cursor()
            try:
                cursor.execute(sql)
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
    context['title'] = 'Production'

    return render(request, 'prod_query/prod_query.html', context)


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

            if times == '1':  # 10pm - 6am
                shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day-1, 22, 0, 0)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '2':  # 11pm - 7am
                shift_start = datetime(
                    inquiry_date.year, inquiry_date.month, inquiry_date.day-1, 23, 0, 0)
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
        sql += 'AND Machine = ' + machine + ' '
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
        sql += 'AND Machine = ' + machine + ' '
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
        sql += 'AND Machine = ' + machine + ' '
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
