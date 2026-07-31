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
        self.assigned_employees_for_date = {}
        self.prev_month_shift_pattern = {}
        self.vacations = {}
        self.sick_leaves = {}


    def set_up_data_holder(self, month, year, holidays_df, shifts_df, employees_df, assignments_df, vacations_df, sick_leaves_df, ft_hours):
        """Initializes the DataHolder with the necessary data to begin with the Scheduling process."""
        self.month = month
        self.year = year
        self._store_dates(month, year)
        self._store_holidays(holidays_df)
        self._store_shifts(shifts_df)
        self._store_employees(employees_df)
        self._store_shift_schedule(assignments_df)
        self._map_weekdays_to_weeks()
        self._map_assigned_employees_for_date()
        self._store_vacations(vacations_df, month, year)
        self._store_sick_leaves(sick_leaves_df, month, year)
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
        for _, row in df.iterrows():
            date_val = pd.to_datetime(row['date']).date()
            shift_id = row['shift_id']
            role = row['role']
            emp_id = row['employee_id']
            if pd.isna(emp_id):
                emp_id = None
            else:
                emp_id = int(emp_id)

            self.shifts_schedule.setdefault(date_val, {}).setdefault(shift_id, {})[role] = emp_id


    def _map_employees_to_hours(self, fulltime_weekly_hours, assignments_df, shifts_df):
        """Calculate target and completed hours for each employee for the specified month and year. Also accounts for vacation days in completed hours for non-flexible contracts."""
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
            
            # Include vacations in completed hours for non-flexible contracts
            vacation_credit = 0.0
            if contract != 'Flexible':
                vac_dates = self.vacations.get(emp_id, set())
                vac_days = sum(1 for d in vac_dates if d.weekday() != 6)
                daily_leave_rate = (fulltime_weekly_hours * fraction) / 6.0
                vacation_credit = round(daily_leave_rate * vac_days, 1)

            self.employee_hours[emp_id] = {
                "target_hours": target,
                "completed_hours": round(completed.get(emp_id, 0.0) + vacation_credit, 1)
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
        Groups the weekday dates (Monday-Friday) from shifts_schedule into weeks. e.g., {'week1': {date_obj: shift_dict}, 'week2': {...}}
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


    def _map_assigned_employees_for_date(self):
        """Creates a mapping of each date to a set of employee IDs that have been assigned to shifts on that date"""
        for date_val, shifts in self.shifts_schedule.items():
            busy = set()
            for shift_id, roles in shifts.items():
                for role, emp_id in roles.items():
                    if emp_id is not None:
                        busy.add(emp_id)
            self.assigned_employees_for_date[date_val] = busy


    def _store_vacations(self, vacations_df, month, year):
        """
        Builds self.vacations: {employee_id: set of vacation dates in this month}. Stores ALL dates — weekends and holidays included.
        """
        if vacations_df is None or vacations_df.empty:
            return
        for _, row in vacations_df.iterrows():
            emp_id = int(row['employee_id'])
            date_val = pd.to_datetime(row['vacation_date']).date()
            if date_val.year == year and date_val.month == month:
                self.vacations.setdefault(emp_id, set()).add(date_val)


    def _store_sick_leaves(self, sick_leaves_df, month, year):
        """
        Builds self.sick_leaves: {employee_id: set of sick leave dates in this month}. Stores ALL dates — weekends and holidays included.
        """
        if sick_leaves_df is None or sick_leaves_df.empty:
            return
        for _, row in sick_leaves_df.iterrows():
            emp_id = int(row['employee_id'])
            date_val = pd.to_datetime(row['sick_leave_date']).date()
            if date_val.year == year and date_val.month == month:
                self.sick_leaves.setdefault(emp_id, set()).add(date_val)


    def _set_prev_month_shift_pattern(self, assignments_df):
        """
        Stores the shift pattern from the last weekday of the previous month, but ONLY if that day was a regular weekday 
        (Mon-Thu) and NOT a holiday. Otherwise sets prev_month_shift_pattern to None. Pattern format: {shift_id: {role: employee_id}}
        """
        if assignments_df.empty:
            self.prev_month_shift_pattern = None
            return

        # Get the date from the first row (all rows share the same date)
        date_val = pd.to_datetime(assignments_df['date'].iloc[0]).date()

        # Only carry over if it's Mon-Thu (0-3) and NOT a holiday
        if date_val.weekday() > 3:  # Friday (4) or weekend (5,6)
            self.prev_month_shift_pattern = None
            return
        if date_val in self.holidays:
            self.prev_month_shift_pattern = None
            return

        # Build the pattern dict
        self.prev_month_shift_pattern = {}
        for _, row in assignments_df.iterrows():
            shift_id = row['shift_id']
            role = row['role']
            emp_id = row['employee_id']
            if pd.notna(emp_id):
                self.prev_month_shift_pattern.setdefault(shift_id, {})[role] = int(emp_id)
            else:
                self.prev_month_shift_pattern.setdefault(shift_id, {})[role] = None


    def _apply_prev_month_pattern(self):
        """If prev_month_shift_pattern is set, copies it into the first weekdays of the new month (until Sunday) that belong
        to the same calendar week as the previous month's last day. Only fills slots that are still None."""
        if not self.prev_month_shift_pattern:
            return

        first_date = self.dates[0]
        if first_date.weekday() == 0 or first_date.weekday() >= 5:
            return  # Month starts on Monday or weekend → nothing to do

        days_until_sunday = 7 - first_date.weekday()

        for i in range(days_until_sunday):
            if i >= len(self.dates):
                break
            date = self.dates[i]
            if date.weekday() >= 5:
                continue
            if date not in self.shifts_schedule:
                continue

            for shift_id in self.shifts_schedule[date]:
                if shift_id in self.prev_month_shift_pattern:
                    for role in ('RS', 'RH'):
                        prev_emp = self.prev_month_shift_pattern[shift_id].get(role)
                        if prev_emp is not None:
                            if self.shifts_schedule[date][shift_id].get(role) is None:
                                self.shifts_schedule[date][shift_id][role] = prev_emp
                                self.employee_hours[prev_emp]["completed_hours"] += self.shifts[shift_id]["shift_duration"]
                                self.assigned_employees_for_date.setdefault(date, set()).add(prev_emp)


    def get_paramedic_ids_by_contract(self, contract_type):
        """This function returns a list of employee IDs who match the specified contract type and have the qualification 'RS' (paramedic)."""
        return [eid for eid, emp in self.employees.items()
                if emp.get('contract_type') == contract_type and emp.get('qualification') == 'RS']


    def select_eligible_employee_id(self, pool, date):
        """Pops and returns the first employee from the pool who is still under their target. Returns None if nobody in the pool has room left."""
        while pool:
            candidate = pool.pop()
            if self.employee_hours[candidate]["completed_hours"] >= self.employee_hours[candidate]["target_hours"]:
                continue
            if candidate in self.assigned_employees_for_date.get(date, set()):
                continue
            if self.is_on_leave(candidate, date):
                continue
            return candidate
        return None


    def is_on_leave(self, emp_id, date):
        """Returns True if the employee is on vacation or sick leave on the given date."""
        return (date in self.vacations.get(emp_id, set()) or date in self.sick_leaves.get(emp_id, set()))


    # ------------------------------------------------------------------
    # RH assignment helpers
    # ------------------------------------------------------------------

    def _get_employee_shift_for_date(self, emp_id, date):
        """Returns (shift_id, role) if the employee is assigned on the given date, otherwise None.
        Looks up shifts_schedule which covers the current month only."""
        shifts_on_date = self.shifts_schedule.get(date)
        if not shifts_on_date:
            return None
        for shift_id, roles in shifts_on_date.items():
            for role, assigned_emp in roles.items():
                if assigned_emp == emp_id:
                    return shift_id, role
        return None


    def is_11h_rest_satisfied(self, emp_id, date, proposed_shift_id):
        """Checks whether assigning emp_id to proposed_shift_id on 'date' respects the 11-hour rest period after their 
        assignment on the previous calendar day. Handles overnight shifts (end < start) by shifting the end datetime forward by one day."""
        prev_date = date - datetime.timedelta(days=1)
        prev_assignment = self._get_employee_shift_for_date(emp_id, prev_date)

        if prev_assignment is None:
            return True  # no previous assignment → no violation

        prev_shift_id, _ = prev_assignment
        prev_shift = self.shifts[prev_shift_id]
        proposed_shift = self.shifts[proposed_shift_id]

        prev_end_time = prev_shift['shift_end']
        prev_start_time = prev_shift['shift_start']
        proposed_start_time = proposed_shift['shift_start']

        # Build full datetime for previous shift's end
        prev_end_dt = datetime.datetime.combine(prev_date, prev_end_time)
        if prev_end_time < prev_start_time:
            # Overnight shift – the end time falls on the next calendar day
            prev_end_dt += datetime.timedelta(days=1)

        # Build full datetime for proposed shift's start
        proposed_start_dt = datetime.datetime.combine(date, proposed_start_time)

        gap_hours = (proposed_start_dt - prev_end_dt).total_seconds() / 3600.0
        return gap_hours >= 11.0


    def get_employees_sorted_by_remaining(self, contract_type):
        """Returns employee IDs of the given contract_type, sorted by remaining hours
        descending (most remaining first). Excludes employees already at or over target."""
        candidates = []
        for eid, emp in self.employees.items():
            if emp.get('contract_type') != contract_type:
                continue
            hrs = self.employee_hours.get(eid)
            if hrs is None:
                continue
            remaining = hrs['target_hours'] - hrs['completed_hours']
            if remaining <= 0:
                continue
            candidates.append((eid, remaining))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [eid for eid, _ in candidates]


    def select_eligible_employee_for_rh(self, pool, date, shift_id):
        """Like select_eligible_employee_id, but additionally enforces the 11-hour rest
        constraint against the previous day's assignment."""
        while pool:
            candidate = pool.pop(0)
            if self.employee_hours[candidate]["completed_hours"] >= self.employee_hours[candidate]["target_hours"]:
                continue
            if candidate in self.assigned_employees_for_date.get(date, set()):
                continue
            if self.is_on_leave(candidate, date):
                continue
            if not self.is_11h_rest_satisfied(candidate, date, shift_id):
                continue
            return candidate
        return None


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