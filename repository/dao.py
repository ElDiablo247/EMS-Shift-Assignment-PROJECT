from repository.db_engine import db_obj
from repository.models import Employee, Shifts, Admin
import pandas as pd

class DatabaseAccess:
    def __init__(self):
        self.db = db_obj


    def add_super_admin(self, username, password_hash, role):
        """Adds a new admin user to the database with a 'super' role."""
        try:
            with self.db.get_session() as session:
                new_admin = Admin(username=username, password_hash=password_hash, role=role)
                session.add(new_admin)
            return True
        except Exception as e:
            print(f"Error adding super admin: {e}")
            return False


    def add_basic_admin(self, username, password_hash, role):
        """Adds a new admin user to the database with a 'basic' role."""
        try:
            with self.db.get_session() as session:
                new_admin = Admin(username=username, password_hash=password_hash, role=role)
                session.add(new_admin)
            return True
        except Exception as e:
            print(f"Error adding basic admin: {e}")
            return False


    def get_admin_details(self, username):
        """
        Retrieves the hashed password and role for a given username.
        By returning just the string hash, we avoid SQLAlchemy DetachedInstanceError
        that can occur if the session is closed before related data is accessed, as per your previous experience.
        """
        try:
            with self.db.get_session() as session:
                admin = session.query(Admin).filter(Admin.username == username).first()
                if admin:
                    return admin.password_hash, admin.role
                return None, None
        except Exception as e:
            print(f"Error retrieving admin details: {e}")
            return None, None


    def admins_exist(self):
        """Checks if any admin exists in the admins table."""
        try:
            with self.db.get_session() as session:
                return session.query(Admin).count() > 0
        except Exception as e:
            print(f"Error checking if admins table is empty: {e}")
            return False


    def add_employee(self, emp_id, name, qualification, contract_type):
        """
        Creates a new employee object and saves it to the database.
        """
        # A new employee object is created with the provided details and the generated ID.
        try:
            with self.db.get_session() as session:
                new_staff = Employee(
                    id=emp_id,
                    name=name,
                    qualification=qualification,
                    contract_type=contract_type
                )
                session.add(new_staff)
            return True
        except Exception as e:
            print(f"Error adding employee: {e}")
            return False


    def add_shift(self, shift_id, shift_name, shift_start, shift_end, shift_duration):
        """
        Creates a new shift object and saves it to the database.
        """
        # A new shift object is created with the provided details and the generated ID.
        try:
            with self.db.get_session() as session:
                new_shift = Shifts(
                    id=shift_id,
                    shift_name=shift_name,
                    shift_start=shift_start,
                    shift_end=shift_end,
                    shift_duration=shift_duration
                )
                session.add(new_shift)
            return True
        except Exception as e:
            print(f"Error adding shift: {e}")
            return False


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


    def get_all_admins(self):
        """Retrieves all admin records from the database and formats them for display."""
        with self.db.get_session() as session:
            query = session.query(Admin).order_by(Admin.id)
            return pd.read_sql(query.statement, session.bind)


    def empty_employee_database(self):
        """Wipes all data from the employees table."""
        try:
            with self.db.get_session() as session:
                session.query(Employee).delete()
            return True
        except Exception as e:
            print(f"Error clearing Employees database: {e}")
            return False


    def empty_shifts_database(self):
        """Wipes all data from the shifts table."""
        try:
            with self.db.get_session() as session:
                session.query(Shifts).delete()
            return True
        except Exception as e:
            print(f"Error clearing Shifts database: {e}")
            return False


    def get_last_employee_id(self):
        """
        Retrieves the highest existing ID in the employees table.
        """
        try:
            with self.db.get_session() as session:
                max_id = session.query(Employee).order_by(Employee.id.desc()).first()
                if max_id:
                    return max_id.id
                else:   
                    return None
        except Exception as e:
            print(f"Error getting last ID: {e}")
            return None


    def get_last_shift_id(self):
        """
        Retrieves the highest existing ID in the shifts table.
        """
        try:
            with self.db.get_session() as session:
                max_id = session.query(Shifts).order_by(Shifts.id.desc()).first()
                if max_id:
                    return max_id.id
                else:   
                    return None
        except Exception as e:
            print(f"Error getting last ID: {e}")
            return None


    def update_employees(self, employees_df):
        """
        Updates employee records based on the edited DataFrame from the UI.
        """
        try:
            with self.db.get_session() as session:
                for _, row in employees_df.iterrows():
                    if pd.notna(row['id']):
                        employee = session.query(Employee).filter(Employee.id == row['id']).first()
                        if employee:
                            employee.name = row['name']
                            employee.qualification = row['qualification']
                            employee.contract_type = row['contract_type']
            return True
        except Exception as e:
            print(f"Error updating data: {e}")
            return False


    def update_shifts(self, shifts_df):
        """
        Updates shift records based on the edited DataFrame from the UI.
        """
        try:
            with self.db.get_session() as session:
                for _, row in shifts_df.iterrows():
                    if pd.notna(row['id']):
                        shift = session.query(Shifts).filter(Shifts.id == row['id']).first()
                        if shift:
                            shift.shift_name = row['shift_name']
                            shift.shift_start = row['shift_start']
                            shift.shift_end = row['shift_end']
                            shift.shift_duration = row['shift_duration']
            return True
        except Exception as e:
            print(f"Error updating data: {e}")
            return False