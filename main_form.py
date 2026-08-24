import tkinter as tk
import sqlite3
import os
from tkinter import ttk, messagebox
from tkinter import *

# -----------------------------
# Main Window
# -----------------------------
root = tk.Tk()
root.title("Patient Report")
root.geometry("500x750")

subject_id_var = tk.StringVar()

outer_container = tk.Frame(root)
outer_container.pack(fill="both", expand=True)

canvas = tk.Canvas(outer_container, highlightthickness=0, bd=0, bg=root.cget("bg"))
v_scrollbar = tk.Scrollbar(outer_container, orient="vertical", command=canvas.yview)
h_scrollbar = tk.Scrollbar(outer_container, orient="horizontal", command=canvas.xview)

main_frame = tk.Frame(canvas, padx=20, pady=20)
main_frame.pack(fill="both", expand=True)
main_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")
canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

v_scrollbar.pack(side="right", fill="y")
h_scrollbar.pack(side="bottom", fill="x")
canvas.pack(side="left", fill="both", expand=True)

def toggle_eligibility_details():
    if eligibilty_var.get() == "Yes":
        eligibility_details_frame.pack(anchor="w", pady=(0,10), after=eligibility_frame)
    else:
        eligibility_details_frame.pack_forget()

def save_form():
    os.makedirs("databases", exist_ok=True)
    print(subject_id_var)
    subject_id = subject_id_var.get()
    cleaned_text = subject_id.replace(" ","")
    subject_id_check = False
    if  not cleaned_text:
        messagebox.showinfo("Subject ID", "Must have Subject ID to continue")
    else:
        subject_id_check = True

    
    conn = sqlite3.connect("databases/patient_data.db")
    cursor = conn.cursor()
    if subject_id_check:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
            subject_id TEXT PRIMARY KEY,
            date TEXT,
            appointment_date TEXT,
            gender TEXT,
            screener TEXT,
            eligibility TEXT,
            high_familial_Risk INTEGER,
            low_familial_Risk INTEGER,
            schedule_date TEXT,
            race TEXT,
            birthweight TEXT,
            gestational TEXT,
            verbal_consent TEXT,
            initials TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO patients (
                subject_id,
                date,
                appointment_date,
                gender,
                screener,
                eligibility,
                high_familial_Risk,
                low_familial_Risk,
                schedule_date,
                race,
                birthweight,
                gestational,
                verbal_consent,
                initials
            ) VALUES (?, ?, ?, ?, ? , ? , ? , ? , ? , ? , ? , ? , ? , ? )
        """,(
                subject_id,
                date,
                appointment,
                gender,
                screener,
                eligibility,
                high_familial_risk,
                low_familial_risk,
                scheduledate,
                race,
                birthweight,
                gestationalperiod,
                verbalconsent,
                initials
            ))
        conn.commit()
        conn.close()
        report_summary = """
            Report Saved!
        """
        messagebox.showinfo("Form Saved", report_summary)


# -----------------------------
# Variables
# -----------------------------
date_var = tk.StringVar()
appointment_date_var = tk.StringVar()
gender_var = tk.StringVar()
screener_var = tk.StringVar()
eligibilty_var = tk.StringVar()
high_familial_risk_var = tk.BooleanVar()
low_familial_risk_var = tk.BooleanVar()
schedule_date_var = tk.StringVar()
race_var = tk.StringVar()
birthweight_var = tk.StringVar()
gestational_var = tk.StringVar()
verbal_consent_var = tk.StringVar()
initials_var = tk.StringVar()

date = date_var.get()
appointment = appointment_date_var.get()
gender = gender_var.get()
screener = screener_var.get()
eligibility = eligibilty_var.get()
high_familial_risk = high_familial_risk_var.get()
low_familial_risk = low_familial_risk_var.get()
scheduledate = schedule_date_var.get()
race = race_var.get()
birthweight = birthweight_var.get()
gestationalperiod = gestational_var.get()
verbalconsent = verbal_consent_var.get()
initials = initials_var.get()

# -----------------------------
# Form Layout
# -----------------------------

tk.Label(main_frame, text="New Patient Report", font=("Arial", 16, "bold")).pack()

# -----------------------------
# File Questionnaire
# -----------------------------
date_frame = tk.Frame(main_frame)
date_frame.pack(anchor="w", pady=5)
tk.Label(date_frame, text="Date").pack(anchor="w")
tk.Entry(date_frame, textvariable=date_var).pack(side="left", padx=(10,0))

subject_frame = tk.Frame(main_frame)
subject_frame.pack(anchor="w", pady=5)
tk.Label(subject_frame, text="Subject ID#").pack(anchor="w")
tk.Entry(subject_frame, textvariable=subject_id_var).pack(side="left", padx=(10,0))

screener_frame = tk.Frame(main_frame)
screener_frame.pack(anchor="w", pady=5)
tk.Label(screener_frame, text="Screener").pack(anchor="w")
tk.Entry(screener_frame, textvariable=screener_var).pack(side="left", padx=(10,0))

# -----------------------------
# Eligibility Frame
# -----------------------------

tk.Label(main_frame, text="Eligible for Participation?").pack(anchor="w")
eligibility_frame = tk.Frame(main_frame)
eligibility_frame.pack(anchor="w")

tk.Radiobutton(eligibility_frame, text="Yes", variable=eligibilty_var, value="Yes",
               command=toggle_eligibility_details).pack(side="left")
tk.Radiobutton(eligibility_frame, text="No", variable=eligibilty_var, value="No",
               command=toggle_eligibility_details).pack(side="left")

eligibility_details_frame = tk.Frame(main_frame)

tk.Checkbutton(eligibility_details_frame, text="High familial risk", variable=high_familial_risk_var).pack(anchor="w")
tk.Checkbutton(eligibility_details_frame, text="Low familial risk", variable=low_familial_risk_var).pack(anchor="w")

schedule_frame = tk.Frame(main_frame)
schedule_frame.pack(anchor="w", pady=5)
tk.Label(schedule_frame, text="Schedule Date").pack(anchor="w")
tk.Entry(schedule_frame, textvariable=schedule_date_var).pack(fill="x", pady=(0,10))

# -----------------------------
# Procedure Table
# -----------------------------



table_frame = tk.Frame(main_frame)
table_frame.pack(anchor="w", pady=20)

table_data = []

headers = ["Time", "Procedure", "Research Assistant", "Room"]

procedures = ["Consents", "Recording", "Neuropsych"]

for col, text in enumerate(headers):
    tk.Label(
        table_frame,
        text=text,
        font=("Arial",10, "bold"),
        borderwidth=1,
        relief="solid",
        width=15
    ).grid(row=0, column=col)

for row, procedure_names in enumerate(procedures, start=1):
    row_data = []

    time_entry = tk.Entry(table_frame, width=17)
    time_entry.grid(row=row, column=0)
    row_data.append(time_entry)

    tk.Label(
        table_frame,
        text=procedure_names,
        borderwidth=1,
        relief="solid",
        width=15
    ).grid(row=row, column=1)

    ra_entry = tk.Entry(table_frame, width=17)
    ra_entry.grid(row=row, column=2)
    row_data.append(ra_entry)

    room_entry = tk.Entry(table_frame, width=17)
    room_entry.grid(row=row, column=3)
    row_data.append(room_entry)

    table_data.append(row_data)

def save_data():
    conn = sqlite3.connect("patient_data.db")
    cursor = conn.cursor()

    for i, row in enumerate(table_data):
        conn = sqlite3.connect("patient_data.db")
        cursor = conn.cursor()

        time = row[0].get()
        ra = row[1].get()
        room = row[2].get()
        procedure = procedures[i]

    
        cursor.execute(
            "INSERT INTO patients (time,procedure, ra, room) VALUES (?,?,?,?)",
            (time, procedure, ra, room)
        )
    conn.commit()
    conn.close()

# -----------------------------
# Additional Questions Frame
# -----------------------------

tk.Label(main_frame, text="Before You Conclude the Interview, Do you have the Following?").pack(anchor="w")
additional_questions_frame = tk.Frame(main_frame)
additional_questions_frame.pack(anchor="w")

tk.Checkbutton(additional_questions_frame, text="Gender", variable=gender_var).pack(side="left", padx=5)
tk.Checkbutton(additional_questions_frame, text="Race", variable=race_var).pack(side="left", padx=5)
tk.Checkbutton(additional_questions_frame, text="Birth WEIGHT", variable=birthweight_var).pack(side="left", padx=5)
tk.Checkbutton(additional_questions_frame, text="GESTATIONAL AGE in Weeks", variable=gestational_var).pack(side="left", padx=5)


consent_frame = tk.Frame(main_frame)
consent_frame.pack(anchor="w", pady=5)
tk.Label(consent_frame, text="Verbal Consent Obtained").pack(anchor="w")

tk.Radiobutton(consent_frame, text="Yes", variable=verbal_consent_var, value=True).pack(side="left")
tk.Radiobutton(consent_frame, text="No", variable=verbal_consent_var, value=False).pack(side="left")

initials_frame = tk.Frame(main_frame)
initials_frame.pack(anchor="w", pady=5)
tk.Label(initials_frame,text = "Initials of person obtaining verbal consent").pack(side="left")
tk.Entry(initials_frame,textvariable=initials_var).pack(side="left" ,pady=(10,0))

# -----------------------------
# Save Button
# -----------------------------
"""
all_var = [date_var, appointment_date_var, gender_var, file_var, subject_id_var
           , screener_var, eligibilty_var, high_familial_risk_var, low_familial_risk_var
           , schedule_date_var, race_var, birthweight_var, gestational_var, verbal_consent_var
           , initials_var]
"""

tk.Button(main_frame, text="Save", command=save_form, bg="green", fg="black",
          font=("Arial", 12, "bold"), width=20).pack(pady=20)


root.mainloop()

    









