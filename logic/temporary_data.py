import pandas as pd
import calendar
import holidays
import datetime


class DataHolder:
    def __init__(self, month, year, assignments_df, employees_df, shifts_df):
        self.month = month
        self.year = year
        self.paramedics = []
        self.assistants = []
        self.assignments = {}
        self.employees = {}
        self.shifts = {}

        self._store_assignments(assignments_df)
        self._store_employees(employees_df)
        self._store_shifts(shifts_df)

    def _store_assignments(self, df):
        """Converts the assignments DataFrame to a dictionary indexed by ID."""
        if not df.empty and 'id' in df.columns:
            self.assignments = df.set_index('id').to_dict('index')
        elif not df.empty:
            self.assignments = df.to_dict('index')

    def _store_employees(self, df):
        """Converts the employees DataFrame to a dictionary indexed by ID."""
        if not df.empty and 'id' in df.columns:
            self.employees = df.set_index('id').to_dict('index')

    def _store_shifts(self, df):
        """Converts the shifts DataFrame to a dictionary indexed by ID."""
        if not df.empty and 'id' in df.columns:
            self.shifts = df.set_index('id').to_dict('index')


    def generate_template_data(self, month, year):
        """Generates the needed data for the empty template generation process"""