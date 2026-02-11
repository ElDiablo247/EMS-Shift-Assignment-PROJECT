from database import db_obj
from models import Employee, Shifts
import pandas as pd

class Manager:
    def __init__(self):
        self.db = db_obj


    def add_employee(self, name, hours_required, qualification, contract_type):
        """
        Creates a new employee object and saves it to the database.
        """
        
        generated_id = self.id_generator() # Uses this class's own method to generate an ID

        if not name:
            return False, "All fields must be populated."

        # A new employee object is created with the provided details and the generated ID.
        try:
            with self.db.get_session() as session:
                new_staff = Employee(
                    id=generated_id,
                    name=name,
                    hours_required=hours_required,
                    hours_completed=0.0,
                    qualification=qualification,
                    contract_type=contract_type
                )
                session.add(new_staff)
            return True, "Employee has been added."
        except Exception as e:
            return False, f"Error occurred: {e}"

    def add_shift(self, shift_id, shift_name, shift_start, shift_end):
        """
        Creates a new shift object and saves it to the database.
        """
        if not shift_name or not shift_start or not shift_end:
            return False, "All fields must be populated."

        try:
            with self.db.get_session() as session:
                new_shift = Shifts(
                    id=shift_id,
                    shift_name=shift_name,
                    shift_start=shift_start,
                    shift_end=shift_end
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

    def id_generator(self):
        """
        Generates an ID for a new employee by finding the current maximum ID in the database and adding 1.
        """
        try:
            with self.db.get_session() as session:
                max_id = session.query(Employee).order_by(Employee.id.desc()).first()
                return (max_id.id + 1) if max_id else 1
        except Exception as e:
            print(f"Error generating ID: {e}")
            return 1   