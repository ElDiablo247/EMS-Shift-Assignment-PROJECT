import streamlit as st
from logic.dev_tools import Developer
from logic.auth_utils import ensure_authenticated
import time


class DeveloperPage:
    def __init__(self):
        # Restrict this purely to super admins (devs)
        ensure_authenticated(role_required='super')
        self.developer = Developer()


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


    def render_page(self):
        """Renders the developer tools page."""
        st.sidebar.title(f"Welcome, {st.session_state['username']}!")
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Refresh Data"):
            st.rerun()
        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        col1, col2 = st.columns([2, 2], gap="xlarge")
        with col1:
            with st.container(border=True):
                self.add_constraint_section()
        with col2:
            with st.container(border=True):
                self.bulk_upload_section()
            with st.container(border=True):
                self.delete_constraint_section()


if __name__ == "__main__":
    page = DeveloperPage()
    page.render_page()