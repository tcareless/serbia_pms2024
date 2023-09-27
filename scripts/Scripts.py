from datetime import datetime
import mysql.connector


file = open("tkb_weekly_goals.csv", "r")
rawFile = file.readlines()
cleanFile = []


for string in rawFile:
    newRow = string.split(',')
    cleanFile.append(newRow)

for i in range(0, len(cleanFile)):


    if i == 0:
        cleanFile[i].append("week")
        cleanFile[i].append("year")
    else:

        thisItem = cleanFile[i]
        timestamp = int(thisItem[3])
        dateTime = datetime.fromtimestamp(timestamp)
        week = datetime.date(dateTime).isocalendar().week
        year = dateTime.year
        

        thisItem.append(str(week))
        thisItem.append(str(year))
        cleanFile[i] = thisItem

#writeFile = open("C://Users/skuehl/Desktop/WeeklyStuff/tkb_weekly_goals_output.csv", "w")






db_params = {'host': '10.4.1.245',
             'database': 'prodrptdb',
             'port': 3306,
             'user': 'stuser',
             'password': 'stp383'}

connection = mysql.connector.connect(**db_params)

for i in range(1,len(cleanFile)):
    id = cleanFile[0]
    week = cleanFile[4]
    year = cleanFile[5]

    sql = 'UPDATE `prodrptdb` '
    sql += f'SET `week` = "{week}", SET `year` = "{year}"' 
    sql += f'WHERE id="{id}" '
    sql += f'LIMIT 1;'


cursor = connection.cursor()
for iteration in range(0, 1000):
    cursor.execute(sql)
    connection.commit()
    print(iteration, ':', cursor.rowcount)