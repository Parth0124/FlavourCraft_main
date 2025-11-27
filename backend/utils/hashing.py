"""
Password hashing and JWT token utilities
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing token payload
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    # Read credentials directly from environment variables
    jwt_secret_key = os.getenv('JWT_SECRET_KEY')
    jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
    access_token_expire_minutes = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '720'))
    
    if not jwt_secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is not set")
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, 
        jwt_secret_key, 
        algorithm=jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: Dictionary containing token payload
        
    Returns:
        Encoded JWT refresh token string
    """
    # Read credentials directly from environment variables
    jwt_secret_key = os.getenv('JWT_SECRET_KEY')
    jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
    refresh_token_expire_days = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    
    if not jwt_secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is not set")
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=refresh_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, 
        jwt_secret_key, 
        algorithm=jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token
    
    Args:
        token: Encoded JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    # Read credentials directly from environment variables
    jwt_secret_key = os.getenv('JWT_SECRET_KEY')
    jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
    
    if not jwt_secret_key:
        return None
    
    try:
        payload = jwt.decode(
            token, 
            jwt_secret_key, 
            algorithms=[jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_token_type(token: str, expected_type: str) -> bool:
    """
    Verify that a token is of the expected type (access or refresh)
    
    Args:
        token: Encoded JWT token string
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        True if token type matches, False otherwise
    """
    payload = decode_token(token)
    if not payload:
        return False
    return payload.get("type") == expected_type