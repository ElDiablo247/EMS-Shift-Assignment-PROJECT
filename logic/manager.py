from repository.dao import DatabaseAccess

class Manager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def add_employee(self, name, qualification, contract_type):
        """
        Validates input, generates an ID, and calls DAO to save employee.
        """
        if not name:
            print("Validation failed: The name field must be populated.")
            return False

        # ID Generation
        last_id = self.dao.get_last_employee_id()
        if last_id is not None:
            new_id = last_id + 1
        else:
            new_id = 6001  # Starting ID for employees if database is empty
        return self.dao.add_employee(new_id, name, qualification, contract_type)


    def add_shift(self, shift_name, shift_start, shift_end, shift_duration):
        """
        Validates input, generates an ID, and calls DAO to save shift.
        """
        if not shift_name or not shift_start or not shift_end:
            print("Validation failed: All shift fields must be populated.")
            return False

        # ID Generation
        last_id = self.dao.get_last_shift_id()
        if last_id is not None:
            new_id = last_id + 1
        else:
            new_id = 101  # Starting ID for shifts if database is empty
        return self.dao.add_shift(new_id, shift_name, shift_start, shift_end, shift_duration)


    def get_all_employees(self):
        """Pass-through to DAO"""
        return self.dao.get_all_employees()


    def get_all_shifts(self):
        """Pass-through to DAO"""
        return self.dao.get_all_shifts()


    def empty_employee_database(self):
        """Pass-through to DAO"""
        return self.dao.empty_employee_database()


    def empty_shifts_database(self):
        """Pass-through to DAO"""
        return self.dao.empty_shifts_database()


    def update_employees(self, employees_df):
        """
        Passes the dataframe to DAO for updates. 
        (Future business logic for updates would go here before calling DAO)
        """
        return self.dao.update_employees(employees_df)


    def update_shifts(self, shifts_df):
        """
        Passes the dataframe to DAO for updates.
        """
        return self.dao.update_shifts(shifts_df)