import streamlit as st
from logic.auth_utils import ensure_authenticated
from logic.manager import Manager
import pandas as pd
import time


class ConstraintsPage:
    def __init__(self):
        ensure_authenticated()
        self.manager = Manager()


    def shifts_per_day_section(self):
        """Section for assigning which shifts are available on which days using a multiselect table."""
        st.header("Shifts Per Day Configuration")
        st.info("Select the shifts that should run on each specific day.")
        
        # 1. Fetch the shifts per day constraints from the database and the shift names, with the help of the manager.
        shifts_df = self.manager.get_shifts_per_day_constraints()
        available_shifts = self.manager.return_shift_names()
        
        # 2. Configure the data_editor columns
        column_config = {
            "id": None,  # Hide ID
            "category": None, # Hide category
            "constraint_key": st.column_config.TextColumn("Day", disabled=True),
            "description": st.column_config.TextColumn("Description", disabled=True),
            "constraint_value": st.column_config.MultiselectColumn(
                "Assigned Shifts",
                options=available_shifts,
                help="Select all shifts that apply to this day"
            )
        }
        
        # 3. Display the data
        edited_df = st.data_editor(
            shifts_df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            key="shifts_per_day_editor"
        )
        
        # 4. Save Changes
        if st.button("Save Shift Constraints"):
            success, message = self.manager.update_constraints(edited_df)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def contract_constraints_section(self):
        """Section for configuring the baseline full-time hours."""
        st.header("Contract Hours Baseline")
        st.info("Define the standard hours per week for a 100% Full-Time contract.")

        selected_hours = st.selectbox(
            "Select Full-Time Hours per Week",
            options=[37.5, 40.0, 42.5]
        )
        if st.button("Save Contract Hours"):
            success, message = self.manager.update_fulltime_hours(selected_hours)
            if success:
                st.success(message)
            else:
                st.error(message)


    def render_page(self):
        """Renders the constraints management page layout."""
        st.sidebar.title(f"Welcome, {st.session_state.get('username', 'User')}!")
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Refresh Data"):
            st.rerun()
        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        col1, col2 = st.columns([2, 1], gap="large")
        with col1:
            with st.container(border=True):
                self.shifts_per_day_section()
        with col2:
            with st.container(border=True):
                self.contract_constraints_section()


if __name__ == "__main__":
    page = ConstraintsPage()
    page.render_page()