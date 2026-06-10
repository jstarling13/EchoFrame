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


class SyncDayRequest(BaseModel):
    """Pull a day's data from external connectors and run the full pipeline."""
    date: str
    location_id: str = Field(..., max_length=100)
    pos_source: str = Field("mock", max_length=50)
    timesheet_source: str = Field("mock", max_length=50)
    target_labor_pct: float = Field(30.0, gt=0, le=100)


class PosWebhookRequest(BaseModel):
    """A single POS transaction pushed in real time."""
    transaction: TransactionInput
    target_labor_pct: float = Field(30.0, gt=0, le=100)


class PunchWebhookRequest(BaseModel):
    """A single completed time punch pushed in real time."""
    time_punch: TimePunchInput
    target_labor_pct: float = Field(30.0, gt=0, le=100)
