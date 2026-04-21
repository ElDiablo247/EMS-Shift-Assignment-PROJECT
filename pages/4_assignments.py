import streamlit as st
from repository.dao import DatabaseAccess
from logic.auth_utils import ensure_authenticated


class AssignmentPage:
    def __init__(self):
        ensure_authenticated()
        self.dao = DatabaseAccess()


    def generate_plan_section(self):
        """Placeholder section for configuring and generating the shift plan."""
        st.header("Generate Schedule")
        st.info("Algorithm constraint configurations will go here.")
        
        if st.button("Generate Plan"):
            st.warning("Algorithm engine not yet connected.")
            # TODO: Add logic to call the PlanGenerator when ready
            pass


    def display_assignments_section(self):
        """Placeholder section for displaying the generated shift assignments."""
        st.header("Current Assignments")
        st.info("The generated shift plan and related tables will be displayed here.")
        # TODO: Add logic to fetch assignments from DAO and display them
        pass


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
            
        col1, col2 = st.columns([3, 7], gap="xlarge")
        with col1:
            with st.container(border=True):
                self.generate_plan_section()
        with col2:
            with st.container(border=True):
                self.display_assignments_section()

if __name__ == "__main__":
    page = AssignmentPage()
    page.render_page()