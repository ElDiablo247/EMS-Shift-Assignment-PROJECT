from repository.dao import DatabaseAccess
from datetime import datetime
import pandas as pd


class ShiftManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    @staticmethod
    def calculate_shift_duration(shift_start, shift_end):
        """Derives the stored shift duration by subtracting the legally mandated break:
        - total time between 6 and 9 hours  → 30-minute break
        - total time over 9 and up to 10h45 → 45-minute break
        Returns the net duration in hours, or None if the shift length is outside that range."""
        if shift_start is None or shift_end is None:
            return None

        start_minutes = shift_start.hour * 60 + shift_start.minute
        end_minutes = shift_end.hour * 60 + shift_end.minute
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60  # overnight shift crossing midnight
        total_minutes = end_minutes - start_minutes

        if 6 * 60 <= total_minutes <= 9 * 60:
            net_minutes = total_minutes - 30
        elif 9 * 60 < total_minutes <= 10 * 60 + 45:
            net_minutes = total_minutes - 45
        else:
            return None
        return round(net_minutes / 60, 2)


    def add_shift(self, shift_name, shift_start, shift_end, runs_on_weekend_or_holiday):
        """Validates input, derives the shift duration, generates an ID, and calls DAO to save shift."""
        if not shift_name or not shift_start or not shift_end:
            return False, "Validation failed: Shift fields are missing. Please ensure all fields are filled."

        shift_duration = self.calculate_shift_duration(shift_start, shift_end)
        if shift_duration is None:
            return False, "Validation failed: Shift total time must be between 6 and 10 hours 45 minutes."

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
        """
        Recalculates the duration of every shift from its start/end times before saving, so the stored duration is always 
        a derived value. Rejects the update if any shift falls outside the valid range.
        """
        for idx, row in shifts_df.iterrows():
            if pd.isna(row["id"]):
                continue
            duration = self.calculate_shift_duration(row["shift_start"], row["shift_end"])
            if duration is None:
                return False, (
                    f"Validation failed for shift ID {row['id']}: "
                    "Shift total time must be between 6 hours and 10 hours 45 minutes."
                )
            shifts_df.at[idx, "shift_duration"] = duration

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