from views import *


# This gives you downtime and total produced for a given machine
def get_machine_data(machine, start_date):
    """
    Fetch downtime and production for a single machine.
    
    :param machine: Machine number (string)
    :param start_date: Start date in ISO format (string)
    :return: Tuple (downtime, produced)
    """
    try:
        # Create input for the main function
        machines = [machine]
        input_data = {
            'machines': json.dumps(machines),
            'start_date': start_date,
        }
        request = type('Request', (object,), {'method': 'POST', 'POST': input_data})

        # Call the main function
        response = gfx_downtime_and_produced_view(request)

        # Parse response
        if response.status_code == 200:
            data = json.loads(response.content)
            downtime = next((res['downtime'] for res in data['downtime_results'] if res['machine'] == machine), 0)
            produced = next((res['produced'] for res in data['produced_results'] if res['machine'] == machine), 0)
            return downtime, produced
        else:
            raise ValueError(f"Error from view: {response.content.decode()}")

    except Exception as e:
        raise ValueError(f"Failed to fetch machine data: {e}")
