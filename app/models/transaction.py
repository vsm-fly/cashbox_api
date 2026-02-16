import enum
from datetime import datetime  # <-- добавь

from sqlalchemy import Numeric, String, Enum, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class TxType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[TxType] = mapped_column(Enum(TxType, name="tx_type"), index=True)
    currency: Mapped[str] = mapped_column(String(8), index=True)

    amount: Mapped[object] = mapped_column(Numeric(18, 2))
    rate: Mapped[object | None] = mapped_column(Numeric(18, 6), nullable=True)

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

