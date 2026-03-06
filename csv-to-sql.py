import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# list of datatypes
datatypes = ["Boolean", "Date/Time", "Decimal", "Integer", "Text"]

# stores CSV filename to open
filename = "None"

# stores dataframe
dataframe = pd.DataFrame()

# stores header types
headertypes = []

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
        headertypes += [tk.StringVar()]
        headertypes[i].set(" ")
        optionmenus += [tk.OptionMenu(processor, headertypes[i], None, *datatypes)]

        # display labels & options
        labels[i].grid(row=i, column=0, sticky="W")
        optionmenus[i].grid(row=i, column=1, sticky="W")
    
    # create variable to store name
    global name
    name = tk.StringVar()
    name.set(" ")

    # name database
    label = tk.Label(processor, text="Database Name: ", justify="left")
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
        if type.get() == " ":
            print("failed")
            messagebox.showerror("Error: Type Not Specified", "All columns must have its data type specified.")
            return
    
    # verify that the database has a name
    if name.get() == " ":
        print("failed")
        messagebox.showerror("Error: Name Not Specified", "A name must be specified for the database.")
        return
        
    # create sql database
    print("created database {0}".format(name.get()))
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