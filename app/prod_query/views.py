from django.shortcuts import render
from django.db import connections

from datetime import datetime, timedelta
from .forms import MachineInquiryForm

import time
import logging
logger = logging.getLogger('prod-query')


def prod_query(request):
    context = {}
    if request.method == 'GET':
        form = MachineInquiryForm()
        form.fields['times'].choices.append((9, '1am - 1am'))
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
                machine_list += f'"{machine.strip()}", '
            machine_list = machine_list[:-2]

            parts = form.cleaned_data.get('parts')

            part_list = ''
            for part in parts:
                part_list += f'"{part.strip()}", '
            part_list = part_list[:-2]

            if times == '1': # 10pm - 6am
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day-1, 22,0,0)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '2': # 11pm - 7am
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day-1, 23,0,0)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '3': # 6am - 2pm
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day, 6,0,0)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '4': # 7am - 3pm
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day, 7,0,0)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '5': # 2pm - 10pm
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day, 14,0,0)
                shift_end = shift_start + timedelta(hours=8)
            elif times == '6': # 3pm - 11pm
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day, 15,0,0)
                shift_end = shift_start + timedelta(hours=8)

            elif times == '7': # 6am - 6am
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day, 6,0,0)
                shift_end = shift_start + timedelta(days=1)
            elif times == '8':  # 7am - 7am
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day, 7,0,0)
                shift_end = shift_start + timedelta(days=1)
            
            elif times == '9':  # 11pm to 11pm week
                days_past_sunday = inquiry_date.isoweekday() % 7
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day, 22,0,0)-timedelta(days=days_past_sunday)
                shift_end = shift_start + timedelta(days=7)
            elif times == '10':  # 10pm to 10pmn week
                days_past_sunday = inquiry_date.isoweekday() % 7
                shift_start = datetime(inquiry_date.year, inquiry_date.month, inquiry_date.day, 23,0,0)-timedelta(days=days_past_sunday)
                shift_end = shift_start + timedelta(days=7)



            shift_start_ts = datetime.timestamp(shift_start)

            if int(times) <= 6 :  # 8 hour query
                sql =  'SELECT Machine, Part, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp <= ' + str(shift_start_ts + 3600) + ' THEN 1 ELSE 0 END) as hour1, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 3600) + ' AND TimeStamp < ' + str(shift_start_ts + 7200) + ' THEN 1 ELSE 0 END) as hour2, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 7200) + ' AND TimeStamp < ' + str(shift_start_ts + 10800) + ' THEN 1 ELSE 0 END) as hour3, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 10800) + ' AND TimeStamp < ' + str(shift_start_ts + 14400) + ' THEN 1 ELSE 0 END) as hour4, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 14400) + ' AND TimeStamp < ' + str(shift_start_ts + 18000) + ' THEN 1 ELSE 0 END) as hour5, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 18000) + ' AND TimeStamp < ' + str(shift_start_ts + 21600) + ' THEN 1 ELSE 0 END) as hour6, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 21600) + ' AND TimeStamp < ' + str(shift_start_ts + 25200) + ' THEN 1 ELSE 0 END) as hour7, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 25200) + ' THEN 1 ELSE 0 END) AS hour8 '
                sql += 'FROM GFxPRoduction '
                sql += 'WHERE TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp < ' + str(shift_start_ts + 28800) + ' '
                if len(machine_list) :
                    sql += 'AND Machine IN (' + machine_list + ') '
                if len(part_list) :
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Machine, Part '
                sql += 'ORDER BY Part ASC, Machine ASC;'

            elif int(times) <= 8:  # 24 hour by shift query
                sql =  'SELECT Machine, Part, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp <= ' + str(shift_start_ts + 28800) + ' THEN 1 ELSE 0 END) as shift1, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 28800) + ' AND TimeStamp < ' + str(shift_start_ts + 57600) + ' THEN 1 ELSE 0 END) as shift2, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 57600) + ' THEN 1 ELSE 0 END) AS shift3 '
                sql += 'FROM GFxPRoduction '
                sql += 'WHERE TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp < ' + str(shift_start_ts + 86400) + ' '
                if len(machine_list) :
                    sql += 'AND Machine IN (' + machine_list + ') '
                if len(part_list) :
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Machine, Part '
                sql += 'ORDER BY Part ASC, Machine ASC;'
            
            else: # week at a time query
                sql =  'SELECT Machine, Part, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp <= ' + str(shift_start_ts + 86400) + ' THEN 1 ELSE 0 END) as mon, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 86400) + ' AND TimeStamp < ' + str(shift_start_ts + 172800) + ' THEN 1 ELSE 0 END) as tue, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 172800) + ' AND TimeStamp < ' + str(shift_start_ts + 259200) + ' THEN 1 ELSE 0 END) as wed, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 259200) + ' AND TimeStamp < ' + str(shift_start_ts + 345600) + ' THEN 1 ELSE 0 END) as thur, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 345600) + ' AND TimeStamp < ' + str(shift_start_ts + 432000) + ' THEN 1 ELSE 0 END) as fri, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 432000) + ' AND TimeStamp < ' + str(shift_start_ts + 518400) + ' THEN 1 ELSE 0 END) as sat, '
                sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start_ts + 518400) + ' THEN 1 ELSE 0 END) AS sun '
                sql += 'FROM GFxPRoduction '
                sql += 'WHERE TimeStamp >= ' + str(shift_start_ts) + ' AND TimeStamp < ' + str(shift_start_ts + 604800) + ' '
                if len(machine_list) :
                    sql += 'AND Machine IN (' + machine_list + ') '
                if len(part_list) :
                    sql += 'AND Part IN (' + part_list + ') '
                sql += 'GROUP BY Machine, Part '
                sql += 'ORDER BY Part ASC, Machine ASC;'


            cursor = connections['prodrpt-md'].cursor()
            try:
                cursor.execute(sql)
                result = cursor.fetchall()
                for row in result:
                    row = list(row)
                    row.append(sum(row[2:]))
                    results.append(row)

            except Exception as e:
                print("Oops!", e, "occurred.")
            finally:
                cursor.close()

            context['production'] = results
            context['start'] = shift_start
            context['end'] = shift_end
            context['times'] = int(times)

            toc = time.time()
            logger.info(sql)
            logger.info(f'[{toc-tic:.3f}] machines="{machines}" parts="{parts}" times="{times}" date="{inquiry_date}" {datetime.isoformat(shift_start)} {shift_start_ts:.0f}')


    context['form'] = form
        
    # return render(request, 'prod_query/machine_inquiry.html', context)
    return render(request, 'prod_query/test.html', context)
