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
    """
    Retrieve the date and time from the PLC for a given tag prefix.

    Args:
        tag_prefix (str): The prefix for the PLC tags representing date and time.

    Returns:
        datetime: The date and time retrieved from the PLC.
    """
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
    """
    Check the response status and return the value if successful, otherwise return -1.

    Args:
        resp (Response): The response object from the PLC communication.

    Returns:
        int: The value retrieved from the PLC response, or -1 if unsuccessful.
    """
    if resp.Status == 'Success':
        return resp.Value
    else:
        return -1

def readString(tag):
    """
    Read a string value from the PLC for the given tag.

    Args:
        tag (str): The tag representing the string value in the PLC.

    Returns:
        str: The string value retrieved from the PLC.
    """
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
    """
    Read a boolean value from the PLC for the given tag.

    Args:
        tag (str): The tag representing the boolean value in the PLC.

    Returns:
        bool: The boolean value retrieved from the PLC.
    """
    with PLC() as comm:
        comm.IPAddress = PLC_IP
        comm.ProcessorSlot = PLC_SLOT
        ret = comm.Read(tag)
        return ret.Value == True

def stationBypassed(station):
    """
    Check if a station is bypassed based on the boolean value read from the PLC.

    Args:
        station (int): The station number to check for bypass status.

    Returns:
        bool: True if the station is bypassed, False otherwise.
    """
    return readBoolean(f'Stn0{station}0_Bypass_Data.Gen[21]')


# ==============================================================================
# RABBITS VIEW
# ==============================================================================
# This section contains all the views and logic related to the rabbits feature.
# ==============================================================================

# Function to retrieve the bypass status and datetime for a rabbit mode
def get_rabbit_bypass(prefix):
    """
    Retrieve the bypass status and datetime for a rabbit mode from the PLC.

    Args:
        prefix (str): The prefix representing the rabbit mode in the PLC.

    Returns:
        tuple: A tuple containing the bypass status and datetime retrieved from the PLC.
    """
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
    """
    Retrieve rabbit status data for different stations from the PLC and render it to the template.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The HTTP response containing the rendered template.
    """
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
    """
    View function to retrieve production data from the PLC and render it to the 'production.html' template.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The HTTP response containing the rendered template.
    """
    # PLC connection details
    PLC_IP = '10.4.43.7'
    PLC_SLOT = 3
    
    def get_production(tag_prefix):
        """
        Retrieve production data for a given tag prefix from the PLC.

        Args:
            tag_prefix (str): The prefix for the production data tag in the PLC.

        Returns:
            tuple: A tuple containing hourly production counts and total production counts.
        """
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

    # Retrieve today's production data
    tag_prefix_today = 'Program:Production.ProductionData.HourlyParts.Total.'
    today_hourly, today_totals = get_production(tag_prefix_today)
    
    # Retrieve previous day's production data
    tag_prefix_prev = 'Program:Production.ProductionData.PrevDayHourlyParts[0].Total.'
    prev_hourly, prev_totals = get_production(tag_prefix_prev)

    # Context for rendering the template
    context = {
        'today_totals': today_totals,
        'today_hourly': today_hourly,
        'prev_totals': prev_totals,
        'prev_hourly': prev_hourly
    }

    # Render the data to the 'production.html' template
    return render(request, 'viewer/production.html', context)





# ==============================================================================
# BYPASS STATUS VIEW 
# ==============================================================================
# This section contains all the views and logic related to bypass status
# ==============================================================================


def bypass_status(request):
    """
    View function to retrieve bypass status data from the PLC and render it to the 'bypass_status.html' template.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The HTTP response containing the rendered template.
    """
    data = []
    for station in range(1, 5):
        # Retrieve bypass status for each station
        bypassed = stationBypassed(station)
        
        # Retrieve bypass checks for each station
        checks = []
        for index in range(1, 10):
            checkLabel = readString(f'Stn0{station}0_Bypass_Data.Bypass_ID[{index}]')
            if checkLabel:
                bypassStatus = readBoolean(f'Stn0{station}0_Bypass_Data.Gen[{index}]')
                checks.append({'name': checkLabel, 'status': bypassStatus})
        
        # Append bypass status and checks to the data list
        data.append({'bypassed': bypassed, 'checks': checks})

    # Context for rendering the template
    context = {
        'stations_data': data,
        'stations': range(1, 5),
    }
    
    # Render the data to the 'bypass_status.html' template
    return render(request, 'viewer/bypass_status.html', context)



# ==============================================================================
# BYPASS LOG VIEW 
# ==============================================================================
# This section contains all the views and logic related to bypass log
# ==============================================================================

def bypasslog(request):
    """
    View function to retrieve bypass log data from the PLC and render it to the 'bypasslog.html' template.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The HTTP response containing the rendered template.
    """
    log = []
    for station in range(1, 5):
        for entry in range(0, 25):
            # Retrieve bypass log entry for each station and entry
            time, text = get_bypass_log_entry(station, entry)
            if time and text:
                # Append valid log entries to the log list
                logentry = (time, station, text)
                log.append(logentry)

    # Sort the log entries by timestamp in descending order
    log.sort(key=lambda x: x[0], reverse=True)
    
    # Context for rendering the template
    context = {'log': log}
    
    # Render the data to the 'bypasslog.html' template
    return render(request, 'viewer/bypasslog.html', context)

def get_bypass_log_entry(station, entry):
    """
    Function to retrieve a single bypass log entry from the PLC.

    Args:
        station: The station number.
        entry: The entry number within the bypass log.

    Returns:
        tuple: A tuple containing the timestamp and text of the bypass log entry.
    """
    # Retrieve bypass log text for the specified station and entry
    text = readString(f'Stn0{station}0_Bypass_Data.Bypass_Logging[{entry}].Bypass_String')
    if not text:
        return (None, None)
    # Retrieve timestamp for the bypass log entry
    timestamp = get_date_time(f'Stn0{station}0_Bypass_Data.Bypass_Logging[{entry}].Date_Time.Actual')
    return (timestamp, text)
