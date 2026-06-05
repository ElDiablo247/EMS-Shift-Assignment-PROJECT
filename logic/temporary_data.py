import pandas as pd
import calendar
import holidays
import datetime


class DataHolder:
    def __init__(self, month, year, assignments_df, employees_df, shifts_df):
        self.month = month
        self.year = year
        self.employees = {}
        self.shifts = {}
        self.weekday_weeks = {}
        self.assignments_local = {}
        self.employee_hours = {}
        self.assignments_df = assignments_df

        self._store_employees(employees_df)
        self._init_employee_hours()
        self._store_shifts(shifts_df)
        self._store_assignments_local()
        self._map_weekdays_to_weeks()


    def _store_employees(self, df):
        """Converts the employees DataFrame to a dictionary indexed by ID."""
        if not df.empty and 'id' in df.columns:
            self.employees = df.set_index('id').to_dict('index')


    def _init_employee_hours(self):
        """Maps each employee ID to a starting float value of 0.0 for tracking hours."""
        for emp_id in self.employees.keys():
            self.employee_hours[emp_id] = 0.0


    def _store_shifts(self, df):
        """Converts the shifts DataFrame to a dictionary indexed by ID."""
        if not df.empty and 'id' in df.columns:
            self.shifts = df.set_index('id').to_dict('index')


    def _store_assignments_local(self):
        """
        Parses the assignments DataFrame into a nested dictionary:
        date -> shift_id -> role -> assignment_id
        Only includes slots where employee_id is null (empty).
        """
        if self.assignments_df.empty:
            return
            
        for _, row in self.assignments_df.iterrows():
            if pd.isna(row['employee_id']):
                date_val = row['date']
                shift_id = row['shift_id']
                role = row['role']
                
                self.assignments_local.setdefault(date_val, {}).setdefault(shift_id, {})[role] = row['id']


    def _map_weekdays_to_weeks(self):
        """
        Groups the weekday dates (Monday-Friday) from assignments_local into weeks.
        e.g., {'week1': {date_obj: shift_dict}, 'week2': {...}}
        """
        if not self.assignments_local:
            return
            
        num_days = calendar.monthrange(self.year, self.month)[1]
        week_number = 1
        
        for day in range(1, num_days + 1):
            current_date = datetime.date(self.year, self.month, day)
            
            # If it's a Monday and not the 1st of the month, enter a new week
            if current_date.weekday() == 0 and day != 1:
                week_number += 1
                
            # Check if it's a weekday (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri) and exists in assignments
            if current_date.weekday() < 5 and current_date in self.assignments_local:
                week_key = f"week{week_number}"
                self.weekday_weeks.setdefault(week_key, {})[current_date] = self.assignments_local[current_date]


    def get_debug_string(self):
        """Returns the assignments_local and weekday_weeks dictionaries as a formatted string."""
        debug_str = f"--- DataHolder Debug Print for {self.month}/{self.year} ---\n"
        debug_str += "=== ASSIGNMENTS LOCAL ===\n"
        debug_str += f"{self.assignments_local}\n"
        debug_str += "\n=== WEEKDAY WEEKS ===\n"
        debug_str += f"{self.weekday_weeks}\n"
        debug_str += "--------------------------------------------------\n"
        return debug_str


    def get_db_updates(self):
        """
        Extracts the assignments that were made (where the value was overwritten by an employee_id)
        and formats them into a list of dictionaries for the DAO to update the DB.
        """
        updates = []
        for date_val, shifts in self.assignments_local.items():
            for shift_id, roles in shifts.items():
                for role, assigned_val in roles.items():
                    # If the assigned value exists, it's an employee ID
                    if assigned_val in self.employees:
                        updates.append({
                            'date': date_val,
                            'shift_id': shift_id,
                            'role': role,
                            'employee_id': assigned_val
                        })
        return updates


    def generate_template_data(self, month, year):
        """Generates the needed data for the empty template generation process"""