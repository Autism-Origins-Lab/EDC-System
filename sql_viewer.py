import pandas as pd
import tkinter as tk
import sqlite3
import numpy as np
import os

# get databases
databases = os.listdir("databases")
tables = []

# get tables
def gettables(self):
    connection = sqlite3.connect("databases/{0}".format(db_stringvar.get()))
    result = connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = result.fetchall()
    connection.close()

# view table
def viewtable():
    print("viewing table {0} from {1}".format(table_stringvar.get(), db_stringvar.get()))
    root.destroy()

# create GUI window
root = tk.Tk()
root.minsize(400, 200)
root.title("Choose Table to View")

db_stringvar = tk.StringVar()
table_stringvar = tk.StringVar()

db_label = tk.Label(root, text="Database Name", justify="left")
db_name = tk.OptionMenu(root, db_stringvar, None, *databases, command=gettables)
table_label = tk.Label(root, text="Table Name", justify="left")
table_name = tk.OptionMenu(root, table_stringvar, None, *tables)
submitbutton = tk.Button(root, text="Get Table", command=viewtable)

db_label.grid(row=0, column=0, sticky="W")
db_name.grid(row=0, column=1, sticky="W")
table_label.grid(row=1, column=0, sticky="W")
table_name.grid(row=1, column=1, sticky="W")
submitbutton.grid(row=2, column=0, sticky="W")

# starts the event loop & keeps GUI responsive
def main():
    root.mainloop()

if __name__ == "__main__":
    main()