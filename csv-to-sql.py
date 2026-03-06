import sqlite3
import pandas as pd
import tkinter as tk
import sqlalchemy as db
from tkinter import filedialog
from tkinter import messagebox

# database filename - modify this to modify where the databases are saved
DATABASE_FILENAME = "data.db"

# list of datatypes
datatypes = ["Boolean", "Date/Time", "Decimal", "Integer", "Text"]

# stores CSV filename to open
filename = "None"

# stores dataframe
dataframe = pd.DataFrame()

# stores header types in dictionary
headertypes = {}

# function to choose CSV file
def choose_csv_file():
    global filename
    global label
    filename = filedialog.askopenfilename()
    label["text"] = "File to upload: {0}".format(filename)
    label.pack()
    print(filename)
    return filename

# function to upload CSV file
def upload():
    # stores the filetype
    filetype = None

    # verify the file is a spreadsheet
    if filename[-4:] == '.csv':
        filetype = "csv"
    elif filename[-5:] == '.xlsx':
        filetype = "excel"
    else:
        print("failed")
        messagebox.showerror("Error: Wrong Filetype", "File selected must either end with either .csv or .xlsx.")
        return
    print(filetype)
    root.destroy()

    # read CSV or Excel file into pandas dataframe
    global dataframe
    if filetype == "csv":
        dataframe = pd.read_csv(filename)
    elif filetype == "excel":
        dataframe = pd.read_excel(filename)

    # create new GUI window
    global processor
    processor = tk.Tk()
    processor.minsize(400, 200)
    processor.title("Choose Data Types")

    # stores labels and options
    global headertypes
    labels = []
    optionmenus = []

    # list headers for new GUI window
    for i in range(len(dataframe.columns)):
        # create labels & options
        labels += [tk.Label(processor, text=dataframe.columns[i], justify="left")]
        headertypes[dataframe.columns[i]] = tk.StringVar()
        headertypes[dataframe.columns[i]].set(" ")
        optionmenus += [tk.OptionMenu(processor, headertypes[dataframe.columns[i]], None, *datatypes)]

        # display labels & options
        labels[i].grid(row=i, column=0, sticky="W")
        optionmenus[i].grid(row=i, column=1, sticky="W")
    
    # create variable to store name
    global name
    name = tk.StringVar()
    name.set(" ")

    # name database
    label = tk.Label(processor, text="Table Name", justify="left")
    namefield = tk.Entry(processor, textvariable=name)
    label.grid(row=len(dataframe.columns), column=0, sticky="W")
    namefield.grid(row=len(dataframe.columns), column=1, sticky="W")

    # display button
    submitbutton = tk.Button(processor, text="Create Database", command=create_db)
    submitbutton.grid(row=len(dataframe.columns)+1, column=0, sticky="W")

# command to create database
def create_db():
    # verify that all the columns have been given a type
    for type in headertypes:
        if headertypes[type].get() == " ":
            print("failed")
            messagebox.showerror("Error: Type Not Specified", "All columns must have its data type specified.")
            return
    
    # verify that the database has a name
    if name.get() == " ":
        print("failed")
        messagebox.showerror("Error: Name Not Specified", "A name must be specified for the table.")
        return
    
    # check that name is only alphanumeric characters
    if not name.get().isalnum():
        print("failed")
        messagebox.showerror("Error: Name Must Be Alphanumeric", "The name for the database must only include letters and numbers.")
        return
    
    # go through dictionary and replace types with actual types
    for type in headertypes:
        if headertypes[type] == "Integer":
            headertypes[type] = "INTEGER"
        elif headertypes[type] == "Decimal":
            headertypes[type] = "FLOAT"
        elif headertypes[type] == "Date/Time":
            headertypes[type] = "DATETIME"
        elif headertypes[type] == "Boolean":
            headertypes[type] = "BOOLEAN"
        else:
            headertypes[type] = "TEXT"
    
    # create sql database
    connection = sqlite3.connect(DATABASE_FILENAME)
    dataframe.to_sql(name.get(), connection, if_exists="replace", index=False, dtype=headertypes)

    print("created table {0}".format(name.get()))
    processor.destroy()

# create GUI window
root = tk.Tk()
root.minsize(400, 200)
root.title("Upload Sheet to Database")

# sets up GUI design
label = tk.Label(root, text="File to upload: {0}".format(filename), wraplength=400, justify="center")
filebutton = tk.Button(root, text="Choose Spreadsheet", command=choose_csv_file)
submitbutton = tk.Button(root, text="Upload Spreadsheet", command=upload)

# updates GUI design
label.pack()
filebutton.pack()
submitbutton.pack()

# starts the event loop & keeps GUI responsive
root.mainloop()