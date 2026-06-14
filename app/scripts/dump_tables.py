import sqlite3

db_path = r"C:\Users\saleh\AppData\Roaming\pgAdmin\pgadmin4.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get everything from 'user'
print("--- USER TABLE ---")
cursor.execute("PRAGMA table_info(user);")
cols = [c[1] for c in cursor.fetchall()]
cursor.execute("SELECT * FROM user;")
for r in cursor.fetchall():
    print(dict(zip(cols, r)))

# Get everything from 'keys'
print("\n--- KEYS TABLE ---")
cursor.execute("PRAGMA table_info(keys);")
cols = [c[1] for c in cursor.fetchall()]
cursor.execute("SELECT * FROM keys;")
for r in cursor.fetchall():
    # hide the sensitive values but show schema
    print({k: (v if k != "value" else "<hidden>") for k, v in zip(cols, r)})

# Get everything from 'server'
print("\n--- SERVER TABLE ---")
cursor.execute("PRAGMA table_info(server);")
cols = [c[1] for c in cursor.fetchall()]
cursor.execute("SELECT * FROM server;")
for r in cursor.fetchall():
    print({k: (v if k != "password" else "<encrypted>") for k, v in zip(cols, r)})

conn.close()
