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
        st.caption("Employee Registration Widget")
        with st.form("register_employee_form", clear_on_submit=True):
            max_date = self.staff_manager.max_allowed_date()
            min_date = datetime.date(1900, 1, 1)

            name = st.text_input("Name", placeholder="e.g. Tom Smith")
            date_of_birth = st.date_input("Date of Birth", value=None, min_value=min_date, max_value=max_date, format="DD.MM.YYYY", help="NOTE: Date of Birth must be in the past, and the employee must be at least 18 years old.")
            qualification = st.selectbox("Qualification", ["RS", "RH"], index=None, placeholder="Select qualification", help="Qualification: RS = Paramedic, RH = Assistant.")
            contract_type = st.selectbox("Contract Type", ["100%", "75%", "50%", "Flexible"], index=None, placeholder="Select contract type", help="Contract Type: 100% = Full-time, 75% = Part-time, 50% = Part-time, Flexible = Flexible hours (Max 32 per month).")

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
        st.caption("Register an employee vacation.")
        with st.form("register_vacation_form", clear_on_submit=True):
            employee_id = st.number_input("Employee ID", value=None, step=1, key="vac_emp_id", placeholder="e.g. 6012")
            vacation_start = st.date_input(
                "Vacation Start Date",
                value=None,
                min_value=datetime.date.today(),
                format="DD.MM.YYYY",
                key="vac_start",
                help="Vacation start must be in the future."
            )
            vacation_end = st.date_input(
                "Vacation End Date",
                value=None,
                min_value=vacation_start,
                format="DD.MM.YYYY",
                key="vac_end",
                help="Vacation end must be equal to or after the start date."
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
        st.caption("Enter the vacation ID you wish to delete.")
        with st.form("delete_vacation_form", clear_on_submit=True):
            vacation_id = st.number_input("Vacation ID", value=None, min_value=1, step=1, key="delete_vacation", placeholder="e.g. 4")
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
        
        disabled_cols = ["id"]
        if st.session_state.get("role") == "basic":
            disabled_cols.append("is_active")

        edited_df = st.data_editor(
            personnel,
            column_config=column_config,
            width='stretch',
            height=700,
            hide_index=True,
            disabled=disabled_cols
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
                width='stretch',
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
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            with st.container(border=True, width='stretch'):
                self.display_employee_table()
        with col2:
            with st.container(border=True, width='stretch'):
                self.display_vacation_section()


if __name__ == "__main__":
    page = EmployeePage()
    page.render_page()