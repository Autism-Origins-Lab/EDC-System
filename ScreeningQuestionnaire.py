import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox

root = tk.Tk()
root.title("Screening Questionnaire")
root.geometry("500x750")

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

conn = sqlite3.connect("databases/patient_data.db")
cursor = conn.cursor()

def save_form():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients(
            race TEXT,
            dob TEXT,
            parent_name TEXT,
            child_name TEXT,
            age TEXT,
            sex TEXT,
            address TEXT,
            male INTEGER,
            female INTEGER,
            city TEXT,
            state TEXT,
            zip TEXT,
            home_phone TEXT,
            work_phone TEXT,
            best_time_to_call TEXT,
            fax TEXT,
            email TEXT,
            mother TEXT,
            father TEXT,
            mother_age TEXT,
            father_age TEXT,
            div INTEGER,
            mar INTEGER,
            dec INTEGER,
            biological_mother INTEGER,
            biological_mother_name TEXT,
            biological_father INTEGER,
            biological_father_name TEXT,
            research_study_participitation INTEGER,
            research_study TEXT,
            research_study_when TEXT,
            research_study_where TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO patients (
            race, dob, parent_name, child_name, age, sex, address,
            male, female, city, state, zip,
            home_phone, work_phone, best_time_to_call, fax, email,
            mother, father, mother_age, father_age,
            div, mar, dec,
            biological_mother, biological_mother_name,
            biological_father, biological_father_name,
            research_study_participitation, research_study,
            research_study_when, research_study_where
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        race, dob, parent_name, child_name, Age, sex, address,
        male, female, city, state, zip,
        home_phone, work_phone, best_time_to_call, fax, email,
        mother, father, mother_age, father_age,
        div, mar, dec,
        biological_mother, biological_mother_name,
        biological_father, biological_father_name,
        research_study_participation, research_study,
        research_study_when, research_study_where
    ))

    conn.commit()
    conn.close()


# -----------------------------
# Variables
# -----------------------------

parent_name_var = tk.StringVar()
child_name_var = tk.StringVar()
DOB_var = tk.StringVar()
Age_var = tk.StringVar()
sex_var = tk.StringVar()
race_var = tk.StringVar()
address_var = tk.StringVar()
male_var = tk.BooleanVar()
female_var = tk.BooleanVar()
city_var = tk.StringVar()
state_var = tk.StringVar()
zip_var = tk.StringVar()
home_phone_var = tk.StringVar()
work_phone_var = tk.StringVar()
best_time_to_call_var = tk.StringVar()
fax_var = tk.StringVar()
email_var = tk.StringVar()
mother_var = tk.StringVar()
father_var = tk.StringVar()
mother_age_var = tk.StringVar()
father_age_var = tk.StringVar()
div_var = tk.BooleanVar()
mar_var = tk.BooleanVar()
dec_var = tk.BooleanVar()
biological_mother_var = tk.BooleanVar()
biological_mother_name_var = tk.StringVar()
biological_father_var = tk.BooleanVar()
biological_father_name_var = tk.StringVar()
research_study_participation_var = tk.BooleanVar()
research_study_var = tk.StringVar()
research_study_when_var = tk.StringVar()
research_study_where_var = tk.StringVar()

parent_name = parent_name_var.get()
child_name = child_name_var.get()
dob = DOB_var.get()
Age = Age_var.get()
sex = sex_var.get()
race = race_var.get()
address = address_var.get()
male = male_var.get()
female = female_var.get()
city = city_var.get()
state = state_var.get()
zip = zip_var.get()
home_phone = home_phone_var.get()
work_phone = work_phone_var.get()
best_time_to_call = best_time_to_call_var.get()
fax = fax_var.get()
email = email_var.get()
mother = mother_var.get()
father = father_var.get()
mother_age = mother_age_var.get()
father_age = father_age_var.get()
div = div_var.get()
mar = mar_var.get()
dec = dec_var.get()
biological_mother = biological_mother_var.get()
biological_mother_name = biological_mother_name_var.get()
biological_father = biological_father_var.get()
biological_father_name = biological_father_name_var.get()
research_study_participation = research_study_participation_var.get()
research_study = research_study_var.get()
research_study_when = research_study_when_var.get()
research_study_where = research_study_where_var.get()

