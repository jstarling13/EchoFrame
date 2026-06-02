from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class TimePunch(Base):
    __tablename__ = "time_punches"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(100), ForeignKey("employees.id"), nullable=False, index=True)
    clock_in = Column(DateTime, nullable=False, index=True)
    clock_out = Column(DateTime, nullable=True, index=True)
    location_id = Column(String(100), nullable=False, index=True)
    wage_override = Column(Numeric(8, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="time_punches")

    def __repr__(self):
        return f"<TimePunch(id={self.id}, employee_id={self.employee_id}, clock_in={self.clock_in}, clock_out={self.clock_out})>"
