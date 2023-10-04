import os
import django
from datetime import datetime


#  you have to set the correct path to you settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pms.settings.local")
django.setup()

# from app.prod_query.models import Weekly_Production_Goal

def run():
    # with open("scripts/tkb_weekly_goals.csv", "r") as infile:
    #     # do something with variable
    #     while True:
    #         line = infile.readline()
    #         if not line:
    #             break

    #         id, part_number, goal, timestamp = line.rstrip().split(",")

    #         (year, week, day) = datetime.fromtimestamp(
    #             int(timestamp)).isocalendar()
    #         print(year, week, day, part_number, goal)
    #         a = Weekly_Production_Goal(
    #             part_number=part_number,
    #             goal=goal,
    #             year=year,
    #             week=week)
    #         a.save()
    pass

if __name__ == '__main__':
    run()
