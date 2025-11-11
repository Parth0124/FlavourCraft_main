"""
AI-generated recipe data models and schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class ImageUrls(BaseModel):
    """Image URLs from Cloudinary"""
    url: str  # Full-size image URL
    thumbnail_url: str  # 200x200 thumbnail
    medium_url: str  # 600x600 medium size
    public_id: str  # Cloudinary public ID for deletion
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
                "thumbnail_url": "https://res.cloudinary.com/demo/image/upload/c_thumb,w_200/sample.jpg",
                "medium_url": "https://res.cloudinary.com/demo/image/upload/c_limit,w_600/sample.jpg",
                "public_id": "ingredient_images/user_123/abc123"
            }
        }


class GeneratedRecipeRequest(BaseModel):
    """Request schema for generating a recipe"""
    ingredients: List[str] = Field(..., min_items=2, max_items=50)
    dietary_preferences: Optional[List[str]] = Field(default_factory=list)
    cuisine_type: Optional[str] = None
    cooking_time: Optional[int] = Field(None, gt=0, le=180)
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    image_urls: Optional[ImageUrls] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "ingredients": ["rice", "tomato", "onion", "spices", "oil"],
                "dietary_preferences": ["vegetarian"],
                "cuisine_type": "indian",
                "cooking_time": 45,
                "difficulty": "easy"
            }
        }


class GeneratedRecipe(BaseModel):
    """AI-generated recipe content"""
    title: str
    steps: List[str] = Field(..., min_items=3)
    estimated_time: int  # minutes
    difficulty: str
    tips: Optional[str] = None
    servings: int = Field(default=4)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Spiced Tomato Rice",
                "steps": [
                    "Wash and soak rice for 30 minutes",
                    "Heat oil in a pan, add cumin seeds",
                    "Sauté onions until golden brown",
                    "Add chopped tomatoes and spices, cook until soft",
                    "Add rice and water in 1:2 ratio",
                    "Cover and cook on low heat for 20 minutes",
                    "Fluff with a fork and serve hot"
                ],
                "estimated_time": 35,
                "difficulty": "easy",
                "tips": "Soaking rice ensures better texture. Add vegetables for extra nutrition.",
                "servings": 4
            }
        }


class GeneratedRecipeDocument(BaseModel):
    """Complete generated recipe as stored in database"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    ingredients: List[str]
    generated_recipe: GeneratedRecipe
    source: str = "ai"  # "openai" or "local_model"
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    is_favorite: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dietary_preferences: List[str] = Field(default_factory=list)
    cuisine_type: Optional[str] = None
    image_urls: Optional[ImageUrls] = None  # Ingredient image URLs from Cloudinary
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439012",
                "ingredients": ["rice", "tomato", "onion", "spices"],
                "generated_recipe": {
                    "title": "Spiced Tomato Rice",
                    "steps": [
                        "Wash and soak rice for 30 minutes",
                        "Heat oil, add cumin seeds",
                        "Sauté onions until golden",
                        "Add tomatoes and spices",
                        "Add rice and water, cook until done"
                    ],
                    "estimated_time": 35,
                    "difficulty": "easy",
                    "tips": "Soak rice for better texture"
                },
                "source": "openai_gpt4",
                "confidence_score": 0.89,
                "is_favorite": False,
                "timestamp": "2025-09-17T15:00:00Z"
            }
        }


class GeneratedRecipeResponse(BaseModel):
    """Response schema for generated recipe"""
    id: str
    recipe: GeneratedRecipe
    ingredients_used: List[str]
    created_at: datetime
    is_favorite: bool
    image_urls: Optional[ImageUrls] = None  # Include the ingredient image URLs
    username: Optional[str] = None  # Username of the user who created the recipe
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "recipe": {
                    "title": "Spiced Tomato Rice",
                    "steps": ["Wash rice...", "Heat oil..."],
                    "estimated_time": 35,
                    "difficulty": "easy",
                    "tips": "Soak rice for better texture",
                    "servings": 4
                },
                "ingredients_used": ["rice", "tomato", "onion", "spices"],
                "created_at": "2025-09-17T15:00:00Z",
                "is_favorite": False,
                "image_urls": {
                    "url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
                    "thumbnail_url": "https://res.cloudinary.com/demo/image/upload/c_thumb,w_200/sample.jpg",
                    "medium_url": "https://res.cloudinary.com/demo/image/upload/c_limit,w_600/sample.jpg",
                    "public_id": "ingredient_images/user_123/abc123"
                },
                "username": "chef_john"
            }
        }


class RecipeHistoryResponse(BaseModel):
    """Response for user's recipe history"""
    recipes: List[GeneratedRecipeResponse]
    total: int
    page: int
    page_size: int