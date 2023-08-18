import mysql.connector

# db_params = {'host': '10.4.1.224',
#              'database': 'prodrptdb',
#              'user': 'stuser',
#              'password': 'stp383'}

# db_params = {'host': '10.4.1.245',
#              'database': 'django_pms',
#              'port': 6601,
#              'user': 'muser',
#              'password': 'wsj.231.kql'}

db_params = {'host': '10.4.1.245',
             'database': 'prodrptdb',
             'port': 3306,
             'user': 'stuser',
             'password': 'stp383'}

connection = mysql.connector.connect(**db_params)


sql = 'UPDATE `GFxPRoduction` '
sql += 'SET `part` = "50-9341" '
sql += f'WHERE Machine="1522" '
sql += f'AND Part="9341" '
sql += f'LIMIT 50;'
cursor = connection.cursor()
for iteration in range(0, 1000):
    cursor.execute(sql)
    connection.commit()
    print(iteration, ':', cursor.rowcount)
