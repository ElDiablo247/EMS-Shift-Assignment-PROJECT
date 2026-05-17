import streamlit as st
from logic.auth_utils import ensure_authenticated
from logic.constraint_manager import ConstraintManager
from logic.shift_manager import ShiftManager
import pandas as pd
import time


class ConstraintsPage:
    def __init__(self):
        ensure_authenticated()
        self.constraint_manager = ConstraintManager()
        self.shift_manager = ShiftManager()


    def overview_section(self):
        """Displays a read-only overview of all system constraints."""
        st.header("Configuration Overview")
        st.info("Current active rules for the system.")
        df = self.constraint_manager.get_all_constraints()
        
        if not df.empty:
            # Convert the constraint_value column to strings
            df['constraint_value'] = df['constraint_value'].astype(str)
            st.dataframe(
                df,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "category": st.column_config.TextColumn("Category"),
                    "constraint_key": st.column_config.TextColumn("Key"),
                    "constraint_value": st.column_config.TextColumn("Value", width="medium"),
                    "description": None
                },
                hide_index=True,
                use_container_width=False
            )


    def shifts_per_day_section(self):
        """Section for assigning which shifts are available on which days using a multiselect table."""
        st.header("Shifts Per Day Configuration")
        st.info("Select the shifts that should run on each day category.")
        
        # 1. Fetch the shifts per day constraints from the database and the shift names, with the help of the manager.
        shifts_df = self.constraint_manager.get_shifts_per_day_constraints()
        available_shifts = self.shift_manager.return_shift_names()
        
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
        
        # Wrap the editor and button in a form 
        with st.form("shifts_per_day_form"):
            edited_df = st.data_editor(
                shifts_df,
                column_config=column_config,
                hide_index=True,
                use_container_width=True,
                key="shifts_per_day_editor"
            )
            
            # 4. Save Changes
            if st.form_submit_button("Save Constraints"):
                success, message = self.constraint_manager.update_multiple_constraints(edited_df)
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
            success, message = self.constraint_manager.update_single_constraint("Contract hours", "Full-time", selected_hours)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def holidays_constraint_section(self):
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


    def render_page(self):
        """Renders the constraints page layout."""
        st.sidebar.title(f"Welcome, {st.session_state.get('username', 'User')}!")
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Refresh Data"):
            st.rerun()
        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        with st.container(border=True):
            self.overview_section()

        with st.container(border=True):
            tab1, tab2, tab3 = st.tabs(["Shifts per Day Rules", "Full-time Contract Rules", "Holiday Rules"])
            with tab1:
                self.shifts_per_day_section()
            with tab2:
                self.contract_constraints_section()
            with tab3:
                self.holidays_constraint_section()


if __name__ == "__main__":
    page = ConstraintsPage()
    page.render_page()