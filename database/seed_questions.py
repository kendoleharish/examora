import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Harish2007#",
    "database": "online_examination",
    "port": 3306
}

QUESTIONS = [
    {
        "category": "Computer Science & IT",
        "question": "Who is considered the father of computer science?",
        "optionA": "Charles Babbage",
        "optionB": "Alan Turing",
        "optionC": "John von Neumann",
        "optionD": "Ada Lovelace",
        "correct_answer": "B",
        "marks": 1
    },
    {
        "category": "Computer Science & IT",
        "question": "Which data structure operates on a Last In, First Out (LIFO) basis?",
        "optionA": "Queue",
        "optionB": "Array",
        "optionC": "Stack",
        "optionD": "Binary Tree",
        "correct_answer": "C",
        "marks": 1
    },
    {
        "category": "Programming",
        "question": "In Python, which built-in function returns the number of elements in an iterable?",
        "optionA": "count()",
        "optionB": "len()",
        "optionC": "size()",
        "optionD": "length()",
        "correct_answer": "B",
        "marks": 1
    },
    {
        "category": "Database Management Systems",
        "question": "Which SQL clause is used to filter aggregated group records after a GROUP BY clause?",
        "optionA": "WHERE",
        "optionB": "ORDER BY",
        "optionC": "HAVING",
        "optionD": "FILTER",
        "correct_answer": "C",
        "marks": 1
    },
    {
        "category": "Artificial Intelligence",
        "question": "Which algorithm is guaranteed to find the shortest path in an unweighted graph?",
        "optionA": "Depth First Search (DFS)",
        "optionB": "Breadth First Search (BFS)",
        "optionC": "Genetic Algorithm",
        "optionD": "Hill Climbing",
        "correct_answer": "B",
        "marks": 1
    },
    {
        "category": "Computer Networks",
        "question": "Which standard protocol provides encrypted end-to-end communication for web applications?",
        "optionA": "HTTP",
        "optionB": "FTP",
        "optionC": "HTTPS (TLS/SSL)",
        "optionD": "SNMP",
        "correct_answer": "C",
        "marks": 1
    },
    {
        "category": "Operating Systems",
        "question": "What is the primary role of the Translation Lookaside Buffer (TLB)?",
        "optionA": "File system disk cache",
        "optionB": "Hardware cache for virtual-to-physical address translations",
        "optionC": "Process scheduling queue",
        "optionD": "Interrupt descriptor table",
        "correct_answer": "B",
        "marks": 1
    },
    {
        "category": "Mathematics",
        "question": "What is the derivative of f(x) = x^3 evaluated at x = 2?",
        "optionA": "6",
        "optionB": "8",
        "optionC": "12",
        "optionD": "16",
        "correct_answer": "C",
        "marks": 1
    },
    {
        "category": "Electronics",
        "question": "Which semiconductor device is widely utilized for switching and amplification of signals?",
        "optionA": "Resistor",
        "optionB": "Capacitor",
        "optionC": "Transistor",
        "optionD": "Inductor",
        "correct_answer": "C",
        "marks": 1
    },
    {
        "category": "Database Management Systems",
        "question": "Which ACID property guarantees that committed transactions survive system crashes?",
        "optionA": "Atomicity",
        "optionB": "Consistency",
        "optionC": "Isolation",
        "optionD": "Durability",
        "correct_answer": "D",
        "marks": 1
    }
]

def seed_questions():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    print("Checking question bank...")
    for q in QUESTIONS:
        cursor.execute("SELECT qid FROM questions WHERE question = %s", (q["question"],))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute(
                "INSERT INTO questions (category, question, optionA, optionB, optionC, optionD, correct_answer, marks) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (q["category"], q["question"], q["optionA"], q["optionB"], q["optionC"], q["optionD"], q["correct_answer"], q["marks"])
            )
            print(f"Added question: {q['question']}")

    # Link all questions to CS-101 (exam_id = 1)
    cursor.execute("SELECT qid FROM questions ORDER BY qid ASC")
    all_qids = cursor.fetchall()
    for order, r in enumerate(all_qids, start=1):
        cursor.execute(
            "INSERT IGNORE INTO exam_questions (exam_id, qid, question_order) VALUES (%s, %s, %s)",
            (1, r["qid"], order)
        )

    # Recalculate CS-101 total marks
    cursor.execute("""
        SELECT COALESCE(SUM(q.marks), 0) AS total_marks
        FROM exam_questions eq
        JOIN questions q ON eq.qid = q.qid
        WHERE eq.exam_id = 1
    """)
    tm = cursor.fetchone()["total_marks"]
    cursor.execute("UPDATE examinations SET total_marks = %s WHERE exam_id = 1", (tm,))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Question seeding complete. Total marks for CS-101: {tm}")

if __name__ == "__main__":
    seed_questions()
