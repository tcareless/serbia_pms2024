from django.shortcuts import render
from pylogix import PLC
from datetime import datetime
import humanize

PLC_IP = '10.4.45.106'
PLC_SLOT = 3

def get_date_time(tag_prefix):
    with PLC() as comm:
        comm.IPAddress = PLC_IP
        comm.ProcessorSlot = PLC_SLOT
        tag_list = [
            tag_prefix + '.Year', tag_prefix + '.Month', tag_prefix + '.Day',
            tag_prefix + '.Hour', tag_prefix + '.Min', tag_prefix + '.Sec'
        ]
        x = list(map(test_response, comm.Read(tag_list)))
        if -1 not in x:
            return datetime(*x)

def test_response(resp):
    if resp.Status == 'Success':
        return resp.Value
    else:
        return -1

def get_rabbit_bypass(prefix):
    with PLC() as comm:
        comm.IPAddress = PLC_IP
        comm.ProcessorSlot = PLC_SLOT
        res = comm.Read(prefix + '.Bypassed')
        if res.Status == 'Success':
            if res.Value:
                return res.Value, get_date_time(prefix + '.Date_Time')
            else:
                return res.Value, None
        else:
            return -1, None

def rabbits_view(request):
    data = []
    for station in ['010', '020', '030', '040']:
        last_ran = get_date_time(f'Program:Stn{station}.Stn{station}_Rabbit_Mode.Last_Ran')
        station_data = [
            (last_ran, humanize.naturaltime(last_ran)),
            [
                {'name': '9641-1', 'status': get_rabbit_bypass(f'Program:Stn{station}.Stn{station}_Rabbit_Mode.Override[1]')},
                {'name': '9641-2', 'status': get_rabbit_bypass(f'Program:Stn{station}.Stn{station}_Rabbit_Mode.Override[2]')},
                # Add more rabbits as needed
            ]
        ]
        data.append(station_data)
    
    return render(request, 'viewer/rabbits.html', {'data': data})
