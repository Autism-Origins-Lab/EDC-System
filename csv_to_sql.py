import pandas as pd
import tkinter as tk
import sqlite3
import numpy as np
from tkinter import filedialog
from tkinter import messagebox

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
    # verify the file is a spreadsheet & read into pandas dataframe
    global dataframe
    if filename[-4:] == '.csv':
        try: 
            dataframe = pd.read_csv(filename)
        except:
            messagebox.showerror("Error: Wrong Filetype", "File selected must either end with either .csv or .xlsx.")
            return False
    elif filename[-5:] == '.xlsx':
        try: 
            dataframe = pd.read_excel(filename)
        except:
            messagebox.showerror("Error: Wrong Filetype", "File selected must either end with either .csv or .xlsx.")
            return False
    else:
        print("failed")
        messagebox.showerror("Error: Wrong Filetype", "File selected must either end with either .csv or .xlsx.")
        return False
    root.destroy()
    settypes()
    return True

# create new GUI window
def settypes():
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
        optionmenus += [tk.OptionMenu(processor, headertypes[dataframe.columns[i]], None, *datatypes)]

        # display labels & options
        labels[i].grid(row=i, column=0, sticky="W")
        optionmenus[i].grid(row=i, column=1, sticky="W")
    
    # create variable to store name
    global name
    name = tk.StringVar()

    # name table
    label = tk.Label(processor, text="Table Name", justify="left")
    namefield = tk.Entry(processor, textvariable=name)
    label.grid(row=len(dataframe.columns), column=0, sticky="W")
    namefield.grid(row=len(dataframe.columns), column=1, sticky="W")

    # name database (if not using default)
    global database_filename
    database_filename = tk.StringVar()
    if not defaultdatabase.get():
        databaselabel = tk.Label(processor, text="Database Name", justify="left")
        databasefield = tk.Entry(processor, textvariable=database_filename)
        databaselabel.grid(row=len(dataframe.columns)+1, column=0, sticky="W")
        databasefield.grid(row=len(dataframe.columns)+1, column=1, sticky="W")
    else:
        database_filename.set("data")

    # display button
    submitbutton = tk.Button(processor, text="Create Database", command=create_db)
    submitbutton.grid(row=len(dataframe.columns)+2, column=0, sticky="W")

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

# method to verify if float data in a column is valid
# if boolean or int, check if conversion should take place
# for all other types, return an error message
def verify_float_column(column):
    int_conversion = None
    boolean_conversion = None
    for i in range(dataframe.shape[0]):
        item = dataframe.iloc[i][column]
        if type(item) is not np.float64:
            if type(item) is np.int64:
                if int_conversion == None:
                    int_conversion = messagebox.askyesno("Integer Conversion", "Value \"{0}\" at row {1} in column {2} is an integer. Convert column to decimals?".format(item, i+2, column))
                if int_conversion == False:
                    return (True, "Error: Integer Converted To Decimal", "Value \"{0}\" at row {1} in column {2} is an integer. It should be a decimal.".format(item, i+2, column))
            elif type(item) is pd.Timestamp:
                return (True, "Error: Date/Time Converted To Decimal", "Value \"{0}\" at row {1} in column {2} is a date/time. It should be a decimal.".format(item, i+2, column))
            elif type(item) is np.bool:
                if boolean_conversion == None:
                    boolean_conversion = messagebox.askyesno("Boolean Conversion", "Value \"{0}\" at row {1} in column {2} is a boolean. Convert column to decimals?".format(item, i+2, column))
                if boolean_conversion == False:
                    return (True, "Error: Boolean Converted To Decimal", "Value \"{0}\" at row {1} in column {2} is a boolean. It should be a decimal.".format(item, i+2, column))
            elif type(item) is str:
                return (True, "Error: Text Converted To Decimal", "Value \"{0}\" at row {1} in column {2} is text. It should be a decimal.".format(item, i+2, column))
            else:
                return (True, "Error: Unknown Type Converted To Decimal", "Value \"{0}\" at row {1} in column {2} is an unknown type. It should be a decimal.".format(item, i+2, column))
    return (False, "No Error Found", "There are no errors in this column.")

