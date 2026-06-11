from repository.dao import DatabaseAccess


class ConstraintManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def populate_constraints(self):
        """
        The purpose of the function is to insert the available constraints to the Database so the user can later modify their values.
        """
        # Check if constraints already exist to prevent duplicates
        if not self.get_all_constraints().empty:
            return False, "Constraints already exist in the system."

        fulltime_contract_100 = {
            "category": "Contract hours",
            "constraint_key": "Full-time 100%",
            "constraint_value": None,
            "description": "How many hours a Full-time employee should work per week"
        }
        parttime_contract_75 = {
            "category": "Contract hours",
            "constraint_key": "Part-time 75%",
            "constraint_value": None,
            "description": "How many hours a 75% Part-time employee should work per week"
        }
        parttime_contract_50 = {
            "category": "Contract hours",
            "constraint_key": "Part-time 50%",
            "constraint_value": None,
            "description": "How many hours a 50% Part-time employee should work per week"
        }
        flexible_contract = {
            "category": "Contract hours",
            "constraint_key": "Flexible",
            "constraint_value": "32.0",
            "description": "MAXIMUM hours a flexible employee should work per week"
        }
        holiday_region = {
            "category": "Holidays",
            "constraint_key": "Region",
            "constraint_value": None,
            "description": "German State for public holidays (initials)"
        }
        break_between_shifts = {
            "category": "Work hours rules",
            "constraint_key": "Rest between Shifts",
            "constraint_value": 11,
            "description": "This is the minimum rest period (in hours) between shifts"
        }
        weekly_max_hours = {
            "category": "Work hours rules",
            "constraint_key": "Weekly Max hours",
            "constraint_value": 48,
            "description": "This is the maximum hours an employee can work per week"
        }

        constraints_list = [
            fulltime_contract_100,
            parttime_contract_75,
            parttime_contract_50,
            flexible_contract,
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


    def update_single_constraint(self, category, key, new_value):
        """Utility function to update a single constraint value, used for the holiday region and full-time hours."""
        if self.dao.update_single_constraint(category, key, new_value):
            return True, f"{key} constraint updated successfully."
        return False, f"Failed to update {key} constraint. Please try again."


    def update_parttime_contract_constraints(self, fulltime_hours):
        """When the full-time hours are updated, the part-time constraints should be updated accordingly to maintain their percentage."""
        parttime_75_hours = round(fulltime_hours * 0.75, 2)
        parttime_50_hours = round(fulltime_hours * 0.5, 2)

        success_75, message_75 = self.update_single_constraint("Contract hours", "Part-time 75%", parttime_75_hours)
        success_50, message_50 = self.update_single_constraint("Contract hours", "Part-time 50%", parttime_50_hours)

        if success_75 and success_50:
            return True, "Part-time contract constraints updated successfully."
        else:
            return False, "Failed to update Part-time 50% and 75% constraints."