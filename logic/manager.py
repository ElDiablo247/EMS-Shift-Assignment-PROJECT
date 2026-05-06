from repository.dao import DatabaseAccess
import bcrypt
import re
import pandas as pd
from datetime import datetime

class Manager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def verify_login(self, username, password):
        """
        Verifies user credentials and returns their role on success.
        Returns: (bool: success, str: role or None)
        """
        password_hash, role = self.dao.get_admin_details(username)
        if password_hash:
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return True, role
        return False, None


    def admins_exist(self):
        """Checks if there are any admins in the database."""
        return self.dao.admins_exist()


    def register_super_admin(self, username, password, confirm_password):
        """Registers a new super admin if the username is unique and passwords match."""
        if not username or not password or not confirm_password:
            return False, "All fields are required."
        if password != confirm_password:
            return False, "Passwords do not match."
        if not self.is_password_strong(password):
            return False, "Password must be at least 8 characters long, and include at least one uppercase letter and one symbol."

        if self.dao.get_admin_details(username)[0] is not None:
            return False, "Username already exists."

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        success = self.dao.add_super_admin(username, hashed_pw, role='super')
        if success:
            return True, "Super Admin registered successfully."
        else:
            return False, "Error registering Super Admin. Please try again."


    def register_basic_admin(self, username, password, confirm_password, role):
        """Registers a new basic admin if the username is unique and passwords match, through the admin control panel."""
        if not username or not password or not confirm_password or not role:
            return False, "All fields are required."
        if password != confirm_password:
            return False, "Passwords do not match."
        if not self.is_password_strong(password):
            return False, "Password must be at least 8 characters long, and include at least one uppercase letter and one symbol."

        if self.dao.get_admin_details(username)[0] is not None:
            return False, "Username already exists."
        
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        success = self.dao.add_basic_admin(username, hashed_pw, role=role)
        if success:
            return True, "Basic admin registered successfully."
        else:
            return False, "Error registering basic admin. Please try again."


    def is_password_strong(self, password):
        """
        Verifies if a password meets the security constraints.
        - At least 8 characters
        - At least one uppercase letter
        - At least one symbol
        Returns True if the password is strong, False otherwise.
        """
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[^a-zA-Z0-9]', password):
            return False
        return True


    def upload_bulk_employees(self, uploaded_file):
        """
        Reads an uploaded file (CSV or Excel), converts it to a DataFrame,
        and iterates through it to bulk add employees.
        """
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
        except Exception as e:
            return False, f"Error reading file: {e}"

        failed_rows = []
        
        if not df.empty:
            # Make all column names to lowercase for accurate matching
            df.columns = [col.lower().strip() for col in df.columns]

            for index, row in df.iterrows():
                name = row.get('name')
                qualification = row.get('qualification')
                contract_type = row.get('contract type')
            
                # If any employee fails validation or insertion, we add its index to the failed_rows list
                success, _ = self.add_employee(name, qualification, contract_type)
                if not success:
                    failed_rows.append(str(index + 2))
        else:
            return False, "The uploaded file is empty. Please provide a valid file with employee data."
        
        message = "Bulk upload completed. The following rows failed (likely due to missing values): " + ", ".join(failed_rows) if failed_rows else "All employees added successfully."
        return True, message


    def upload_bulk_shifts(self):
        """
        Populates the shifts table with a predefined set of shifts. This is a one-click solution to quickly set up the system with commonly used shifts.
        """
        shifts = [
            {"name": "K1", "start": "06:30", "end": "15:00", "duration": 8},
            {"name": "K2", "start": "06:30", "end": "15:00", "duration": 8},
            {"name": "K4", "start": "15:00", "end": "23:30", "duration": 8},
            {"name": "K5", "start": "15:00", "end": "23:30", "duration": 8},
            {"name": "K3", "start": "07:30", "end": "16:00", "duration": 8},
            {"name": "K6", "start": "21:00", "end": "05:30", "duration": 8}
        ]
        for shift in shifts: 
            start_time = datetime.strptime(shift["start"], "%H:%M").time()
            end_time = datetime.strptime(shift["end"], "%H:%M").time()
            self.add_shift(shift["name"], start_time, end_time, shift["duration"])


    def delete_admin(self, admin_id):
        if self.dao.delete_admin(admin_id):
            return True, f"Admin with ID {admin_id} has been deleted."
        return False, "Failed to delete admin. Please check the ID and try again."


    def delete_employee(self, emp_id):
        if self.dao.delete_employee(emp_id):
            return True, f"Employee with ID {emp_id} has been deleted."
        return False, "Failed to delete employee. Please check the ID and try again."


    def delete_shift(self, shift_id):
        if self.dao.delete_shift(shift_id):
            return True, f"Shift with ID {shift_id} has been deleted."
        return False, "Failed to delete shift. Please check the ID and try again."


    def add_employee(self, name, qualification, contract_type):
        """
        Validates input, generates an ID, and calls DAO to save employee.
        """
        if not name:
            return False, "Validation failed: Name field is missing."
        if not qualification:
            return False, "Validation failed: Qualification field is missing."
        if not contract_type:
            return False, "Validation failed: Contract type field is missing."
        
        # ID Generation
        last_id = self.dao.get_last_employee_id()
        if last_id is not None:
            new_id = last_id + 1
        else:
            new_id = 6001  # Starting ID for employees if database is empty
        success = self.dao.add_employee(new_id, name, qualification, contract_type)
        if success:
            return True, "Employee added successfully."
        else:
            return False, "Error adding employee. Please try again."


    def add_shift(self, shift_name, shift_start, shift_end, shift_duration):
        """
        Validates input, generates an ID, and calls DAO to save shift.
        """
        if not shift_name or not shift_start or not shift_end:
            return False, "Validation failed: All shift fields must be populated."

        # ID Generation
        last_id = self.dao.get_last_shift_id()
        if last_id is not None:
            new_id = last_id + 1
        else:
            new_id = 101  # Starting ID for shifts if database is empty
        success = self.dao.add_shift(new_id, shift_name, shift_start, shift_end, shift_duration)
        if success:
            return True, "Shift added successfully."
        else:
            return False, "Error adding shift. Please try again."


    def get_all_employees(self):
        """Pass-through to DAO"""
        return self.dao.get_all_employees()


    def get_all_shifts(self):
        """Pass-through to DAO"""
        return self.dao.get_all_shifts()


    def get_all_admins(self):
        """Pass-through to DAO."""
        return self.dao.get_all_admins()


    def empty_employee_database(self):
        if self.dao.empty_employee_database():
            return True, "All employee data has been cleared."
        return False, "Failed to clear employee data."


    def empty_shifts_database(self):
        if self.dao.empty_shifts_database():
            return True, "All shifts have been cleared."
        return False, "Failed to clear shift data."


    def update_employees(self, employees_df):
        if self.dao.update_employees(employees_df):
            return True, "Personnel changes saved successfully."
        return False, "Failed to save personnel changes."


    def update_shifts(self, shifts_df):
        if self.dao.update_shifts(shifts_df):
            return True, "Shift definitions updated successfully."
        return False, "Failed to update shift definitions."
    

    def populate_constraints(self):
        """
        This function is executed the very first moment when the super admin is registered.
        The purpose of the function is to insert the available constraints to the Database so the user can later modify their values.
        """
        weekday_shifts = {
            "category": "Shifts per day",
            "constraint_key": "Weekdays",
            "constraint_value": [],
            "description": "These shifts should run on a regular weekday (Monday to Friday)"
        }
        saturday_shifts = {
            "category": "Shifts per day",
            "constraint_key": "Saturday",
            "constraint_value": [],
            "description": "These shifts should run on a regular Saturday"
        }
        sunday_shifts = {
            "category": "Shifts per day",
            "constraint_key": "Sunday",
            "constraint_value": [],
            "description": "These shifts should run on a regular Sunday"
        }
        holiday_shifts = {
            "category": "Shifts per day",
            "constraint_key": "Holiday",
            "constraint_value": [],
            "description": "These shifts should run on public holidays for the given German state."
        }
        fulltime_hours = {
            "category": "Contract hours",
            "constraint_key": "Full-time",
            "constraint_value": None,
            "description": "How many hours a Full-time employee should work per week"
        }
        holiday_region = {
            "category": "Holidays",
            "constraint_key": "Region",
            "constraint_value": None,
            "description": "German State for public holidays (initials)"
        }
        break_between_shifts = {
            "category": "Work hours",
            "constraint_key": "Between Shifts",
            "constraint_value": 11,
            "description": "This is the minimum rest period (in hours) between shifts"
        }
        weekly_max_hours = {
            "category": "Work hours",
            "constraint_key": "Weekly Max",
            "constraint_value": 48,
            "description": "This is the maximum hours an employee can work per week"
        }


        constraints_list = [
            weekday_shifts,
            saturday_shifts,
            sunday_shifts,
            holiday_shifts,
            fulltime_hours,
            holiday_region,
            break_between_shifts,
            weekly_max_hours,
        ]

        if self.dao.populate_constraints(constraints_list):
            return True, "Constraints were successfully inserted in the Database!"
        return False, "Insertion of constraints in the database failed. Check the constraints and try again"


    def return_shift_names(self):
        """Fetches all shifts and filters out just the active shift names as a list."""
        shifts_df = self.get_all_shifts()
        if shifts_df.empty:
            return []
        
        active_shifts = shifts_df[shifts_df['is_active'] == True]
        return active_shifts['shift_name'].tolist()


    def get_all_constraints(self):
        """Pass-through to fetch constraints DataFrame."""
        return self.dao.get_all_constraints()


    def update_multiple_constraints(self, constraints_df):
        """Calls DAO to update constraints."""
        if self.dao.update_multiple_constraints(constraints_df):
            return True, "Constraints updated successfully."
        return False, "Failed to update constraints."


    def get_shifts_per_day_constraints(self):
        """Fetches and filters constraints specifically for the shifts per day section."""
        df = self.get_all_constraints()
        if df.empty:
            return df
        return df[df['category'].isin(['Shifts per day'])].copy()


    def update_single_constraint(self, category, key, new_value):
        """Utility function to update a single constraint value, used for the holiday region and full-time hours."""
        if self.dao.update_single_constraint(category, key, new_value):
            return True, f"{key} constraint updated successfully."
        return False, f"Failed to update {key} constraint. Please try again."


    def dev_add_constraint(self, category, key, value_str, description):
        """Developer tool to inject constraints natively."""
        import json
        if not category or not key:
            return False, "Category and Key are required fields."
        
        parsed_value = None
        if value_str:
            try:
                parsed_value = json.loads(value_str)
            except Exception:
                parsed_value = value_str  # Fallback to pure string if it isn't valid JSON list/number

        if self.dao.dev_add_constraint(category, key, parsed_value, description):
            return True, f"Constraint '{key}' successfully injected."
        return False, "Failed to inject constraint."


    def dev_delete_constraint(self, constraint_id):
        """Developer tool to delete constraints by ID."""
        if self.dao.dev_delete_constraint(constraint_id):
            return True, f"Constraint with ID {constraint_id} has been deleted."
        return False, "Failed to delete constraint. Please check the input and try again."