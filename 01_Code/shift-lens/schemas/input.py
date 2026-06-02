from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class TransactionInput(BaseModel):
    timestamp: datetime
    amount: float = Field(..., ge=0)
    order_id: str = Field(..., max_length=255)
    location_id: str = Field(..., max_length=100)
    payment_method: Optional[str] = None

class TimePunchInput(BaseModel):
    employee_id: str = Field(..., max_length=100)
    clock_in: datetime
    clock_out: datetime
    location_id: str = Field(..., max_length=100)
    wage: float = Field(..., gt=0)

class IngestTransactionsRequest(BaseModel):
    location_id: str = Field(..., max_length=100)
    transactions: List[TransactionInput]

class IngestPunchesRequest(BaseModel):
    location_id: str = Field(..., max_length=100)
    time_punches: List[TimePunchInput]

class ProcessDayRequest(BaseModel):
    date: str
    location_id: str = Field(..., max_length=100)
    transactions: List[TransactionInput]
    time_punches: List[TimePunchInput]
    target_labor_pct: float = Field(30.0, gt=0, le=100)
