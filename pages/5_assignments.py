import streamlit as st
from logic.auth_utils import ensure_authenticated
from logic.schedule_manager import ScheduleManager
from logic.staff_manager import StaffManager
from logic.shift_manager import ShiftManager
import datetime
import time


class AssignmentPage:
    def __init__(self):
        ensure_authenticated()
        self.staff_manager = StaffManager()
        self.schedule_manager = ScheduleManager()
        self.shift_manager = ShiftManager()


    def display_schedule_section(self):
        """Section for displaying the generated shift assignments."""
        st.header("Schedule Overview")
        
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


    def errors_section(self):
        """Section for scanning the schedule for constraint errors."""
        st.header("Errors Overview")
        st.info("Scan for constraint errors (11-hour rest, double shifts, vacations, missing paramedics and night shift fairness).")

        now = datetime.datetime.now()
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            v_month = st.selectbox("Month", range(1, 13), index=now.month - 1, key="v_month")
        with col2:
            v_year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="v_year")
        with col3:
            if st.button("Find Constraint Errors", use_container_width=True, key="v_button"):
                with st.spinner("Scanning schedule..."):
                    errors = self.schedule_manager.find_schedule_errors(v_month, v_year)
                if errors:
                    st.session_state["errors_result"] = errors
                else:
                    st.session_state["errors_result"] = []

        result = st.session_state.get("errors_result", None)
        if result is None:
            return
        if result:
            st.error(f"Found {len(result)} error(s):")
            st.dataframe(
                result,
                column_config={
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Shift": st.column_config.TextColumn("Shift", width="medium"),
                    "Employee": st.column_config.TextColumn("Employee", width="medium"),
                    "Type": st.column_config.TextColumn("Type", width="medium"),
                    "Description": st.column_config.TextColumn("Description", width="large"),
                },
                width='content',
                hide_index=True,
            )
        else:
            st.success("No errors found — schedule is clean!")


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


    def swap_shifts_section(self):
        """Bulk-swap employees between two shift-role slots across a date range."""
        st.info("Swap employees between two shifts for a specific role across a date range.")
        now = datetime.datetime.now()

        default_range = (
            datetime.date(now.year, now.month, 1),
            datetime.date(now.year, now.month, now.day),
        )
        date_range = st.date_input("Date range", value=default_range, key="swap_range")

        active_shift_names = self.shift_manager.return_shift_names()
        if not active_shift_names:
            st.warning("No active shifts found.")
            return

        col_a, col_b = st.columns(2)
        with col_a:
            shift_a_name = st.selectbox("Shift A", active_shift_names, key="swap_shift_a")
        with col_b:
            shift_b_name = st.selectbox("Shift B", active_shift_names, key="swap_shift_b")

        role = st.selectbox("Role", ["RS", "RH"], key="swap_role")

        if st.button("Execute Swap", use_container_width=True, key="swap_button"):
            success, message = self.schedule_manager.swap_shift_employees(
                date_range, shift_a_name, shift_b_name, role
            )
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
            with st.expander("Swap Shift Employees", expanded=False):
                self.swap_shifts_section()
        
        with st.container(border=True):
            self.display_schedule_section()

        left, right = st.columns([7, 5])
        with left:
            with st.container(border=True):
                self.errors_section()
        with right:
            with st.container(border=True):
                self.employee_hours_section()


if __name__ == "__main__":
    page = AssignmentPage()
    page.render_page()