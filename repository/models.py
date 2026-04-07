from sqlalchemy import Column, Integer, String, Float, Time
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    qualification = Column(String, nullable=False) 
    contract_type = Column(String, nullable=False)

class Shifts(Base):
    __tablename__ = 'shifts'
    
    id = Column(Integer, primary_key=True, nullable=False)
    shift_name = Column(String, nullable=False)
    shift_start = Column(Time, nullable=False) 
    shift_end = Column(Time, nullable=False) 
    shift_duration = Column(Float, nullable=False)

class Admin(Base):
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'super' or 'basic'