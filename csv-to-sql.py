import tkinter as tk
from tkinter.filedialog import askopenfilename

# stores CSV filename to open
filename = "None"

# function to choose CSV file
def choose_csv_file(label):
    filename = askopenfilename()
    label["text"] = "File to upload: {0}".format(filename)
    label.pack()
    print(filename)

# create GUI window
root = tk.Tk()
root.minsize(400, 200)
root.title("Upload CSV")

# sets up GUI design
label = tk.Label(root, text="File to upload: {0}".format(filename), wraplength=400, justify="center")
filebutton = tk.Button(root, text="Choose CSV", command=lambda label=label : choose_csv_file(label))

# updates GUI design
label.pack()
filebutton.pack()

# starts the event loop & keeps GUI responsive
root.mainloop()