# -----------------------------
# Form Layout
# -----------------------------

tk.Label(main_frame, text="IDENTIFYING INFORMATION", font=("Arial", 16, "bold")).pack(anchor="w")

parent_name_frame = tk.Frame(main_frame)
parent_name_frame.pack(anchor="w", pady=5)
tk.Label(parent_name_frame, text="Name of Parent").pack(anchor="w")
tk.Entry(parent_name_frame, textvariable=parent_name_var).pack(side="left", padx=(10,0))

child_name_frame = tk.Frame(main_frame)
child_name_frame.pack(anchor="w", pady=5)
tk.Label(child_name_frame, text="Name of Child").pack(anchor="w")
tk.Entry(child_name_frame, textvariable=child_name_var).pack(side="left", padx=(10,0))

dob_frame = tk.Frame(main_frame)
dob_frame.pack(anchor="w", pady=5)
tk.Label(dob_frame, text="Date of Birth of Child").pack(anchor="w")
tk.Entry(dob_frame, textvariable=DOB_var).pack(side="left", padx=(10,0))

tk.Label(dob_frame, text="Age").pack(side="left", padx=(10,0))
tk.Entry(dob_frame, textvariable=Age).pack(side="left", padx=(5,0))

tk.Checkbutton(dob_frame, text="Male", variable=male_var).pack(side="left", padx=5)
tk.Checkbutton(dob_frame, text="Female", variable=female_var).pack(side="left", padx=5)

race_frame = tk.Frame(main_frame)
race_frame.pack(anchor="w", pady=5)
tk.Label(race_frame, text="Race of Child").pack(anchor="w")
tk.Entry(race_frame, textvariable=race_var).pack(side="left", padx=(10,0))

address_frame = tk.Frame(main_frame)
address_frame.pack(anchor="w", pady=5)
tk.Label(address_frame, text="Address").pack(anchor="w")
tk.Entry(address_frame, textvariable=address_var).pack(side="left", padx=(10,0))

city_state_zip_frame = tk.Frame(main_frame)
city_state_zip_frame.pack(anchor="w", pady=5)
tk.Label(city_state_zip_frame, text="Home Phone").pack(anchor="w")
tk.Entry(city_state_zip_frame, textvariable=city_var).pack(side="left", padx=(10,0))

tk.Label(city_state_zip_frame, text="State").pack(side="left")
tk.Entry(city_state_zip_frame, textvariable=state_var).pack(side="left", padx=(10,0))

tk.Label(city_state_zip_frame, text="Zip").pack(side="left")
tk.Entry(city_state_zip_frame, textvariable=zip_var).pack(side="left", padx=(10.0))

phone_frame = tk.Frame(main_frame)
phone_frame.pack(anchor="w", pady=5)
tk.Label(phone_frame, text="Home Phone").pack(anchor="w")
tk.Entry(phone_frame, textvariable=home_phone_var).pack(side="left", padx=(10,0))

tk.Label(phone_frame, text="Work Phone").pack(anchor="w")
tk.Entry(phone_frame, textvariable=work_phone_var).pack(side="left", padx=(10,0))

call_frame = tk.Frame(main_frame)
call_frame.pack(anchor="w", pady=5)

tk.Label(call_frame, text="Best Time and Place to Call").pack(anchor="w")
tk.Entry(call_frame, textvariable=best_time_to_call_var).pack(side="left", padx=(10,0))

fax_email_frame = tk.Frame(main_frame)
fax_email_frame.pack(anchor="w", pady=5)
tk.Label(fax_email_frame, text="Fax").pack(anchor="w")
tk.Entry(fax_email_frame, textvariable=fax_var).pack(side="left", padx=(10,0))

tk.Label(fax_email_frame, text="Email").pack(anchor="w")
tk.Entry(fax_email_frame, textvariable=email_var).pack(side="left", padx=(10,0))

mother_frame = tk.Frame(main_frame)
mother_frame.pack(anchor="w", pady=5)
tk.Label(mother_frame, text="Mother").pack(anchor="w")
tk.Entry(mother_frame, textvariable=mother_var).pack(side="left", padx=(10,0))

