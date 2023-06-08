import mysql.connector

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


sql = 'DELETE FROM `GFxPRoduction` '
sql += f'WHERE Part="undefined" '
sql += f'LIMIT 5000;'
cursor = connection.cursor()
for iteration in range(0, 1000):
    cursor.execute(sql)
    connection.commit()
    print(iteration, ':', cursor.rowcount)
