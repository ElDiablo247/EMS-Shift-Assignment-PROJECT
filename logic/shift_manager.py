from repository.dao import DatabaseAccess
from datetime import datetime


class ShiftManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def add_shift(self, shift_name, shift_start, shift_end, shift_duration, runs_on_weekend_or_holiday):
        """
        Validates input, generates an ID, and calls DAO to save shift.
        """
        if not shift_name or not shift_start or not shift_end:
            return False, "Validation failed: All shift fields must be populated."

        # ID Generation
        last_id = self.dao.get_last_shift_id()
        if last_id is not None:
            new_id = last_id + 1
        else:
            new_id = 101  # Starting ID for shifts if database is empty
        success = self.dao.add_shift(new_id, shift_name, shift_start, shift_end, shift_duration, runs_on_weekend_or_holiday)
        if success:
            return True, "Shift added successfully."
        else:
            return False, "Error adding shift. Please try again."
        

    def get_all_shifts(self):
        """Pass-through to DAO"""
        return self.dao.get_all_shifts()


    def update_shifts(self, shifts_df):
        if self.dao.update_shifts(shifts_df):
            return True, "Shift definitions updated successfully."
        return False, "Failed to update shift definitions."


    def return_shift_names(self):
        """Fetches all shifts and filters out just the active shift names as a list."""
        shifts_df = self.get_all_shifts()
        if shifts_df.empty:
            return []
        
        active_shifts = shifts_df[shifts_df['is_active'] == True]
        return active_shifts['shift_name'].tolist()