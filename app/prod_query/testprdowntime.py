from useful_functions import fetch_downtime_entries
from datetime import datetime

def test_fetch_downtime_entries():
    """
    Test function for `fetch_downtime_entries`.
    Calls the function with test inputs and prints the results in a human-readable format.
    """
    # Define the test variables
    assetnum = "1703"  # Change to test different asset numbers
    called4helptime = "2024-10-21T00:00:00"  # Change to test different start times
    completedtime = "2024-12-03T23:59:59"  # Change to test different end times

    try:
        # Call the function
        results = fetch_downtime_entries(assetnum, called4helptime, completedtime)

        # Print the results in a readable format
        if not results:
            print("No downtime entries found.")
            return

        print("Downtime Entries:")
        print("=" * 50)
        for row in results:
            problem = row[0] if len(row) > 0 else "Unknown Problem"
            called_for_help = row[1] if len(row) > 1 else "Unknown Called-for-Help Time"
            completed = row[2] if len(row) > 2 else "Unknown Completed Time"

            # Ensure timestamps are strings and convert to human-readable format if possible
            if not isinstance(called_for_help, str):
                called_for_help = str(called_for_help)
            if not isinstance(completed, str):
                completed = str(completed)

            try:
                called_for_help = datetime.fromisoformat(called_for_help).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass

            try:
                completed = datetime.fromisoformat(completed).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass

            print(f"Problem: {problem}")
            print(f"Called For Help: {called_for_help}")
            print(f"Completed Time: {completed}")
            print("-" * 50)

    except Exception as e:
        print(f"An error occurred during testing: {e}")

# Run the test function
if __name__ == "__main__":
    test_fetch_downtime_entries()
