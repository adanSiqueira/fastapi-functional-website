from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile, 
    status,
    Query,
    BackgroundTasks
)
from auth import (
    CurrentUser,
    create_access_token, 
    hash_password, 
    verify_password,
    generate_reset_token,
    hash_reset_token
)
from schemas import (
    PostResponse, 
    UserCreate, 
    UserPublicResponse,
    UserPrivateResponse, 
    UserUpdate,
    Token,
    PaginatedPostsResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)

from image_utils import (
    process_profile_image,
    delete_profile_image
)

from email_utils import send_password_reset_email

from starlette.concurrency import run_in_threadpool
from PIL import UnidentifiedImageError
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func
from sqlalchemy import delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from datetime import timedelta, UTC, datetime
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

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == request_data.email.lower())
    )
    user = result.scalars().first()

    if user:
        # Delete any existing reset tokens for this user to prevent multiple valid tokens
        await db.execute(
            sql_delete(models.PasswordResetToken)
            .where(models.PasswordResetToken.user_id == user.id)
        )

        # Generate a reset token and store its hash in the database
        token = generate_reset_token()
        token_hash = hash_reset_token(token)
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.reset_token_expire_minutes)

        # Persist the reset token hash and expiration in the database
        reset_token_entry = models.PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(reset_token_entry)
        await db.commit()

        # Send password reset email in the background
        background_tasks.add_task(
            send_password_reset_email,
            to_email=user.email,
            username=user.username,
            token=token
        )

    # Always return 202 Accepted to prevent email enumeration attacks
    return {"message": "If an account with that email exists, a password reset link has been sent."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # 1. Verify the reset token
    result = await db.execute(
        select(models.PasswordResetToken).where(models.PasswordResetToken.token_hash == hash_reset_token(request_data.token))
    )
    reset_token = result.scalars().first()

    # 2. Verify if token exists and is not expired
    if not reset_token or reset_token.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    # 3. Verify and find the user associated with the reset token
    result = await db.execute(select(models.User).where(models.User.id == reset_token.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # 4. Update the user's password
    hashed_password = hash_password(request_data.new_password)
    user.password_hash = hashed_password

    # 5. Delete the used reset token
    await db.execute(
        sql_delete(models.PasswordResetToken).where(models.PasswordResetToken.id == reset_token.id)
    )

    # 6. Commit the transaction
    await db.commit()

    return {"message": "Password updated successfully."}

@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Verify the current password
    if not verify_password(request_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    # Update the password
    hashed_password = hash_password(request_data.new_password)
    current_user.password_hash = hashed_password

    # Delete any existing reset tokens for this user since the password has been changed
    await db.execute(
        sql_delete(models.PasswordResetToken).where(
            models.PasswordResetToken.user_id == current_user.id
        )
    )

    # Commit the transaction
    await db.commit()
    return {"message": "Password updated successfully."}


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


@router.get("/{user_id}/posts", response_model=PaginatedPostsResponse)
async def get_user_posts(
    user_id: int, 
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10):

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    count_result = await db.execute(
        select(func.count())
        .select_from(models.Post)
        .where(models.Post.user_id == user_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))  ## Lazy Loading
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()

    has_more = skip + len(posts) < total

    return PaginatedPostsResponse(
        posts=[PostResponse.model_validate(post) for post in posts],
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )


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
    
    old_filename = user.image_file
    
    db.delete(user)
    await db.commit()

    if old_filename:
        delete_profile_image(old_filename)

## Upload Profile Picture Endpoint
@router.patch("/{user_id}/picture", response_model=UserPrivateResponse)
async def upload_profile_picture(
    user_id: int,
    file: UploadFile,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's picture",
        )

    content = await file.read()

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // (1024 * 1024)}MB",
        )

    try:
        new_filename = await run_in_threadpool(process_profile_image, content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP).",
        ) from err

    old_filename = current_user.image_file

    current_user.image_file = new_filename
    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_image(old_filename)

    return current_user


## Delete Profile Picture Endpoint
@router.delete("/{user_id}/picture", response_model=UserPrivateResponse)
async def delete_user_picture(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user's picture",
        )

    old_filename = current_user.image_file

    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture to delete",
        )

    current_user.image_file = None
    await db.commit()
    await db.refresh(current_user)

    delete_profile_image(old_filename)

    return current_user


