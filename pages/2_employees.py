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
        with st.form("delete_employee_form", clear_on_submit=True):
            id_to_delete = st.number_input("Employee ID", min_value=6001, step=1, key="delete_employee")
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


    def add_vacation_section(self):
        """Section for adding employee vacation."""
        employee_id = st.number_input("Employee ID", min_value=6001, step=1, key="vac_emp_id")
        date_range = st.date_input(
            "Vacation Dates",
            value=(datetime.date.today(), datetime.date.today() + datetime.timedelta(days=1)),
            min_value=datetime.date.today(),
            format="DD/MM/YYYY",
            key="vac_dates"
        )
        if st.button("Add Vacation"):
            if not isinstance(date_range, tuple) or len(date_range) != 2:
                st.error("Please select a start and end date.")
            else:
                start_date, end_date = date_range[0], date_range[1]
                success, message = self.staff_manager.add_vacation(employee_id, start_date, end_date)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def delete_vacation_section(self):
        """Section for deleting vacation entries."""
        with st.form("delete_vacation_form", clear_on_submit=True):
            vacation_id = st.number_input("Vacation ID", min_value=1, step=1, key="delete_vacation")
            if st.form_submit_button("Delete Vacation"):
                success, message = self.staff_manager.delete_vacation(vacation_id)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def add_sick_leave_section(self):
        """Section for adding sick leave entries."""
        employee_id = st.number_input("Employee ID", min_value=6001, step=1, key="sick_emp_id")
        date_range = st.date_input(
            "Sick Leave Dates",
            value=(datetime.date.today(), datetime.date.today() + datetime.timedelta(days=1)),
            min_value=datetime.date.today(),
            format="DD/MM/YYYY",
            key="sick_dates"
        )
        if st.button("Add Sick Leave"):
            if not isinstance(date_range, tuple) or len(date_range) != 2:
                st.error("Please select a start and end date.")
            else:
                start_date, end_date = date_range[0], date_range[1]
                success, message = self.staff_manager.add_sick_leave(employee_id, start_date, end_date)
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


    def display_vacation_sick_leave_section(self):
        """Display vacation and sick leave tables in tabs."""
        st.header("Vacations and Sick leaves Overview")
        tab1, tab2 = st.tabs(["Vacations", "Sick Leaves"])
        
        with tab1:
            df = self.staff_manager.get_all_vacations_pivot()
            if df.empty:
                st.info("No vacations registered.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
        
        with tab2:
            df = self.staff_manager.get_all_sick_leaves_pivot()
            if df.empty:
                st.info("No sick leaves registered.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)


    def render_page(self):
        """Renders the employee management page."""
        # Sidebar: Action widgets with expanders
        with st.sidebar:
            with st.expander("Add Employee", expanded=False, ):
                self.add_employee_section()
            with st.expander("Delete Employee", expanded=False):
                self.delete_employee_section()
            with st.expander("Register Vacation", expanded=False):
                self.add_vacation_section()
            with st.expander("Delete Vacation", expanded=False):
                self.delete_vacation_section()
            with st.expander("Register Sick Leave", expanded=False):
                self.add_sick_leave_section()

        # Main Area. On the left, the Employees table, and on the right using tabs, the Vacation and Sick leave table.
        col1, col2 = st.columns([6, 4], gap="medium")
        with col1:
            with st.container(border=True):
                self.display_employee_table()
        with col2:
            with st.container(border=True):
                self.display_vacation_sick_leave_section()


if __name__ == "__main__":
    page = EmployeePage()
    page.render_page()