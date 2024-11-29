import os
import django
import sys

from datetime import datetime, timedelta
from django.db import connections

sys.path.append('/home/tcareless/pms2024/app')  # Path to your Django project root directory


# Set up Django environment to access settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms.settings') 
django.setup()

# Downtime threshold per machine (in minutes)
MACHINE_THRESHOLDS = {
    "1704R": 5, 
    "616": 5,
}

# Define machine-specific part numbers
MACHINE_PARTS = {
    "1704R": ["50-0450", "50-8670"],  # Parts for machine 1703R
    "616": ["50-0450", "50-8670"],  # Parts for machine 1703R
}

# List of machines to test
TEST_MACHINES = ["616"]  # Update with alphanumeric machines to test


def calculate_downtime(machine, parts, start_timestamp, end_timestamp, downtime_threshold, cursor):
    machine_downtime = 0
    all_timestamps = []

    for part in parts:
        query = """
            SELECT TimeStamp
            FROM GFxPRoduction
            WHERE Machine = %s AND TimeStamp BETWEEN %s AND %s AND Part = %s
            ORDER BY TimeStamp ASC;
        """
        cursor.execute(query, (machine, start_timestamp, end_timestamp, part))
        timestamps = [row[0] for row in cursor.fetchall()]
        # Convert timestamps to datetime objects
        all_timestamps.extend([datetime.fromtimestamp(ts) for ts in timestamps])

    all_timestamps.sort()

    if not all_timestamps:
        total_potential_minutes = (end_timestamp - start_timestamp) / 60
        return total_potential_minutes, []

    deltas = []
    prev_timestamp = None

    for current_timestamp in all_timestamps:
        if prev_timestamp is not None:
            time_delta = (current_timestamp - prev_timestamp).total_seconds() / 60  # Convert to minutes
            over_threshold = max(0, time_delta - downtime_threshold)
            if over_threshold > 0:  # Only include events exceeding the threshold
                deltas.append({'part': part, 'delta': time_delta, 'over_threshold': over_threshold})
            machine_downtime += over_threshold
        prev_timestamp = current_timestamp

    # Handle the remaining time after the last timestamp
    if prev_timestamp:
        remaining_time = (datetime.fromtimestamp(end_timestamp) - prev_timestamp).total_seconds() / 60
        over_threshold = max(0, remaining_time - downtime_threshold)
        if over_threshold > 0:
            deltas.append({'part': 'Remaining', 'delta': remaining_time, 'over_threshold': over_threshold})
        machine_downtime += over_threshold

    return machine_downtime, deltas

def main():
    # Define the specific test period
    start_date = datetime(2024, 11, 17, 23, 0)  # November 17, 2024, 23:00
    end_date = datetime(2024, 11, 22, 23, 0)    # November 22, 2024, 23:00
    start_timestamp = start_date.timestamp()
    end_timestamp = end_date.timestamp()

    # Connect to the database via Django's connection
    with connections['prodrpt-md'].cursor() as cursor:
        for machine in TEST_MACHINES:
            print(f"Processing Machine {machine}...\n")
            downtime_threshold = MACHINE_THRESHOLDS.get(machine, 0)

            # Retrieve parts for the current machine
            parts = MACHINE_PARTS.get(machine, [])
            if not parts:
                print(f"No parts defined for machine {machine}. Skipping...\n")
                continue

            # Calculate downtime
            machine_downtime, deltas = calculate_downtime(
                machine, parts, start_timestamp, end_timestamp, downtime_threshold, cursor
            )

            # Print results
            print(f"Machine {machine} Downtime Summary:")
            print(f"{'Part':<15}{'Delta (min)':<15}{'Over Threshold':<15}")
            for delta in deltas:
                print(f"{delta['part']:<15}{delta['delta']:<15.2f}{delta['over_threshold']:<15.2f}")

            print(f"\nTotal Downtime for Machine {machine}: {machine_downtime:.2f} minutes\n")
            print("-" * 50)

if __name__ == "__main__":
    main()