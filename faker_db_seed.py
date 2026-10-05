# Thus script is intended to be run from the command line, with the arguments --count and --seed.
# 		python faker_db_seed.py --count 60 --seed 42
# It will add synthetic patients and related form data to the local database.


import argparse
from datetime import datetime, timezone

from faker import Faker

from app.database.connection import get_connection
from app.database.migration import run_migrations


def seed_fake_data(patient_count: int = 60, seed: int = 42) -> int:
	if patient_count < 1:
		raise ValueError("patient_count must be at least 1")

	fake = Faker()
	fake.seed_instance(seed)
	run_migrations()

	with get_connection() as connection:
		existing_ids = connection.execute( # because we want to avoid duplicate subject_ids, we need to find the highest existing FAKE- number and increment from there
			"SELECT subject_id FROM patients WHERE subject_id LIKE 'FAKE-%'"
		).fetchall()
		fake_numbers = []
		for row in existing_ids:
			try:
				fake_numbers.append(int(row["subject_id"].removeprefix("FAKE-")))
			except ValueError:
				continue
		next_number = max(fake_numbers, default=0) + 1

		# patient overview data
		for offset in range(patient_count):
			child_name = fake.name()
			date_of_birth = fake.date_between(
				start_date="-8y", end_date="-1y"
			).isoformat()
			sex = fake.random_element(("Female", "Male"))
			race = fake.random_element(
				("Asian", "Black", "White", "Multiracial", "Other")
			)
			subject_id = f"FAKE-{next_number + offset:06d}"

			cursor = connection.execute(
				"""
				INSERT INTO patients (subject_id, child_name, form_status,
									 date_of_birth, sex, race)
				VALUES (?, ?, ?, ?, ?, ?)
				""",
				(subject_id, child_name, fake.random_element(("Pending", "In Progress", "Complete")),
				 date_of_birth, sex, race),
			)
			patient_id = cursor.lastrowid
			parent_name = fake.name()
			screening_date = fake.date_between(start_date="-2y", end_date="today")
			eligibility = fake.random_element(("Yes", "No", "Pending"))

			# screening questionnaires
			connection.execute(
				"""
				INSERT INTO telephone_screenings (
					patient_id, screening_date, appointment_date, screener,
					eligibility, eligibility_comment, high_familial_risk,
					low_familial_risk, schedule_date, birthweight, gestational,
					verbal_consent, consent_initials
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				(
					patient_id,
					screening_date.isoformat(),
					fake.future_date(end_date="+90d").isoformat(),
					fake.name(),
					eligibility,
					"Not eligible for x reason" if eligibility == "No" else None,
					int(fake.boolean()),
					int(fake.boolean()),
					fake.future_date(end_date="+90d").isoformat(),
					f"{fake.pydecimal(min_value=2, max_value=5, right_digits=1)} kg",
					f"{fake.random_int(min=35, max=41)} weeks",
					int(fake.boolean(chance_of_getting_true=85)),
					fake.bothify(text="??").upper(),
				),
			)

			# family history and demographics
			connection.execute(
				"""
				INSERT INTO screening_questionnaires (
					patient_id, parent_name, child_name, date_of_birth, age,
					sex, race, address, city, state, zip_code, home_phone,
					email, mother_name, father_name, mother_age, father_age,
					biological_mother, biological_mother_name,
					biological_father, biological_father_name,
					research_participation, research_study
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				(
					patient_id, parent_name, child_name, date_of_birth,
					str((datetime.now(timezone.utc).date() - datetime.fromisoformat(date_of_birth).date()).days // 365),
					sex, race, fake.street_address(), fake.city(), fake.state_abbr(),
					fake.postcode(), fake.phone_number(), fake.email(),
					parent_name, fake.name(), str(fake.random_int(min=20, max=45)),
					str(fake.random_int(min=20, max=50)), int(fake.boolean()),
					parent_name, int(fake.boolean()), fake.name(), int(fake.boolean()),
					fake.catch_phrase(),
				),
			)

			# medical history
			connection.execute(
				"""
				INSERT INTO medical_histories (
					patient_id, general_health, seen_neurologist,
					neurologist_description, head_injury, head_injury_description,
					genetic_abnormalities, genetic_abnormalities_description,
					seizure_epileptic_attack, gestational_age, birthweight,
					birthlength, pregnancy_complications,
					pregnancy_complications_description
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				(
					patient_id, fake.random_element(("Excellent", "Good", "Fair")),
					int(fake.boolean(chance_of_getting_true=10)), None,
					int(fake.boolean(chance_of_getting_true=8)), None,
					int(fake.boolean(chance_of_getting_true=5)), None,
					int(fake.boolean(chance_of_getting_true=4)),
					f"{fake.random_int(min=35, max=41)} weeks",
					f"{fake.pydecimal(min_value=2, max_value=5, right_digits=1)} kg",
					f"{fake.pydecimal(min_value=40, max_value=55, right_digits=1)} cm",
					int(fake.boolean(chance_of_getting_true=15)), None,
				),
			)
			connection.execute(
				"""
				INSERT INTO family_medical_histories (
					patient_id, family_psychiatric, family_psychiatric_description,
					parent_autism, parent_schizophrenia, parent_learning_disability,
					parent_substance_abuse, has_siblings, sibling_autism,
					sibling_adhd, same_father_as_older_sibling,
					same_mother_as_older_sibling
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				(
					patient_id, int(fake.boolean(chance_of_getting_true=15)), None,
					int(fake.boolean(chance_of_getting_true=5)),
					int(fake.boolean(chance_of_getting_true=3)),
					int(fake.boolean(chance_of_getting_true=8)),
					int(fake.boolean(chance_of_getting_true=8)),
					int(fake.boolean(chance_of_getting_true=60)),
					int(fake.boolean(chance_of_getting_true=5)),
					int(fake.boolean(chance_of_getting_true=10)),
					int(fake.boolean()), int(fake.boolean()),
				),
			)
	return patient_count



def main() -> None:
	parser = argparse.ArgumentParser(description="Add synthetic patients and form data to the local database.")
	parser.add_argument("--count", type=int, default=60, help="Number of fake patients to add (default: 60).")
	parser.add_argument("--seed", type=int, default=42, help="Faker random seed (default: 42).")
	args = parser.parse_args()

	added = seed_fake_data(args.count, args.seed)
	print(f"Added {added} fake patients and related records.")


if __name__ == "__main__":
	main()
