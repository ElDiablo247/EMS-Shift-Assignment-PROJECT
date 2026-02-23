import streamlit as st
from logic.manager import Manager

class Homepage:
    def __init__(self):
        self.manager = Manager()
        st.set_page_config(page_title="Shifts Planner for EMS", layout="wide")

    def add_employee_section(self):
        """Handles all inputs and logic in the sidebar"""
        st.sidebar.header("Employee Registration")
        
        name = st.sidebar.text_input("Employee Name")
        qualification = st.sidebar.selectbox("Role", ["Paramedic", "Assistant"])
        contract_type = st.sidebar.selectbox("Contract Type", ["Full-Time", "Part-Time", "Flexible"])
        
        if st.sidebar.button("Add to System"):
            success, message = self.manager.add_employee(name, qualification, contract_type)
            if success:
                st.sidebar.success(message)
            else:
                st.sidebar.error(message)

    def add_shift_section(self):
        """Handles the input and display logic for Shifts"""
        st.header("Shift Management")

        shift_name = st.text_input("Shift Name")
        shift_start = st.time_input("Start Time", value=None)
        shift_end = st.time_input("End Time", value=None)
        shift_duration = st.number_input("Shift Duration (hours)", max_value=12.0, step=1.0)

        if st.button("Add Shift"):
            success, message = self.manager.add_shift(shift_name, shift_start, shift_end, shift_duration)
            if success:
                st.success(message)
                st.rerun() 
            else:
                st.error(message)
        shifts_data = self.manager.get_all_shifts()
        if shifts_data.empty:
            st.info("No shifts created yet.")
        else:
            st.dataframe(shifts_data, use_container_width=True)

    def render_main_area(self):
        """Handles the title, general info, and emptyy database button"""
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
        st.header("Available Personnel")

        personnel = self.manager.get_all_employees()
        if personnel.empty:
            st.info("No staff registered yet. Use the sidebar to add employees.")
        else:
            st.dataframe(personnel, use_container_width=True)

    def run(self):
        """The main entry point that calls all other methods in order"""
        self.add_employee_section()

        # Create a layout with a left and right column area
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            self.render_main_area()
            self.display_personnel()
        with col_right:
            self.add_shift_section()

if __name__ == "__main__":
    homepage = Homepage()
    homepage.run() 