# method to verify if datetime data in a column is valid
# attempt to convert strings to datetime if possible
# otherewise, returns an error message
def verify_datetime_column(column):
    string_conversion = None
    for i in range(dataframe.shape[0]):
        item = dataframe.at[i, column]
        if type(item) is not pd.Timestamp:
            if type(item) is np.int64:
                return (True, "Error: Integer Converted To Date/Time", "Value \"{0}\" at row {1} in column {2} is an integer. It should be a date/time.".format(item, i+2, column))
            elif type(item) is np.float64:
                return (True, "Error: Float Converted To Date/Time", "Value \"{0}\" at row {1} in column {2} is a decimal. It should be a date/time.".format(item, i+2, column))
            elif type(item) is np.bool:
                return (True, "Error: Boolean Converted To Date/Time", "Value \"{0}\" at row {1} in column {2} is a boolean. It should be a date/time.".format(item, i+2, column))
            elif type(item) is str:
                if string_conversion == None:
                    string_conversion = messagebox.askyesno("Text Conversion", "Value \"{0}\" at row {1} in column {2} is text. Convert column to dates/times?".format(item, i+2, column))
                if string_conversion == True:
                    try:
                        dataframe.at[i, column] = pd.to_datetime(item).isoformat()
                    except:
                        return (True, "Error: Text Cannot Be Converted To Date/Time", "Value \"{0}\" at row {1} in column {2} cannot be converted to a date/time.".format(item, i+2, column))
                if string_conversion == False:
                    return (True, "Error: Text Converted To Date/Time", "Value \"{0}\" at row {1} in column {2} is text. It should be a date/time.".format(item, i+2, column))
            else:
                return (True, "Error: Unknown Type Converted To Date/Time", "Value \"{0}\" at row {1} in column {2} is an unknown type. It should be a date/time.".format(item, i+2, column))
    return (False, "No Error Found", "There are no errors in this column.")

# method to verify if boolean data in a column is valid
# returns an error message
def verify_boolean_column(column):
    for i in range(dataframe.shape[0]):
        item = dataframe.at[i, column]
        if type(item) is not np.bool:
            if type(item) is np.int64:
                return (True, "Error: Integer Converted To Boolean", "Value \"{0}\" at row {1} in column {2} is an integer. It should be a boolean.".format(item, i+2, column))
            elif type(item) is np.float64:
                return (True, "Error: Float Converted To Boolean", "Value \"{0}\" at row {1} in column {2} is a decimal. It should be a boolean.".format(item, i+2, column))
            elif type(item) is pd.Timestamp:
                return (True, "Error: Date/Time Converted To Boolean", "Value \"{0}\" at row {1} in column {2} is a date/time. It should be a boolean.".format(item, i+2, column))
            elif type(item) is str:
                return (True, "Error: Text Converted To Boolean", "Value \"{0}\" at row {1} in column {2} is text. It should be a boolean.".format(item, i+2, column))
            else:
                return (True, "Error: Unknown Type Converted To Date/Time", "Value \"{0}\" at row {1} in column {2} is an unknown type. It should be a date/time.".format(item, i+2, column))
    return (False, "No Error Found", "There are no errors in this column.")

