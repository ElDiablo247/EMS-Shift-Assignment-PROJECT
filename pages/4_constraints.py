import streamlit as st
from logic.auth_utils import ensure_authenticated
from logic.constraint_manager import ConstraintManager
from logic.shift_manager import ShiftManager
import pandas as pd
import datetime
import time


class ConstraintsPage:
    def __init__(self):
        ensure_authenticated()
        self.constraint_manager = ConstraintManager()
        self.shift_manager = ShiftManager()


    def create_defaults_section(self):
        st.info("Populate the system with default constraint values.")
        if st.button("Create Default Constraints"):
            success, message = self.constraint_manager.populate_constraints()
            if success:
                st.success(message)
            else:
                st.error(message)
            time.sleep(1.5)
            st.rerun()


    def overview_section(self):
        """Displays a read-only overview of all system constraints."""
        st.header("Constraints Overview")
        st.info("Current active rules for the system.")

        df = self.constraint_manager.get_all_constraints()
        
        if not df.empty:
            df['constraint_value'] = df['constraint_value'].astype(str)
            st.dataframe(
                df,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "category": st.column_config.TextColumn("Category"),
                    "constraint_key": st.column_config.TextColumn("Key"),
                    "constraint_value": st.column_config.TextColumn("Value", width="medium"),
                    "description": st.column_config.TextColumn("Description", width="medium")
                },
                hide_index=True,
                use_container_width=False
            )


    def contract_constraints_section(self):
        """Section for configuring the baseline full-time hours."""
        st.header("Contract Hours Baseline")
        st.info("Define the standard hours per week for a 100% Full-Time contract.")

        options = [35.0, 35.5, 36.0, 36.5, 37.0, 37.5, 38.0, 38.5, 39.0, 39.5, 40.0, 40.5, 41.0, 41.5, 42.0, 42.5]
        selected_hours = st.selectbox(
            "Select Full-Time Hours per Week",
            options=options,
            index=options.index(40.0)
        )
        if st.button("Save Contract Hours"):
            success, message = self.constraint_manager.update_single_constraint("Contract hours", "Full-time 100%", selected_hours)
            if success:
                st.success(message)
                
                pt_success, pt_message = self.constraint_manager.update_parttime_contract_constraints(selected_hours)
                if pt_success:
                    st.success(pt_message)
                else:
                    st.error(pt_message)
                    
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def holidays_region_section(self):
        """Section for managing the permanent holiday region."""
        st.header("Holiday Management")
        st.info("Select the German state the company operates in.")

        state_code = st.selectbox("State Code", options=["BE", "BW", "BY", "HB", "HE", "HH", "MV", "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH"])
        if st.button("Save Region"):
            success, message = self.constraint_manager.update_single_constraint("Holidays", "Region", state_code)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def generate_holidays_section(self):
        st.info("Generate the public holidays for a specific year.")
        year_for_holidays = st.number_input("Year", min_value=datetime.datetime.now().year - 1, max_value=2130, value=datetime.datetime.now().year, step=1, key="holiday_year")
        if st.button("Generate Holidays"):
            success, message = self.constraint_manager.generate_year_holidays(year_for_holidays)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def display_holidays_section(self):
        """Displays the contents of the holidays table."""
        st.header("Holidays Overview")
        
        now = datetime.datetime.now()
        view_year = st.number_input("View Holidays for Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="holiday_view_year")
        
        holidays_df = self.constraint_manager.get_all_holidays_df(year=view_year)
        if holidays_df.empty:
            st.warning(f"No holidays found for {view_year}. Use the 'Generate Holidays' tool.")
        else:
            st.dataframe(holidays_df, use_container_width=True, hide_index=True)


    def render_page(self):
        """Renders the constraints page layout."""
        # Sidebar: Action widgets with expanders
        with st.sidebar:
            with st.expander("Create Defaults", expanded=False):
                self.create_defaults_section()
            with st.expander("Contract Hours", expanded=False):
                self.contract_constraints_section()
            with st.expander("Holiday Region", expanded=False):
                self.holidays_region_section()
            with st.expander("Generate Holidays", expanded=False):
                self.generate_holidays_section()
        
        # Main area: 50-50 constraints table and holidays table
        col1, col2 = st.columns([3, 2], gap="large")
        with col1:
            with st.container(border=True):
                self.overview_section()
        with col2:
            with st.container(border=True):
                self.display_holidays_section()

if __name__ == "__main__":
    page = ConstraintsPage()
    page.render_page()