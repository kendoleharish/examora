import mysql.connector
import os

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Harish2007#",
    "database": "online_examination"
}

def backup():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        with open("db_backup_pre_multitenant.sql", "w", encoding="utf-8") as f:
            for (table_name,) in tables:
                cursor.execute(f"SHOW CREATE TABLE {table_name}")
                create_stmt = cursor.fetchone()[1]
                f.write(f"{create_stmt};\n\n")
                
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                if rows:
                    cols = [desc[0] for desc in cursor.description]
                    for row in rows:
                        vals = []
                        for val in row:
                            if val is None:
                                vals.append('NULL')
                            elif isinstance(val, str):
                                vals.append(f"'{val.replace('\'', '\'\'')}'")
                            else:
                                vals.append(str(val))
                        f.write(f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({', '.join(vals)});\n")
                f.write("\n")
                
        print("Backup created successfully.")
    except Exception as e:
        print(f"Backup failed: {e}")

if __name__ == '__main__':
    backup()
