import os
import sqlite3

db_path = r"C:\Users\saleh\AppData\Roaming\pgAdmin\pgadmin4.db"

if not os.path.exists(db_path):
    print(f"Error: pgadmin4.db does not exist at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print("Tables in pgadmin4.db:", tables)

# Inspect server table if exists
if "server" in tables:
    try:
        cursor.execute("PRAGMA table_info(server);")
        columns = [c[1] for c in cursor.fetchall()]
        print("\nServer table columns:", columns)

        cursor.execute("SELECT * FROM server;")
        rows = cursor.fetchall()
        print(f"\nFound {len(rows)} servers:")
        for row in rows:
            server_dict = dict(zip(columns, row))
            # Hide sensitive fields but show host, port, username, database, etc.
            clean_dict = {
                k: v
                for k, v in server_dict.items()
                if k in ["name", "host", "port", "username", "maintenance_db", "id"]
            }
            print(clean_dict)
    except Exception as e:
        print("Error querying server table:", e)
else:
    print("\nNo 'server' table found.")

conn.close()
