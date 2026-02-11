from sqlalchemy import Column, Integer, String, Float
from database import Base

# Definition of the tables. We have an employees table and a shifts table. Each class corresponds to a table in the database, and the attributes correspond to columns.
class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    hours_required = Column(Float) 
    hours_completed = Column(Float, default=0.0)
    qualification = Column(String) 
    contract_type = Column(String)

class Shifts(Base):
    __tablename__ = 'shifts'
    
    id = Column(Integer, primary_key=True)
    shift_name = Column(String)
    shift_start = Column(String) 
    shift_end = Column(String) 