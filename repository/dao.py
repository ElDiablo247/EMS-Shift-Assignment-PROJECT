from repository.db_engine import db_obj
from repository.models import Employee, Shift, Admin, Constraint
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


    def delete_admin(self, admin_id):
        """Deletes an admin from the database based on their ID."""
        try:
            with self.db.get_session() as session:
                admin_to_delete = session.query(Admin).filter(Admin.id == admin_id).first()
                if admin_to_delete:
                    session.delete(admin_to_delete)
                    return True
                else:
                    print(f"Admin with ID {admin_id} not found.")
                    return False
        except Exception as e:
            print(f"Error deleting admin: {e}")
            return False


    def delete_employee(self, emp_id):
        """Deletes an employee from the database based on their ID."""
        try:
            with self.db.get_session() as session:
                employee_to_delete = session.query(Employee).filter(Employee.id == emp_id).first()
                if employee_to_delete:
                    session.delete(employee_to_delete)
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Error deleting employee: {e}")
            return False


    def delete_shift(self, shift_id):
        """Deletes a shift from the database based on its ID."""
        try:
            with self.db.get_session() as session:
                shift_to_delete = session.query(Shift).filter(Shift.id == shift_id).first()
                if shift_to_delete:
                    session.delete(shift_to_delete)
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Error deleting shift: {e}")
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
                new_shift = Shift(
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
            query = session.query(Shift).order_by(Shift.shift_name)
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
                session.query(Shift).delete()
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
                max_id = session.query(Shift).order_by(Shift.id.desc()).first()
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
                            employee.is_active = row['is_active']
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
                        shift = session.query(Shift).filter(Shift.id == row['id']).first()
                        if shift:
                            shift.shift_name = row['shift_name']
                            shift.shift_start = row['shift_start']
                            shift.shift_end = row['shift_end']
                            shift.shift_duration = row['shift_duration']
                            shift.is_active = row['is_active']
            return True
        except Exception as e:
            print(f"Error updating data: {e}")
            return False
        

    def populate_constraints(self, constraints_list):
        """
        Takes a list of dictionaries and bulk inserts them into the constraints table.
        This should typically only be run once during initial setup.
        """
        try:
            with self.db.get_session() as session:
                # bulk_insert_mappings is incredibly fast and takes your list of dicts directly!
                session.bulk_insert_mappings(Constraint, constraints_list)
            return True
        except Exception as e:
            print(f"Error seeding constraints: {e}")
            return False


    def get_all_constraints(self):
        """Retrieves all constraints from the database as a DataFrame."""
        with self.db.get_session() as session:
            query = session.query(Constraint).order_by(Constraint.id)
            return pd.read_sql(query.statement, session.bind)


    def update_constraints(self, constraints_df):
        """
        Updates constraint records based on the edited DataFrame from the UI.
        """
        try:
            with self.db.get_session() as session:
                for _, row in constraints_df.iterrows():
                    if pd.notna(row['id']):
                        constraint = session.query(Constraint).filter(Constraint.id == row['id']).first()
                        if constraint:
                            constraint.constraint_value = row['constraint_value']
            return True
        except Exception as e:
            print(f"Error updating constraints: {e}")
            return False


    def update_single_constraint(self, category, key, new_value):
        """
        Updates a single constraint record directly based on category and key, without using Pandas DataFrames.
        """
        try:
            with self.db.get_session() as session:
                constraint = session.query(Constraint).filter(
                    Constraint.category == category, 
                    Constraint.constraint_key == key
                ).first()
                if constraint:
                    constraint.constraint_value = new_value
                    return True
                return False
        except Exception as e:
            print(f"Error updating single constraint: {e}")
            return False
