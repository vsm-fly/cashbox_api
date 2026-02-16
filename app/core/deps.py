from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import async_session
from app.models.user import User

bearer = HTTPBearer(auto_error=True)

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> User:
    try:
        payload = decode_token(creds.credentials)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    async with async_session() as session:
        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
