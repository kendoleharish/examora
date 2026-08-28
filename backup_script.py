import os
import mysql.connector

try:
    conn = mysql.connector.connect(host='localhost',user='root',password='Harish2007#',database='online_examination')
    cursor = conn.cursor(dictionary=True)
    
    # 1. Take a full database backup manually
    backup_file = 'db_backup_pre_migration.sql'
    cursor.execute("SHOW TABLES")
    tables = [t[list(t.keys())[0]] for t in cursor.fetchall()]
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        for table in tables:
            cursor.execute(f"SHOW CREATE TABLE {table}")
            create_stmt = cursor.fetchone()[f"Create Table"]
            f.write(f"DROP TABLE IF EXISTS {table};\n")
            f.write(create_stmt + ";\n\n")
            
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            if rows:
                f.write(f"INSERT INTO {table} VALUES \n")
                values = []
                for row in rows:
                    row_vals = []
                    for k, v in row.items():
                        if v is None:
                            row_vals.append('NULL')
                        elif isinstance(v, (int, float)):
                            row_vals.append(str(v))
                        else:
                            val_str = str(v).replace("'", "''").replace("\\", "\\\\")
                            row_vals.append(f"'{val_str}'")
                    values.append("(" + ",".join(row_vals) + ")")
                f.write(",\n".join(values) + ";\n\n")
    
    print(f'Backup successful: {backup_file} created.')

    # 2. Record existing row counts
    tables_to_count = ['questions', 'students', 'examinations', 'student_results', 'student_exam_sessions', 'student_answers']
    counts = {}
    
    print('\n--- PRE-MIGRATION RECORD COUNTS ---')
    for t in tables_to_count:
        cursor.execute(f'SELECT COUNT(*) as c FROM {t}')
        row = cursor.fetchone()
        counts[t] = row['c']
        print(f"{t.ljust(25)}: {row['c']}")
        
    cursor.close()
    conn.close()
    
    with open('migration_counts.txt', 'w') as f:
        f.write('PRE-MIGRATION COUNTS\n')
        for k, v in counts.items():
            f.write(f'{k}:{v}\n')

except Exception as e:
    print(f'Error taking backup or counting records: {e}')