tk.Label(mother_frame, text="Age").pack(side="left")
tk.Entry(mother_frame, textvariable=mother_age_var).pack(side="left", padx=(10,0))
tk.Checkbutton(mother_frame, text="Div", variable=div_var).pack(side="left", padx=5)
tk.Checkbutton(mother_frame, text="Mar", variable=mar_var).pack(side="left", padx=5)
tk.Checkbutton(mother_frame, text="Dec", variable=dec_var).pack(side="left", padx=5)

father_frame = tk.Frame(main_frame)
father_frame.pack(anchor="w", pady=5)
tk.Label(father_frame, text="Father").pack(anchor="w")
tk.Entry(father_frame, textvariable=father_var).pack(side="left", padx=(10,0))

tk.Label(father_frame, text="Age").pack(side="left")
tk.Entry(father_frame, textvariable=father_age_var).pack(side="left", padx=(10,0))
tk.Checkbutton(father_frame, text="Div", variable=div_var).pack(side="left", padx=5)
tk.Checkbutton(father_frame, text="Mar", variable=mar_var).pack(side="left", padx=5)
tk.Checkbutton(father_frame, text="Dec", variable=dec_var).pack(side="left", padx=5)

# -----------------------------
# Biological Parents Layout
# -----------------------------

biological_mother_frame = tk.Frame(main_frame)
biological_mother_frame.pack(anchor="w", pady=5)
biological_mother_entry = tk.Entry(biological_mother_frame, textvariable=biological_mother_name, state="disabled")
biological_mother_entry.pack(side="left")
tk.Label(biological_mother_frame, text="Clarify whether the person listed under Mother is the newborn's biological mother?").pack(anchor="w")

def toggle_mother():
    if biological_mother_var.get() == True:
        biological_mother_name.set(mother_var.get())
        biological_mother_entry.config(state="disabled")
    else:
        biological_mother_name.set("")
        biological_mother_entry.config(state="normal")

tk.Radiobutton(biological_mother_frame, text="Yes, biological mother's name is listed above", variable=biological_mother_var, value=True, command=toggle_mother).pack(anchor="w")
tk.Radiobutton(biological_mother_frame, text="No. The newborn's biological mother's name is", variable=biological_mother_var, value=False, command=toggle_mother).pack(anchor="w")

biological_father_frame = tk.Frame(main_frame)
biological_father_frame.pack(anchor="w", pady=5)
biological_father_entry = tk.Entry(biological_father_frame, textvariable=biological_father_name, state="disabled")
biological_father_entry.pack(side="left")
tk.Label(biological_father_frame, text="Clarify whether the person listed under Father is the newborn's biological father?").pack(anchor="w")

def toggle_father():
    if biological_father_var.get() == True:
        biological_father_name.set(father_var.get())
        biological_father_entry.config(state="disabled")
    else:
        biological_father_name.set("")
        biological_father_entry.config(state="normal")

tk.Radiobutton(biological_father_frame, text="Yes, biological father's name is listed above", variable=biological_father_var, value=True, command=toggle_father).pack(anchor="w")
tk.Radiobutton(biological_father_frame, text="No. The newborn's biological father's name is", variable=biological_father_var, value=False, command=toggle_father).pack(anchor="w")

research_study_frame = tk.Frame(main_frame)
research_study_frame.pack(anchor="w", pady=5)

tk.Label(research_study_frame, text="Is your family presently or have they ever participated in a Research study").pack(anchor="w")
tk.Radiobutton(research_study_frame, text="Yes", variable=research_study_participation, value=True).pack(anchor="w")
tk.Radiobutton(research_study_frame, text="No", variable=research_study_participation, value=False).pack(anchor="w")
tk.Label(research_study_frame, text="If yes, what study").pack(anchor="w")
tk.Entry(research_study_frame, textvariable=research_study).pack(side="left")
tk.Label(research_study_frame, text="When?").pack(anchor="w")
tk.Entry(research_study_frame, textvariable=research_study_when).pack(side="left")
tk.Label(research_study_frame, text="Where?").pack(anchor="w")
tk.Entry(research_study_frame, textvariable=research_study_where).pack(side="left")

# -----------------------------
# Save Button
# -----------------------------
tk.Button(main_frame, text="Save", command=save_form, bg="green", fg="black",
          font=("Arial", 12, "bold"), width=20).pack(pady=20)

root.mainloop()
