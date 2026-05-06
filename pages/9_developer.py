import streamlit as st
from logic.manager import Manager
from logic.auth_utils import ensure_authenticated
import time


class DeveloperPage:
    def __init__(self):
        # Restrict this purely to super admins (devs)
        ensure_authenticated(role_required='super')
        self.manager = Manager()


    def bulk_upload_section(self):
        """Section for bulk uploading employees via Excel or CSV."""
        st.header("Bulk Employee Upload")
        st.info("Upload an Excel or CSV file with columns: Name, Role, Contract Type")
        uploaded_file = st.file_uploader("Choose a file", type=["xlsx", "xls", "csv"])
        
        if uploaded_file is not None:
            if st.button("Upload Data", use_container_width=True):
                success, message = self.manager.upload_bulk_employees(uploaded_file)
                if success:
                    st.success(message)
                else:
                    st.error(message)


    def bulk_upload_shifts_section(self):
        """Button for uploading predefined shifts."""
        st.header("Shift Upload")
        if st.button("Upload Shifts"):
            self.manager.upload_bulk_shifts()
            st.success("Shifts populated successfully.")


    def dev_add_constraint_section(self):
        """Developer widget to directly inject constraints without wiping the database."""
        st.header("Inject Constraint")
        st.info("Add a constraint directly. Type lists like [\"K1\"] or numbers like 40.0.")
        with st.form("dev_add_constraint_form", clear_on_submit=True):
            category = st.text_input("Category (e.g., Shifts per day)")
            key = st.text_input("Constraint Key (e.g., Weekdays)")
            value_str = st.text_input("Constraint Value (e.g., [\"K1\", \"K2\"] or 40.0 or BY)")
            description = st.text_input("Description")
            
            if st.form_submit_button("Inject to Database"):
                success, message = self.manager.dev_add_constraint(category, key, value_str, description)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)

    
    def dev_delete_constraint_section(self):
        """Developer widget to delete constraints by ID."""
        st.header("Delete Constraint")
        st.info("Delete a constraint by specifying its ID.")
        with st.form("dev_delete_constraint_form", clear_on_submit=True):
            constraint_id = st.number_input("Constraint ID", min_value=1, step=1)
            
            if st.form_submit_button("Delete Constraint"):
                success, message = self.manager.dev_delete_constraint(constraint_id)
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
                self.dev_add_constraint_section()
        with col2:
            with st.container(border=True):
                self.bulk_upload_section()
            with st.container(border=True):
                self.bulk_upload_shifts_section()
            with st.container(border=True):
                self.dev_delete_constraint_section()


if __name__ == "__main__":
    page = DeveloperPage()
    page.render_page()