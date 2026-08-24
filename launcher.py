import sqlite3
import pandas as pd

# 1. Connect to your SQLite database file
conn = sqlite3.connect("databases/patient_data.db")
cursor = conn.cursor()

# 2. Query the system master table for 'table' types
"""
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

# 3. Fetch and print all table names
tables = cursor.fetchall()
for table in tables:
    print(table[0])
"""
query = "SELECT * FROM patients"

# 3. Read the data directly into a pandas DataFrame
df = pd.read_sql_query(query, conn)

# 4. Export the DataFrame to an Excel spreadsheet
df.to_excel("database_export.xlsx", index=False)

conn.close()

print("Database table successfully exported to Excel!")