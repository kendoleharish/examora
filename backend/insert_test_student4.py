import mysql.connector
cfg={'host':'localhost','user':'root','password':'Harish2007#','database':'online_examination','port':3306}
conn=mysql.connector.connect(**cfg)
cursor=conn.cursor()
cursor.execute("INSERT INTO students (student_name, username, password, email) VALUES (%s,%s,%s,%s)", ('Test Student 4','test_student4','pass123','test4@example.com'))
conn.commit()
print('Inserted', cursor.lastrowid)
cursor.close()
conn.close()
