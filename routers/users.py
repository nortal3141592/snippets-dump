# USERS.PY

from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from schemas import UserCreate, UserPrivate, UserPublic, UserUpdate, Token
import models

from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from auth import hash_password, verify_password, create_access_token, verify_access_token, CurrentUser

from config import settings

from limiter import limiter

router = APIRouter()

@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def create_user(request: Request, user_data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(func.lower(models.User.username) == user_data.username.lower()))

    existing_username = result.scalars().first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user with username already exists")
    
    result = await db.execute(select(models.User).where(func.lower(models.User.email) == user_data.email.lower()))

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with username already exists")

    new_user = models.User(
        username = user_data.username,
        email = user_data.email.lower(),
        hashed_password = hash_password(user_data.password),
    )

    db.add(new_user)

    await db.commit()
    await db.refresh(new_user)

    return new_user

@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(func.lower(models.User.email) == form_data.username.lower()))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    
    expiry_time = timedelta(minutes = settings.access_token_expire_time)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=expiry_time)

    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user : CurrentUser):
    return current_user

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    return user

@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(user_id: int, current_user: CurrentUser,user_data: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You're not allowed to make changes to this user")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user_data.username is not None and user_data.username.lower() != user.username.lower():
        result = await db.execute(select(models.User).where(func.lower(models.User.username) == user_data.username.lower()))

        existing_username = result.scalars().first()
        if existing_username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with username already exists")
    
    if user_data.email is not None and user_data.email.lower() != user.email.lower():
        result = await db.execute(select(models.User).where(func.lower(models.User.email) == user_data.email.lower()))
        existing_email = result.scalars().first()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with email already exists")
    
    if user_data.username is not None:
        user.username = user_data.username
    if user_data.email is not None:
        user.email = user_data.email.lower()
    if user_data.image_file is not None:
        user.image_file = user_data.image_file
    
    await db.commit()
    await db.refresh(user)

    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You're not authorised to delete this user's account")
    
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await db.delete(user)
    await db.commit()