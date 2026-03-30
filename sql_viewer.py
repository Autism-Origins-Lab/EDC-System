import pandas as pd
import tkinter as tk
import sqlite3
import numpy as np
import os
from tkinter import ttk

# get databases
databases = os.listdir("databases")
tables = []

# get tables
def gettables(database):
    connection = sqlite3.connect("databases/{0}".format(database))
    result = connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [x[0] for x in result.fetchall()]
    connection.close()
    return tables

# update the tables for the tkinter gui
def updatetables(self):
    tables = gettables(db_stringvar.get())
    table_name["menu"].delete(0, "end")
    for table in tables:
        table_name["menu"].add_command(label=table, command=lambda v=table: table_stringvar.set(v))

# get table
def gettabledata(database, table):
    connection = sqlite3.connect("databases/{0}".format(database))
    result = pd.read_sql_query("SELECT * FROM {0}".format(table), connection)
    connection.close()
    return result

# view table
def viewtable():
    print("viewing table {0} from {1}".format(table_stringvar.get(), db_stringvar.get()))
    root.destroy()

    # get table
    tabledata = gettabledata(db_stringvar.get(), table_stringvar.get())

    # view table
    viewer = tk.Tk()
    viewer.minsize(400, 200)
    viewer.title("{0} - {1}".format(table_stringvar.get(), db_stringvar.get()))

    # set up columns and tree
    cols = list(tabledata.columns)
    tree = ttk.Treeview(viewer, columns=cols, show='headings')
    tree.pack(fill="both", expand=True)
    
    # display column headers
    for col in cols:
        tree.column(col, anchor="w")
        tree.heading(col, text=col, anchor='w')

    # populate table with data
    for index, row in tabledata.iterrows():
        tree.insert("", tk.END, text=index, values=list(row))

    # configure scrollbars
    vertical_scrollbar = ttk.Scrollbar(viewer, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=vertical_scrollbar.set)
    vertical_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# create GUI window
root = tk.Tk()
root.minsize(400, 200)
root.title("Choose Table to View")

db_stringvar = tk.StringVar()
table_stringvar = tk.StringVar()

db_label = tk.Label(root, text="Database Name", justify="left")
db_name = tk.OptionMenu(root, db_stringvar, None, *databases, command=updatetables)
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