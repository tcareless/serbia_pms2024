import mysql.connector
import time

# db_params = {'host': '10.4.1.224',
#              'database': 'prodrptdb',
#              'user': 'stuser',
#              'password': 'stp383'}

db_params = {'host': '10.4.1.245',
             'database': 'django_pms',
             'port': 6601,
             'user': 'muser',
             'password': 'wsj.231.kql'}

connection = mysql.connector.connect(**db_params)
tic = time.time()

sql = f'SELECT * FROM `GFxPRoduction` '
sql += f'WHERE Machine=261 '
sql += f'AND TimeStamp BETWEEN 1687312800 AND 1687341600 '
sql += f'ORDER BY Id;'
cursor = connection.cursor(dictionary=True)
cursor.execute(sql)
lastrow = -1
times = {}

row = cursor.fetchone()
while row:
    if lastrow == -1:
        lastrow = row["TimeStamp"]
        continue
    cycle = f'{row["TimeStamp"]-lastrow:0>5.0f}'
    times[cycle] = times.get(cycle, 0) + 1
    lastrow = row["TimeStamp"]
    row = cursor.fetchone()

for k, v in sorted(times.items()):
    print(f'{int(k)}:{v}')

toc = time.time()
print(f'Elapsed: {toc-tic:.3f}')
