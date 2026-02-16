from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, LogoutRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    res = await svc.login(payload.email, payload.password)
    if res.get("error"):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(**res)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    res = await svc.refresh(payload.refresh_token)
    if res.get("error"):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return TokenResponse(**res)


@router.post("/logout")
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    await svc.logout(payload.refresh_token)
    return {"ok": True}
