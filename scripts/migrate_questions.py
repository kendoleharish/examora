import json
import mysql.connector

conn = mysql.connector.connect(host='localhost',user='root',password='Harish2007#',database='online_examination')
cursor = conn.cursor(dictionary=True)

cursor.execute("SELECT qid, question, optionA, optionB, optionC, optionD, correct_answer FROM questions WHERE content IS NULL")
rows = cursor.fetchall()

update_cursor = conn.cursor()
count = 0
for row in rows:
    content = {
        "text": row['question'],
        "options": [
            {"id": "A", "text": row['optionA']},
            {"id": "B", "text": row['optionB']},
            {"id": "C", "text": row['optionC']},
            {"id": "D", "text": row['optionD']}
        ],
        "correct_answer": row['correct_answer']
    }
    
    # Store legacy data securely in new JSON format
    content_json = json.dumps(content)
    update_cursor.execute("UPDATE questions SET type = 'MCQ', content = %s WHERE qid = %s", (content_json, row['qid']))
    count += 1

conn.commit()
cursor.close()
update_cursor.close()
conn.close()

print(f"Migrated {count} questions to new flexible format.")
