"""
User data models and schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserPreferences(BaseModel):
    """User dietary and cuisine preferences"""
    dietary_restrictions: List[str] = Field(default_factory=list)
    cuisine_preferences: List[str] = Field(default_factory=list)
    cooking_skill: str = "beginner"


class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "chef_parth",
                "email": "parth@example.com",
                "password": "SecurePass123!"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "parth@example.com",
                "password": "SecurePass123!"
            }
        }


class UserResponse(BaseModel):
    """Schema for user response (excludes password)"""
    id: str = Field(alias="_id")
    username: str
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "username": "chef_parth",
                "email": "parth@example.com",
                "created_at": "2025-09-17T12:00:00Z",
                "last_login": "2025-09-17T15:30:00Z",
                "preferences": {
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_preferences": ["indian", "italian"],
                    "cooking_skill": "intermediate"
                }
            }
        }


class UserInDB(BaseModel):
    """Complete user model as stored in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    preferences: Optional[UserPreferences] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "chef_parth_updated",
                "preferences": {
                    "dietary_restrictions": ["vegetarian", "gluten-free"],
                    "cuisine_preferences": ["indian", "italian", "thai"],
                    "cooking_skill": "advanced"
                }
            }
        }


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token"""
    email: Optional[str] = None
    user_id: Optional[str] = None