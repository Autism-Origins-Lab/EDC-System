import pandas as pd
import tkinter as tk
import sqlite3
import numpy as np
import datetime
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
actual_headertypes = {}

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

# method to verify if integer data in a column is valid
# if boolean, check if conversion should take place
# for all other types, return an error message
def verify_int_column(column):
    boolean_conversion = None
    for i in range(dataframe.shape[0]):
        item = dataframe.iloc[i][column]
        if type(item) is not np.int64:
            if type(item) is np.float64:
                return (True, "Error: Float Converted To Integer", "Value \"{0}\" at row {1} in column {2} is a decimal. It should be an integer.".format(item, i+2, column))
            elif type(item) is pd.Timestamp:
                return (True, "Error: Date/Time Converted To Integer", "Value \"{0}\" at row {1} in column {2} is a date/time. It should be an integer.".format(item, i+2, column))
            elif type(item) is np.bool:
                if boolean_conversion == None:
                    boolean_conversion = messagebox.askyesno("Boolean Conversion", "Value \"{0}\" at row {1} in column {2} is a boolean. Convert column to integers?".format(item, i+2, column))
                if boolean_conversion == False:
                    return (True, "Error: Boolean Converted To Integer", "Value \"{0}\" at row {1} in column {2} is a boolean. It should be an integer.".format(item, i+2, column))
            elif type(item) is str:
                return (True, "Error: Text Converted To Integer", "Value \"{0}\" at row {1} in column {2} is text. It should be an integer.".format(item, i+2, column))
            else:
                return (True, "Error: Unknown Type Converted To Integer", "Value \"{0}\" at row {1} in column {2} is an unknown type. It should be an integer.".format(item, i+2, column))
    return (False, "No Error Found", "There are no errors in this column.")

def verify_float_column(column):
    return (False, "No Error Found", "There are no errors in this column.")

def verify_datetime_column(column):
    return (False, "No Error Found", "There are no errors in this column.")

def verify_boolean_column(column):
    return (False, "No Error Found", "There are no errors in this column.")

def verify_text_column(column):
    return (False, "No Error Found", "There are no errors in this column.")

# command to create database
def create_db():
    # verify that all the columns have been given a type & assign types to dictionary
    for header in headertypes:
        # replace types in dictionary
        if headertypes[header].get() == "Integer":
            actual_headertypes[header] = "INTEGER"
        elif headertypes[header].get() == "Decimal":
            actual_headertypes[header] = "FLOAT"
        elif headertypes[header].get() == "Date/Time":
            actual_headertypes[header] = "DATETIME"
        elif headertypes[header].get() == "Boolean":
            actual_headertypes[header] = "BOOLEAN"
        elif headertypes[header].get() == "Text":
            actual_headertypes[header] = "TEXT"
        else:
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

    # verify each row as appropriate
    for column in dataframe.columns.values.tolist():
        # set default error messages
        error = False
        error_name = "Error Not Specified"
        error_message = "The current error is not specified"

        # for each column, check if there's any errors in the column
        if actual_headertypes[column] == "INTEGER":
            (error, error_name, error_message) = verify_int_column(column)
        elif actual_headertypes[column] == "FLOAT":
            (error, error_name, error_message) = verify_float_column(column)
        elif actual_headertypes[column] == "DATETIME":
            (error, error_name, error_message) = verify_datetime_column(column)
        elif actual_headertypes[column] == "BOOLEAN":
            (error, error_name, error_message) = verify_boolean_column(column)
        elif actual_headertypes[column] == "TEXT":
            (error, error_name, error_message) = verify_text_column(column)
        else:
            error = True
            error_name = "Error: Invalid Column Type"
            error_message = "Column {0} must have its data type specified.".format(column)
        
        # if there is an error in a row, output the error
        if error:
            print("failed")
            messagebox.showerror(error_name, error_message)
            return
        
    
    # create sql database
    connection = sqlite3.connect(DATABASE_FILENAME)
    dataframe.to_sql(name.get(), connection, if_exists="replace", index=False, dtype=actual_headertypes)

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