# method to verify if string data in a column is valid
# attempts to convert to strings if requested
# otherwise, returns an error message
def verify_text_column(column):
    int_conversion = None
    float_conversion = None
    datetime_conversion = None
    boolean_conversion = None
    for i in range(dataframe.shape[0]):
        item = dataframe.at[i, column]
        if type(item) is not str:
            if type(item) is np.int64:
                if int_conversion == None:
                    int_conversion = messagebox.askyesno("Integer Conversion", "Value \"{0}\" at row {1} in column {2} is an integer. Convert column to text?".format(item, i+2, column))
                if int_conversion == False:
                    return (True, "Error: Integer Converted To Text", "Value \"{0}\" at row {1} in column {2} is an integer. It should be text.".format(item, i+2, column))
            elif type(item) is np.float64:
                if float_conversion == None:
                    float_conversion = messagebox.askyesno("Decimal Conversion", "Value \"{0}\" at row {1} in column {2} is a decimal. Convert column to text?".format(item, i+2, column))
                if float_conversion == False:
                    return (True, "Error: Float Converted To Text", "Value \"{0}\" at row {1} in column {2} is a decimal. It should be text.".format(item, i+2, column))
            elif type(item) is pd.Timestamp:
                if datetime_conversion == None:
                    datetime_conversion = messagebox.askyesno("Date/Time Conversion", "Value \"{0}\" at row {1} in column {2} is a date/time. Convert column to text?".format(item, i+2, column))
                if datetime_conversion == False:
                    return (True, "Error: Date/Time Converted To Text", "Value \"{0}\" at row {1} in column {2} is a date/time. It should be text.".format(item, i+2, column))
            elif type(item) is np.bool:
                if boolean_conversion == None:
                    boolean_conversion = messagebox.askyesno("Boolean Conversion", "Value \"{0}\" at row {1} in column {2} is a boolean. Convert column to text?".format(item, i+2, column))
                if boolean_conversion == False:
                    return (True, "Error: Text Converted To Text", "Value \"{0}\" at row {1} in column {2} is text. It should be text.".format(item, i+2, column))
            else:
                return (True, "Error: Unknown Type Converted To Text", "Value \"{0}\" at row {1} in column {2} is an unknown type. It should be text.".format(item, i+2, column))
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
        
    # check that name is only alphanumeric characters
    if not name.get().isalnum():
        print("failed")
        messagebox.showerror("Error: Name Must Be Alphanumeric", "The name for the table must only include letters and numbers.")
        return
    
    # check that database name is only alphanumeric characters
    if not database_filename.get().isalnum():
        print("failed")
        messagebox.showerror("Error: Database Name Must Be Alphanumeric", "The name for the database must only include letters and numbers.")
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
    connection = sqlite3.connect("databases/{0}.db".format(database_filename.get()))
    if rewrite.get():
        dataframe.to_sql(name.get(), connection, if_exists="replace", index=False, dtype=actual_headertypes)
    else:
        dataframe.to_sql(name.get(), connection, if_exists="append", index=False, dtype=actual_headertypes)

    print("created table {0}".format(name.get()))
    processor.destroy()

# create GUI window
root = tk.Tk()
root.minsize(400, 200)
root.title("Upload Sheet to Database")

# stores whether we're using a default database or not
global defaultdatabase
defaultdatabase = tk.BooleanVar()

# stores whether to rewrite or add to database if already exists
global rewrite
rewrite = tk.BooleanVar()

# sets up GUI design
label = tk.Label(root, text="File to upload: {0}".format(filename), wraplength=400, justify="center")
defaultcheck = tk.Checkbutton(root, text='Use Default Database?',variable=defaultdatabase, onvalue=1, offvalue=0)
rewritecheck = tk.Checkbutton(root, text="Rewrite If Preexisting?", variable=rewrite, onvalue=1, offvalue=0)
filebutton = tk.Button(root, text="Choose Spreadsheet", command=choose_csv_file)
submitbutton = tk.Button(root, text="Upload Spreadsheet", command=upload)

# updates GUI design
label.pack()
defaultcheck.pack()
rewritecheck.pack()
filebutton.pack()
submitbutton.pack()
defaultcheck.select()
rewritecheck.select()

# starts the event loop & keeps GUI responsive
def main():
    root.mainloop()

if __name__ == "__main__":
    main()