from fastapi import (
    APIRouter,
    Depends,
    HTTPException, 
    status
)
from auth import (
    CurrentUser,
    create_access_token, 
    hash_password, 
    verify_password
)
from schemas import (
    PostResponse, 
    UserCreate, 
    UserPublicResponse,
    UserPrivateResponse, 
    UserUpdate,
    Token
)
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from datetime import timedelta
from config import settings

# -----------------------------------------------------------------------------------------------#

#Instantiate router
router = APIRouter()

#Endpoints
@router.post("", response_model=UserPrivateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):

    if (await db.execute(select(models.User).where(func.lower(models.User.username)== user.username.lower()))).scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    if (await db.execute(select(models.User).where(func.lower(models.User.email) == user.email.lower()))).scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        username = user.username,
        email = user.email.lower(),
        password_hash = hash_password(user.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[AsyncSession, Depends(get_db)]
):
    # Look up user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email

    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower()
        )
    )
    user = result.scalars().first()

    # Verify user exists and password is correct
    # Do not reveal which one failed (security best pratice)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return Token(access_token = access_token, token_type="bearer")

@router.get("/me", response_model=UserPrivateResponse)
async def get_current_user(
        current_user: CurrentUser
):
    """Get the currently authenticated user"""    
    return current_user

@router.get("/{user_id}", response_model=UserPublicResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("", response_model=list[UserPublicResponse])
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.User))
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="Users not found")

    return users


@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(select(models.Post)
                              .where(models.Post.user_id == user_id)
                              .order_by(models.Post.date_posted.desc()))
    return result.scalars().all()


@router.patch("/{user_id}", response_model=UserPrivateResponse)
async def update_user (
     user_id: int,
     user_update: UserUpdate,
     current_user: CurrentUser,
     db: Annotated[AsyncSession, Depends(get_db)]):
    
    ## Validating User
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
            )
     
    # Only allow users to update their own account
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user."
        )

    # Check if new username already exists in the database
    if user_update.username is not None and user_update.username.lower() != user.username.lower():
        result = await db.execute(
              select(models.User).where(func.lower(models.User.username) == user_update.username.lower())
        )

        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail ="Username already exists"
            )
        

    #Check if new email already existis in the database
    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        result = await db.execute(
            select(models.User).where(func.lower(models.User.email) == user_update.email.lower())
        )

        existing_email = result.scalars().first()

        if existing_email:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Email already registered"
            )
        
    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email.lower()
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "User not found.")

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user."
        )
    
    db.delete(user)
    await db.commit()