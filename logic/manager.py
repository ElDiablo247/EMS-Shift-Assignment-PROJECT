from repository.dao import DatabaseAccess
import bcrypt
import re
import pandas as pd

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