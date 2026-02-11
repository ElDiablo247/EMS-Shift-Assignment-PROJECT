import streamlit as st
from manager import Manager

class GUI:
    def __init__(self):
        self.manager = Manager()
        
        # Initial page setup
        st.set_page_config(page_title="Shifts Planner for EMS", page_icon="🚑")

    def render_sidebar(self):
        """Handles all inputs and logic in the sidebar"""
        st.sidebar.header("Employee Registration")
        
        name = st.sidebar.text_input("Employee Name")
        hours_required = st.sidebar.number_input("Work Hours Required", max_value=168.0, step=1.00)
        qualification = st.sidebar.selectbox("Role", ["Paramedic", "Assistant"])
        contract_type = st.sidebar.selectbox("Contract Type", ["Full-Time", "Part-Time", "Flexible"])

        if st.sidebar.button("Add to System"):
            success, message = self.manager.add_employee(name, hours_required, qualification, contract_type)
            if success:
                st.sidebar.success(message)
            else:
                st.sidebar.error(message)

    def render_shift_section(self):
        """Handles the input and display logic for Shifts"""
        st.header("⏰ Shift Management")
        
        # Expander for the input form to keep the UI tidy
        with st.expander("Create New Shift"):
            shift_id = st.number_input("Shift ID", min_value=1, step=1)
            shift_name = st.text_input("Shift Name")
            col1, col2 = st.columns(2)
            with col1:
                shift_start = st.text_input("Start Time")
            with col2:
                shift_end = st.text_input("End Time")

            if st.button("Add Shift to System"):
                success, message = self.manager.add_shift(shift_id, shift_name, shift_start, shift_end)
                if success:
                    st.success(message)
                    st.rerun() # Refresh to update the shift table
                else:
                    st.error(message)
        # Fetch and display all shifts
        shifts_data = self.manager.get_all_shifts()
        if shifts_data.empty:
            st.info("No shifts created yet.")
        else:
            st.dataframe(shifts_data, use_container_width=True)

    def render_main_area(self):
        """Handles the title, general info, and clear database button"""

        st.title("Shifts Planner for EMS")
        st.write("Use this tool to manage your staff and generate weekly plans.")

        if st.button("Empty Database"):
            success, message = self.manager.empty_database()
            if success:
                st.success(message)
            else:
                st.error(message)

    def display_personnel(self):
        """Handles fetching and displaying the employee table"""
        st.header("Active Personnel")
        
        personnel = self.manager.get_all_employees()

        if personnel.empty:
            st.info("No staff registered yet. Use the sidebar to add someone.")
        else:
            # We use the dataframe here for a nicer look and to save space
            st.dataframe(personnel, use_container_width=True)

    def run(self):
        """The main entry point that calls all other methods in order"""
        self.render_sidebar()
        self.render_main_area()
        self.display_personnel()
        self.render_shift_section()

if __name__ == "__main__":
    gui = GUI()
    gui.run() # Inititate the GUI application