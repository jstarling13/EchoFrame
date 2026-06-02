from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric
from models.base import Base

class POSTransaction(Base):
    __tablename__ = "pos_transactions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    order_id = Column(String(255), nullable=False, index=True)
    location_id = Column(String(100), nullable=False, index=True)
    payment_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<POSTransaction(id={self.id}, timestamp={self.timestamp}, amount={self.amount}, order_id={self.order_id})>"
