from django.shortcuts import render
from django.http import HttpResponse
import os
import importlib.util

def prodmon_ping(request):
    """
    View to handle prodmon_ping requests.
    Dynamically imports get_db_connection from settings.py, connects to the database,
    and prints debug messages to verify the status.
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
        print("Database connection established successfully.")  # Debugging statement

        # Get a cursor to execute queries
        cursor = connection.cursor()
        print("Cursor obtained successfully.")  # Debugging statement

        # Close the connection
        connection.close()
        print("Database connection closed successfully.")  # Debugging statement

        # Return a success message to the user
        return HttpResponse("Database connection successful. Check the console for details.")

    except Exception as e:
        # Log the error and provide feedback
        print(f"An error occurred: {e}")  # Debugging statement
        return HttpResponse(f"An error occurred: {e}")
