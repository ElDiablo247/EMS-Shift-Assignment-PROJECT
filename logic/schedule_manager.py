import random
from repository.dao import DatabaseAccess
import pandas as pd
import calendar
import holidays
import datetime
from logic.temporary_data import DataHolder


class ScheduleManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def generate_template_data(self, month, year):
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
        success, msg = self.generate_empty_template(month_dates, year, shift_map)
        return success, msg


    def generate_empty_template(self, month_dates, year, shift_map):
        """Iterates through the dates of the month, determines their type, and creates empty shift assignments based on constraints."""
        
        shifts_per_day_dict = self.dao.get_constraints_by_category("Shifts per day")
        assignments_to_insert = []

        for date in month_dates:
            date_type = self.get_date_type(date, year)
            is_holiday = (date_type == "Holiday")
            required_shifts = shifts_per_day_dict.get(date_type, [])

            for shift_name in required_shifts:
                self.append_empty_assignment(date, shift_name, None, "RS", is_holiday, shift_map, assignments_to_insert)
                self.append_empty_assignment(date, shift_name, None, "RH", is_holiday, shift_map, assignments_to_insert)
        
        # Once all loops are done, send the massive list to the database in one single query
        if assignments_to_insert:
            if self.dao.bulk_insert_assignments(assignments_to_insert):
                return True, f"Successfully generated {len(assignments_to_insert)} assignment slots for {month_dates[0].month}/{year}!"
            return False, "A database error occurred while saving the assignments."
        else:
            return False, "No slots created. Please go to the 'Constraints' page and assign shifts to the days of the week."


    def append_empty_assignment(self, date, shift_name, employee_id, role, is_holidays, shift_map, assignments_list):
        """Translates shift_name to shift_id and appends the assignment dictionary to a list."""
        shift_id = shift_map.get(shift_name)
        if shift_id:
            assignments_list.append({
                "date": date,
                "shift_id": shift_id,
                "employee_id": employee_id,
                "role": role,
                "is_holidays": is_holidays
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


    def generate_year_holidays(self, year):
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
            
        # Fetch related data to perform the joins in-memory
        shifts_df = self.dao.get_all_shifts()
        employees_df = self.dao.get_all_employees()
        
        # Map shift_id to shift_name using a dictionary
        shift_name_map = dict(zip(shifts_df['id'], shifts_df['shift_name']))
        df['shift_name'] = df['shift_id'].map(shift_name_map)
        
        # Map employee_id to employee name
        emp_name_map = dict(zip(employees_df['id'], employees_df['name']))
        df['employee_name'] = df['employee_id'].map(emp_name_map)
        
        # Format date so the pivot column headers look nice
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%d.%m.%Y')
        
        # Replace NaN with 'Empty' ONLY for slots that actually exist in the DB
        df['employee_name'] = df['employee_name'].fillna("Empty")
        
        # Combine shift and role to create the column headers (e.g., "K1 - RS")
        df['shift_role'] = df['shift_name'] + ' - ' + df['role']
        
        # Pivot: rows = dates, columns = shift_role, values = employee_name
        pivot_df = df.pivot(index='date', columns='shift_role', values='employee_name')
        
        # Replace NaN with '-' for cells created by the pivot (shifts that don't run that day)
        pivot_df = pivot_df.fillna("-")
        
        # Reset index to make date a standard column
        pivot_df = pivot_df.reset_index()
        pivot_df.columns.name = None
        
        return pivot_df


    def save_edited_assignments(self, edited_df):
        """Translates the edited UI grid back into database updates (un-pivot)."""
        
        # Fetch employees to map names back to IDs
        employees_df = self.dao.get_all_employees()
        emp_name_to_id = dict(zip(employees_df['name'], employees_df['id']))
        emp_name_to_id['Empty'] = None
        
        # Fetch shifts to map shift_name back to shift_id
        shifts_df = self.dao.get_all_shifts()
        shift_name_to_id = dict(zip(shifts_df['shift_name'], shifts_df['id']))
        
        # Melt the dataframe (un-pivot)
        shift_role_columns = [col for col in edited_df.columns if col != 'date']
        melted_df = edited_df.melt(id_vars=['date'], value_vars=shift_role_columns, var_name='shift_role_str', value_name='employee_name')
        
        # Filter out cells that were filled with "-" (Days where a specific shift doesn't run)
        melted_df = melted_df[melted_df['employee_name'] != '-']
        
        updates_list = []
        for _, row in melted_df.iterrows():
            # Split the column header back into shift name and role
            shift_name, role = row['shift_role_str'].split(' - ')
            
            # Convert date string back to actual date object
            date_obj = datetime.datetime.strptime(row['date'], '%d.%m.%Y').date()
            shift_id = shift_name_to_id.get(shift_name)
            
            if shift_id:
                updates_list.append({
                    'date': date_obj,
                    'shift_id': shift_id,
                    'role': role,
                    'employee_id': emp_name_to_id.get(row['employee_name'])
                })
                
        return self.dao.update_monthly_assignments(updates_list), "Schedule saved successfully!"


    def load_data_for_assignment(self, month, year):
        """Fetches assignments, employees, and shifts for a given month/year and returns an initialized DataHolder."""
        assignments_df = self.dao.get_assignments_for_month(month, year)
        employees_df = self.dao.get_all_employees()
        shifts_df = self.dao.get_all_shifts()
        
        return DataHolder(month, year, assignments_df, employees_df, shifts_df)
    

    def assign_paramedics_to_shifts(self, month, year):
        """Developer tool to assign paramedics to all empty RS slots for a given month/year. This is a one-click solution to quickly fill the schedule with valid assignments."""
        data_holder = self.load_data_for_assignment(month, year)
        shift_ids = list(data_holder.shifts.keys())
        
        # Iterate over the week keys ('week1', 'week2')
        for week_key, dates_dict in data_holder.weekday_weeks.items():
            # Refresh the pool of employees for the new week
            fulltime_employees_ids = list(data_holder.employees.keys())
            
            random.shuffle(shift_ids)
            random.shuffle(fulltime_employees_ids)
            for local_shift_id in shift_ids: 
                local_employee = None
                
                # Find the next available RS employee
                while fulltime_employees_ids:
                    candidate_id = fulltime_employees_ids.pop()
                    if data_holder.employees[candidate_id].get('qualification') == 'RS':
                        local_employee = candidate_id
                        break
                
                if local_employee:
                    for date in dates_dict:
                        if local_shift_id in data_holder.assignments_local.get(date, {}):
                            data_holder.assignments_local[date][local_shift_id]["RS"] = local_employee
                            
        # Extract the new assignments and send them to the database
        updates_list = data_holder.get_db_updates()
        if updates_list:
            if self.dao.update_monthly_assignments(updates_list):
                return True, f"Successfully auto-assigned {len(updates_list)} paramedic slots!"
            return False, "Database error: Failed to save the auto-assignments."
        return False, "No paramedics were available to assign."