

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

    machine_downtime = 0  # Accumulate total downtime here
    prev_timestamp = None  # Store the previous timestamp for interval calculations

    # If no parts are provided, assume the machine was entirely down during the period
    if not machine_parts:
        total_potential_minutes = (end_timestamp - start_timestamp) / 60  # Convert seconds to minutes
        return round(total_potential_minutes)

    # Construct the SQL query to fetch timestamps for the specified machine and parts
    # The IN clause uses placeholders to handle dynamic part filtering safely
    placeholders = ','.join(['%s'] * len(machine_parts))  # Create placeholders for part list
    query = f"""
        SELECT TimeStamp
        FROM GFxPRoduction
        WHERE Machine = %s AND TimeStamp BETWEEN %s AND %s AND Part IN ({placeholders})
        ORDER BY TimeStamp ASC;
    """
    params = [machine, start_timestamp, end_timestamp] + machine_parts  # Combine parameters
    cursor.execute(query, params)  # Execute the query

    # Flag to determine if any timestamps were fetched
    timestamps_fetched = False

    # Iterate over the cursor to process timestamps one at a time
    # This ensures that rows are not loaded into memory all at once
    for row in cursor:
        timestamps_fetched = True
        current_timestamp = row[0]  # Extract the timestamp from the row

        if prev_timestamp is not None:
            time_delta = (current_timestamp - prev_timestamp) / 60  # Convert seconds to minutes
            # Add only the downtime that exceeds the threshold
            minutes_over = max(0, time_delta - downtime_threshold)
            machine_downtime += minutes_over

        # Update the previous timestamp to the current one
        prev_timestamp = current_timestamp

    # If no timestamps were fetched, assume the machine was entirely down during the period
    if not timestamps_fetched:
        total_potential_minutes = (end_timestamp - start_timestamp) / 60  # Convert seconds to minutes
        return round(total_potential_minutes)

    # Handle the time from the last production timestamp to the end of the period
    remaining_time = (end_timestamp - prev_timestamp) / 60  # Convert seconds to minutes
    machine_downtime += remaining_time

    # Return the total calculated downtime in minutes
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
    total_entries = 0  # Initialize total count of produced parts

    # Loop through each part in the provided list of machine parts
    for part in machine_parts:
        # Construct the query to count the number of entries for the current part
        query = """
            SELECT COUNT(*)
            FROM GFxPRoduction
            WHERE Machine = %s AND TimeStamp BETWEEN %s AND %s AND Part = %s;
        """

        # Execute the query with the parameters: machine, timestamps, and current part
        cursor.execute(query, (machine, start_timestamp, end_timestamp, part))

        # Fetch the count for the current part from the query result
        # `fetchone` returns a tuple, and we extract the first value (the count)
        part_total = cursor.fetchone()[0] or 0  # Handle cases where the count might be None

        # Add the count for the current part to the running total
        total_entries += part_total

    # Return the total count of produced parts
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
