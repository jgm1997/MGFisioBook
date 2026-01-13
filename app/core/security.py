from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings


bearer_scheme = HTTPBearer()


async def get_current_user(token: str = Depends(bearer_scheme)):
    try:
        payload = jwt.decode(
            token.credentials,
            settings.supabase_secret_key,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase token",
        )
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "patient"),
    }


def require_role(*roles):
    async def wrapper(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return user

    return wrapper
