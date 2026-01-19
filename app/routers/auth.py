from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AuthInvalidCredentialsError
from supabase_auth import AuthResponse

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.supabase_client import supabase
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserInfo
from app.schemas.patient import PatientCreate
from app.services.patient_service import create_patient

router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        result: AuthResponse = supabase.auth.sign_up(
            {"email": data.email, "password": data.password},
        )
    except AuthInvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = result.user
    token = result.session.access_token
    role = "patient"

    supabase.auth.update_user(
        {
            "data": {
                "first_name": data.first_name,
                "last_name": data.last_name,
                "role": role,
            }
        }
    )

    await create_patient(
        db,
        PatientCreate(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=None,
            notes=None,
            supabase_user_id=UUID(user.id),
        ),
    )

    return TokenResponse(access_token=token, role=role)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )
    except AuthInvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_data = supabase.auth.get_user(result.session.access_token)
    role = user_data.user.user_metadata.get("role", "patient")

    return TokenResponse(access_token=result.session.access_token, role=role)


@router.get("/me", response_model=UserInfo)
async def me(user=Depends(get_current_user)):
    return UserInfo(**user)
