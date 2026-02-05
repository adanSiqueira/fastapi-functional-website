from datetime import UTC, datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from config import settings

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")

def hash_password(password:str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password:str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """ Create a JWT access token. """    

    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta

    to_encode = data.copy()
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm = settings.algorithm
    )

    return encoded_jwt

def verify_access_token(token:str) -> str | None:
    """Veriyfy a JWT access token and return the subject (user_id) if valid."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms = [settings.algorithm],
            options = {"require": ["exp", "sub"]}
        )
    
    except jwt.InvalidTokenError:
        print("Invalid Token Error.")
        return None

    else:
        return payload.get("sub")