from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, condecimal


class TransactionCreate(BaseModel):
    type: str = Field(..., description="income | expense")
    currency: str = Field(..., min_length=1, max_length=8)
    amount: condecimal(gt=0, max_digits=18, decimal_places=2)
    comment: Optional[str] = None
    client_id: Optional[int] = None
    rate: Optional[condecimal(gt=0, max_digits=18, decimal_places=6)] = None
    timestamp: Optional[datetime] = None  # если не передали — поставим now()


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    type: str
    currency: str
    amount: Decimal
    rate: Optional[Decimal] = None
    client_id: Optional[int] = None
    comment: Optional[str] = None
    created_by: int
    created_at: datetime
