from repository.dao import DatabaseAccess
from datetime import datetime


class StaffManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def add_employee(self, name, date_of_birth, qualification, contract_type):
        """
        Validates input, generates an ID, and calls DAO to save employee.
        """
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


    def update_employees(self, employees_df):
        if self.dao.update_employees(employees_df):
            return True, "Personnel changes saved successfully."
        return False, "Failed to save personnel changes."


    def get_all_employees(self):
        """Pass-through to DAO"""
        return self.dao.get_all_employees()


    def delete_employee(self, emp_id):
        if self.dao.delete_employee(emp_id):
            return True, f"Employee with ID {emp_id} has been deleted."
        return False, "Failed to delete employee. Please check the ID and try again."


    def empty_employee_database(self):
        if self.dao.empty_employee_database():
            return True, "All employee data has been cleared."
        return False, "Failed to clear employee data."


    def max_allowed_date(self):
        """Utility function to set the maximum allowed date for the date of birth field when adding employees."""
        today = datetime.today()
        max_date = datetime(today.year - 18, today.month, today.day)  # Assuming minimum working age is 18
        return max_date.date()