from repository.dao import DatabaseAccess
import bcrypt

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
        if self.dao.get_admin_details(username)[0] is not None:
            return False, "Username already exists."

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        success = self.dao.add_super_admin(username, hashed_pw, role='super')
        if success:
            return True, "Super Admin registered successfully."
        else:
            return False, "Error registering Super Admin. Please try again."


    def register_basic_admin(self, username, password, role):
        """Registers a new basic admin if the username is unique"""
        if not username or not password or not role:
            return False, "All fields are required."
        if self.dao.get_admin_details(username)[0] is not None:
            return False, "Username already exists."
        
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        success = self.dao.add_basic_admin(username, hashed_pw, role=role)
        if success:
            return True, "Basic admin registered successfully."
        else:
            return False, "Error registering basic admin. Please try again."


    def upload_bulk_employees(self, df):
        """Iterates through a dataframe to bulk add employees."""
        success = True
        for _, row in df.iterrows():
            # Handles slightly different column name formats
            name = row.get('name') or row.get('Name')
            role = row.get('qualification') or row.get('Role') or row.get('role')
            contract = row.get('contract_type') or row.get('Contract Type') or row.get('contract type')
            
            if name and role and contract:
                if not self.add_employee(name, role, contract):
                    success = False
        return success


    def delete_admin(self, admin_id):
        """Asks DAO to delete an admin using their ID. If DAO returns True, deletion was successful, otherwise it failed."""
        return self.dao.delete_admin(admin_id)


    def add_employee(self, name, qualification, contract_type):
        """
        Validates input, generates an ID, and calls DAO to save employee.
        """
        if not name:
            return False, "Validation failed: The name field must be populated."

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
        """Pass-through to DAO"""
        return self.dao.empty_employee_database()


    def empty_shifts_database(self):
        """Pass-through to DAO"""
        return self.dao.empty_shifts_database()


    def update_employees(self, employees_df):
        """Passes the dataframe to DAO for updates"""
        return self.dao.update_employees(employees_df)


    def update_shifts(self, shifts_df):
        """
        Passes the dataframe to DAO for updates.
        """
        return self.dao.update_shifts(shifts_df)