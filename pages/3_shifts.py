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
        st.header("Shift Registration")
        name = st.text_input("Shift Name")
        start = st.time_input("Start Time", value=None)
        end = st.time_input("End Time", value=None)
        duration = st.number_input("Duration (hours)", value=8.0, max_value=12.0, step=0.5)
        runs_on_weekend_or_holiday = st.checkbox("Runs on Weekends/Holidays")
        
        if st.button("Add Shift"):
            success, message = self.shift_manager.add_shift(name, start, end, duration, runs_on_weekend_or_holiday)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def delete_shift_section(self):
        """Section for deleting shifts from the system."""
        st.header("Delete Shift")
        with st.form("delete_shift_form", clear_on_submit=True):
            id_to_delete = st.number_input("Shift ID", value=None, placeholder="Shift ID to delete")
            submitted = st.form_submit_button("Delete Shift")
            if submitted:
                if st.session_state.get('role') == 'basic':
                    st.error('Only "super" admins are allowed to delete.')
                    return
                
                success, message = self.shift_manager.delete_shift(id_to_delete)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def display_shift_table(self):
        """Displays the shift data in an editable table format."""
        st.header("Shift Management")
        
        if st.button("Clear All Shifts"):
            success, message = self.shift_manager.empty_shifts_database()
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)
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
        
        edited_df = st.data_editor(
            shifts,
            column_config=column_config,
            width='stretch',
            hide_index=True,
            disabled=["id"]
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
            with st.expander("Delete Shift", expanded=False):
                self.delete_shift_section()
        
        # Main area: Display only 
        with st.container(border=True):
            self.display_shift_table()


if __name__ == "__main__":
    page = ShiftPage()
    page.render_page()