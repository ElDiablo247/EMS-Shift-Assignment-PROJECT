from logic.database import db_obj
from logic.models import Employee, Shifts, Assignments
import pandas as pd

class Manager:
    def __init__(self):
        self.db = db_obj


    def add_employee(self, name, qualification, contract_type):
        """
        Creates a new employee object and saves it to the database.
        """
        
        generated_id = self.employee_id_generator() # Uses this class's own method to generate an employee ID

        if not name:
            return False, "All fields must be populated."

        # A new employee object is created with the provided details and the generated ID.
        try:
            with self.db.get_session() as session:
                new_staff = Employee(
                    id=generated_id,
                    name=name,
                    qualification=qualification,
                    contract_type=contract_type
                )
                session.add(new_staff)
            return True, "Employee has been added."
        except Exception as e:
            return False, f"Error occurred: {e}"

    def add_shift(self, shift_name, shift_start, shift_end, shift_duration):
        """
        Creates a new shift object and saves it to the database.
        """
        generated_id = self.shift_id_generator() # Uses this class's own method to generate a shift ID

        if not shift_name or not shift_start or not shift_end:
            return False, "All fields must be populated."
        # A new shift object is created with the provided details and the generated ID.
        try:
            with self.db.get_session() as session:
                new_shift = Shifts(
                    id=generated_id,
                    shift_name=shift_name,
                    shift_start=shift_start,
                    shift_end=shift_end,
                    shift_duration=shift_duration
                )
                session.add(new_shift)
            return True, "Shift has been added."
        except Exception as e:
            return False, f"Error occurred: {e}"

    def get_all_employees(self):
        """
        Retrieves all employees from the database and formats them for display.
        """
        with self.db.get_session() as session:
            query = session.query(Employee).order_by(Employee.id)
            # Using pandas to convert the SQLAlchemy query result into a DataFrame for easier display in Streamlit
            return pd.read_sql(query.statement, session.bind)
        
    def get_all_shifts(self):
        """
        Retrieves all shifts from the database and formats them for display.
        """
        with self.db.get_session() as session:
            query = session.query(Shifts).order_by(Shifts.shift_name)
            return pd.read_sql(query.statement, session.bind)
        
    def empty_database(self):
        """Wipes all data from the tables."""
        try:
            with self.db.get_session() as session:
                session.query(Employee).delete()
                session.query(Shifts).delete()
            return True, "All data has been cleared."
        except Exception as e:
            return False, f"Error clearing database: {e}"

    def employee_id_generator(self):
        """
        Sets the employee_id for a new employee. Starts at 6001 if no employees exist, else increments from the highest existing ID in the employees table.
        """
        try:
            with self.db.get_session() as session:
                max_id = session.query(Employee).order_by(Employee.id.desc()).first()
                if max_id:
                    return max_id.id + 1
                else:   
                    return 6001
        except Exception as e:
            print(f"Error generating ID: {e}")
            return 6001
        
    def shift_id_generator(self):
        """
        Sets the shift_id for a new shift. Starts at 1 if no shifts exist, else increments from the highest existing ID in the shifts table.
        """
        try:
            with self.db.get_session() as session:
                max_id = session.query(Shifts).order_by(Shifts.id.desc()).first()
                if max_id:
                    return max_id.id + 1
                else:   
                    return 1
        except Exception as e:
            print(f"Error generating ID: {e}")
            return 1