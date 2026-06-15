from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Numeric
from sqlalchemy.orm import relationship
from models.base import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    base_wage = Column(Numeric(8, 2), nullable=False)
    location_id = Column(String(100), nullable=False, index=True)

    time_punches = relationship("TimePunch", back_populates="employee")

    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.name}, base_wage={self.base_wage})>"
