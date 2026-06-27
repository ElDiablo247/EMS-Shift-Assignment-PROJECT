import streamlit as st
from logic.dev_tools import Developer
from logic.auth_utils import ensure_authenticated
from logic.schedule_manager import ScheduleManager
import time
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


    def add_constraint_section(self):
        """Developer widget to directly inject constraints without wiping the database."""
        st.header("Inject Constraint")
        st.info("Add a constraint directly. Type lists like [\"K1\"] or numbers like 40.0.")
        with st.form("dev_add_constraint_form", clear_on_submit=True):
            category = st.text_input("Category (e.g., Shifts per day)")
            key = st.text_input("Constraint Key (e.g., Weekdays)")
            value_str = st.text_input("Constraint Value (e.g., [\"K1\", \"K2\"] or 40.0 or BY)")
            description = st.text_input("Description")
            
            if st.form_submit_button("Inject to Database"):
                success, message = self.developer.dev_add_constraint(category, key, value_str, description)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)

    
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


    def dataholder_test_section(self):
        """Section to instantiate DataHolder and test its dictionaries."""
        st.header("DataHolder Tester")
        st.info("Load the DataHolder for a specific month and print its data to the console.")
        
        now = datetime.datetime.now()
        col1, col2 = st.columns(2)
        with col1:
            month = st.number_input("Test Month", min_value=1, max_value=12, value=now.month, step=1, key="dh_test_month")
        with col2:
            year = st.number_input("Test Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="dh_test_year")
            
        if st.button("Load DataHolder"):
            dh = self.schedule_manager.load_data_for_assignment(month, year)
            st.session_state['test_dataholder'] = dh
            st.success(f"DataHolder for {month}/{year} initialized and saved in memory.")
            
        if st.button("Print Dictionaries to UI"):
            if 'test_dataholder' in st.session_state:
                debug_str = st.session_state['test_dataholder'].get_debug_string()
                st.code(debug_str, language="plaintext")
            else:
                st.error("Please click 'Load DataHolder' first.")


    def render_page(self):
        """Renders the developer tools page."""
        col1, col2 = st.columns([2, 2], gap="xlarge")
        with col1:
            with st.container(border=True):
                self.add_constraint_section()
            with st.container(border=True):
                self.dataholder_test_section()
        with col2:
            with st.container(border=True):
                self.bulk_upload_section()
            with st.container(border=True):
                self.delete_constraint_section()


if __name__ == "__main__":
    page = DeveloperPage()
    page.render_page()