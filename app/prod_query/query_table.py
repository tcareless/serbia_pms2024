import os
import importlib.util
import mysql.connector
from mysql.connector import Error

# Dynamically import `settings.py` from your Django project
def load_django_settings():
    """ Load Django settings.py dynamically to access database connection details. """
    settings_path = os.path.join(os.path.dirname(__file__), '../pms/settings.py')
    
    spec = importlib.util.spec_from_file_location("settings", settings_path)
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    
    return settings

# Load settings
settings = load_django_settings()

# Extract database connection details for Dave's database
DB_HOST = settings.DAVE_HOST
DB_USER = settings.DAVE_USER
DB_PASSWORD = settings.DAVE_PASSWORD
DB_NAME = settings.DAVE_DB

def get_press_changeover_data():
    """
    Connects to the database and retrieves machines (assetnum) with their distinct last 9 digits 
    of 'problem' as part numbers.
    """
    try:
        # Establish database connection
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Query to get distinct assetnum and last 9 digits of problem (part number)
            query = """
                SELECT DISTINCT asset, SUBSTRING(problem, -9) AS part_number
                FROM Press_Changeovers
                WHERE LENGTH(problem) >= 9
                ORDER BY asset, part_number;
            """
            cursor.execute(query)

            # Fetch results
            results = cursor.fetchall()

            # Group results by assetnum
            asset_part_map = {}
            for asset, part_number in results:
                if asset not in asset_part_map:
                    asset_part_map[asset] = set()
                asset_part_map[asset].add(part_number)

            # Print results
            print("\n=== Machine Parts Report ===")
            for asset, part_numbers in asset_part_map.items():
                print(f"\nMachine (AssetNum): {asset}")
                for part in sorted(part_numbers):
                    print(f"  - Part Number: {part}")

            return asset_part_map

    except Error as e:
        print(f"Error: {e}")
        return {}

    finally:
        # Close the database connection
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    get_press_changeover_data()
