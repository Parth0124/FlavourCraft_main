"""
Cuisine collection routes - Browse recipes by cuisine type
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from models.user import UserResponse
from models.cuisine_collection import (
    AllCuisinesResponse,
    CuisineCollectionResponse,
    CuisineStats
)
from services.cuisine_service import CuisineCollectionService
from services.storage_service import get_database
from dependencies import get_current_user
from utils.logger import get_logger

router = APIRouter(prefix="/cuisines", tags=["Cuisine Collections"])
logger = get_logger(__name__)


@router.get("/", response_model=dict)
async def get_all_cuisines(
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_database),
    user_only: bool = Query(False, description="Show only current user's cuisines")
):
    """
    Get all available cuisine types with recipe counts
    
    Returns a list of all cuisines that have recipes, with counts and metadata
    
    - **user_only**: If true, only show cuisines from current user's recipes
    
    **Example Response:**
    ```json
    {
      "cuisines": [
        {
          "cuisine_type": "italian",
          "recipe_count": 15,
          "emoji": "🇮🇹",
          "description": "Classic Italian cuisine..."
        }
      ],
      "total_cuisines": 8,
      "total_recipes": 67
    }
    ```
    """
    try:
        cuisine_service = CuisineCollectionService(db)
        
        user_id = str(current_user.id) if user_only else None
        
        result = await cuisine_service.get_all_cuisines(user_id=user_id)
        
        logger.info(f"Retrieved {result['total_cuisines']} cuisines for user {current_user.email}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving cuisines: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving cuisines"
        )


@router.get("/{cuisine_type}", response_model=dict)
async def get_cuisine_collection(
    cuisine_type: str,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_database),
    skip: int = Query(0, ge=0, description="Number of recipes to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of recipes to return"),
    user_only: bool = Query(False, description="Show only current user's recipes")
):
    """
    Get all recipes for a specific cuisine type
    
    Perfect for building a cuisine collection page in frontend!
    
    - **cuisine_type**: Type of cuisine (e.g., "italian", "mexican", "chinese")
    - **skip**: Pagination offset
    - **limit**: Number of recipes per page (max 100)
    - **user_only**: Filter to only current user's recipes
    
    **Example Response:**
    ```json
    {
      "cuisine_type": "italian",
      "total_recipes": 15,
      "recipes": [
        {
          "id": "...",
          "title": "Pasta Carbonara",
          "estimated_time": 25,
          "difficulty": "easy",
          "ingredients": ["pasta", "eggs", "bacon"]
        }
      ],
      "popular_ingredients": ["pasta", "tomatoes", "olive oil"],
      "avg_cooking_time": 32.5,
      "difficulty_breakdown": {"easy": 8, "medium": 5, "hard": 2},
      "page_info": {
        "current_page": 1,
        "page_size": 20,
        "total_pages": 1
      }
    }
    ```
    """
    try:
        cuisine_service = CuisineCollectionService(db)
        
        user_id = str(current_user.id) if user_only else None
        
        result = await cuisine_service.get_cuisine_collection(
            cuisine_type=cuisine_type,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        if result["total_recipes"] == 0:
            logger.info(f"No recipes found for cuisine: {cuisine_type}")
            return {
                "cuisine_type": cuisine_type,
                "total_recipes": 0,
                "recipes": [],
                "message": f"No recipes found for {cuisine_type} cuisine. Try generating one!",
                "popular_ingredients": [],
                "difficulty_breakdown": {},
                "page_info": {
                    "current_page": 1,
                    "page_size": limit,
                    "total_pages": 0
                }
            }
        
        logger.info(f"Retrieved {len(result['recipes'])} recipes for {cuisine_type} cuisine")
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving {cuisine_type} cuisine collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving {cuisine_type} cuisine collection"
        )


@router.get("/{cuisine_type}/stats", response_model=dict)
async def get_cuisine_statistics(
    cuisine_type: str,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_database),
    user_only: bool = Query(False, description="Show only current user's stats")
):
    """
    Get detailed statistics for a specific cuisine
    
    Provides analytics and insights for the cuisine collection page
    
    - **cuisine_type**: Type of cuisine
    - **user_only**: Calculate stats only from current user's recipes
    
    **Example Response:**
    ```json
    {
      "cuisine_type": "italian",
      "total_recipes": 15,
      "total_users": 8,
      "avg_rating": 4.3,
      "most_used_ingredients": ["pasta", "tomatoes", "olive oil"],
      "difficulty_distribution": {"easy": 8, "medium": 5, "hard": 2},
      "time_distribution": {"under_30": 6, "30_60": 7, "over_60": 2},
      "created_this_week": 3,
      "created_this_month": 12,
      "avg_cooking_time": 35.2
    }
    ```
    """
    try:
        cuisine_service = CuisineCollectionService(db)
        
        user_id = str(current_user.id) if user_only else None
        
        stats = await cuisine_service.get_cuisine_detailed_stats(
            cuisine_type=cuisine_type,
            user_id=user_id
        )
        
        logger.info(f"Retrieved detailed stats for {cuisine_type} cuisine")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving cuisine stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving cuisine statistics"
        )


@router.get("/{cuisine_type}/search", response_model=List[dict])
async def search_cuisine_by_ingredients(
    cuisine_type: str,
    ingredients: str = Query(..., description="Comma-separated list of ingredients"),
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_database),
    limit: int = Query(20, ge=1, le=100),
    user_only: bool = Query(False, description="Search only current user's recipes")
):
    """
    Search recipes within a cuisine by ingredients
    
    Find specific recipes within a cuisine that contain certain ingredients
    
    - **cuisine_type**: Type of cuisine to search within
    - **ingredients**: Comma-separated ingredients (e.g., "tomatoes,pasta,garlic")
    - **limit**: Maximum number of results
    - **user_only**: Search only current user's recipes
    
    **Example:**
    ```
    GET /cuisines/italian/search?ingredients=pasta,tomatoes,basil
    ```
    
    **Response:**
    ```json
    [
      {
        "id": "...",
        "title": "Fresh Tomato Basil Pasta",
        "estimated_time": 25,
        "difficulty": "easy",
        "ingredients": ["pasta", "tomatoes", "basil", "olive oil"],
        "cuisine_type": "italian"
      }
    ]
    ```
    """
    try:
        cuisine_service = CuisineCollectionService(db)
        
        # Parse ingredients
        ingredient_list = [ing.strip() for ing in ingredients.split(",") if ing.strip()]
        
        if not ingredient_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one ingredient is required"
            )
        
        user_id = str(current_user.id) if user_only else None
        
        results = await cuisine_service.search_by_cuisine_and_ingredients(
            cuisine_type=cuisine_type,
            ingredients=ingredient_list,
            user_id=user_id,
            limit=limit
        )
        
        logger.info(f"Found {len(results)} recipes for {cuisine_type} with ingredients: {ingredient_list}")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching cuisine by ingredients: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while searching recipes"
        )


@router.get("/trending/now", response_model=List[dict])
async def get_trending_cuisines(
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_database),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=20, description="Number of trending cuisines")
):
    """
    Get trending cuisines based on recent activity
    
    Shows which cuisines are most popular recently
    
    - **days**: How many days back to analyze (default: 7)
    - **limit**: Number of trending cuisines to return
    
    **Example Response:**
    ```json
    [
      {
        "cuisine_type": "italian",
        "recipe_count": 25,
        "emoji": "🇮🇹",
        "description": "Classic Italian cuisine..."
      },
      {
        "cuisine_type": "mexican",
        "recipe_count": 18,
        "emoji": "🇲🇽",
        "description": "Vibrant Mexican dishes..."
      }
    ]
    ```
    """
    try:
        cuisine_service = CuisineCollectionService(db)
        
        trending = await cuisine_service.get_trending_cuisines(
            days=days,
            limit=limit
        )
        
        logger.info(f"Retrieved {len(trending)} trending cuisines from last {days} days")
        
        return trending
        
    except Exception as e:
        logger.error(f"Error retrieving trending cuisines: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving trending cuisines"
        )