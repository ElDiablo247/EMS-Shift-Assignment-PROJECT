import streamlit as st
from logic.manager import Manager
from logic.auth_utils import ensure_authenticated
import time


class EmployeePage:
    def __init__(self):
        ensure_authenticated()
        self.manager = Manager()


    def add_employee_section(self):
        """Section for adding new employees to the system."""
        st.header("Employee Registration")
        name = st.text_input("Employee Name")
        qualification = st.selectbox("Role", ["Paramedic", "Assistant"])
        contract_type = st.selectbox("Contract Type", ["Full-Time", "Part-Time"])
        
        if st.button("Add to System"):
            if self.manager.add_employee(name, qualification, contract_type):
                st.success(f"{name} has been added.")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("Failed to add employee.")


    def display_employee_table(self):
        """Displays the employee data in an editable table format."""
        st.header("Personnel Management")
        
        if st.button("Wipe Employee Data", help="Danger: This will delete all employees."):
            if self.manager.empty_employee_database():
                st.success("All employee data has been cleared.")
                time.sleep(1.5)
                st.rerun()
        personnel = self.manager.get_all_employees()
        if personnel.empty:
            st.info("No staff registered yet. Use the sidebar to add employees.")
            return
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "name": st.column_config.TextColumn("Name"),
            "qualification": st.column_config.SelectboxColumn("Role", options=["Paramedic", "Assistant"], required=True),
            "contract_type": st.column_config.SelectboxColumn("Contract Type", options=["Full-Time", "Part-Time"], required=True)
        }
        
        edited_df = st.data_editor(
            personnel,
            column_config=column_config,
            width='stretch',
            height=500,
            hide_index=True,
            disabled=["id"]
        )
        if st.button("Save Personnel Changes"):
            if self.manager.update_employees(edited_df):
                st.success("Changes saved.")
                time.sleep(1.5)
                st.rerun()


    def render_page(self):
        """Renders the employee management page."""
        st.sidebar.title(f"Welcome, {st.session_state['username']}!")
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Refresh Data"):
            st.rerun()
        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            
        col1, col2 = st.columns([3, 7], gap="xlarge")
        with col1:
            with st.container(border=True):
                self.add_employee_section()
        with col2:
            with st.container(border=True):
                self.display_employee_table()


if __name__ == "__main__":
    page = EmployeePage()
    page.render_page()