import os
import importlib.util
from datetime import datetime, timedelta
from django.shortcuts import render
import pytz


def get_stale_ping_entries():
    """
    Fetch assets from the prodmon_ping table that haven't pinged for over 15 minutes.
    """
    try:
        # Define the relative path to settings.py
        settings_path = os.path.join(
            os.path.dirname(__file__), '../../pms/settings.py'
        )

        # Dynamically import settings.py
        spec = importlib.util.spec_from_file_location("settings", settings_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)

        # Access get_db_connection from settings
        get_db_connection = settings.get_db_connection

        # Establish database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # Calculate the threshold time (15 minutes ago)
        threshold_time = datetime.utcnow() - timedelta(minutes=15)

        # Query to find all entries
        query = """
            SELECT Name, Timestamp
            FROM prodmon_ping
            ORDER BY Timestamp DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # Close the connection
        cursor.close()
        connection.close()

        # Process results: filter entries older than 15 minutes
        est = pytz.timezone('US/Eastern')  # Define EST timezone
        stale_entries = []
        for row in results:
            asset_name = row[0]
            last_ping_time = datetime.utcfromtimestamp(row[1]).replace(tzinfo=pytz.utc).astimezone(est)
            time_since_ping = datetime.now(pytz.utc).astimezone(est) - last_ping_time

            # Only include entries older than 15 minutes
            if time_since_ping > timedelta(minutes=15):
                stale_entries.append({
                    "asset_name": asset_name,
                    "last_ping_time": last_ping_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "time_since_ping": str(time_since_ping).split('.')[0],  # Human-readable format without microseconds
                })

        return stale_entries

    except Exception as e:
        print(f"An error occurred while fetching stale ping entries: {e}")
        return []

def prodmon_ping(request):
    """
    View to display assets that haven't pinged for over 15 minutes.
    Queries the database using a helper function and renders the data in a template.
    """
    try:
        # Fetch stale ping entries
        stale_entries = get_stale_ping_entries()

        # If no stale entries, set an empty message
        if not stale_entries:
            message = "All assets have pinged within the last 15 minutes."
        else:
            message = None

        # Render the template with the data
        return render(request, 'prodmon_ping.html', {
            'stale_entries': stale_entries,
            'message': message
        })

    except Exception as e:
        print(f"An error occurred in prodmon_ping view: {e}")
        return render(request, 'prodmon_ping.html', {
            'stale_entries': [],
            'message': f"An error occurred: {e}"
        })