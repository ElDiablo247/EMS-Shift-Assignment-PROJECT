from repository.dao import DatabaseAccess
import pandas as pd
import calendar
import holidays
import datetime


class PlanGenerator:
    def __init__(self):
        self.dao = DatabaseAccess()


    def generate_logic(self, month, year):
        """Generates the needed data for the empty template generation process"""

        # 1. Generate a list of all dates in the month
        month_dates = []
        num_days = calendar.monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            current_date = datetime.date(year, month, day)
            month_dates.append(current_date)

        # 2. Fetch shifts to create a name-to-id map to avoid database queries in the loop
        shifts_df = self.dao.get_all_shifts()
        shift_map = dict(zip(shifts_df['shift_name'], shifts_df['id'])) # Key: shift_name, Value: shift_id

        # 3. Iterate through the dates, determine their type, and create 2 empty assignments per shift
        self.itterate_dates(month_dates, year, shift_map)


    def itterate_dates(self, month_dates, year, shift_map):
        """Iterates through the dates of the month, determines their type, and creates empty shift assignments based on constraints."""
        
        shifts_per_day_dict = self.dao.get_constraints_by_category("Shifts per day")
        assignments_to_insert = []

        for date in month_dates:
            date_type = self.get_date_type(date, year)
            required_shifts = shifts_per_day_dict.get(date_type, [])

            for shift in required_shifts:
                # Transform the name to ID and append to our master list
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
        elif date.weekday() == 6:  # 5 = Saturday, 6 = Sunday
            return "Sunday"
        elif date.weekday() == 5:
            return "Saturday"
        else:
            return "Weekdays"


    def generate_holidays(self, year):
        """Generates a list of holidays for the given year."""
        region = self.dao.get_single_constraint("Holidays", "Region")
        ger_holidays = holidays.Germany(years=year, prov=region)

        success_count = 0
        for date, name in ger_holidays.items():
            if self.dao.insert_holiday(year, date, name):
                success_count += 1
                
        if success_count > 0:
            return True, f"{success_count} holidays added successfully for {year}."
        return False, f"Failed to add holidays for {year}. Check if they already exist."