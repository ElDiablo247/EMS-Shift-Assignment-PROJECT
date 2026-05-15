import streamlit as st
from logic.auth_utils import ensure_authenticated
from logic.algorithm import PlanGenerator
from logic.manager import Manager
import datetime
import time


class AssignmentPage:
    def __init__(self):
        ensure_authenticated()
        self.manager = Manager()
        self.generator = PlanGenerator()


    def generate_plan_section(self):
        """Section for generating the holidays for a given year and the shift plan. Tabs are used to separate the two processes."""
        st.header("Shift Schedule Generation")

        tab1, tab2 = st.tabs(["1. Generate Holidays", "2. Generate Empty Template"])

        with tab1:
            st.subheader("Yearly Holiday Generation")
            st.info("Generate the public holidays for a specific year. This must be done before generating a template.")
            year_for_holidays = st.number_input("Year", min_value=datetime.datetime.now().year - 1, max_value=2130, value=datetime.datetime.now().year, step=1, key="holiday_year")
            if st.button("Generate Holidays"):
                success, message = self.generator.generate_holidays(year_for_holidays)
                if success:
                    st.success(message)
                else:
                    st.error(message)
                time.sleep(1.5)
                st.rerun()

        with tab2:
            st.subheader("Monthly Template Generation")
            st.info("Select the month and year to generate the initial assignment template.")
            now = datetime.datetime.now()
            col1, col2 = st.columns(2)
            with col1:
                month = st.selectbox("Month", range(1, 13), index=now.month - 1)
            with col2:
                year = st.number_input("Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1)

            if st.button("Generate Empty Template"):
                self.generator.generate_logic(month, year)
                st.success(f"Successfully generated empty template for {month}/{year}!")
                time.sleep(1.5)
                st.rerun()


    def display_holidays_section(self):
        """Displays the contents of the holidays table."""
        st.header("Holidays Overview")
        
        now = datetime.datetime.now()
        view_year = st.number_input("View Holidays for Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="holiday_view_year")
        
        holidays_df = self.generator.get_all_holidays_df(year=view_year)
        if holidays_df.empty:
            st.warning(f"No holidays found for {view_year}. Use the 'Generate Holidays' tool.")
        else:
            st.dataframe(holidays_df, use_container_width=True, hide_index=True)


    def display_assignments_section(self):
        """Section for displaying the generated shift assignments."""
        st.header("Current Assignments")
        st.info("View the generated shift plan.")
        
        now = datetime.datetime.now()
        col1, col2 = st.columns(2)
        with col1:
            view_month = st.selectbox("View Month", range(1, 13), index=now.month - 1, key="view_month")
        with col2:
            view_year = st.number_input("View Year", min_value=now.year - 1, max_value=2130, value=now.year, step=1, key="view_year")

        df = self.manager.get_assignments_pivot(view_month, view_year)

        if df.empty:
            st.warning(f"No assignments found for {view_month}/{view_year}.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)


    def render_page(self):
        """Renders the assignments management page."""
        st.sidebar.title(f"Welcome, {st.session_state.get('username', 'User')}!")
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Refresh Data"):
            st.rerun()
        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        top_col1, top_col2 = st.columns([5, 5], gap="large")
        with top_col1:
            with st.container(border=True):
                self.generate_plan_section()
        with top_col2:
            with st.container(border=True):
                self.display_holidays_section()

        st.markdown("---")

        with st.container(border=True):
            self.display_assignments_section()


if __name__ == "__main__":
    page = AssignmentPage()
    page.render_page()