"""
Authentication service - handles user registration and login
"""
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.user import UserCreate, UserInDB, UserResponse, Token
from utils.hashing import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token
)
from utils.validators import validate_password_strength
from utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service class"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
    
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Register a new user
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user response
            
        Raises:
            HTTPException: If user already exists or validation fails
        """
        # Validate password strength
        is_valid, error_message = validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Check if user already exists
        existing_user = await self.users_collection.find_one({
            "$or": [
                {"email": user_data.email},
                {"username": user_data.username}
            ]
        })
        
        if existing_user:
            if existing_user.get("email") == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user document
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "preferences": {
                "dietary_restrictions": [],
                "cuisine_preferences": [],
                "cooking_skill": "beginner"
            }
        }
        
        # Insert into database
        result = await self.users_collection.insert_one(user_dict)
        
        # Retrieve created user
        created_user = await self.users_collection.find_one({"_id": result.inserted_id})
        
        logger.info(f"New user registered: {user_data.email}")
        
        # Return user response (without password)
        return UserResponse(
            _id=str(created_user["_id"]),
            username=created_user["username"],
            email=created_user["email"],
            created_at=created_user["created_at"],
            last_login=created_user.get("last_login"),
            preferences=created_user.get("preferences", {})
        )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate user credentials
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User document if authenticated, None otherwise
        """
        user = await self.users_collection.find_one({"email": email})
        
        if not user:
            return None
        
        if not verify_password(password, user["password_hash"]):
            return None
        
        return user
    
    async def login_user(self, email: str, password: str) -> Token:
        """
        Login user and generate tokens
        
        Args:
            email: User email
            password: User password
            
        Returns:
            JWT tokens
            
        Raises:
            HTTPException: If authentication fails
        """
        user = await self.authenticate_user(email, password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        await self.users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create tokens
        token_data = {
            "sub": user["email"],
            "user_id": str(user["_id"])
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info(f"User logged in: {email}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            User document or None
        """
        return await self.users_collection.find_one({"email": email})
    
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """
        Get user by ID
        
        Args:
            user_id: User ID as string
            
        Returns:
            User document or None
        """
        from bson import ObjectId
        
        try:
            return await self.users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None
    
    async def update_user_profile(
        self, 
        user_id: str, 
        update_data: dict
    ) -> Optional[UserResponse]:
        """
        Update user profile
        
        Args:
            user_id: User ID
            update_data: Data to update
            
        Returns:
            Updated user response or None
        """
        from bson import ObjectId
        
        try:
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_data:
                return None
            
            # Update user
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            # Get updated user
            updated_user = await self.get_user_by_id(user_id)
            
            if not updated_user:
                return None
            
            logger.info(f"User profile updated: {user_id}")
            
            return UserResponse(
                _id=str(updated_user["_id"]),
                username=updated_user["username"],
                email=updated_user["email"],
                created_at=updated_user["created_at"],
                last_login=updated_user.get("last_login"),
                preferences=updated_user.get("preferences", {})
            )
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return None