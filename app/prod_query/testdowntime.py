import os
import sys
import django
from django.db import connections
from useful_functions import calculate_downtime  # Import the function to test

# Hardcode the path to settings.py
sys.path.append('/home/tcareless/pms2024/app/')  # Add the base path to the project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pms.settings")
django.setup()  # Initialize Django

def test_calculate_downtime():
    # Test parameters
    machine = "1532"
    machine_parts = ["50-9341"]
    start_timestamp = 1732507200  # Example epoch start time
    end_timestamp = 1732939200  # Example epoch end time
    downtime_threshold = 5  # Threshold in minutes

    # Using Django's database connection
    with connections['prodrpt-md'].cursor() as cursor:
        # Call the calculate_downtime function with the test parameters
        downtime = calculate_downtime(
            machine,
            cursor,
            start_timestamp,
            end_timestamp,
            machine_parts=machine_parts,
        )
        
        # Output the result
        print(f"Total downtime for machine {machine} from {start_timestamp} to {end_timestamp}: {downtime} minutes")

if __name__ == "__main__":
    test_calculate_downtime()
