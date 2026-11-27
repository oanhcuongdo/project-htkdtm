"""API auth JSON dưới prefix /api/v1/auth."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.dependencies import get_current_user
from app.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserOut
from app.database import get_db
from app.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
Database = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterRequest, db: Database):
    return service.register(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Database, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return service.login(db, payload)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Database, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return service.refresh(db, payload.refresh_token)


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]):
    return user
