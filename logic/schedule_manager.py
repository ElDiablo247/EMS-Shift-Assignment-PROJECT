from repository.dao import DatabaseAccess
import pandas as pd
import calendar
import holidays
import datetime


class ScheduleManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def generate_logic(self, month, year):
        """Generates the needed data for the empty template generation process"""

        # 1. Business logic check: If the 1st of the month exists, the template is already generated.
        first_day_of_month = datetime.date(year, month, 1)
        if self.dao.assignments_exist_for_date(first_day_of_month):
            return False, "A schedule template for the given month and year already exists!"
        
        # 2. Generate a list of all dates in the month
        month_dates = []
        num_days = calendar.monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            current_date = datetime.date(year, month, day)
            month_dates.append(current_date)

        # 3. Fetch shifts to create a name-to-id map to avoid database queries in the loop
        shifts_df = self.dao.get_all_shifts()
        shift_map = dict(zip(shifts_df['shift_name'], shifts_df['id'])) # Key: shift_name, Value: shift_id

        # 4. Iterate through the dates, determine their type, and create 2 empty assignments per shift
        self.iterate_dates(month_dates, year, shift_map)
        
        return True, f"Successfully generated empty template for {month}/{year}!"


    def iterate_dates(self, month_dates, year, shift_map):
        """Iterates through the dates of the month, determines their type, and creates empty shift assignments based on constraints."""
        
        shifts_per_day_dict = self.dao.get_constraints_by_category("Shifts per day")
        assignments_to_insert = []

        for date in month_dates:
            date_type = self.get_date_type(date, year)
            required_shifts = shifts_per_day_dict.get(date_type, [])

            for shift in required_shifts:
                self.append_empty_assignment(date, shift, None, shift_map, assignments_to_insert)
                self.append_empty_assignment(date, shift, None, shift_map, assignments_to_insert)
        
        # Once all loops are done, send the massive list to the database in one single query
        if assignments_to_insert:
            self.dao.bulk_insert_assignments(assignments_to_insert)


    def append_empty_assignment(self, date, shift_name, employee_id, shift_map, assignments_list):
        """Translates shift_name to shift_id and appends the assignment dictionary to a list."""
        shift_id = shift_map.get(shift_name)
        if shift_id:
            assignments_list.append({
                "date": date,
                "shift_id": shift_id,
                "employee_id": employee_id
            })
        else:
            print(f"Warning: Shift name '{shift_name}' not found in database.")


    def get_all_holidays_df(self, year=None):
        """Pass-through to DAO to get holidays as a DataFrame, optionally filtered by year."""
        return self.dao.get_all_holidays(year)


    def get_date_type(self, date, year):
        """Determines the type of a given date (weekday, weekend, or holiday)."""

        # Fetch the list of holidays for the year from the database
        holidays_list = self.dao.get_holidays_by_year(year)

        if date in holidays_list:
            return "Holiday"
        elif date.weekday() == 6:  # 6 = Sunday
            return "Sunday"
        elif date.weekday() == 5:  # 5 = Saturday
            return "Saturday"
        else:
            return "Weekdays"


    def generate_holidays(self, year):
        """Generates a list of holidays for the given year."""
        region = self.dao.get_single_constraint("Holidays", "Region")
        if not region:
            return False, "Holiday region not set. Please set the holiday region in the constraints before generating the holidays."

        ger_holidays = holidays.Germany(years=year, prov=region)

        success_count = 0
        for date, name in ger_holidays.items():
            if self.dao.insert_holiday(year, date, name):
                success_count += 1
                
        if success_count > 0:
            return True, f"{success_count} holidays added successfully for {year}."
        return False, f"Failed to add holidays for {year}. Check if they already exist."


    def get_assignments_pivot(self, month, year):
        """Fetches assignments for a month and pivots them into a wide format for the UI."""
        df = self.dao.get_assignments_for_month(month, year)
        if df.empty:
            return df
            
        # Differentiate between the 2 identical shift assignments (Paramedic vs Assistant)
        df['slot'] = df.groupby(['date', 'shift_name']).cumcount()
        role_map = {0: 'RS', 1: 'RH'}
        df['shift_role'] = df['shift_name'] + ' (' + df['slot'].map(role_map).fillna(df['slot'].astype(str)) + ')'
        
        # Format date so the pivot column headers look nice
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%d.%m.%Y')
        
        # Replace NaN with 'Unassigned' ONLY for slots that actually exist in the DB
        df['employee_name'] = df['employee_name'].fillna("Empty")
        
        # Pivot: index=shift_role, columns=date, values=employee_name
        pivot_df = df.pivot(index='shift_role', columns='date', values='employee_name')
        
        # Replace NaN with '-' for cells created by the pivot (shifts that don't run that day)
        pivot_df = pivot_df.fillna("-")
        
        # Reset index to make 'shift_role' a standard column, and rename it for the UI
        pivot_df = pivot_df.reset_index()
        pivot_df = pivot_df.rename(columns={'shift_role': 'Shift'})
        pivot_df.columns.name = None
        
        return pivot_df