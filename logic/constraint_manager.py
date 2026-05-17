from repository.dao import DatabaseAccess


class ConstraintManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def populate_constraints(self):
        """
        This function is executed the very first moment when the super admin is registered.
        The purpose of the function is to insert the available constraints to the Database so the user can later modify their values.
        """
        weekday_shifts = {
            "category": "Shifts per day",
            "constraint_key": "Weekdays",
            "constraint_value": [],
            "description": "These shifts should run on a regular weekday (Monday to Friday)"
        }
        saturday_shifts = {
            "category": "Shifts per day",
            "constraint_key": "Saturday",
            "constraint_value": [],
            "description": "These shifts should run on a regular Saturday"
        }
        sunday_shifts = {
            "category": "Shifts per day",
            "constraint_key": "Sunday",
            "constraint_value": [],
            "description": "These shifts should run on a regular Sunday"
        }
        holiday_shifts = {
            "category": "Shifts per day",
            "constraint_key": "Holiday",
            "constraint_value": [],
            "description": "These shifts should run on public holidays for the given German state."
        }
        fulltime_hours = {
            "category": "Contract hours",
            "constraint_key": "Full-time",
            "constraint_value": None,
            "description": "How many hours a Full-time employee should work per week"
        }
        holiday_region = {
            "category": "Holidays",
            "constraint_key": "Region",
            "constraint_value": None,
            "description": "German State for public holidays (initials)"
        }
        break_between_shifts = {
            "category": "Work hours",
            "constraint_key": "Between Shifts",
            "constraint_value": 11,
            "description": "This is the minimum rest period (in hours) between shifts"
        }
        weekly_max_hours = {
            "category": "Work hours",
            "constraint_key": "Weekly Max",
            "constraint_value": 48,
            "description": "This is the maximum hours an employee can work per week"
        }

        constraints_list = [
            weekday_shifts,
            saturday_shifts,
            sunday_shifts,
            holiday_shifts,
            fulltime_hours,
            holiday_region,
            break_between_shifts,
            weekly_max_hours,
        ]

        if self.dao.populate_constraints(constraints_list):
            return True, "Constraints were successfully inserted in the Database!"
        return False, "Insertion of constraints in the database failed. Check the constraints and try again"


    def get_all_constraints(self):
        """Pass-through to fetch constraints DataFrame."""
        return self.dao.get_all_constraints()


    def update_multiple_constraints(self, constraints_df):
        """Calls DAO to update constraints."""
        if self.dao.update_multiple_constraints(constraints_df):
            return True, "Constraints updated successfully."
        return False, "Failed to update constraints."


    def get_shifts_per_day_constraints(self):
        """Fetches and filters constraints specifically for the shifts per day section."""
        df = self.get_all_constraints()
        if df.empty:
            return df
        return df[df['category'].isin(['Shifts per day'])].copy()


    def update_single_constraint(self, category, key, new_value):
        """Utility function to update a single constraint value, used for the holiday region and full-time hours."""
        if self.dao.update_single_constraint(category, key, new_value):
            return True, f"{key} constraint updated successfully."
        return False, f"Failed to update {key} constraint. Please try again."