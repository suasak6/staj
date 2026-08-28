import sqlite3

connection = sqlite3.connect("route_database.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    district TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    service_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    district TEXT NOT NULL,
    start_latitude REAL NOT NULL,
    start_longitude REAL NOT NULL,
    end_latitude REAL NOT NULL,
    end_longitude REAL NOT NULL,
    capacity INTEGER NOT NULL
)
""")

# Employees tablosunda service_id yoksa ekle
cursor.execute("PRAGMA table_info(employees)")
columns = [column[1] for column in cursor.fetchall()]

if "service_id" not in columns:
    cursor.execute("""
    ALTER TABLE employees ADD COLUMN service_id INTEGER
    """)

connection.commit()
connection.close()

print("Database ve tablolar hazır!")