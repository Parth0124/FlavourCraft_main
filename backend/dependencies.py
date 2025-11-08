"""
FastAPI dependencies - authentication, database, etc.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from services.storage_service import get_database
from services.auth_service import AuthService
from utils.hashing import decode_token
from models.user import TokenData, UserResponse
from utils.logger import get_logger

logger = get_logger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserResponse:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: JWT credentials from Authorization header
        db: Database instance
        
    Returns:
        Current user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract token
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract user data
    email: str = payload.get("sub")
    user_id: str = payload.get("user_id")
    
    if email is None or user_id is None:
        raise credentials_exception
    
    # Get user from database
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    # Return user response
    return UserResponse(
        _id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"],
        last_login=user.get("last_login"),
        preferences=user.get("preferences", {})
    )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Optional[UserResponse]:
    """
    Optional authentication dependency - doesn't raise exception if not authenticated
    
    Args:
        credentials: Optional JWT credentials
        db: Database instance
        
    Returns:
        Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def get_auth_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthService:
    """
    Dependency to get AuthService instance
    
    Args:
        db: Database instance
        
    Returns:
        AuthService instance
    """
    return AuthService(db)