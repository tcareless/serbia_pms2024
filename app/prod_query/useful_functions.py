from views import *


def calculate_downtime(machine, machine_parts, start_timestamp, end_timestamp, downtime_threshold, cursor):
    """
    Calculate downtime for a specific machine over a given time period in a memory-efficient manner,
    without altering the original logic.
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
    Calculate the total produced parts for a specific machine over a given time period.

    :param machine: Machine number
    :param machine_parts: List of parts associated with the machine
    :param start_timestamp: Start timestamp for the analysis
    :param end_timestamp: End timestamp for the analysis
    :param cursor: Database cursor for querying production data
    :return: Total produced count
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
