"""
Cuisine collection models and schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CuisineInfo(BaseModel):
    """Information about a cuisine type"""
    cuisine_type: str
    recipe_count: int
    description: Optional[str] = None
    emoji: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "cuisine_type": "italian",
                "recipe_count": 15,
                "description": "Classic Italian recipes with pasta, pizza, and more",
                "emoji": "🇮🇹"
            }
        }


class CuisineCollectionResponse(BaseModel):
    """Response for cuisine collection page"""
    cuisine_type: str
    total_recipes: int
    recipes: List[dict]
    popular_ingredients: List[str]
    avg_cooking_time: Optional[float] = None
    difficulty_breakdown: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "cuisine_type": "italian",
                "total_recipes": 15,
                "recipes": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "title": "Pasta Carbonara",
                        "estimated_time": 25,
                        "difficulty": "easy"
                    }
                ],
                "popular_ingredients": ["pasta", "tomatoes", "olive oil", "garlic"],
                "avg_cooking_time": 32.5,
                "difficulty_breakdown": {
                    "easy": 8,
                    "medium": 5,
                    "hard": 2
                }
            }
        }


class AllCuisinesResponse(BaseModel):
    """Response listing all available cuisines"""
    cuisines: List[CuisineInfo]
    total_cuisines: int
    total_recipes: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "cuisines": [
                    {
                        "cuisine_type": "italian",
                        "recipe_count": 15,
                        "emoji": "🇮🇹"
                    },
                    {
                        "cuisine_type": "mexican",
                        "recipe_count": 12,
                        "emoji": "🇲🇽"
                    }
                ],
                "total_cuisines": 8,
                "total_recipes": 67
            }
        }


class CuisineStats(BaseModel):
    """Statistics for a specific cuisine"""
    cuisine_type: str
    total_recipes: int
    total_users: int
    avg_rating: Optional[float] = None
    most_used_ingredients: List[str]
    difficulty_distribution: dict
    time_distribution: dict
    created_this_week: int
    created_this_month: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "cuisine_type": "italian",
                "total_recipes": 15,
                "total_users": 8,
                "avg_rating": 4.3,
                "most_used_ingredients": ["pasta", "tomatoes", "olive oil"],
                "difficulty_distribution": {
                    "easy": 8,
                    "medium": 5,
                    "hard": 2
                },
                "time_distribution": {
                    "under_30": 6,
                    "30_60": 7,
                    "over_60": 2
                },
                "created_this_week": 3,
                "created_this_month": 12
            }
        }