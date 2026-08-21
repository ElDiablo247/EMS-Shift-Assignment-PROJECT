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
        st.caption("Employee Registration Widget. NOTE: Date of Birth must be in the past, and the employee must be at least 18 years old.")
        with st.form("register_employee_form", clear_on_submit=True):
            max_date = self.staff_manager.max_allowed_date()
            min_date = datetime.date(1900, 1, 1)

            name = st.text_input("Name", placeholder="e.g. Tom Smith")
            date_of_birth = st.date_input("Date of Birth", value=None, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
            qualification = st.selectbox("Qualification", ["RS", "RH"], index=None, placeholder="Select qualification")
            contract_type = st.selectbox("Contract Type", ["100%", "75%", "50%", "Flexible"], index=None, placeholder="Select contract type")

            submitted = st.form_submit_button("Add to System")
            if submitted:
                success, message = self.staff_manager.add_employee(name, date_of_birth, qualification, contract_type)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def add_vacation_section(self):
        """Section for adding employee vacation."""
        with st.form("register_vacation_form", clear_on_submit=True):
            employee_id = st.number_input("Employee ID", value=None, min_value=6001, step=1, key="vac_emp_id", placeholder="Emp ID e.g. 6001")
            vacation_start = st.date_input(
                "Vacation Start Date",
                value=None,
                min_value=datetime.date.today(),
                format="DD.MM.YYYY",
                key="vac_start",
            )
            vacation_end = st.date_input(
                "Vacation End Date",
                value=None,
                min_value=vacation_start,
                format="DD.MM.YYYY",
                key="vac_end",
            )

            submitted = st.form_submit_button("Add Vacation")
            if submitted:
                success, message = self.staff_manager.add_vacation(employee_id, vacation_start, vacation_end)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def delete_vacation_section(self):
        """Section for deleting vacation entries."""
        with st.form("delete_vacation_form", clear_on_submit=True):
            vacation_id = st.number_input("Vacation ID", value=None, min_value=1, step=1, key="delete_vacation", placeholder="Vacation ID e.g. 4")
            if st.form_submit_button("Delete Vacation"):
                success, message = self.staff_manager.delete_vacation(vacation_id)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def display_employee_table(self):
        """Displays the employee data in an editable table format."""
        st.header("Staff Management")
        
        personnel = self.staff_manager.get_all_employees()
        if personnel.empty:
            st.info("No staff registered yet. Use the sidebar to add employees.")
            return
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "name": st.column_config.TextColumn("Name"),
            "date_of_birth": st.column_config.DateColumn("Date of Birth", format="DD.MM.YYYY", required=True),
            "qualification": st.column_config.SelectboxColumn("Qualification", options=["RS", "RH"], required=True),
            "contract_type": st.column_config.SelectboxColumn("Contract Type", options=["100%", "75%", "50%", "Flexible"], required=True),
            "is_active": st.column_config.CheckboxColumn("Active", required=True)
        }
        
        edited_df = st.data_editor(
            personnel,
            column_config=column_config,
            width='stretch',
            height=700,
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


    def display_vacation_section(self):
        """Display vacation table."""
        st.header("Vacations Overview")
        df = self.staff_manager.get_all_vacations_pivot()
        if df.empty:
            st.info("No vacations registered.")
        else:
            st.dataframe(
                df,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "employee_name": st.column_config.TextColumn("Employee Name"),
                    "vacation_date": st.column_config.DateColumn("Vacation Date", format="DD.MM.YYYY"),
                },
                use_container_width=True,
                hide_index=True,
                height=750
            )


    def render_page(self):
        """Renders the employee management page."""
        # Sidebar: Action widgets with expanders
        with st.sidebar:
            with st.expander("Add Employee", expanded=False, ):
                self.add_employee_section()
            with st.expander("Register Vacation", expanded=False):
                self.add_vacation_section()
            with st.expander("Delete Vacation", expanded=False):
                self.delete_vacation_section()

        # Main Area. On the left, the Employees table, and on the right, the Vacation table.
        col1, col2 = st.columns([6, 4], gap="medium")
        with col1:
            with st.container(border=True):
                self.display_employee_table()
        with col2:
            with st.container(border=True):
                self.display_vacation_section()


if __name__ == "__main__":
    page = EmployeePage()
    page.render_page()