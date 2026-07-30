from repository.dao import DatabaseAccess
from datetime import datetime


class StaffManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def add_employee(self, name, date_of_birth, qualification, contract_type):
        """Validates input, generates an ID, and calls DAO to save employee."""
        if not name:
            return False, "Validation failed: Name field is missing."
        if not date_of_birth:
            return False, "Validation failed: Date of birth field is missing."
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
        success = self.dao.add_employee(new_id, name, date_of_birth, qualification, contract_type)
        if success:
            return True, "Employee added successfully."
        else:
            return False, "Error adding employee. Please try again."


    def add_vacation(self, employee_id, start_date, end_date):
        """Validates input and calls DAO to insert vacation."""
        if not employee_id:
            return False, "Validation failed: Employee ID is missing."
        if not start_date:
            return False, "Validation failed: Start date is missing."
        if not end_date:
            return False, "Validation failed: End date is missing."
        
        success = self.dao.insert_vacation(employee_id, start_date, end_date)
        if success:
            return True, "Vacation added successfully."
        else:
            return False, "Error adding vacation. Please try again."


    def delete_vacation(self, vacation_id):
        """Validates input and calls DAO to delete vacation."""
        if not vacation_id:
            return False, "Validation failed: Vacation ID is missing."
        
        success = self.dao.delete_vacation(vacation_id)
        if success:
            return True, "Vacation deleted successfully."
        else:
            return False, "Error deleting vacation. Please try again."


    def add_sick_leave(self, employee_id, start_date, end_date):
        """Validates input and calls DAO to insert a sick leave for an employee"""
        if not employee_id:
            return False, "Validation failed: Employee ID is missing."
        if not start_date:
            return False, "Validation failed: Start date is missing."
        if not end_date:
            return False, "Validation failed: End date is missing."
        
        success = self.dao.insert_sick_leave(employee_id, start_date, end_date)
        if success:
            return True, "Sick leave added successfully."
        else:
            return False, "Error adding sick leave. Please try again."


    def get_all_vacations_pivot(self):
        df = self.dao.get_all_vacations()
        if df.empty:
            return df
        employees_df = self.dao.get_all_employees()
        name_map = dict(zip(employees_df['id'], employees_df['name']))
        df['employee_name'] = df['employee_id'].map(name_map)
        return df[['id', 'employee_name', 'start_date', 'end_date']]


    def get_all_sick_leaves_pivot(self):
        df = self.dao.get_all_sick_leaves()
        if df.empty:
            return df
        employees_df = self.dao.get_all_employees()
        name_map = dict(zip(employees_df['id'], employees_df['name']))
        df['employee_name'] = df['employee_id'].map(name_map)
        return df[['id', 'employee_name', 'start_date', 'end_date']]


    def update_employees(self, employees_df):
        if self.dao.update_employees(employees_df):
            return True, "Personnel changes saved successfully."
        return False, "Failed to save personnel changes."


    def get_all_employees(self):
        """Pass-through to DAO"""
        return self.dao.get_all_employees()


    def max_allowed_date(self):
        """Utility function to set the maximum allowed date for the date of birth field when adding employees."""
        today = datetime.today()
        max_date = datetime(today.year - 18, today.month, today.day)  # Assuming minimum working age is 18
        return max_date.date()