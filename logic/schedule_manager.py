import random
from repository.dao import DatabaseAccess
import pandas as pd
import calendar
import datetime
from logic.temporary_data import DataHolder


class ScheduleManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def generate_empty_template(self, month, year):
        """Iterates through the dates of the month, determines their type, and creates empty shift assignments based on constraints."""

        # 1. Business logic check: If the 1st of the month exists, the template is already generated.
        first_day_of_month = datetime.date(year, month, 1)
        if self.dao.assignments_exist_for_date(first_day_of_month):
            return False, "A schedule template for the given month and year already exists!", None
        
        # 2. Generate the Data Holder object that will store neccessary data in memory for the template generation process.initialization.
        data_holder = self.generate_data_holder(month, year)

        # 3. Create the empty template in the DataHolder object based on constraints.
        for date in data_holder.dates: # Itterate over all dates of the month
            data_holder.shifts_schedule[date] = {} 
            if date in data_holder.holidays or date.weekday() >= 5: # If current date is a Holiday or weekend
                for shift_id, values in data_holder.shifts.items(): # Itterate over all shifts
                    if values['runs_on_weekend_or_holiday'] == True: # If the shift runs on holidays/weekends, create an entry for it.
                        data_holder.shifts_schedule[date][shift_id] = {"RS": None, "RH": None}
            else: # Else if current date is a Weekday
                for shift_id in data_holder.shifts: # Create entries for all shifts on weekdays
                    data_holder.shifts_schedule[date][shift_id] = {"RS": None, "RH": None}
        
        # 4. Map the weekday dates to their respective weeks (e.g., 1st week of the month, 2nd week of the month, etc.)
        data_holder._map_weekdays_to_weeks() 

        # 5. Convert the nested dictionary empty template to a flattened list and push it to the database
        flat_template = data_holder.return_flattened_empty_template()
        if self.dao.bulk_insert_assignments(flat_template):
            return True, f"Empty shift template for {data_holder.month}/{data_holder.year} generated and saved!", data_holder
        return False, "Database error: Failed to save the empty template.", None


    def generate_data_holder(self, month, year):
        """Fetches assignments, employees, and shifts for a given month/year and returns an initialized DataHolder."""
        data_holder = DataHolder()
        shifts_df = self.dao.get_all_shifts()
        holidays_df = self.dao.get_all_holidays(year)
        employees_df = self.dao.get_all_employees()
        assignments_df = self.dao.get_assignments_for_month(month, year)
        ft_hours = self.dao.get_single_constraint("Contract hours", "Full-time 100%")
        ft_hours = float(ft_hours) if ft_hours else 42.5   # convert string to float
        data_holder.set_up_data_holder(month, year, holidays_df, shifts_df, employees_df, assignments_df, ft_hours)
        return data_holder


    def assign_paramedics_to_weekdays_shifts(self, month, year):
        """Creates a DataHolder with data from DB, assigns paramedics (RS) to weekday RS slots, prioritising by their contract type 
        in this order (100%, 75%, 50%), then saves to DB."""
        # Check if a partial schedule already exists for the month/year. If yes, return an error message, if not, proceed.
        first_day_of_month = datetime.date(year, month, 1)
        if not self.dao.assignments_exist_for_date(first_day_of_month):
            return False, "No schedule template exists for this month. Generate an empty template first."
        
        # Generate a DataHolder with all the necessary data for the month/year, and get the shift schedule of the last day of previous month.
        # Then apply the previous month's shift pattern to the current month, and get the list of shift IDs for assignment.
        data_holder = self.generate_data_holder(month, year)
        self._load_prev_month_shift_pattern(month, year, data_holder)
        data_holder._apply_prev_month_pattern()
        shift_ids = data_holder.get_shift_ids()
        
        # Iterate over the contract types in order of priority (100%, 75%, 50%) and then over each week of the month.
        for contract_type in ["100%", "75%", "50%"]:
            for week_key, dates_dict in data_holder.weekday_weeks.items():
                employee_ids = data_holder.get_paramedic_ids_by_contract(contract_type)
                if not employee_ids:
                    continue  # No remaining employees with this contract type, skip to next type.
                
                random.shuffle(shift_ids)
                for local_shift_id in shift_ids:
                    self.fill_dates_of_week_with_paramedics(data_holder, local_shift_id, dates_dict, employee_ids)

        # Extract the new assignments and send them to the database to be saved.
        updates_list = data_holder.get_db_updates()
        if updates_list:
            if self.dao.update_monthly_assignments(updates_list):
                return True, f"Successfully auto-assigned paramedic slots!"
            return False, "Database error: Failed to save the auto-assignments."
        return False, "No paramedics were available to assign."


    def fill_dates_of_week_with_paramedics(self, data_holder, shift_id, dates_dict, employee_ids):
        """Helper function to fill a week's worth of shifts with paramedics of a specific contract type."""
        local_employee = 'empty'

        for date in dates_dict:
            if shift_id not in data_holder.shifts_schedule.get(date, {}) or data_holder.shifts_schedule[date][shift_id].get("RS") is not None:
                continue # If the shift doesn't exist on this date or is already filled, skip to the next date.
            
            if local_employee == 'empty':
                local_employee = data_holder.select_eligible_employee_id(employee_ids, date)
                if local_employee is None: 
                    break # This means there are no more eligible employees at all so the rest of the week will remain unassigned for this shift.
            
            data_holder.shifts_schedule[date][shift_id]["RS"] = local_employee
            data_holder.assigned_employees_for_date[date].add(local_employee) 
            data_holder.employee_hours[local_employee]["completed_hours"] += data_holder.shifts[shift_id]["shift_duration"]
            if data_holder.employee_hours[local_employee]["completed_hours"] >= data_holder.employee_hours[local_employee]["target_hours"]:
                local_employee = 'empty'


    def _load_prev_month_shift_pattern(self, month, year, data_holder):
        """Finds the last weekday of the previous month, fetches its assignments from the DB, and passes them to the DataHolder for carry-over."""
        if month == 1:
            prev_month, prev_year = 12, year - 1
        else:
            prev_month, prev_year = month - 1, year

        num_days = calendar.monthrange(prev_year, prev_month)[1]
        last_weekday_date = None
        for day in range(num_days, 0, -1):
            date = datetime.date(prev_year, prev_month, day)
            if date.weekday() < 5:
                last_weekday_date = date
                break

        if last_weekday_date:
            df = self.dao.get_assignments_for_date(last_weekday_date)
            data_holder._set_prev_month_shift_pattern(df)


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
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%d.%m.%Y - %A')
        
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


    def get_employee_hours_pivot(self, month, year):
        """Builds an employee hours DataFrame from a fresh DataHolder."""
        dh = self.generate_data_holder(month, year)
        rows = []
        for emp_id, hours in dh.employee_hours.items():
            emp_name = dh.employees.get(emp_id, {}).get('name', f'ID {emp_id}')
            rows.append({
                'Employee': emp_name,
                'Target Hours': hours['target_hours'],
                'Completed Hours': hours['completed_hours']
            })
        return pd.DataFrame(rows)


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
            date_str = row['date'].split(' - ')[0]
            date_obj = datetime.datetime.strptime(date_str, '%d.%m.%Y').date()
            shift_id = shift_name_to_id.get(shift_name)
            
            if shift_id:
                updates_list.append({
                    'date': date_obj,
                    'shift_id': shift_id,
                    'role': role,
                    'employee_id': emp_name_to_id.get(row['employee_name'])
                })
                
        return self.dao.update_monthly_assignments(updates_list), "Schedule saved successfully!"