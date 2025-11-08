"""
Models package - exports all data models
"""
from .user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserInDB,
    UserUpdate,
    UserPreferences,
    Token,
    TokenData
)
from .static_recipe import (
    StaticRecipe,
    RecipeFilter,
    RecipeSearchResponse,
    RecipeCreate,
    NutritionInfo
)
from .generated_recipe import (
    GeneratedRecipeRequest,
    GeneratedRecipe,
    GeneratedRecipeDocument,
    GeneratedRecipeResponse,
    RecipeHistoryResponse
)

__all__ = [
    # User models
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserInDB",
    "UserUpdate",
    "UserPreferences",
    "Token",
    "TokenData",
    # Static recipe models
    "StaticRecipe",
    "RecipeFilter",
    "RecipeSearchResponse",
    "RecipeCreate",
    "NutritionInfo",
    # Generated recipe models
    "GeneratedRecipeRequest",
    "GeneratedRecipe",
    "GeneratedRecipeDocument",
    "GeneratedRecipeResponse",
    "RecipeHistoryResponse",
]