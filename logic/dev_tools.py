from repository.dao import DatabaseAccess
from datetime import datetime
import json
from logic.schedule_manager import ScheduleManager


class Developer:
    def __init__(self):
        # Initialize all the standard managers to act as our Facade.
        # This gives the Developer class safe access to all business logic.
        self.dao = DatabaseAccess()


    def dev_upload_bulk_employees(self):
        """Populates the database with staff members."""
        
        staff_data = [
            {"name": "Tom Holland", "date_of_birth": "1996-06-01", "qualification": "RS", "contract_type": "100%", "is_active": True},
            {"name": "Raul Birta", "date_of_birth": "1992-03-15", "qualification": "RH", "contract_type": "75%", "is_active": True},
            {"name": "Sarah Jenkins", "date_of_birth": "1988-11-20", "qualification": "RS", "contract_type": "Flexible", "is_active": True},
            {"name": "Michael Chen", "date_of_birth": "1994-07-12", "qualification": "RH", "contract_type": "100%", "is_active": True},
            {"name": "Elena Rodriguez", "date_of_birth": "1991-01-30", "qualification": "RS", "contract_type": "75%", "is_active": True},
            {"name": "James Wilson", "date_of_birth": "1985-09-05", "qualification": "RH", "contract_type": "50%", "is_active": True},
            {"name": "Amina Yusuf", "date_of_birth": "1997-04-22", "qualification": "RS", "contract_type": "100%", "is_active": True},
            {"name": "David Thompson", "date_of_birth": "1990-12-10", "qualification": "RH", "contract_type": "100%", "is_active": True},
            {"name": "Lucia Rossi", "date_of_birth": "1993-02-28", "qualification": "RS", "contract_type": "75%", "is_active": True},
            {"name": "Kevin O'Sullivan", "date_of_birth": "1989-08-14", "qualification": "RH", "contract_type": "Flexible", "is_active": True},
            {"name": "Sophie Martin", "date_of_birth": "1995-10-03", "qualification": "RS", "contract_type": "100%", "is_active": True},
            {"name": "Ahmed Al-Farsi", "date_of_birth": "1994-05-18", "qualification": "RH", "contract_type": "75%", "is_active": True},
            {"name": "Emma Watson", "date_of_birth": "1990-04-15", "qualification": "RS", "contract_type": "Flexible", "is_active": True},
            {"name": "Liam Gallagher", "date_of_birth": "1972-09-21", "qualification": "RH", "contract_type": "100%", "is_active": True},
            {"name": "Chloe Bennett", "date_of_birth": "1992-04-18", "qualification": "RS", "contract_type": "50%", "is_active": True},
            {"name": "Raaaa", "date_of_birth": "1997-12-29", "qualification": "RS", "contract_type": "100%", "is_active": True}
        ]

        for person in staff_data:
            # ID Generation
            last_id = self.dao.get_last_employee_id()
            if last_id is not None:
                new_id = last_id + 1
            else:
                new_id = 6001  # Starting ID for employees if database is empty
            dob_obj = datetime.strptime(person["date_of_birth"], "%Y-%m-%d").date() # Convert string DOB to date object 
            self.dao.add_employee(
                emp_id=new_id, 
                name=person["name"], 
                date_of_birth=dob_obj, 
                qualification=person["qualification"], 
                contract_type=person["contract_type"]
            )
        return True, "Bulk employees successfully added."


    def dev_upload_bulk_shifts(self):
        """Populates the shifts table with a predefined set of shifts. This is a one-click solution to quickly set up the system with shifts."""
        shifts = [
            {"name": "K1", "start": "06:30", "end": "15:00", "duration": 8, "runs_on_weekend_or_holiday": True},
            {"name": "K2", "start": "06:30", "end": "15:00", "duration": 8, "runs_on_weekend_or_holiday": False},
            {"name": "K4", "start": "15:00", "end": "23:30", "duration": 8, "runs_on_weekend_or_holiday": False},
            {"name": "K5", "start": "15:00", "end": "23:30", "duration": 8, "runs_on_weekend_or_holiday": False},
            {"name": "K3", "start": "07:30", "end": "16:00", "duration": 8, "runs_on_weekend_or_holiday": False},
            {"name": "K6", "start": "21:00", "end": "05:30", "duration": 8, "runs_on_weekend_or_holiday": False}
        ]
        for shift in shifts:
            last_id = self.dao.get_last_shift_id()
            if last_id is not None:
                new_id = last_id + 1
            else:
                new_id = 101  # Starting ID for shifts if database is empty
            start_time = datetime.strptime(shift["start"], "%H:%M").time()
            end_time = datetime.strptime(shift["end"], "%H:%M").time()
            self.dao.add_shift(new_id, shift["name"], start_time, end_time, shift["duration"], shift["runs_on_weekend_or_holiday"])
        return True, "Bulk shifts populated successfully."


    def dev_add_constraint(self, category, key, value_str, description):
        """Developer tool to inject constraints natively."""
        if not category or not key:
            return False, "Category and Key are required fields."
        
        parsed_value = None
        if value_str:
            try:
                parsed_value = json.loads(value_str)
            except Exception:
                parsed_value = value_str

        if self.dao.dev_add_constraint(category, key, parsed_value, description):
            return True, f"Constraint '{key}' successfully injected."
        return False, f"Failed to inject constraint '{key}'."


    def dev_delete_constraint(self, constraint_id):
        """Developer tool to delete constraints by ID."""
        if self.dao.dev_delete_constraint(constraint_id):
            return True, f"Constraint with ID {constraint_id} has been deleted."
        return False, "Failed to delete constraint. Please check the input and try again."


    def dev_full_schedule_run(self, month, year):
        """Runs all three scheduling steps at once for testing — template → paramedics → RH."""
        sm = ScheduleManager()

        # Step 1: empty template
        success, message, _ = sm.generate_empty_template(month, year)
        if not success:
            return False, f"Template failed: {message}"

        # Step 2: paramedics
        success, message = sm.assign_paramedics_to_weekdays_shifts(month, year)
        if not success:
            return False, f"Paramedics failed: {message}"

        # Step 3: assistants
        success, message = sm.assign_rh_to_weekdays_shifts(month, year)
        if not success:
            return False, f"Assistants failed: {message}"

        return True, f"Full schedule for {month}/{year} completed — template, paramedics, and assistants."


    def dev_delete_assignments_for_month(self, month, year):
        """Permanently deletes all assignment records for a specific month and year."""
        success, count = self.dao.dev_delete_assignments_for_month(month, year)
        if success:
            return True, f"Successfully deleted {count} assignment(s) for {month}/{year}."
        return False, "Database error: Failed to delete assignments."