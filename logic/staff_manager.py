from repository.dao import DatabaseAccess
from datetime import datetime
from datetime import timedelta


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
        """Expands the date range into individual dates and inserts one row per date."""
        employees = self.dao.get_all_employees()
        if employee_id not in employees['id'].values:
            return False, "Validation failed: Employee ID does not exist."
        if not employee_id:
            return False, "Validation failed: Employee ID is missing."
        if employee_id < 6001:
            return False, "Validation failed: Employee ID is below the valid range."
        if not start_date:
            return False, "Validation failed: Start date is missing."
        if not end_date:
            return False, "Validation failed: End date is missing."
        if end_date < start_date:
            return False, "Validation failed: End date cannot be before start date."
        
        from datetime import timedelta
        current = start_date
        count = 0
        while current <= end_date:
            if self.dao.insert_vacation(employee_id, current):
                count += 1
            current += timedelta(days=1)
        
        if count > 0:
            return True, f"{count} vacation day(s) added successfully."
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


    def get_all_vacations_pivot(self):
        df = self.dao.get_all_vacations()
        if df.empty:
            return df
        employees_df = self.dao.get_all_employees()
        name_map = dict(zip(employees_df['id'], employees_df['name']))
        df['employee_name'] = df['employee_id'].map(name_map)
        return df[['id', 'employee_name', 'vacation_date']]


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