from sqlalchemy import Column, Integer, String, Float, Time, Date, ForeignKey, Boolean, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    qualification = Column(String, nullable=False) 
    contract_type = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    assignments = relationship('Assignment', back_populates='employee') # Hidden attribute that all employee objects have


class Shift(Base):
    __tablename__ = 'shifts'
    
    id = Column(Integer, primary_key=True, nullable=False)
    shift_name = Column(String, nullable=False)
    shift_start = Column(Time, nullable=False) 
    shift_end = Column(Time, nullable=False) 
    shift_duration = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    assignments = relationship('Assignment', back_populates='shift') # Hidden attribute that all shift objects have


class Admin(Base):
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'super' or 'basic'


class Assignment(Base):
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    shift_id = Column(Integer, ForeignKey('shifts.id'), nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=True)

    # Hidden attributes that all assignment objects have
    employee = relationship('Employee', back_populates='assignments') 
    shift = relationship('Shift', back_populates='assignments')


class Constraint(Base):
    __tablename__ = 'constraints'
    
    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False)
    constraint_key = Column(String, nullable=False)    
    constraint_value = Column(JSON, nullable=True)
    description = Column(String, nullable=False)