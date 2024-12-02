

def calculate_downtime(machine, machine_parts, start_timestamp, end_timestamp, downtime_threshold, cursor):
    """
        Calculate the total downtime for a specific machine over a given time period.

        The downtime is calculated based on the intervals between consecutive production timestamps
        that exceed a given threshold. If no production timestamps are present, the entire period is
        considered downtime.

        Parameters:
        - machine (str): The identifier of the machine being analyzed.
        - machine_parts (list): A list of part identifiers associated with the machine.
        - start_timestamp (int): The starting timestamp of the analysis period (epoch time in seconds).
        - end_timestamp (int): The ending timestamp of the analysis period (epoch time in seconds).
        - downtime_threshold (int): The threshold (in minutes) above which an interval is considered downtime.
        - cursor (object): A database cursor for querying production data.

        Returns:
        - int: The total downtime in minutes for the specified machine and time period.
        """
    machine_downtime = 0
    prev_timestamp = None

    if not machine_parts:
        # No parts provided; entire period is downtime
        total_potential_minutes = (end_timestamp - start_timestamp) / 60  # Convert to minutes
        return round(total_potential_minutes)

    # Construct placeholders for the SQL IN clause
    placeholders = ','.join(['%s'] * len(machine_parts))
    query = f"""
        SELECT TimeStamp
        FROM GFxPRoduction
        WHERE Machine = %s AND TimeStamp BETWEEN %s AND %s AND Part IN ({placeholders})
        ORDER BY TimeStamp ASC;
    """
    params = [machine, start_timestamp, end_timestamp] + machine_parts
    cursor.execute(query, params)

    timestamps_fetched = False
    for row in cursor:
        timestamps_fetched = True
        current_timestamp = row[0]
        if prev_timestamp is not None:
            time_delta = (current_timestamp - prev_timestamp) / 60  # Convert to minutes
            minutes_over = max(0, time_delta - downtime_threshold)
            machine_downtime += minutes_over
        prev_timestamp = current_timestamp

    if not timestamps_fetched:
        # No production data; entire period is downtime
        total_potential_minutes = (end_timestamp - start_timestamp) / 60  # Convert to minutes
        return round(total_potential_minutes)

    # Account for the time between the last timestamp and the end of the period
    remaining_time = (end_timestamp - prev_timestamp) / 60
    machine_downtime += remaining_time

    return round(machine_downtime)


def calculate_total_produced(machine, machine_parts, start_timestamp, end_timestamp, cursor):
    """
    Calculate the total number of parts produced by a specific machine over a given time period.

    This function queries a production database to count the number of records for the specified
    machine and parts within the given time range. It iterates over the provided parts and
    sums up the production counts for each part.

    Parameters:
    - machine (str): The identifier of the machine being analyzed.
    - machine_parts (list): A list of part identifiers associated with the machine.
    - start_timestamp (int): The starting timestamp of the analysis period (epoch time in seconds).
    - end_timestamp (int): The ending timestamp of the analysis period (epoch time in seconds).
    - cursor (object): A database cursor for querying production data.

    Returns:
    - int: The total count of parts produced by the machine during the specified time period.
    """
    total_entries = 0

    for part in machine_parts:
        query = """
            SELECT COUNT(*)
            FROM GFxPRoduction
            WHERE Machine = %s AND TimeStamp BETWEEN %s AND %s AND Part = %s;
        """
        cursor.execute(query, (machine, start_timestamp, end_timestamp, part))
        part_total = cursor.fetchone()[0] or 0
        total_entries += part_total

    return total_entries


def calculate_oa_metrics(data):
    """
    Calculate OA, P, A, and Q metrics from the provided data.

    :param data: Dictionary containing input data for calculation
    :return: Dictionary with OA, P, A, Q metrics or raises an exception for invalid input
    """
    try:
        # Extract variables
        total_downtime = int(data.get('totalDowntime', 0))
        total_produced = int(data.get('totalProduced', 0))
        total_target = int(data.get('totalTarget', 0))
        total_potential = int(data.get('totalPotentialMinutes', 0))
        total_scrap = int(data.get('totalScrap', 0))

        # Validate inputs
        if total_target <= 0:
            raise ValueError('Total target must be greater than 0')
        if total_potential <= 0:
            raise ValueError('Total potential must be greater than 0')

        # Calculate P, A, Q
        P = total_produced / total_target
        A = (total_potential - total_downtime) / total_potential
        Q = total_produced / (total_produced + total_scrap) if (total_produced + total_scrap) > 0 else 0

        # Calculate OA
        OA = P * A * Q

        return {'OA': OA, 'P': P, 'A': A, 'Q': Q}

    except KeyError as e:
        raise ValueError(f"Missing key in input data: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid input: {e}")
