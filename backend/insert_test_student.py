import mysql.connector
cfg={'host':'localhost','user':'root','password':'Harish2007#','database':'online_examination','port':3306}
conn=mysql.connector.connect(**cfg)
cursor=conn.cursor()
cursor.execute("INSERT INTO students (student_name, username, password, email) VALUES (%s,%s,%s,%s)", ('Test Student 3','test_student3','pass123','test3@example.com'))
conn.commit()
print('Inserted', cursor.lastrowid)
cursor.close()
conn.close()
