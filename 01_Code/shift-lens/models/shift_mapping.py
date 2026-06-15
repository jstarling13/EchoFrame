from decimal import Decimal
from sqlalchemy import Column, Integer, Date, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models.base import Base, utcnow

class ShiftMapping(Base):
    __tablename__ = "shift_mappings"

    id = Column(Integer, primary_key=True, index=True)
    shift_definition_id = Column(Integer, ForeignKey("shift_definitions.id"), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("pos_transactions.id"), nullable=True, index=True)
    time_punch_id = Column(Integer, ForeignKey("time_punches.id"), nullable=True, index=True)
    revenue_allocation = Column(Numeric(10, 2), default=0)
    labor_allocation = Column(Numeric(10, 2), default=0)
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow)

    shift_definition = relationship("ShiftDefinition", back_populates="shift_mappings")

    def __repr__(self):
        return f"<ShiftMapping(id={self.id}, shift_definition_id={self.shift_definition_id}, date={self.date})>"
