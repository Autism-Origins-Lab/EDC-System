import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# list of datatypes
datatypes = ["Integer", "Decimal", "Date/Time", "Text", "Boolean"]

# stores CSV filename to open
filename = "None"

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
    dataframe = pd.DataFrame()
    if filetype == "csv":
        dataframe = pd.read_csv(filename)
    elif filetype == "excel":
        dataframe = pd.read_excel(filename)

    # create new GUI window
    processor = tk.Tk()
    processor.minsize(400, 200)
    processor.title("Choose Data Types")

    # stores labels and options
    labels = []
    options = []
    optionmenus = []

    # list headers for new GUI window
    for i in range(len(dataframe.columns)):
        # create labels & options
        labels += [tk.Label(processor, text=dataframe.columns[i], justify="left")]
        labels[i].grid(row=i, column=0, sticky="W")
        options += [tk.StringVar()]
        optionmenus += [tk.OptionMenu(processor, options[i], "Choose an option...", *datatypes)]
        optionmenus[i].grid(processor=i, column=1, sticky="W")

        # display labels & options
        labels[i].pack()
        optionmenus[i].pack()


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