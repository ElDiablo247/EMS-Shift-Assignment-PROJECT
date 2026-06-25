import streamlit as st
from logic.staff_manager import StaffManager
from logic.auth_utils import ensure_authenticated
import time
import datetime


class EmployeePage:
    def __init__(self):
        ensure_authenticated()
        self.staff_manager = StaffManager()


    def add_employee_section(self):
        """Section for adding new employees to the system."""
        st.header("Employee Registration")
        max_date = self.staff_manager.max_allowed_date()
        min_date = datetime.date(1900, 1, 1)

        name = st.text_input("Name")
        date_of_birth = st.date_input("Date of Birth", value=max_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
        qualification = st.selectbox("Role", ["RS", "RH"])
        contract_type = st.selectbox("Contract Type", ["100%", "75%", "50%", "Flexible"])
        
        if st.button("Add to System"):
            success, message = self.staff_manager.add_employee(name, date_of_birth, qualification, contract_type)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def delete_employee_section(self):
        """Section for deleting employees from the Database. This will only be used during development and will not be made available to users."""
        st.header("Delete Employee")
        with st.form("delete_employee_form", clear_on_submit=True):
            id_to_delete = st.number_input("Employee ID", value=None, placeholder="Employee ID to delete")
            submitted = st.form_submit_button("Delete Employee")
            if submitted:
                if st.session_state.get('role') == 'basic':
                    st.error('Only "super" admins are allowed to delete.')
                    return
                
                success, message = self.staff_manager.delete_employee(id_to_delete)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def display_employee_table(self):
        """Displays the employee data in an editable table format."""
        st.header("Staff Management")
        
        if st.button("Wipe Employee Data", help="Danger: This will delete all employees."):
            success, message = self.staff_manager.empty_employee_database()
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)
        personnel = self.staff_manager.get_all_employees()
        if personnel.empty:
            st.info("No staff registered yet. Use the sidebar to add employees.")
            return
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "name": st.column_config.TextColumn("Name"),
            "date_of_birth": st.column_config.DateColumn("Date of Birth", format="DD/MM/YYYY", required=True),
            "qualification": st.column_config.SelectboxColumn("Role", options=["RS", "RH"], required=True),
            "contract_type": st.column_config.SelectboxColumn("Contract Type", options=["100%", "75%", "50%", "Flexible"], required=True),
            "is_active": st.column_config.CheckboxColumn("Active", required=True)
        }
        
        edited_df = st.data_editor(
            personnel,
            column_config=column_config,
            width='stretch',
            height=500,
            hide_index=True,
            disabled=["id"]
        )
        if st.button("Save Changes"):
            success, message = self.staff_manager.update_employees(edited_df)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def render_page(self):
        """Renders the employee management page."""
        # Sidebar: Action widgets with expanders
        with st.sidebar:
            with st.expander("Add Employee", expanded=True):
                self.add_employee_section()
            with st.expander("Delete Employee", expanded=False):
                self.delete_employee_section()
        
        # Main area: Display only 
        with st.container(border=True):
            self.display_employee_table()


if __name__ == "__main__":
    page = EmployeePage()
    page.render_page()