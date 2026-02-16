from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc

from app.core.deps import get_current_user
from app.db.session import async_session
from app.models.transaction import Transaction, TxType
from app.models.user import User
from app.schemas.transactions import TransactionCreate, TransactionOut


router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=TransactionOut)
async def create_transaction(
    payload: TransactionCreate,
    user: User = Depends(get_current_user),
):
    # Валидируем type -> Enum
    try:
        tx_type = TxType(payload.type)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid type (use income|expense)")

    ts = payload.timestamp or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    async with async_session() as session:
        tx = Transaction(
            timestamp=ts,
            type=tx_type,
            currency=payload.currency,
            amount=payload.amount,
            rate=payload.rate,
            client_id=payload.client_id,
            comment=payload.comment,
            created_by=user.id,
        )
        session.add(tx)
        await session.commit()
        await session.refresh(tx)
        return tx


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    async with async_session() as session:
        q = (
            select(Transaction)
            .order_by(desc(Transaction.id))
            .offset(offset)
            .limit(limit)
        )
        rows = (await session.execute(q)).scalars().all()
        return rows


@router.get("/{tx_id}", response_model=TransactionOut)
async def get_transaction(tx_id: int):
    async with async_session() as session:
        tx = (await session.execute(select(Transaction).where(Transaction.id == tx_id))).scalar_one_or_none()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return tx
