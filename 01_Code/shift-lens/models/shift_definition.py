from datetime import time
from sqlalchemy import Column, Integer, String, Time
from sqlalchemy.orm import relationship
from models.base import Base

class ShiftDefinition(Base):
    __tablename__ = "shift_definitions"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(String(100), nullable=False, index=True)
    shift_name = Column(String(255), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    shift_mappings = relationship("ShiftMapping", back_populates="shift_definition")
    shift_pl_results = relationship("ShiftPLResult", back_populates="shift_definition")

    def __repr__(self):
        return f"<ShiftDefinition(id={self.id}, shift_name={self.shift_name}, day_of_week={self.day_of_week}, {self.start_time}-{self.end_time})>"
