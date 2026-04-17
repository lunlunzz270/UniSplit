from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal

class SettlementBase(BaseModel):
    expense_id: int
    payer_id: int
    payee_id: int
    amount: Decimal = Field(..., max_digits=10, decimal_places=2, gt=0)
    note: Optional[str] = None

class SettlementCreate(SettlementBase):
    pass

class SettlementRead(SettlementBase):
    id: int
    group_id: int

    model_config = ConfigDict(from_attributes=True)