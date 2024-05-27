from django.shortcuts import render
from pylogix import PLC
from datetime import datetime
import humanize

# PLC connection details
PLC_IP = '10.4.43.7'
PLC_SLOT = 3

# Function to get the date and time from the PLC tags
def get_date_time(tag_prefix):
    with PLC() as comm:
        comm.IPAddress = PLC_IP
        comm.ProcessorSlot = PLC_SLOT
        tag_list = [
            f'{tag_prefix}.Year', f'{tag_prefix}.Month', f'{tag_prefix}.Day',
            f'{tag_prefix}.Hour', f'{tag_prefix}.Min', f'{tag_prefix}.Sec'
        ]
        responses = comm.Read(tag_list)
        x = list(map(test_response, responses))
        if -1 not in x:
            return datetime(*x)
        else:
            print(f"Error reading date time for tag: {tag_prefix}. Responses: {[r.Status for r in responses]}")
            return None

# Helper function to test the response of the PLC read operation
def test_response(resp):
    if resp.Status == 'Success':
        return resp.Value
    else:
        return -1

# Function to get the bypass status and datetime for a rabbit mode
def get_rabbit_bypass(prefix):
    with PLC() as comm:
        comm.IPAddress = PLC_IP
        comm.ProcessorSlot = PLC_SLOT
        res = comm.Read(prefix + '.Bypassed')
        if res.Status == 'Success':
            if res.Value:
                dt = get_date_time(prefix + '.Date_Time')
                print(f"Bypass status for {prefix}: {res.Value}, Date Time: {dt}")
                return res.Value, dt
            else:
                return res.Value, None
        else:
            print(f"Error reading bypass status for {prefix}. Status: {res.Status}")
            return -1, None

# View to display the rabbit status for different stations
def rabbits_view(request):
    data = []

    # Retrieve data for Station 010 (using dummy data for last_ran as Stn010 is not working)
    last_ran = get_date_time('Program:Stn020.Stn020_Rabbit_Mode.Last_Ran')
    stn10 = [
        (last_ran, humanize.naturaltime(last_ran)),
        [
            {'name': '9641-1', 'status': get_rabbit_bypass('Stn010_Rabbit_Mode.Override[1]')},
            {'name': '9641-2', 'status': get_rabbit_bypass('Stn010_Rabbit_Mode.Override[2]')},
            {'name': '4865-1', 'status': get_rabbit_bypass('Stn010_Rabbit_Mode.Override[3]')},
            {'name': '4865-2', 'status': get_rabbit_bypass('Stn010_Rabbit_Mode.Override[4]')}
        ]
    ]

    # Retrieve data for Station 020
    last_ran = get_date_time('Program:Stn020.Stn020_Rabbit_Mode.Last_Ran')
    stn20 = [
        (last_ran, humanize.naturaltime(last_ran)),
        [
            {'name': '9641-1', 'status': get_rabbit_bypass('Program:Stn020.Stn020_Rabbit_Mode.Override[1]')},
            {'name': '9641-2', 'status': get_rabbit_bypass('Program:Stn020.Stn020_Rabbit_Mode.Override[2]')},
            {'name': '9641-3', 'status': get_rabbit_bypass('Program:Stn020.Stn020_Rabbit_Mode.Override[3]')},
            {'name': '4865-1', 'status': get_rabbit_bypass('Program:Stn020.Stn020_Rabbit_Mode.Override[4]')},
            {'name': '4865-2', 'status': get_rabbit_bypass('Program:Stn020.Stn020_Rabbit_Mode.Override[5]')},
            {'name': '4865-3', 'status': get_rabbit_bypass('Program:Stn020.Stn020_Rabbit_Mode.Override[6]')}
        ]
    ]

    # Retrieve data for Station 030
    last_ran = get_date_time('Program:Stn030.Stn030_Rabbit_Mode.Last_Ran')
    stn30 = [
        (last_ran, humanize.naturaltime(last_ran)),
        [
            {'name': '9641-1', 'status': get_rabbit_bypass('Program:Stn030.Stn030_Rabbit_Mode.Override[1]')},
            {'name': '4865-1', 'status': get_rabbit_bypass('Program:Stn030.Stn030_Rabbit_Mode.Override[2]')}
        ]
    ]

    # Retrieve data for Station 040
    last_ran = get_date_time('Program:Stn040.Stn040_Rabbit_Mode.Last_Ran')
    stn40 = [
        (last_ran, humanize.naturaltime(last_ran)),
        [
            {'name': '9641-1', 'status': get_rabbit_bypass('Program:Stn040.Stn040_Rabbit_Mode.Override[1]')},
            {'name': '9641-2', 'status': get_rabbit_bypass('Program:Stn040.Stn040_Rabbit_Mode.Override[2]')},
            {'name': '4865-1', 'status': get_rabbit_bypass('Program:Stn040.Stn040_Rabbit_Mode.Override[3]')},
            {'name': '4865-2', 'status': get_rabbit_bypass('Program:Stn040.Stn040_Rabbit_Mode.Override[4]')}
        ]
    ]

    # Combine all station data
    data = [stn10, stn20, stn30, stn40]

    # Render the data to the template
    return render(request, 'viewer/rabbits.html', {'data': data})



def production(request):
    PLC_IP = '10.4.43.7'
    PLC_SLOT = 3
    
    def get_production(tag_prefix):
        with PLC() as comm:
            comm.IPAddress = PLC_IP
            comm.ProcessorSlot = PLC_SLOT
            hourly = []
            totals = []
            for shift in range(3):
                shift_counts = []
                for hour in range(8):
                    tag_name = f"{tag_prefix}Shift_{shift+1}_Hour_{hour+1}_Total"
                    ret = comm.Read(tag_name)
                    shift_counts.append(ret.Value if ret.Status == 'Success' else 'Error')
                hourly.append(shift_counts)
                tag_name = f"{tag_prefix}Shift_{shift+1}_Total"
                ret = comm.Read(tag_name)
                totals.append(ret.Value if ret.Status == 'Success' else 'Error')
            return (hourly, totals)

    tag_prefix_today = 'Program:Production.ProductionData.HourlyParts.Total.'
    today_hourly, today_totals = get_production(tag_prefix_today)
    tag_prefix_prev = 'Program:Production.ProductionData.PrevDayHourlyParts[0].Total.'
    prev_hourly, prev_totals = get_production(tag_prefix_prev)

    context = {
        'today_totals': today_totals,
        'today_hourly': today_hourly,
        'prev_totals': prev_totals,
        'prev_hourly': prev_hourly
    }

    return render(request, 'viewer/production.html', context)