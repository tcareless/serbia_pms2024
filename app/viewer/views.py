from django.shortcuts import render
from pylogix import PLC
from datetime import datetime
import humanize
import logging


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================
# This section contains utility functions that are used across different sections.
# ==============================================================================


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PLC connection details
PLC_IP = '10.4.43.7'
PLC_SLOT = 3

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
            logging.error(f"Error reading date time for tag: {tag_prefix}. Responses: {[r.Status for r in responses]}")
            return None

def test_response(resp):
    if resp.Status == 'Success':
        return resp.Value
    else:
        return -1

def readString(tag):
    with PLC() as comm:
        comm.IPAddress = PLC_IP
        comm.ProcessorSlot = PLC_SLOT
        length = comm.Read('{}.LEN'.format(tag))
        if not (length.Status == 'Success'):
            return length
        if not length.Value:
            return None
        ret = comm.Read(tag + '.DATA', length.Value)
        if ret.Status == 'Success':
            return ''.join(chr(i) for i in ret.Value)
        else:
            return ret

def readBoolean(tag):
    with PLC() as comm:
        comm.IPAddress = PLC_IP
        comm.ProcessorSlot = PLC_SLOT
        ret = comm.Read(tag)
        return ret.Value == True

def stationBypassed(station):
    return readBoolean(f'Stn0{station}0_Bypass_Data.Gen[21]')

# ==============================================================================
# RABBITS VIEW
# ==============================================================================
# This section contains all the views and logic related to the rabbits feature.
# ==============================================================================


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




# ==============================================================================
# PRODUCTION VIEW
# ==============================================================================
# This section contains all the views and logic related to the production feature.
# ==============================================================================


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




# ==============================================================================
# BYPASS STATUS VIEW 
# ==============================================================================
# This section contains all the views and logic related to bypass status
# ==============================================================================


# Bypass status view
def bypass_status(request):
    data = []
    for station in range(1, 5):
        bypassed = stationBypassed(station)
        
        checks = []
        for index in range(1, 10):
            checkLabel = readString(f'Stn0{station}0_Bypass_Data.Bypass_ID[{index}]')
            if checkLabel:
                bypassStatus = readBoolean(f'Stn0{station}0_Bypass_Data.Gen[{index}]')
                checks.append({'name': checkLabel, 'status': bypassStatus})
        
        data.append({'bypassed': bypassed, 'checks': checks})

    context = {
        'stations_data': data,
        'stations': range(1, 5),
    }
    return render(request, 'viewer/bypass_status.html', context)



# ==============================================================================
# BYPASS LOG VIEW 
# ==============================================================================
# This section contains all the views and logic related to bypass log
# ==============================================================================

def bypasslog(request):
    log = []
    for station in range(1, 5):
        for entry in range(0, 25):
            time, text = get_bypass_log_entry(station, entry)
            if time and text:
                logentry = (time, station, text)
                log.append(logentry)

    log.sort(key=lambda x: x[0], reverse=True)
    return render(request, 'viewer/bypasslog.html', {'log': log})

def get_bypass_log_entry(station, entry):
    text = readString(
        f'Stn0{station}0_Bypass_Data.Bypass_Logging[{entry}].Bypass_String')
    if not text:
        return (None, None)
    timestamp = get_date_time(
        f'Stn0{station}0_Bypass_Data.Bypass_Logging[{entry}].Date_Time.Actual')
    return (timestamp, text)
