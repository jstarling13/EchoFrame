from decimal import Decimal
from sqlalchemy import Column, Integer, Date, Numeric, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.base import Base, utcnow

class ShiftPLResult(Base):
    __tablename__ = "shift_pl_results"

    id = Column(Integer, primary_key=True, index=True)
    shift_definition_id = Column(Integer, ForeignKey("shift_definitions.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_revenue = Column(Numeric(10, 2), default=0)
    total_labor_cost = Column(Numeric(10, 2), default=0)
    labor_pct = Column(Numeric(5, 2), nullable=True)
    contribution = Column(Numeric(10, 2), default=0)
    status = Column(String(50), default="healthy")
    created_at = Column(DateTime, default=utcnow)

    shift_definition = relationship("ShiftDefinition", back_populates="shift_pl_results")

    def __repr__(self):
        return f"<ShiftPLResult(id={self.id}, shift_definition_id={self.shift_definition_id}, date={self.date}, status={self.status})>"
