import pandas as pd
import tkinter as tk
import sqlite3
import os
from tkinter import ttk

# store current metric sorted by
current_column = None
ascending_sort = False

# store current table
table = None

# get databases
databases = [db[:-3] for db in os.listdir("databases")]
databases.remove("test")
tables = []

# get tables
def gettables(database):
    connection = sqlite3.connect("databases/{0}.db".format(database))
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
    connection = sqlite3.connect("databases/{0}.db".format(database))
    result = pd.read_sql_query("SELECT * FROM {0}".format(table), connection)
    connection.close()
    return result

# sort column data
def sort(column, table):
    # set direction of sort
    global current_column
    global ascending_sort
    ascending_sort = not ascending_sort if column is current_column else True
    current_column = column

    # sort data
    return table.sort_values(column, ascending=ascending_sort)

# update the view based on sorted column data
def update_sortedview(column, tree):
    old_column = current_column
    sorted = sort(column, table)

    # clear current treeview
    tree.delete(*tree.get_children())

    # replace column headers
    if old_column is not None:
        tree.heading(old_column, text=old_column, anchor='w', command=lambda x = old_column, y = tree: update_sortedview(x, y))
    tree.heading(column, text="↑ {0} ↑".format(column) if ascending_sort else "↓ {0} ↓".format(column), anchor='w', command=lambda x = column, y = tree: update_sortedview(x, y))

    # replace treeview data
    for index, row in sorted.iterrows():
        tree.insert("", tk.END, text=index, values=list(row))

# filter a table and return the dataframe
def filter_table(operation, column, value, df):
    if operation == "Exclude":
        return df[~df[column].astype(str).str.contains(value)]
    elif operation == "Include":
        return df[df[column].astype(str).str.contains(value)]
    elif operation == "Greater":
        return df[df[column].astype(float) > float(value)]
    elif operation == "Lesser":
        return df[df[column].astype(float) < float(value)]
    elif operation == "Equal":
        return df[df[column].astype(str) == value]
    elif operation == "Not":
        return df[df[column].astype(str) != value]
    elif operation == "Before":
        return df[pd.to_datetime(df[column]) < pd.to_datetime(value)]
    elif operation == "After":
        return df[pd.to_datetime(df[column]) > pd.to_datetime(value)]
    else:
        return df

# update the view based on filtered data
def update_filteredview(tree):
    # get whether this is an inclusion or exclusion filter
    operation = filtertype_stringvar.get()
    column = filtercol_stringvar.get()
    value = filter_stringvar.get()

    # get current table data, set up filter, and filter table
    global table
    table = gettabledata(db_stringvar.get(), table_stringvar.get())
    table = filter_table(operation, column, value, table)

    # clear current treeview
    tree.delete(*tree.get_children())

    # replace column headers
    global current_column
    if current_column is not None:
        tree.heading(current_column, text=current_column, anchor='w', command=lambda x = current_column, y = tree: update_sortedview(x, y))
    current_column = None

    # replace treeview data
    for index, row in table.iterrows():
        tree.insert("", tk.END, text=index, values=list(row))

# reset viewer
def reset_view(tree):
    # get current table data, set up filter, and filter table
    global table
    table = gettabledata(db_stringvar.get(), table_stringvar.get())

    # clear current treeview
    tree.delete(*tree.get_children())

    # replace column headers
    global current_column
    if current_column is not None:
        tree.heading(current_column, text=current_column, anchor='w', command=lambda x = current_column, y = tree: update_sortedview(x, y))
    current_column = None

    # replace treeview data
    for index, row in table.iterrows():
        tree.insert("", tk.END, text=index, values=list(row))

# view table
def viewtable():
    print("viewing table {0} from {1}".format(table_stringvar.get(), db_stringvar.get()))
    root.destroy()

    # get table
    global table
    table = gettabledata(db_stringvar.get(), table_stringvar.get())

    # view table
    viewer = tk.Tk()
    viewer.minsize(400, 300)
    viewer.title("{0} - {1}".format(table_stringvar.get(), db_stringvar.get()))
    viewer.rowconfigure(1, weight=1)
    viewer.columnconfigure(3, weight=1)

    # set up columns
    cols = list(table.columns)

    # create tree
    tree = ttk.Treeview(viewer, columns=cols, show='headings')

    # create filter UI
    global filtertype_stringvar
    global filtercol_stringvar
    global filter_stringvar
    filtertype_stringvar = tk.StringVar()
    filtercol_stringvar = tk.StringVar()
    filter_stringvar = tk.StringVar()
    filter_type = tk.OptionMenu(viewer, filtertype_stringvar, None, *["Include", "Exclude", "Greater", "Lesser", "Equal", "Not", "Before", "After"])
    filter_column = tk.OptionMenu(viewer, filtercol_stringvar, None, *cols)
    filter = tk.Entry(viewer, textvariable=filter_stringvar)
    filter_button = tk.Button(viewer, text="Apply Filter", command=lambda x = tree: update_filteredview(x))
    reset_button = tk.Button(viewer, text="Reset Filter", command=lambda x = tree: reset_view(x))

    # add everything to grid
    filter_type.grid(row=0, column=0, sticky='w')
    filter_column.grid(row=0, column=1, sticky='w')
    filter.grid(row=0, column=2, sticky='w')
    filter_button.grid(row=0, column=3, sticky='w')
    reset_button.grid(row=0, column=4, sticky='w')
    tree.grid(row=1, columnspan=5, sticky="nsew")
    
    # display column headers
    for col in cols:
        tree.column(col, anchor="w")
        tree.heading(col, text=col, anchor='w', command=lambda x = col, y = tree: update_sortedview(x, y))

    # populate table with data
    for index, row in table.iterrows():
        tree.insert("", tk.END, text=index, values=list(row))

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