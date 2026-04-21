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
        name = st.text_input("Name")
        qualification = st.selectbox("Role", ["Paramedic", "Assistant"])
        contract_type = st.selectbox("Contract Type", ["Full-Time", "Part-Time", "Flexible"])
        
        if st.button("Add to System"):
            success, message = self.manager.add_employee(name, qualification, contract_type)
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
            id_to_delete = st.number_input("Employee ID", value=None, placeholder="Enter the ID of the employee to delete.")
            submitted = st.form_submit_button("Delete Employee")
            if submitted:
                if st.session_state.get('role') == 'basic':
                    st.error('Only "super" admins are allowed to delete.')
                    return
                
                success, message = self.manager.delete_employee(id_to_delete)
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
            success, message = self.manager.empty_employee_database()
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)
        personnel = self.manager.get_all_employees()
        if personnel.empty:
            st.info("No staff registered yet. Use the sidebar to add employees.")
            return
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "name": st.column_config.TextColumn("Name"),
            "qualification": st.column_config.SelectboxColumn("Role", options=["Paramedic", "Assistant"], required=True),
            "contract_type": st.column_config.SelectboxColumn("Contract Type", options=["Full-Time", "Part-Time", "Flexible"], required=True),
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
            success, message = self.manager.update_employees(edited_df)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


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
            with st.container(border=True):
                self.delete_employee_section()
        with col2:
            with st.container(border=True):
                self.display_employee_table()


if __name__ == "__main__":
    page = EmployeePage()
    page.render_page()