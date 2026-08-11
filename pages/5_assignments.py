import streamlit as st
from logic.auth_utils import ensure_authenticated
from logic.schedule_manager import ScheduleManager
from logic.staff_manager import StaffManager
import datetime
import time


class AssignmentPage:
    def __init__(self):
        ensure_authenticated()
        self.staff_manager = StaffManager()
        self.schedule_manager = ScheduleManager()


    def generate_empty_template_section(self):
        """Section for generating an empty assignment template for a specific month and year."""
        st.info("Select the month and year to generate the initial empty assignment template.")
        now = datetime.datetime.now()
        col_1, col_2 = st.columns(2)
        with col_1:
            month = st.selectbox("Month", range(1, 13), index=now.month - 1)
        with col_2:
            year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1)
        if st.button("Generate"):
            success, message, _ = self.schedule_manager.generate_empty_template(month, year)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)
                time.sleep(1.5)
                st.rerun()


    def auto_assign_section(self):
        """Section for auto-assigning paramedics to shifts for a specific month and year."""
        st.info("Trigger the auto-assignment algorithm for shifts that require paramedics in a specific month.")
        now = datetime.datetime.now()
        col_1, col_2 = st.columns(2)
        with col_1:
            a_month = st.number_input("Month", min_value=1, max_value=12, value=now.month, step=1, key="aa_month")
        with col_2:
            a_year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="aa_year")
        
        if st.button("Assign"):
            success, message = self.schedule_manager.assign_paramedics_to_weekdays_shifts(a_month, a_year)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)
                time.sleep(1.5)
                st.rerun()


    def auto_assign_rh_section(self):
        """Section for auto-assigning assistants (RH) to shifts for a specific month and year."""
        st.info("Trigger the auto-assignment algorithm for shifts that require assistants (RH) in a specific month.")
        now = datetime.datetime.now()
        col_1, col_2 = st.columns(2)
        with col_1:
            rh_month = st.number_input("Month", min_value=1, max_value=12, value=now.month, step=1, key="rh_month")
        with col_2:
            rh_year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="rh_year")

        if st.button("Fill Assistant Slots"):
            success, message = self.schedule_manager.assign_rh_to_weekdays_shifts(rh_month, rh_year)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)
                time.sleep(1.5)
                st.rerun()


    def display_schedule_section(self):
        """Section for displaying the generated shift assignments."""
        st.header("Current Assignments")
        
        now = datetime.datetime.now()
        col1, col2 = st.columns(2)
        with col1:
            view_month = st.selectbox("View Month", range(1, 13), index=now.month - 1, key="view_month")
        with col2:
            view_year = st.number_input("View Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="view_year")
        st.subheader(f"Showing: {view_month}/{view_year}")

        df = self.schedule_manager.get_assignments_pivot(view_month, view_year)

        if df.empty:
            st.warning(f"No assignments found for {view_month}/{view_year}.")
        else:
            # 1. Prepare options for the dropdowns (all employees, including inactive for past schedules)
            employees_df = self.staff_manager.get_all_employees()
            employee_names = employees_df['name'].tolist() if not employees_df.empty else []
            employee_names.insert(0, "-")

            # 2. Build the Column Configuration dynamically
            column_config = {
                "date": st.column_config.TextColumn("Date", disabled=True)
            }
            
            for col in df.columns:
                if col != "date":
                    column_config[col] = st.column_config.SelectboxColumn(col, options=employee_names, required=True)
            
            # 3. Render the interactive table
            with st.form("assignments_editor_form"):
                edited_df = st.data_editor(
                    df, 
                    column_config=column_config, 
                    use_container_width=True, 
                    hide_index=True, 
                    height='content',
                    key="monthly_assignments_editor"
                )
                
                if st.form_submit_button("Save Schedule"):
                    success, message = self.schedule_manager.save_edited_assignments(edited_df)
                    if success:
                        st.success(message)
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Failed to save schedule changes.")


    def employee_hours_section(self):
        """Display target and completed hours for all active employees for the selected month and year."""
        st.header("Employee Worktime Overview")
        
        now = datetime.datetime.now()
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            view_month = st.selectbox("Month", range(1, 13), index=now.month - 1, key="eh_month")
        with col2:
            view_year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="eh_year")
        with col3:
            if st.button("Display", use_container_width=True, key="eh_display"):
                st.subheader(f"Showing: {view_month}/{view_year}")
                st.session_state["hours_target"] = (view_month, view_year)

        target = st.session_state.get("hours_target")
        if not target:
            st.info("Select a month and year, then click Display.")
            return
        
        target_month, target_year = target
        df = self.schedule_manager.get_employee_hours_pivot(target_month, target_year)
        
        if df.empty:
            st.warning("No employee data found.")
        else:
            st.data_editor(
                df,
                column_config={
                    "Employee": st.column_config.TextColumn("Employee", disabled=True),
                    "Role": st.column_config.TextColumn("Role", disabled=True),
                    "Target Hours": st.column_config.NumberColumn("Target Hours", disabled=True),
                    "Completed Hours": st.column_config.NumberColumn("Completed Hours", disabled=True),
                },
                use_container_width=True,
                hide_index=True,
                key="employee_hours_editor"
            )


    def violations_section(self):
        """Section for scanning the schedule for constraint violations."""
        st.header("Violations")
        st.info("Scan for constraint violations (11-hour rest, double shifts, vacations, missing paramedics).")

        now = datetime.datetime.now()
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            v_month = st.selectbox("Month", range(1, 13), index=now.month - 1, key="v_month")
        with col2:
            v_year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="v_year")
        with col3:
            if st.button("Find Constraint Violations", use_container_width=True, key="v_button"):
                with st.spinner("Scanning schedule..."):
                    violations = self.schedule_manager.find_schedule_violations(v_month, v_year)
                if violations:
                    st.session_state["violations_result"] = violations
                else:
                    st.session_state["violations_result"] = []

        result = st.session_state.get("violations_result", None)
        if result is None:
            return
        if result:
            st.error(f"Found {len(result)} violation(s):")
            st.dataframe(
                result,
                column_config={
                    "Date": st.column_config.TextColumn("Date"),
                    "Shift": st.column_config.TextColumn("Shift"),
                    "Employee": st.column_config.TextColumn("Employee"),
                    "Type": st.column_config.TextColumn("Type"),
                    "Description": st.column_config.TextColumn("Description"),
                },
                use_container_width=True,
                width='content',
                hide_index=True,
            )
        else:
            st.success("No violations found — schedule is clean!")


    def generate_schedule_section(self):
        """One-click: generates the full schedule (template + RS + RH) in one shot."""
        st.info("Generate the complete schedule — all stages in memory, single DB commit.")
        now = datetime.datetime.now()
        col_1, col_2 = st.columns(2)
        with col_1:
            month = st.selectbox("Month", range(1, 13), index=now.month - 1, key="gs_month")
        with col_2:
            year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="gs_year")
        if st.button("Generate Full Schedule", use_container_width=True):
            with st.spinner("Generating schedule in memory..."):
                success, message = self.schedule_manager.generate_schedule(month, year)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)
                time.sleep(2)
                st.rerun()


    def render_page(self):
        """Renders the assignments management page."""
        with st.sidebar:
            with st.expander("Generate Full Schedule", expanded=True):
                self.generate_schedule_section()
        
        with st.container(border=True):
            self.display_schedule_section()

        left, right = st.columns([7, 5])
        with left:
            with st.container(border=True):
                self.violations_section()
        with right:
            with st.container(border=True):
                self.employee_hours_section()


if __name__ == "__main__":
    page = AssignmentPage()
    page.render_page()