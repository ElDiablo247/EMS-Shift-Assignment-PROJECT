import streamlit as st
from logic.manager import Manager
from logic.auth_utils import ensure_authenticated
import time


class ShiftPage:
    def __init__(self):
        ensure_authenticated()
        self.manager = Manager()


    def add_shift_section(self):
        """Section for adding new shifts to the system."""
        st.header("Add New Shift")
        name = st.text_input("Shift Name")
        start = st.time_input("Start Time", value=None)
        end = st.time_input("End Time", value=None)
        duration = st.number_input("Duration (hours)", max_value=12.0, step=0.5)
        
        if st.button("Add Shift"):
            if self.manager.add_shift(name, start, end, duration):
                st.success("Shift added.")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("Failed to add shift.")


    def display_shift_table(self):
        """Displays the shift data in an editable table format."""
        st.header("Shift Requirements")
        
        if st.button("Clear All Shifts"):
            if self.manager.empty_shifts_database():
                st.success("All shifts cleared.")
                time.sleep(1.5)
                st.rerun()
        shifts = self.manager.get_all_shifts()
        if shifts.empty:
            st.info("No shifts defined. Use the sidebar to add them.")
            return
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "shift_name": st.column_config.TextColumn("Shift Name"),
            "shift_start": st.column_config.TimeColumn("Start Time", format="HH:mm"),
            "shift_end": st.column_config.TimeColumn("End Time", format="HH:mm"),
            "shift_duration": st.column_config.NumberColumn("Duration minus breaks(hrs)")
        }
        
        edited_df = st.data_editor(
            shifts,
            column_config=column_config,
            width='stretch',
            hide_index=True,
            disabled=["id"]
        )
        if st.button("Update Shift Definitions"):
            if self.manager.update_shifts(edited_df):
                st.success("Shifts updated.")
                time.sleep(1.5)
                st.rerun()


    def render_page(self):
        """Renders the shift management page."""
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
            self.add_shift_section()
        with col2:
            self.display_shift_table()


if __name__ == "__main__":
    page = ShiftPage()
    page.render_page()