from pwdlib import PasswordHash
import jwt

from fastapi import (
    Depends,
    HTTPException,
    status
)
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Annotated
from datetime import UTC, datetime, timedelta

from config import settings
import models
from database import get_db


# ------------------------------------------------------------------------------------
# Password hashing configuration
# ------------------------------------------------------------------------------------

password_hash = PasswordHash.recommended()


# ------------------------------------------------------------------------------------
# OAuth2 scheme configuration
# ------------------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using a secure one-way hashing algorithm.

    Purpose
    -------
    Passwords must NEVER be stored in plain text in a database.
    If a database leak happens, storing raw passwords would immediately compromise
    all user accounts.

    Hashing vs Encryption 
    ------------------------------
    - Hashing is one-way: you cannot "decrypt" a password hash back into the password.
    - Encryption is reversible: if the key leaks, all passwords can be recovered.

    Modern password hashing algorithms (bcrypt, argon2, scrypt, etc.) are designed
    to be intentionally slow, which makes brute-force attacks harder.

    What this function does
    ------------------------
    Uses pwdlib's recommended secure hashing configuration to generate a password hash.

    Output
    ------
    Returns a string that contains:
    - the algorithm identifier
    - the salt
    - the hash

    That string is what is stored in the database (in athe `password_hash` field).
    """
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify whether a plain-text password matches a stored password hash.

    Purpose
    -------
    During login, you never compare passwords directly.
    Instead, you hash the user input using the same algorithm and salt
    embedded in the stored hash, and then compare the result.

    How it works (Theory)
    ---------------------
    Password hashes typically contain the salt inside them.
    That means the verification function can automatically extract the salt
    and re-run the correct hashing process.

    Example Flow
    ------------
    1. User registers with password "123456"
    2. We store: "$argon2id$v=19$...$hash..."
    3. Later, user logs in and sends "123456"
    4. We verify it against the stored hash

    Output
    ------
    - True if the password is correct
    - False if the password is incorrect
    """
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create and sign a JWT access token.

    Purpose
    -------
    JWT (JSON Web Token) is used to represent an authenticated user session
    without storing session data on the server.

    Instead of the server remembering who is logged in, the server issues a signed token.
    The client stores the token and sends it back on every request.

    How JWT works (Theory)
    ----------------------
    A JWT has 3 parts:
        HEADER.PAYLOAD.SIGNATURE

    - HEADER: algorithm + token type
    - PAYLOAD: claims (data like "sub", "exp", etc.)
    - SIGNATURE: cryptographic proof that the token was created by the server

    If the token payload is modified by an attacker, the signature becomes invalid.

    Important Claims
    ----------------
    - "sub" (subject): identifies the user (commonly user_id or email)
    - "exp" (expiration): defines when the token becomes invalid

    What `data` should contain
    --------------------------
    `data` is expected to include authentication-related claims, most importantly:

        {"sub": "<user_id>"}

    The "sub" claim is the standard way to store the identity of the token owner.

    Expiration logic
    ----------------
    If `expires_delta` is not provided, the expiration is calculated using the default
    configured in settings (`access_token_expire_minutes`).

    If `expires_delta` is provided, it overrides the default.

    Security Note
    -------------
    The secret key must be strong and never exposed.
    If the secret key leaks, attackers can generate valid JWT tokens.

    Output
    ------
    Returns a signed JWT token string that the client can store and use
    in future requests as:

        Authorization: Bearer <token>
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta

    to_encode = data.copy()

    # "exp" is a standard registered JWT claim that defines token expiration time.
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm
    )

    return encoded_jwt


def verify_access_token(token: str) -> str | None:
    """
    Verify and decode a JWT access token.

    Purpose
    -------
    This function is responsible for validating that a JWT token is:
    - authentic (was signed with our secret key)
    - not expired
    - structurally valid
    - contains the required authentication claims

    How it works (Theory)
    ---------------------
    `jwt.decode()` performs multiple checks:
    1. Validates the signature using the secret key.
    2. Checks the "exp" claim to ensure the token is not expired.
    3. Decodes the payload into a Python dictionary.

    Required claims
    ---------------
    The `options={"require": ["exp", "sub"]}` enforces that the payload MUST contain:
    - exp (expiration time)
    - sub (subject/user identifier)

    If those claims are missing, the token is considered invalid.

    What we return
    --------------
    Instead of returning the full payload, this function returns the "sub" claim.

    In your project, "sub" represents the user_id.
    That means the token is basically carrying the user's identity.

    Why return None instead of raising an error?
    -------------------------------------------
    This design keeps the verification logic reusable.
    Higher-level functions (like get_current_user) can decide what HTTP response
    should be returned.

    Output
    ------
    - Returns the subject ("sub") if token is valid
    - Returns None if token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]}
        )

    except jwt.InvalidTokenError:
        # This includes invalid signature, expired token, malformed token, missing claims, etc.
        print("Invalid Token Error.")
        return None

    else:
        return payload.get("sub")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> models.User | None:
    """
    Resolve and return the currently authenticated user based on the JWT token.

    Purpose
    -------
    This function is the core authentication dependency for protected routes.

    In FastAPI, authentication is usually implemented using Dependency Injection (DI).
    That means instead of manually checking the token inside every endpoint,
    you create a reusable dependency that performs the authentication once.

    What FastAPI does here
    ----------------------
    token: Annotated[str, Depends(oauth2_scheme)]
        - FastAPI calls `oauth2_scheme`
        - oauth2_scheme extracts the token from:
              Authorization: Bearer <token>
        - The extracted token string is injected into this function

    db: Annotated[AsyncSession, Depends(get_db)]
        - FastAPI creates an async database session
        - Injects it here
        - Ensures proper session cleanup after the request finishes

    Authentication flow (Step-by-step)
    ----------------------------------
    1. Client sends request with Authorization header.
    2. FastAPI extracts the token using OAuth2PasswordBearer.
    3. verify_access_token(token) checks if token is valid.
    4. If valid, we extract the "sub" claim (user_id).
    5. We query the database to fetch the user.
    6. If user exists, return the User model.

    Why do we fetch the user from the DB?
    -------------------------------------
    Even if the token is valid, the user might:
    - have been deleted
    - have been deactivated
    - have changed permissions/roles

    So we validate that the user still exists and is still valid.

    Why raise HTTPException?
    ------------------------
    FastAPI expects authentication dependencies to raise 401 when invalid.

    Also, the header:
        {"WWW-Authenticate": "Bearer"}
    is part of the HTTP standard and tells clients that Bearer authentication is required.

    Output
    ------
    Returns:
        models.User object if authenticated

    Raises:
        HTTPException(401) if token is invalid or user does not exist
    """
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWT payload values are usually strings, so we ensure user_id is a valid integer.
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(models.User).where(models.User.id == user_id_int))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# ------------------------------------------------------------------------------------
# Type alias for cleaner endpoint signatures
# ------------------------------------------------------------------------------------

CurrentUser = Annotated[models.User, Depends(get_current_user)]
"""
A reusable type alias for injecting the authenticated user into protected endpoints.

Purpose
-------
Instead of writing this repeatedly:

    user: Annotated[models.User, Depends(get_current_user)]

You can simply write:

    user: CurrentUser

This improves readability and standardizes how authentication is applied.

Example usage
-------------
@router.get("/me")
async def read_me(user: CurrentUser):
    return user

This ensures:
- the token is extracted
- the token is verified
- the user is loaded from the database
- the endpoint receives a fully validated User object
"""
