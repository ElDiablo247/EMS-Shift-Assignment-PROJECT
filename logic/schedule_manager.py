import random
from repository.dao import DatabaseAccess
import pandas as pd
import calendar
import datetime
from logic.temporary_data import Cache


class ScheduleManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def generate_template(self, month, year):
        """Builds the empty template in memory. Returns (cache, None) on success,
        or (None, error_msg) if a schedule already exists for this month.
        Does NOT commit to DB — the caller chains into the next stage."""
        first_day_of_month = datetime.date(year, month, 1)
        if self.dao.assignments_exist_for_date(first_day_of_month):
            return None, "A schedule template for the given month and year already exists!"

        cache = self.generate_cache(month, year)

        for date in cache.dates:
            cache.shifts_schedule[date] = {}
            if date in cache.holidays or date.weekday() >= 5:
                for shift_id, values in cache.shifts.items():
                    if not values.get('is_active', True):
                        continue
                    if values['runs_on_weekend_or_holiday'] == True:
                        cache.shifts_schedule[date][shift_id] = {"RS": None, "RH": None}
            else:
                for shift_id, values in cache.shifts.items():
                    if not values.get('is_active', True):
                        continue
                    cache.shifts_schedule[date][shift_id] = {"RS": None, "RH": None}

        cache._map_weekdays_to_weeks()
        cache._map_assigned_employees_for_date()
        return cache, None


    def generate_schedule(self, month, year):
        """One-shot: template → RS → RH → single DB commit."""
        cache, error_message = self.generate_template(month, year)
        if error_message:
            return False, error_message
        cache = self.assign_paramedics(cache)
        return self.assign_rest_of_employees(cache)


    def generate_cache(self, month, year):
        """Fetches assignments, employees, and shifts for a given month/year and returns an initialized Cache."""
        cache = Cache()
        shifts_df = self.dao.get_all_shifts()
        holidays_df = self.dao.get_all_holidays(year)
        employees_df = self.dao.get_all_employees()
        assignments_df = self.dao.get_assignments_for_month(month, year)
        vacations_df = self.dao.get_all_vacations()
        ft_hours = self.dao.get_single_constraint("Contract hours", "Full-time 100%")
        ft_hours = float(ft_hours) if ft_hours else 42.5   # convert string to float
        cache.set_up_cache(month, year, holidays_df, shifts_df, employees_df, assignments_df, vacations_df, ft_hours)
        return cache


    def assign_paramedics(self, cache):
        """Assigns paramedics (RS) to the given Cache in memory.
        Carries over the previous-month shift pattern first, then fills RS slots.
        Does NOT commit to DB — returns cache for the next stage."""
        self._load_prev_month_shift_pattern(cache.month, cache.year, cache)
        cache._apply_prev_month_pattern()
        shift_ids = cache.get_shift_ids()

        for contract_type in ["100%", "75%", "50%"]:
            for week_key, dates_dict in cache.weekday_weeks.items():
                employee_ids = cache.get_paramedic_ids_by_contract(contract_type)
                if not employee_ids:
                    continue
                random.shuffle(shift_ids)
                for local_shift_id in shift_ids:
                    self.assign_week_with_paramedics(cache, local_shift_id, dates_dict, employee_ids)

        return cache


    def assign_week_with_paramedics(self, cache, shift_id, dates_dict, employee_ids):
        """Helper function to fill a week's worth of shifts with paramedics of a specific contract type."""
        local_employee = 'empty'

        for date in dates_dict:
            if shift_id not in cache.shifts_schedule.get(date, {}) or cache.shifts_schedule[date][shift_id].get("RS") is not None:
                continue # If the shift doesn't exist on this date or is already filled, skip to the next date.
            
            if local_employee == 'empty':
                local_employee = cache.select_eligible_employee_id(employee_ids, date)
                if local_employee is None: 
                    break # This means there are no more eligible employees at all so the rest of the week will remain unassigned for this shift.
            if local_employee != 'empty' and cache.is_on_leave(local_employee, date):
                local_employee = 'empty'
                continue

            cache.shifts_schedule[date][shift_id]["RS"] = local_employee
            cache.assigned_employees_for_date[date].add(local_employee) 
            cache.employee_hours[local_employee]["completed_hours"] += cache.shifts[shift_id]["shift_duration"]
            if cache.employee_hours[local_employee]["completed_hours"] >= cache.employee_hours[local_employee]["target_hours"]:
                local_employee = 'empty'


    def assign_rest_of_employees(self, cache):
        """Assigns assistants (RH) to the given Cache in memory,
        then commits the FULL schedule to the database in one shot."""
        shift_ids = cache.get_shift_ids()

        for contract_type in ["100%", "75%", "50%", "Flexible"]:
            for week_key, dates_dict in cache.weekday_weeks.items():
                employee_ids = cache.get_employees_sorted_by_remaining(contract_type)
                if not employee_ids:
                    continue
                random.shuffle(shift_ids)
                for local_shift_id in shift_ids:
                    self.assign_week_with_rest_employees(cache, local_shift_id, dates_dict, employee_ids)

        flat = cache.return_flattened_empty_template()
        if self.dao.bulk_insert_assignments(flat):
            return True, f"Full schedule for {cache.month}/{cache.year} generated and saved!"
        return False, "Database error: Failed to save the schedule."


    def assign_week_with_rest_employees(self, cache, shift_id, dates_dict, employee_ids):
        """Fills a week's worth of RH slots for one shift. Keeps the same employee across
        all dates of the week until they hit their target, then picks the next eligible one.
        Each candidate must pass: under target, not already on that date, and 11h rest."""
        local_employee = 'empty'

        for date in dates_dict:
            if (shift_id not in cache.shifts_schedule.get(date, {})
                    or cache.shifts_schedule[date][shift_id].get("RH") is not None):
                continue

            if local_employee == 'empty':
                local_employee = cache.select_eligible_employee_for_rh(employee_ids, date, shift_id)
                if local_employee is None:
                    break  # No more eligible employees for this shift/week, leave the rest unassigned.
            if local_employee != 'empty' and cache.is_on_leave(local_employee, date):
                local_employee = 'empty'
                continue

            cache.shifts_schedule[date][shift_id]["RH"] = local_employee
            cache.assigned_employees_for_date[date].add(local_employee)
            cache.employee_hours[local_employee]["completed_hours"] += cache.shifts[shift_id]["shift_duration"]

            if cache.employee_hours[local_employee]["completed_hours"] >= cache.employee_hours[local_employee]["target_hours"]:
                local_employee = 'empty'


    def _load_prev_month_shift_pattern(self, month, year, cache):
        """Finds the last weekday of the previous month, fetches its assignments from the DB, and passes them to the Cache for carry-over."""
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
            cache._set_prev_month_shift_pattern(df)


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
        """Builds an employee hours DataFrame from a fresh Cache.
        Shows active employees, plus any inactive ones who still appear in this month's schedule."""
        cache = self.generate_cache(month, year)

        # Collect IDs of employees who have at least one assignment this month
        scheduled_ids = set()
        for date_shifts in cache.shifts_schedule.values():
            for roles in date_shifts.values():
                for emp_id in roles.values():
                    if emp_id is not None:
                        scheduled_ids.add(emp_id)

        rows = []
        for emp_id, hours in cache.employee_hours.items():
            emp_data = cache.employees.get(emp_id, {})
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
        """Translates the edited UI grid back into database updates (un-pivot).
        Only sends rows that actually changed — diffs, not the full schedule."""

        employees_df = self.dao.get_all_employees()
        emp_name_to_id = dict(zip(employees_df['name'], employees_df['id']))
        emp_name_to_id['-'] = None
        
        shifts_df = self.dao.get_all_shifts()
        shift_name_to_id = dict(zip(shifts_df['shift_name'], shifts_df['id']))
        
        # 1. Load current DB schedule as lookup for comparison
        date_columns = [col for col in edited_df.columns if col != 'date']
        first_date_str = edited_df['date'].iloc[0].split(' - ')[0] # Extract the date part before the ' - ' separator
        day, month = first_date_str.split('.')
        year = self._current_view_year
        current_db = self.dao.get_assignments_for_month(int(month), year)
        
        # 2. Format current DB into a lookup dict: (date, shift_id, role) -> employee_id
        db_lookup = {}
        if not current_db.empty:
            for _, row in current_db.iterrows():
                date_val = pd.to_datetime(row['date']).date()
                key = (date_val, row['shift_id'], row['role'])
                emp = row['employee_id']
                db_lookup[key] = int(emp) if pd.notna(emp) else None
        
        # 3. Format the edited DataFrame into a long format for comparison
        melted_df = edited_df.melt(
            id_vars=['date'], value_vars=date_columns,
            var_name='shift_role_str', value_name='employee_name'
        )
        
        # 4. Compare each row in the melted edited DataFrame with the current DB lookup, and keep only the rows that have changed
        updates_list = []
        for _, row in melted_df.iterrows():
            shift_name, role = row['shift_role_str'].split(' - ')
            
            date_str = row['date'].split(' - ')[0]
            day, month = date_str.split('.')
            date_obj = datetime.date(year, int(month), int(day))
            shift_id = shift_name_to_id.get(shift_name)
            
            if not shift_id:
                continue
            
            new_emp_id = emp_name_to_id.get(row['employee_name'])
            key = (date_obj, shift_id, role)
            old_emp_id = db_lookup.get(key)
            
            # Only include if the assignment actually changed
            if old_emp_id != new_emp_id:
                updates_list.append({
                    'date': date_obj,
                    'shift_id': shift_id,
                    'role': role,
                    'employee_id': new_emp_id
                })
        
        # 5. Commit the changes to the database if there are any updates
        if updates_list:
            if self.dao.update_monthly_assignments(updates_list):
                return True, "Schedule saved successfully!"
            return False, "Database error: Failed to save changes."
        return True, "No changes detected."


    def swap_shift_employees(self, date_range, shift_a_name, shift_b_name, role):
        """Swaps the employees of two shift-role slots for each day inside the date range.
        Handles all validation and shift-name resolution; commits only the swapped days."""
        if not (isinstance(date_range, tuple) and len(date_range) == 2):
            return False, "Please select a full date range (start and end)."

        start_date, end_date = date_range
        if (start_date.year, start_date.month) != (end_date.year, end_date.month):
            return False, "The date range must stay within a single month."
        if shift_a_name == shift_b_name:
            return False, "Please choose two different shifts."

        shifts_df = self.dao.get_all_shifts()
        shift_name_to_id = dict(zip(shifts_df['shift_name'], shifts_df['id']))
        shift_a_id = shift_name_to_id.get(shift_a_name)
        shift_b_id = shift_name_to_id.get(shift_b_name)
        if shift_a_id is None or shift_b_id is None:
            return False, "One of the selected shifts could not be found."

        month, year = start_date.month, start_date.year
        cache = self.generate_cache(month, year)
        updates = []
        for date in cache.dates:
            if not (start_date <= date <= end_date):
                continue
            day = cache.shifts_schedule.get(date)
            if not day or shift_a_id not in day or shift_b_id not in day:
                continue  # one of the shifts doesn't run on this date
            emp_a = day[shift_a_id].get(role)
            emp_b = day[shift_b_id].get(role)
            if emp_a == emp_b:
                continue  # identity swap, skip silently
            day[shift_a_id][role], day[shift_b_id][role] = emp_b, emp_a
            updates.append({'date': date, 'shift_id': shift_a_id, 'role': role, 'employee_id': emp_b})
            updates.append({'date': date, 'shift_id': shift_b_id, 'role': role, 'employee_id': emp_a})

        if not updates:
            return False, "No days found in the range where both shifts run."
        if self.dao.update_monthly_assignments(updates):
            return True, f"Swap executed successfully for {len(updates) // 2} day(s)."
        return False, "Database error: Failed to save the swap."


    def find_schedule_violations(self, month, year):
        """Runs all constraint checks on the schedule and returns a list of violation dicts."""
        cache = self.generate_cache(month, year)

        violations = []
        violations.extend(self.check_11_hour_violation(cache))
        violations.extend(self.check_double_shifts_violation(cache))
        violations.extend(self.check_vacation_violation(cache))
        violations.extend(self.check_shifts_lack_paramedic_violation(cache))
        violations.extend(self.check_night_shift_violation(cache))
        return violations


    def check_double_shifts_violation(self, cache):
        """Violations where an employee is assigned to multiple shifts on the same day."""
        violations = []

        for date_val, shifts in cache.shifts_schedule.items():
            emp_roles = {}
            for shift_id, roles in shifts.items():
                shift_name = cache.shifts.get(shift_id, {}).get('shift_name', '?')
                for role, emp_id in roles.items():
                    if emp_id is not None:
                        emp_roles.setdefault(emp_id, []).append(f"{shift_name}-{role}")

            for emp_id, assigned in emp_roles.items():
                if len(assigned) > 1:
                    name = cache.employees.get(emp_id, {}).get('name', f'ID {emp_id}')
                    violations.append({
                        'Date': date_val.strftime('%d.%m.%Y'),
                        'Shift': ', '.join(assigned),
                        'Employee': name,
                        'Type': 'Double shift',
                        'Description': f'{name} assigned to {", ".join(assigned)} on same day'
                    })

        return violations


    def check_shifts_lack_paramedic_violation(self, cache):
        """Violations where a shift has no qualified paramedic (RS) in its RS slot."""
        violations = []

        for date_val, shifts in cache.shifts_schedule.items():
            for shift_id, roles in shifts.items():
                rs_emp = roles.get('RS')
                shift_name = cache.shifts.get(shift_id, {}).get('shift_name', '?')

                if rs_emp is None:
                    violations.append({
                        'Date': date_val.strftime('%d.%m.%Y'),
                        'Shift': shift_name,
                        'Employee': '-',
                        'Type': 'Missing paramedic',
                        'Description': f'{shift_name} has no RS assigned'
                    })
                else:
                    qual = cache.employees.get(rs_emp, {}).get('qualification', '')
                    if qual != 'RS':
                        name = cache.employees.get(rs_emp, {}).get('name', f'ID {rs_emp}')
                        violations.append({
                            'Date': date_val.strftime('%d.%m.%Y'),
                            'Shift': shift_name,
                            'Employee': name,
                            'Type': 'Missing paramedic',
                            'Description': f'{shift_name} RS slot filled by {name} ({qual}), not a paramedic'
                        })

        return violations


    def check_11_hour_violation(self, cache):
        """Violations where an employee has < 11h rest between consecutive-day shifts."""
        violations = []

        for date_val, shifts in cache.shifts_schedule.items():
            for shift_id, roles in shifts.items():
                if shift_id not in cache.shifts:
                    continue
                shift_name = cache.shifts.get(shift_id, {}).get('shift_name', '?')
                for role, emp_id in roles.items():
                    if emp_id is None:
                        continue
                    if not cache.is_11h_rest_satisfied(emp_id, date_val, shift_id):
                        name = cache.employees.get(emp_id, {}).get('name', f'ID {emp_id}')
                        violations.append({
                            'Date': date_val.strftime('%d.%m.%Y'),
                            'Shift': f'{shift_name}-{role}',
                            'Employee': name,
                            'Type': '11-hour rest',
                            'Description': f'{name} has less than 11h rest before {shift_name}-{role}'
                        })

        return violations


    def check_vacation_violation(self, cache):
        """Violations where an employee is assigned on a day they are on vacation."""
        violations = []

        for date_val, shifts in cache.shifts_schedule.items():
            for shift_id, roles in shifts.items():
                shift_name = cache.shifts.get(shift_id, {}).get('shift_name', '?')
                for role, emp_id in roles.items():
                    if emp_id is not None and cache.is_on_leave(emp_id, date_val):
                        name = cache.employees.get(emp_id, {}).get('name', f'ID {emp_id}')
                        violations.append({
                            'Date': date_val.strftime('%d.%m.%Y'),
                            'Shift': f'{shift_name}-{role}',
                            'Employee': name,
                            'Type': 'On leave',
                            'Description': f'{name} is on vacation but assigned to {shift_name}-{role}'
                        })

        return violations


    def check_night_shift_violation(self, cache):
        """Violations where an employee worked more than 5 days of night shifts in the month."""
        violations = []

        night_days = {}  # employee_id -> set of dates with a night shift
        for date_val, shifts in cache.shifts_schedule.items():
            for shift_id, roles in shifts.items():
                if not cache.is_night_shift(shift_id):
                    continue
                for role, emp_id in roles.items():
                    if emp_id is not None:
                        night_days.setdefault(emp_id, set()).add(date_val)

        for emp_id, dates in night_days.items():
            if len(dates) > 5:
                name = cache.employees.get(emp_id, {}).get('name', f'ID {emp_id}')
                violations.append({
                    'Date': '-',
                    'Shift': 'Night shifts',
                    'Employee': name,
                    'Type': 'Night shift limit',
                    'Description': f'{name} worked {len(dates)} night shifts (limit=5)'
                })

        return violations