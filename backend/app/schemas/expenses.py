from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from decimal import Decimal

# Expense Participant (Split Details)
class ExpenseParticipantBase(BaseModel):
    user_id: int
    share: Decimal = Field(..., max_digits=10, decimal_places=2) # Ensures financial precision

class ExpenseParticipantRead(ExpenseParticipantBase):
    id: int
    expense_id: int
    is_settled: bool

    model_config = ConfigDict(from_attributes=True)

# Main Expense
class ExpenseBase(BaseModel):
    # Validates amount > 0 and ensures 2 decimal places precision
    amount: Decimal = Field(..., max_digits=10, decimal_places=2, gt=0)
    category: str
    description: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    paid_by: int
    # Requires a list of participants when creating a new expense
    participants: List[ExpenseParticipantBase]

class ExpenseRead(ExpenseBase):
    id: int
    group_id: int
    paid_by: int
    participants: List[ExpenseParticipantRead] = []

    model_config = ConfigDict(from_attributes=True)