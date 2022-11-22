import pdb


from django.shortcuts import render
from django.db import connections
from django.utils import timezone
import zoneinfo

from datetime import datetime
import time
from prod_query.forms import ShiftLineForm


# from trakberry/trakberry/views_mod2.py
# Calculate Unix Shift Start times and return information
def stamp_shift_start(request):
    stamp=int(time.time())
    tm = time.localtime(stamp)
    print(stamp,':',tm)
    hour1 = tm[3]
    t=int(time.time())
    tm = time.localtime(t)
    shift_start = -2
    current_shift = 3
    if tm[3]<22 and tm[3]>=14:
        shift_start = 14
    elif tm[3]<14 and tm[3]>=6:
        shift_start = 6
    cur_hour = tm[3]
    if cur_hour == 22:
        cur_hour = -1

    # Unix Time Stamp for start of shift Area 1
    u = t - (((cur_hour-shift_start)*60*60)+(tm[4]*60)+tm[5])

    # Amount of seconds run so far on the shift
    shift_time = t-u

    # Amount of seconds left on the shift to run
    shift_left = 28800 - shift_time

    # Unix Time Stamp for the end of the shift
    shift_end = t + shift_left

    print(u)
    return u,shift_time,shift_left,shift_end


# from https://github.com/DaveClark-Stackpole/trakberry/blob/e9fa660e2cdd5ef4d730e0d00d888ad80311cacc/trakberry/views_db.py#L59# from https://github.com/DaveClark-Stackpole/trakberry/blob/e9fa660e2cdd5ef4d730e0d00d888ad80311cacc/trakber$
# import MySQLdb

data =[
       {'op': 'op10',
        'wip': 200,
        'machines': [{'asset': '1501', 'target_cycle': 73},
                     {'asset': '1502', 'target_cycle': 63},],
       },
       {'op': 'op20',
        'wip': 42,
        'machines': [{'asset': '1503', 'target_cycle': 42},
                     {'asset': '1504', 'target_cycle': 39},
                     {'asset': '1504', 'target_cycle': 41},],
       }]

def test(request):
    cursor = connections['prodrpt-md'].cursor()
    sql = 'SHOW TABLES;'
    cursor.execute(sql)
    context = list(cursor.fetchall())
    return render(request, 'pms/test.html', {'results': context})

def uplift_rar(request):
    
    cursor = connections['prodrpt-md'].cursor()
    print('cursor=', cursor)

    shift_start, elapsed, remaining, shift_end = stamp_shift_start(request)
    print('shift_start=', shift_start)

    sql =  'SELECT Machine, '
    sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start) + ' AND TimeStamp <= ' + str(shift_start + 3600) + ' THEN 1 ELSE 0 END) as hour1, '
    sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start + 3600) + ' AND TimeStamp < ' + str(shift_start + 7200) + ' THEN 1 ELSE 0 END) as hour2, '
    sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start + 7200) + ' AND TimeStamp < ' + str(shift_start + 10800) + ' THEN 1 ELSE 0 END) as hour3, '
    sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start + 10800) + ' AND TimeStamp < ' + str(shift_start + 14400) + ' THEN 1 ELSE 0 END) as hour4, '
    sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start + 14400) + ' AND TimeStamp < ' + str(shift_start + 18000) + ' THEN 1 ELSE 0 END) as hour5, '
    sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start + 18000) + ' AND TimeStamp < ' + str(shift_start + 21600) + ' THEN 1 ELSE 0 END) as hour6, '
    sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start + 21600) + ' AND TimeStamp < ' + str(shift_start + 25200) + ' THEN 1 ELSE 0 END) as hour7, '
    sql += 'SUM(CASE WHEN TimeStamp >= ' + str(shift_start + 25200) + ' THEN 1 ELSE 0 END) AS hour8 '
    sql += 'FROM GFxPRoduction '
    sql += 'WHERE TimeStamp >= ' + str(shift_start) + ' AND TimeStamp < ' + str(shift_start + 28800) + ' '
    sql += 'AND Machine IN ("1546","1548","1549L","1549R","1552") '
    sql += 'GROUP BY Machine '
    sql += 'ORDER BY Machine ASC;'


    cursor.execute(sql)
    query_result = list(cursor.fetchall())

    results = []

    if query_result:
        for machine in query_result:
            results.append(machine)

    shift_date_time = datetime.datetime.fromtimestamp(shift_start)
    print(shift_date_time)

    data = {'production': results,
            'start': shift_date_time,
           }

    return render(request,'rar.html',{'data': data})







def shift_line(request):
    # timezone.activate('America/Toronto')
    if request.method == 'GET':
        form = ShiftLineForm()

    if request.method == 'POST':
        print('got post')
        form = ShiftLineForm(request.POST)

        if form.is_valid():
            print('form valid')
            line = form.cleaned_data.get('line')

            shift_start = curent_shift_start()

            sql = ("SELECT COUNT(*) from `GFxPRoduction`"
                  "WHERE timestamp > %s "
                  "AND timestamp < %s "
                  "AND Machine = %s "
                  "AND Part = %s")
            machine = '1723'
            part = '50-8670'

            print('running')
            cursor = connections['prodrpt-md'].cursor()
            for hour in range(8):
                start = int(shift_start.replace(hour=shift_start.hour+hour).timestamp())
                end = int(start + 60*60)
                try:
                    cursor.execute(sql, [start, end, machine, part])
                    row = cursor.fetchone()
                    print(hour, start, end)
                except Exception as e:
                    print("Oops!", e, "occurred.")
                finally:
                    cursor.close()

    context = {
        'form': form,
    }
 

    return render(request, 'prod_query/prod_query.html', context)


def curent_shift_start():
    now = timezone.now().replace(minute=0, second=0, microsecond=0)
    now = timezone.localtime(now, zoneinfo.ZoneInfo('America/Toronto'))
    shift_hour = int((now.hour+1)/8)*8-1
    shift_start = now.replace(hour=shift_hour)
    return shift_start
    
