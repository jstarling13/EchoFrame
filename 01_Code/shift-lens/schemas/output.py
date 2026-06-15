from typing import Optional
from pydantic import BaseModel, ConfigDict

class ShiftResultOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    revenue: float
    labor_cost: float
    labor_pct: Optional[float]
    contribution: float
    status: str
    recommendation: str
