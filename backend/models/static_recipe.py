"""
Static recipe data models and schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId


class NutritionInfo(BaseModel):
    """Nutritional information for a recipe"""
    calories: int
    protein: int  # grams
    carbs: int  # grams
    fat: int  # grams


class StaticRecipe(BaseModel):
    """Pre-loaded recipe structure"""
    id: Optional[str] = Field(None, alias="_id")
    title: str = Field(..., min_length=3, max_length=200)
    ingredients: List[str] = Field(..., min_items=2)
    instructions: str = Field(..., min_length=20)
    tags: List[str] = Field(default_factory=list)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    prep_time: int = Field(..., gt=0)  # minutes
    cook_time: int = Field(..., gt=0)  # minutes
    servings: int = Field(default=4, gt=0)
    nutrition: Optional[NutritionInfo] = None
    image_url: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "title": "Paneer Butter Masala",
                "ingredients": [
                    "500g paneer, cubed",
                    "2 large tomatoes, pureed",
                    "200ml heavy cream",
                    "2 tbsp butter",
                    "1 onion, finely chopped",
                    "2 tsp garam masala",
                    "1 tsp kasuri methi",
                    "Salt to taste"
                ],
                "instructions": "1. Heat butter in a pan over medium heat.\n2. Add onions and sauté until golden.\n3. Add tomato puree and cook for 10 minutes.\n4. Add garam masala and kasuri methi.\n5. Add cream and paneer cubes.\n6. Simmer for 5 minutes and serve hot.",
                "tags": ["vegetarian", "north-indian", "main-course"],
                "difficulty": "medium",
                "prep_time": 15,
                "cook_time": 30,
                "servings": 4,
                "nutrition": {
                    "calories": 450,
                    "protein": 20,
                    "carbs": 15,
                    "fat": 35
                }
            }
        }


class RecipeFilter(BaseModel):
    """Filter criteria for searching recipes"""
    tags: Optional[List[str]] = None
    ingredients: Optional[List[str]] = None
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    max_prep_time: Optional[int] = Field(None, gt=0)
    max_cook_time: Optional[int] = Field(None, gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tags": ["vegetarian", "indian"],
                "ingredients": ["paneer", "tomato"],
                "difficulty": "medium",
                "max_prep_time": 30,
                "max_cook_time": 60
            }
        }


class RecipeSearchResponse(BaseModel):
    """Response for recipe search"""
    recipes: List[StaticRecipe]
    total: int
    page: int
    page_size: int


class RecipeCreate(BaseModel):
    """Schema for creating a new static recipe (admin only)"""
    title: str = Field(..., min_length=3, max_length=200)
    ingredients: List[str] = Field(..., min_items=2)
    instructions: str = Field(..., min_length=20)
    tags: List[str] = Field(default_factory=list)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    prep_time: int = Field(..., gt=0)
    cook_time: int = Field(..., gt=0)
    servings: int = Field(default=4, gt=0)
    nutrition: Optional[NutritionInfo] = None
    image_url: Optional[str] = None