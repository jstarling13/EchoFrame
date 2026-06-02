from typing import Optional
from pydantic import BaseModel

class ShiftResultOutput(BaseModel):
    label: str
    revenue: float
    labor_cost: float
    labor_pct: Optional[float]
    contribution: float
    status: str
    recommendation: str

    class Config:
        from_attributes = True
