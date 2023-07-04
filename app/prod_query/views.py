from django.shortcuts import render
from django.db import connections
import mysql.connector

from datetime import datetime, timedelta
from .forms import MachineInquiryForm
from .forms import CycleQueryForm
from .forms import DowntimeKeywordForm

from query_tracking.models import record_execution_time

import time
import logging
logger = logging.getLogger('prod-query')    

def downtime_keyword_view(request):
    context = {}
    if request.method == 'GET':
        form = DowntimeKeywordForm()

    if request.method == 'POST':
        form = DowntimeKeywordForm(request.POST)
        if form.is_valid():
            keywords = form.cleaned_data.get('keywords')
            target_date = form.cleaned_data.get('target_date')

            start = []
            end = []
            track = 0
            for i in keywords:
                word = i.strip()
                name = word + "_count"
                if track + 1 != len(keywords):
                    start.append(f'SUM(`problem` like \'%{word}%\') AS {name},\n')
                    end.append(f'{name} > 0 OR ')
                else:
                    start.append(f'SUM(`problem` like \'%{word}%\') AS {name}\n')
                    end.append(f'{name} > 0\n')
                track += 1
            
            sql = (
                f'SELECT DATE(`called4helptime`) as "Date", `assetnum` as "Machine", \n{"".join(start)}'
                f'FROM `pr_downtime1`\n'
                f'WHERE DATE(`called4helptime`) = \'{target_date}\'\n'
                f'GROUP BY DATE(`called4helptime`), `assetnum`\n'
                f'HAVING {"".join(end)}'
                f'ORDER BY DATE(`called4helptime`) DESC, length(`assetnum`), `assetnum` LIMIT 100'
            )

            db_params = {'host': '10.4.1.224',
                        'database': 'prodrptdb',
                        'port': 3306,
                        'user': 'stuser',
                        'password': 'stp383'}
            connection = mysql.connector.connect(**db_params)

            tic = time.time()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(sql)
            res = []
            row = cursor.fetchone()
            while row:
                res.append(row)
                row = cursor.fetchone()
            context['result'] = res

            toc = time.time()
            record_execution_time("cycle_times", sql, toc-tic)
            context['time'] = f'Elapsed: {toc-tic:.3f}'

    context['form'] = form
    context['title'] = 'Downtime Keyword Count'

    return render(request, 'prod_query/downtime_counts.html', context)

def cycle_times(request):
    context = {}
    if request.method == 'GET':
        form = CycleQueryForm()

    if request.method == 'POST':
        form = CycleQueryForm(request.POST)
        if form.is_valid():
            target_date = form.cleaned_data.get('target_date')
            times = form.cleaned_data.get('times')
            machine = form.cleaned_data.get('machine')
            trim = form.cleaned_data.get('trim_percent')

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
                    row = cursor.fetchone()
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

            it = iter(res)
            val = next(it)

            remove = round(count * trim)
            low_trimindex = remove
            high_trimindex = count - remove

            trimsum = 0
            track = 0
            valAdd = 0
            for i in range(high_trimindex):
                if(track >= val[1]):
                    val = next(it)
                    track = 0
                if(i > low_trimindex):
                    valAdd += 1
                    trimsum += val[0]
                track += 1
            trimAve = trimsum / valAdd
            context['trimmed'] = f'{trimAve:.3f}'
            context['excluded'] = f'{trim:.2%}'

            # Sums all cycle times that are DOWNTIME_FACTOR times larger than the trimmed average
            DOWNTIME_FACTOR = 3
            threshold = int(trimAve * DOWNTIME_FACTOR)
            downtime = 0
            microstoppage = 0
            for r in res: 
                if(r[0] > trimAve and r[0] < threshold):
                    microstoppage += (r[0] - trimAve) * r[1]
                if(r[0] > threshold):
                    downtime += r[0] * r[1]
            context['microstoppage'] = f'{microstoppage / 60:.1f}'
            context['downtime'] = f'{downtime / 60:.1f}'
            context['factor'] = DOWNTIME_FACTOR

            toc = time.time()
            record_execution_time("cycle_times", sql, toc-tic)
            context['time'] = f'Elapsed: {toc-tic:.3f}'

            context['result'] = res
            context['machine'] = machine

    context['form'] = form
    context['title'] = 'Cycle Time Query'

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
