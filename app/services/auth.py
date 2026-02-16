from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.services.refresh_tokens import (
    generate_refresh_token,
    hash_token,
    refresh_expires,
    utcnow,
)

from app.core.config import settings
REFRESH_DAYS = settings.refresh_days


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, email: str, password: str) -> dict:
        q = await self.db.execute(select(User).where(User.email == email))
        user = q.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            return {"error": "invalid_credentials"}

        access = create_access_token(subject=str(user.id), role=user.role.value)

        refresh = generate_refresh_token()
        self.db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh),
                expires_at=refresh_expires(REFRESH_DAYS),
            )
        )

        try:
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }

    async def refresh(self, refresh_token: str) -> dict:
        token_h = hash_token(refresh_token)

        q = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_h,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > utcnow(),
            )
        )
        rt = q.scalar_one_or_none()
        if not rt:
            return {"error": "invalid_refresh"}

        uq = await self.db.execute(select(User).where(User.id == rt.user_id))
        user = uq.scalar_one_or_none()
        if not user:
            return {"error": "invalid_refresh"}

        # rotation: отзываем старый и выдаём новый в одной транзакции
        rt.revoked_at = utcnow()

        new_refresh = generate_refresh_token()
        self.db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(new_refresh),
                expires_at=refresh_expires(REFRESH_DAYS),
            )
        )

        try:
            # гарантируем, что INSERT/UPDATE попадут в транзакцию до commit
            await self.db.flush()
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

        new_access = create_access_token(subject=str(user.id), role=user.role.value)
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }

    async def logout(self, refresh_token: str) -> None:
        token_h = hash_token(refresh_token)

        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_h, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )

        try:
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise
