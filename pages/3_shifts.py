import streamlit as st
from logic.shift_manager import ShiftManager
from logic.auth_utils import ensure_authenticated
import time


class ShiftPage:
    def __init__(self):
        ensure_authenticated()
        self.shift_manager = ShiftManager()


    def add_shift_section(self):
        """Section for adding new shifts to the system."""
        st.caption("Shift Registration Widget")
        name = st.text_input("Shift Name", placeholder="e.g. Shift 3")
        start = st.time_input("Start Time", value=None, help="NOTE: Shift max. time duration, is 10 hours & 45 minutes. If shift is between 6 and 9 hours, a 30-minute break is deducted. If shift is between 9 and 10 hours & 45 minutes, a 45-minute break is deducted.")
        end = st.time_input("End Time", value=None)
        runs_on_weekend_or_holiday = st.checkbox("Runs on Weekends/Holidays")
        
        if st.button("Add Shift"):
            success, message = self.shift_manager.add_shift(name, start, end, runs_on_weekend_or_holiday)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def display_shift_table(self):
        """Displays the shift data in an editable table format."""
        st.header("Shift Management")
        
        shifts = self.shift_manager.get_all_shifts()
        if shifts.empty:
            st.info("No shifts defined. Use the sidebar to add them.")
            return
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "shift_name": st.column_config.TextColumn("Shift Name"),
            "shift_start": st.column_config.TimeColumn("Start Time", format="HH:mm"),
            "shift_end": st.column_config.TimeColumn("End Time", format="HH:mm"),
            "shift_duration": st.column_config.NumberColumn("Duration minus breaks(hrs)"),
            "runs_on_weekend_or_holiday": st.column_config.CheckboxColumn("Weekend/Holiday", required=True),
            "is_active": st.column_config.CheckboxColumn("Active", required=True)
        }
        
        disabled_cols = ["id", "shift_duration"]  # duration is derived from start/end times
        if st.session_state.get("role") == "basic":
            disabled_cols.append("is_active")

        edited_df = st.data_editor(
            shifts,
            column_config=column_config,
            width='content',
            hide_index=True,
            disabled=disabled_cols
        )
        if st.button("Save Changes"):
            success, message = self.shift_manager.update_shifts(edited_df)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def render_page(self):
        """Renders the shift management page."""
        # Sidebar: Action widgets with expanders
        with st.sidebar:
            with st.expander("Add Shift", expanded=True):
                self.add_shift_section()
        
        # Main area: Display only 
        with st.container(border=True, width='content'):
            self.display_shift_table()


if __name__ == "__main__":
    page = ShiftPage()
    page.render_page()