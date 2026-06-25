import pandas as pd
import calendar
import datetime


class DataHolder:
    def __init__(self):
        self.month = None
        self.year = None
        self.dates = []
        self.holidays = set()
        self.shifts = {}
        self.shifts_schedule = {}
        self.employees = {}
        self.weekday_weeks = {}
        self.employee_hours = {}


    def set_up_data_holder(self, month, year, holidays_df, shifts_df, employees_df, assignments_df, ft_hours):
        """Initializes the DataHolder with the necessary data to begin with the Scheduling process."""
        self.month = month
        self.year = year
        self._store_dates(month, year)
        self._store_holidays(holidays_df)
        self._store_shifts(shifts_df)
        self._store_employees(employees_df)
        self._store_shift_schedule(assignments_df)
        self._map_weekdays_to_weeks()
        self._map_employees_to_hours(ft_hours, assignments_df, shifts_df)


    def _store_dates(self, month, year):
        """Generates a list of date objects for all days in the specified month and year."""
        num_days = calendar.monthrange(year, month)[1]
        self.dates = [datetime.date(year, month, day) for day in range(1, num_days + 1)]


    def _store_holidays(self, df):
        """Converts the holidays DataFrame into a fast-lookup set of date objects."""
        if not df.empty and 'date' in df.columns:
            self.holidays = set(pd.to_datetime(df['date']).dt.date)


    def _store_employees(self, df):
        """Converts the employees DataFrame to a dictionary indexed by ID, keeping only active employees."""
        if not df.empty and 'id' in df.columns:
            active_df = df[df['is_active'] == True]
            self.employees = active_df.set_index('id').to_dict('index')


    def _store_shifts(self, df):
        """Converts the shifts DataFrame to a dictionary indexed by ID, keeping only active shifts."""
        if not df.empty and 'id' in df.columns:
            active_df = df[df['is_active'] == True]
            self.shifts = active_df.set_index('id').to_dict('index') 


    def _store_shift_schedule(self, df):
        """Converts the database assignments DataFrame into the nested shifts_schedule dictionary."""
        if df.empty:
            return
        # Filter to only keep rows where employee_id is missing (NaN/Null)
        unassigned_df = df[df['employee_id'].isna()]
            
        for _, row in unassigned_df.iterrows():
            date_val = pd.to_datetime(row['date']).date()
            shift_id = row['shift_id']
            role = row['role']
            
            # Rebuilds the 3-layer nesting, explicitly setting the slot to None
            self.shifts_schedule.setdefault(date_val, {}).setdefault(shift_id, {})[role] = None


    def _map_employees_to_hours(self, fulltime_weekly_hours, assignments_df, shifts_df):
        """Calculate target and completed hours for each employee."""
        working_days = sum(1 for d in self.dates if d.weekday() < 5 and d not in self.holidays)
        
        shift_duration_map = dict(zip(shifts_df['id'], shifts_df['shift_duration']))
        
        completed = {}
        if not assignments_df.empty:
            for _, row in assignments_df.iterrows():
                if pd.notna(row['employee_id']):
                    emp_id = int(row['employee_id'])
                    duration = shift_duration_map.get(row['shift_id'], 8.0)
                    completed[emp_id] = completed.get(emp_id, 0.0) + duration
        
        for emp_id, emp_data in self.employees.items():
            contract = emp_data.get('contract_type', '100%')
            
            if contract == 'Flexible':
                target = 32.0
            else:
                fraction = float(contract.strip('%')) / 100.0
                daily_hours = (fulltime_weekly_hours * fraction) / 5.0
                target = round(daily_hours * working_days, 1)
            
            self.employee_hours[emp_id] = {
                "target_hours": target,
                "completed_hours": round(completed.get(emp_id, 0.0), 1)
            }


    def return_flattened_empty_template(self):
        """
        Flattens the nested shifts_schedule dictionary into a list of database-ready dictionaries.
        It also determines the 'is_holidays' boolean for each assignment dynamically.
        """
        flat_list = []
        for date_val, shifts in self.shifts_schedule.items():
            is_holiday = date_val in self.holidays
            for shift_id, roles in shifts.items():
                for role, employee_id in roles.items():
                    flat_list.append({
                        'date': date_val,
                        'shift_id': shift_id,
                        'role': role,
                        'employee_id': employee_id,  # Will be None for templates
                        'is_holidays': is_holiday
                    })
        return flat_list


    def _map_weekdays_to_weeks(self):
        """
        Groups the weekday dates (Monday-Friday) from shifts_schedule into weeks.
        e.g., {'week1': {date_obj: shift_dict}, 'week2': {...}}
        """
        if not self.shifts_schedule:
            return
            
        num_days = calendar.monthrange(self.year, self.month)[1]
        week_number = 1
        
        for day in range(1, num_days + 1):
            current_date = datetime.date(self.year, self.month, day)
            
            # If it's a Monday and not the 1st of the month, enter a new week
            if current_date.weekday() == 0 and day != 1:
                week_number += 1
                
            # Check if it's a weekday (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri) and exists in shifts_schedule
            if current_date.weekday() < 5 and current_date in self.shifts_schedule:
                week_key = f"week{week_number}"
                self.weekday_weeks.setdefault(week_key, {})[current_date] = self.shifts_schedule[current_date]


    def get_fulltime_paramedic_ids(self):
        """Returns a list of employee IDs who are full-time (100%) and have the 'RS' qualification."""
        return [emp_id for emp_id, emp_data in self.employees.items() 
                if emp_data.get('contract_type') == '100%' and emp_data.get('qualification') == 'RS']


    def get_shift_ids(self):
        """Returns a list of all active shift IDs."""
        return list(self.shifts.keys())


    def get_db_updates(self):
        """
        Extracts the assignments that were made (where the value was overwritten by an employee_id)
        and formats them into a list of dictionaries for the DAO to update the DB.
        """
        updates = []
        for date_val, shifts in self.shifts_schedule.items():
            for shift_id, roles in shifts.items():
                for role, assigned_val in roles.items():
                    if assigned_val is not None:
                        updates.append({
                            'date': date_val,
                            'shift_id': shift_id,
                            'role': role,
                            'employee_id': assigned_val
                        })
        return updates