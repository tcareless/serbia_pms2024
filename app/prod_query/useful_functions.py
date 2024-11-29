from views import *


def calculate_downtime(machine, machine_parts, start_timestamp, end_timestamp, downtime_threshold, cursor):
    """
    Calculate downtime for a specific machine over a given time period.

    :param machine: Machine number
    :param machine_parts: List of parts associated with the machine
    :param start_timestamp: Start timestamp for the analysis
    :param end_timestamp: End timestamp for the analysis
    :param downtime_threshold: Threshold in minutes for downtime calculation
    :param cursor: Database cursor for querying production data
    :return: Downtime in minutes
    """
    machine_downtime = 0
    all_timestamps = []

    # Collect all timestamps for this machine across all parts
    for part in machine_parts:
        query = """
            SELECT TimeStamp
            FROM GFxPRoduction
            WHERE Machine = %s AND TimeStamp BETWEEN %s AND %s AND Part = %s
            ORDER BY TimeStamp ASC;
        """
        cursor.execute(query, (machine, start_timestamp, end_timestamp, part))
        timestamps = [row[0] for row in cursor.fetchall()]
        all_timestamps.extend(timestamps)

    # Sort all timestamps
    all_timestamps.sort()

    # Process the sorted timestamps
    prev_timestamp = None
    for current_timestamp in all_timestamps:
        if prev_timestamp is not None:
            time_delta = (current_timestamp - prev_timestamp) / 60  # Convert to minutes
            minutes_over = max(0, time_delta - downtime_threshold)
            machine_downtime += minutes_over
        prev_timestamp = current_timestamp

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
