from sqlalchemy import Column, Integer, String, Float, Time
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    qualification = Column(String) 
    contract_type = Column(String)

class Shifts(Base):
    __tablename__ = 'shifts'
    
    id = Column(Integer, primary_key=True)
    shift_name = Column(String)
    shift_start = Column(Time) 
    shift_end = Column(Time) 
    shift_duration = Column(Float)