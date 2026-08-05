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
                    if not values.get('is_active', True):
                        continue
                    if values['runs_on_weekend_or_holiday'] == True: # If the shift runs on holidays/weekends, create an entry for it.
                        data_holder.shifts_schedule[date][shift_id] = {"RS": None, "RH": None}
            else: # Else if current date is a Weekday
                for shift_id, values in data_holder.shifts.items(): # Create entries for all shifts on weekdays
                    if not values.get('is_active', True):
                        continue
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
        vacations_df = self.dao.get_all_vacations()
        sick_leaves_df = self.dao.get_all_sick_leaves()
        ft_hours = self.dao.get_single_constraint("Contract hours", "Full-time 100%")
        ft_hours = float(ft_hours) if ft_hours else 42.5   # convert string to float
        data_holder.set_up_data_holder(month, year, holidays_df, shifts_df, employees_df, assignments_df, vacations_df, sick_leaves_df, ft_hours)
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
            if local_employee != 'empty' and data_holder.is_on_leave(local_employee, date):
                local_employee = 'empty'
                continue

            data_holder.shifts_schedule[date][shift_id]["RS"] = local_employee
            data_holder.assigned_employees_for_date[date].add(local_employee) 
            data_holder.employee_hours[local_employee]["completed_hours"] += data_holder.shifts[shift_id]["shift_duration"]
            if data_holder.employee_hours[local_employee]["completed_hours"] >= data_holder.employee_hours[local_employee]["target_hours"]:
                local_employee = 'empty'


    def assign_rh_to_weekdays_shifts(self, month, year):
        """Creates a DataHolder (with RS assignments already loaded from DB), then fills
        weekday RH slots. Priority: contract tier (100% → 75% → 50% → Flexible), and
        within each tier by remaining hours (most first). Finally saves to DB."""
        first_day_of_month = datetime.date(year, month, 1)
        if not self.dao.assignments_exist_for_date(first_day_of_month):
            return False, "No schedule template exists for this month. Generate an empty template first."

        data_holder = self.generate_data_holder(month, year)
        self._load_prev_month_shift_pattern(month, year, data_holder)
        data_holder._apply_prev_month_pattern()
        shift_ids = data_holder.get_shift_ids()

        for contract_type in ["100%", "75%", "50%", "Flexible"]:
            for week_key, dates_dict in data_holder.weekday_weeks.items():
                employee_ids = data_holder.get_employees_sorted_by_remaining(contract_type)
                if not employee_ids:
                    continue

                random.shuffle(shift_ids)
                for local_shift_id in shift_ids:
                    self.fill_dates_of_week_with_rh(data_holder, local_shift_id, dates_dict, employee_ids)

        updates_list = data_holder.get_db_updates()
        if updates_list:
            if self.dao.update_monthly_assignments(updates_list):
                return True, "Successfully auto-assigned RH slots!"
            return False, "Database error: Failed to save the RH auto-assignments."
        return False, "No employees were available to assign to RH slots."


    def fill_dates_of_week_with_rh(self, data_holder, shift_id, dates_dict, employee_ids):
        """Fills a week's worth of RH slots for one shift. Keeps the same employee across
        all dates of the week until they hit their target, then picks the next eligible one.
        Each candidate must pass: under target, not already on that date, and 11h rest."""
        local_employee = 'empty'

        for date in dates_dict:
            if (shift_id not in data_holder.shifts_schedule.get(date, {})
                    or data_holder.shifts_schedule[date][shift_id].get("RH") is not None):
                continue

            if local_employee == 'empty':
                local_employee = data_holder.select_eligible_employee_for_rh(employee_ids, date, shift_id)
                if local_employee is None:
                    break  # No more eligible employees for this shift/week, leave the rest unassigned.
            if local_employee != 'empty' and data_holder.is_on_leave(local_employee, date):
                local_employee = 'empty'
                continue

            data_holder.shifts_schedule[date][shift_id]["RH"] = local_employee
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
        self._current_view_year = year
        
        df = self.dao.get_assignments_for_month(month, year)
        if df.empty:
            return df
        
        shifts_df = self.dao.get_all_shifts()
        employees_df = self.dao.get_all_employees()
        
        active_shift_ids = set(shifts_df[shifts_df['is_active'] == True]['id'])
        df = df[df['shift_id'].isin(active_shift_ids)]
        if df.empty:
            return df
        
        shift_name_map = dict(zip(shifts_df['id'], shifts_df['shift_name']))
        df['shift_name'] = df['shift_id'].map(shift_name_map)
        
        emp_name_map = dict(zip(employees_df['id'], employees_df['name']))
        df['employee_name'] = df['employee_id'].map(emp_name_map)
        
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%d.%m - %a')
        df['employee_name'] = df['employee_name'].fillna("-")
        
        df['shift_role'] = df['shift_name'] + ' - ' + df['role']
        
        # Pivot: rows = dates, columns = shift_role, values = employee_name
        pivot_df = df.pivot(index='date', columns='shift_role', values='employee_name')
        pivot_df = pivot_df.fillna("empty")

        # Sort columns by shift name then role (RS before RH)
        cols = list(pivot_df.columns)
        cols.sort(key=lambda x: (x.split(' - ')[0], 0 if ' - RS' in x else 1))
        pivot_df = pivot_df[cols]

        pivot_df = pivot_df.reset_index()
        pivot_df.columns.name = None

        return pivot_df


    def get_employee_hours_pivot(self, month, year):
        """Builds an employee hours DataFrame from a fresh DataHolder.
        Shows active employees, plus any inactive ones who still appear in this month's schedule."""
        dh = self.generate_data_holder(month, year)

        # Collect IDs of employees who have at least one assignment this month
        scheduled_ids = set()
        for date_shifts in dh.shifts_schedule.values():
            for roles in date_shifts.values():
                for emp_id in roles.values():
                    if emp_id is not None:
                        scheduled_ids.add(emp_id)

        rows = []
        for emp_id, hours in dh.employee_hours.items():
            emp_data = dh.employees.get(emp_id, {})
            is_active = emp_data.get('is_active', True)
            if not is_active and emp_id not in scheduled_ids:
                continue
            rows.append({
                'Employee': emp_data.get('name', f'ID {emp_id}'),
                'Role': emp_data.get('qualification', '-'),
                'Target Hours': hours['target_hours'],
                'Completed Hours': hours['completed_hours'],
                'Remaining Hours': hours['target_hours'] - hours['completed_hours']
            })
        return pd.DataFrame(rows)


    def save_edited_assignments(self, edited_df):
        """Translates the edited UI grid back into database updates (un-pivot)."""
        
        employees_df = self.dao.get_all_employees()
        emp_name_to_id = dict(zip(employees_df['name'], employees_df['id']))
        emp_name_to_id['-'] = None
        
        shifts_df = self.dao.get_all_shifts()
        shift_name_to_id = dict(zip(shifts_df['shift_name'], shifts_df['id']))
        
        # Melt the dataframe (un-pivot)
        date_columns = [col for col in edited_df.columns if col != 'date']
        melted_df = edited_df.melt(id_vars=['date'], value_vars=date_columns, var_name='shift_role_str', value_name='employee_name')
        
        # Filter out slots where the shift doesn't run (marked "empty")
        melted_df = melted_df[melted_df['employee_name'] != 'empty']
        
        updates_list = []
        for _, row in melted_df.iterrows():
            shift_name, role = row['shift_role_str'].split(' - ')
            
            # Convert date string back to actual date object (format: "01.08 - Mon")
            date_str = row['date'].split(' - ')[0]
            day, month = date_str.split('.')
            date_obj = datetime.date(self._current_view_year, int(month), int(day))
            shift_id = shift_name_to_id.get(shift_name)
            
            if shift_id:
                updates_list.append({
                    'date': date_obj,
                    'shift_id': shift_id,
                    'role': role,
                    'employee_id': emp_name_to_id.get(row['employee_name'])
                })
                
        return self.dao.update_monthly_assignments(updates_list), "Schedule saved successfully!"


    def find_schedule_violations(self, month, year):
        """Runs all constraint checks on the schedule and returns a list of violation dicts."""
        dh = self.generate_data_holder(month, year)

        violations = []
        violations.extend(self.check_11_hour_violation(dh))
        violations.extend(self.check_double_shifts_violation(dh))
        violations.extend(self.check_vacation_violation(dh))
        violations.extend(self.check_shifts_have_paramedic_violation(dh))
        return violations


    def check_double_shifts_violation(self, dh):
        """Violations where an employee is assigned to multiple shifts on the same day."""
        violations = []

        for date_val, shifts in dh.shifts_schedule.items():
            emp_roles = {}
            for shift_id, roles in shifts.items():
                shift_name = dh.shifts.get(shift_id, {}).get('shift_name', '?')
                for role, emp_id in roles.items():
                    if emp_id is not None:
                        emp_roles.setdefault(emp_id, []).append(f"{shift_name}-{role}")

            for emp_id, assigned in emp_roles.items():
                if len(assigned) > 1:
                    name = dh.employees.get(emp_id, {}).get('name', f'ID {emp_id}')
                    violations.append({
                        'Date': date_val.strftime('%d.%m.%Y'),
                        'Shift': ', '.join(assigned),
                        'Employee': name,
                        'Type': 'Double shift',
                        'Description': f'{name} assigned to {", ".join(assigned)} on same day'
                    })

        return violations


    def check_shifts_have_paramedic_violation(self, dh):
        """Violations where a shift has no paramedic (RS) assigned."""
        violations = []

        for date_val, shifts in dh.shifts_schedule.items():
            for shift_id, roles in shifts.items():
                if roles.get('RS') is None:
                    shift_name = dh.shifts.get(shift_id, {}).get('shift_name', '?')
                    violations.append({
                        'Date': date_val.strftime('%d.%m.%Y'),
                        'Shift': shift_name,
                        'Employee': '-',
                        'Type': 'Missing paramedic',
                        'Description': f'{shift_name} has no RS assigned'
                    })

        return violations


    def check_11_hour_violation(self, dh):
        """Violations where an employee has < 11h rest between consecutive-day shifts."""
        violations = []

        for date_val, shifts in dh.shifts_schedule.items():
            for shift_id, roles in shifts.items():
                if shift_id not in dh.shifts:
                    continue
                shift_name = dh.shifts.get(shift_id, {}).get('shift_name', '?')
                for role, emp_id in roles.items():
                    if emp_id is None:
                        continue
                    if not dh.is_11h_rest_satisfied(emp_id, date_val, shift_id):
                        name = dh.employees.get(emp_id, {}).get('name', f'ID {emp_id}')
                        violations.append({
                            'Date': date_val.strftime('%d.%m.%Y'),
                            'Shift': f'{shift_name}-{role}',
                            'Employee': name,
                            'Type': '11-hour rest',
                            'Description': f'{name} has less than 11h rest before {shift_name}-{role}'
                        })

        return violations


    def check_vacation_violation(self, dh):
        """Violations where an employee is assigned on a day they are on vacation or sick leave."""
        violations = []

        for date_val, shifts in dh.shifts_schedule.items():
            for shift_id, roles in shifts.items():
                shift_name = dh.shifts.get(shift_id, {}).get('shift_name', '?')
                for role, emp_id in roles.items():
                    if emp_id is not None and dh.is_on_leave(emp_id, date_val):
                        name = dh.employees.get(emp_id, {}).get('name', f'ID {emp_id}')
                        violations.append({
                            'Date': date_val.strftime('%d.%m.%Y'),
                            'Shift': f'{shift_name}-{role}',
                            'Employee': name,
                            'Type': 'On leave',
                            'Description': f'{name} is on leave but assigned to {shift_name}-{role}'
                        })

        return violations