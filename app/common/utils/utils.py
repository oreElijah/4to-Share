from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from itsdangerous import URLSafeTimedSerializer
from typing import Any
import logging
import uuid
import jwt

from settings.config import GlobalConfig as Config
from app.auth.schemas.login_schema import TokenData

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    pbkdf2_sha256__default_rounds=30000  # Adjust rounds for security/speed
)

auth_s = URLSafeTimedSerializer(
    secret_key=Config.SECRET_KEY,
    salt="email-confirmation-salt")

def generate_password_hash(password: str) -> str:
    """Generate a hashed password."""
    hash = pwd_context.hash(password)

    return hash

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_data: dict, refresh: bool= False, expiry_time: timedelta= None) -> str: # type: ignore
    payload: dict[str, Any] = {}

    expire = datetime.now(timezone.utc) + (expiry_time if expiry_time is not None else timedelta(seconds=Config.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload["user"] = user_data
    payload["jti"] = str(uuid.uuid4())
    payload["exp"] = expire
    payload["refresh"] = refresh

    token = jwt.encode(payload=payload,
                       key=Config.SECRET_KEY,
                         algorithm=Config.ALGORITHM)
    return token

def decode_access_token(token: str)-> dict[str, Any] :
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.SECRET_KEY,
            algorithms=[Config.ALGORITHM]
        )
        return token_data
    
    except jwt.PyJWTError as e:
        logging.error(e)
        return {}
    
def create_url_safe_token(user_data: dict) -> str:
    token = auth_s.dumps(user_data)

    return token

def decode_url_safe_token(token: str, expiration: int= 3600) -> dict[str, Any]:
    try:
        token_data = auth_s.loads(
            token,
            max_age=expiration
        )
        return token_data
    
    except Exception as e:
        logging.error(e)
        return {}