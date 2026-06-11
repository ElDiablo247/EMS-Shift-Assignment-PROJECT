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

        if st.button("Create Default Constraints"):
            success, message = self.constraint_manager.populate_constraints()
            if success:
                st.success(message)
                time.sleep(1.5)
            else:
                st.error(message)
                time.sleep(1.5)

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

        col1, col2 = st.columns([2, 2], gap="small")
        with col1:
            with st.container(border=True):
                self.overview_section()
        has_constraints = not self.constraint_manager.get_all_constraints().empty
        with col2:
            if has_constraints:
                with st.container(border=True):
                    self.contract_constraints_section()
                    st.divider()
                    self.holidays_constraint_section()


if __name__ == "__main__":
    page = ConstraintsPage()
    page.render_page()