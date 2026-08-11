import streamlit as st
from logic.dev_tools import Developer
from logic.auth_utils import ensure_authenticated
from logic.schedule_manager import ScheduleManager
import datetime


class DeveloperPage:
    def __init__(self):
        # Restrict this purely to super admins (devs)
        ensure_authenticated(role_required='super')
        self.developer = Developer()
        self.schedule_manager = ScheduleManager()


    def bulk_upload_section(self):
        """Button for uploading predefined shifts."""
        st.header("Employees & Shifts Bulk Upload")

        if st.button("Upload Shifts"):
            success, msg = self.developer.dev_upload_bulk_shifts()
            st.success(msg)
        if st.button("Upload Employees"):
            success, msg = self.developer.dev_upload_bulk_employees()
            st.success(msg)


    def delete_constraint_section(self):
        """Developer widget to delete constraints by ID."""
        st.header("Delete Constraint")
        st.info("Delete a constraint by specifying its ID.")
        with st.form("dev_delete_constraint_form", clear_on_submit=True):
            constraint_id = st.number_input("Constraint ID", min_value=1, step=1)
            
            if st.form_submit_button("Delete Constraint"):
                success, message = self.developer.dev_delete_constraint(constraint_id)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def full_schedule_section(self):
        """One-click full schedule for testing — template → paramedics → assistants."""
        st.header("Full Schedule Generator")
        st.info("Generate empty template, assign paramedics, and assign assistants in one click.")
        
        now = datetime.datetime.now()
        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("Month", range(1, 13), index=now.month - 1, key="dev_full_month")
        with col2:
            year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="dev_full_year")
        
        if st.button("Generate Full Schedule"):
            success, message = self.developer.dev_full_schedule_run(month, year)
            if success:
                st.success(message)
            else:
                st.error(message)
            time.sleep(1.5)
            st.rerun()


    def delete_DB_assignments(self):
        """Widget to permanently delete all assignments for a selected month and year."""
        st.header("Delete DB Assignments")
        st.warning("⚠️ This permanently removes all schedule data for the selected month and year.")
        
        now = datetime.datetime.now()
        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("Month", range(1, 13), index=now.month - 1, key="del_month")
        with col2:
            year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="del_year")

        if st.button("Delete Assignments", type="primary"):
            success, message = self.developer.dev_delete_assignments_for_month(month, year)
            if success:
                st.success(message)
            else:
                st.error(message)
            time.sleep(1.5)
            st.rerun()


    def render_page(self):
        """Renders the developer tools page."""
        col1, col2 = st.columns([2, 2], gap="xlarge")
        with col1:
            with st.container(border=True):
                self.bulk_upload_section()
            with st.container(border=True):
                self.delete_DB_assignments()
        with col2:
            with st.container(border=True):
                self.delete_constraint_section()
            with st.container(border=True):
                self.full_schedule_section()


if __name__ == "__main__":
    page = DeveloperPage()
    page.render_page()