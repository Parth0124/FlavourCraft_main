"""
Recipe routes - static recipes and AI-generated recipes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Optional

from models.user import UserResponse
from models.generated_recipe import (
    GeneratedRecipeRequest,
    GeneratedRecipeResponse,
    RecipeHistoryResponse
)
from models.static_recipe import StaticRecipe, RecipeFilter, RecipeSearchResponse
from dependencies import get_current_user, get_optional_current_user
from services.storage_service import get_database
from services.recipe_service import RecipeGenerationService, StaticRecipeService
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/recipes", tags=["Recipes"])


# ============= Static Recipes =============

@router.get("/static", response_model=RecipeSearchResponse)
async def get_static_recipes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Optional[UserResponse] = Depends(get_optional_current_user)
):
    """
    Get all static recipes (paginated)
    
    - **page**: Page number (default: 1)
    - **page_size**: Number of recipes per page (default: 20, max: 100)
    
    Authentication is optional for browsing static recipes
    """
    try:
        recipe_service = StaticRecipeService(db)
        
        # Empty filter to get all recipes
        results = await recipe_service.search_recipes(
            filters=RecipeFilter(),
            page=page,
            page_size=page_size
        )
        
        return RecipeSearchResponse(**results)
        
    except Exception as e:
        logger.error(f"Error fetching static recipes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching recipes"
        )


@router.get("/static/search", response_model=RecipeSearchResponse)
async def search_static_recipes(
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    ingredients: Optional[str] = Query(None, description="Comma-separated ingredients"),
    difficulty: Optional[str] = Query(None, pattern="^(easy|medium|hard)$"),
    max_prep_time: Optional[int] = Query(None, ge=1),
    max_cook_time: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Search static recipes with filters
    
    - **tags**: Filter by tags (e.g., "vegetarian,indian")
    - **ingredients**: Filter by ingredients (e.g., "paneer,tomato")
    - **difficulty**: Filter by difficulty (easy/medium/hard)
    - **max_prep_time**: Maximum prep time in minutes
    - **max_cook_time**: Maximum cook time in minutes
    - **page**: Page number
    - **page_size**: Recipes per page
    """
    try:
        # Parse comma-separated values
        tags_list = tags.split(",") if tags else None
        ingredients_list = ingredients.split(",") if ingredients else None
        
        # Create filter
        filters = RecipeFilter(
            tags=tags_list,
            ingredients=ingredients_list,
            difficulty=difficulty,
            max_prep_time=max_prep_time,
            max_cook_time=max_cook_time
        )
        
        recipe_service = StaticRecipeService(db)
        results = await recipe_service.search_recipes(filters, page, page_size)
        
        return RecipeSearchResponse(**results)
        
    except Exception as e:
        logger.error(f"Error searching recipes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while searching recipes"
        )


@router.get("/static/{recipe_id}", response_model=StaticRecipe)
async def get_static_recipe(
    recipe_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get a specific static recipe by ID
    
    - **recipe_id**: Recipe ID
    """
    try:
        recipe_service = StaticRecipeService(db)
        recipe = await recipe_service.get_recipe_by_id(recipe_id)
        
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        return recipe
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the recipe"
        )


# ============= AI-Generated Recipes =============

@router.post("/generate", response_model=GeneratedRecipeResponse, status_code=status.HTTP_201_CREATED)
async def generate_recipe(
    request: GeneratedRecipeRequest,  # This will receive the entire body
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate a new recipe using AI based on ingredients
    """
    try:
        recipe_service = RecipeGenerationService(db)
        
        # Extract image_urls if present in the request
        image_urls = None
        if hasattr(request, 'image_urls') and request.image_urls:
            image_urls = request.image_urls.model_dump() if hasattr(request.image_urls, 'model_dump') else dict(request.image_urls)
        
        recipe = await recipe_service.generate_and_save_recipe(
            user_id=current_user.id,
            request=request,
            image_urls=image_urls
        )
        
        logger.info(f"Recipe generated for user {current_user.email}: {recipe.recipe.title}")
        
        return recipe
        
    except Exception as e:
        logger.error(f"Error generating recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the recipe"
        )

@router.get("/history", response_model=RecipeHistoryResponse)
async def get_recipe_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current user's recipe generation history
    
    - **page**: Page number (default: 1)
    - **page_size**: Recipes per page (default: 10, max: 50)
    
    Returns paginated list of user's generated recipes
    """
    try:
        recipe_service = RecipeGenerationService(db)
        
        results = await recipe_service.get_user_recipe_history(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )
        
        return RecipeHistoryResponse(**results)
        
    except Exception as e:
        logger.error(f"Error fetching recipe history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching recipe history"
        )


@router.get("/generated/{recipe_id}", response_model=GeneratedRecipeResponse)
async def get_generated_recipe(
    recipe_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get a specific generated recipe by ID
    
    - **recipe_id**: Generated recipe ID
    
    Only the user who created the recipe can access it
    """
    try:
        from bson import ObjectId
        from models.generated_recipe import GeneratedRecipe, ImageUrls
        
        recipe_service = RecipeGenerationService(db)
        
        doc = await recipe_service.generated_recipes_collection.find_one({
            "_id": ObjectId(recipe_id),
            "user_id": current_user.id
        })
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        # Parse image URLs if present
        image_urls = None
        if doc.get("image_urls"):
            image_urls = ImageUrls(**doc["image_urls"])
        
        return GeneratedRecipeResponse(
            id=str(doc["_id"]),
            recipe=GeneratedRecipe(**doc["generated_recipe"]),
            ingredients_used=doc["ingredients"],
            created_at=doc["timestamp"],
            is_favorite=doc.get("is_favorite", False),
            image_urls=image_urls
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching generated recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the recipe"
        )


@router.put("/generated/{recipe_id}/favorite")
async def toggle_favorite_recipe(
    recipe_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Toggle favorite status of a generated recipe
    
    - **recipe_id**: Generated recipe ID
    
    Returns success message
    """
    try:
        recipe_service = RecipeGenerationService(db)
        
        success = await recipe_service.toggle_favorite(recipe_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        return {"message": "Favorite status toggled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating favorite status"
        )


@router.get("/favorites", response_model=RecipeHistoryResponse)
async def get_favorite_recipes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current user's favorite recipes
    
    - **page**: Page number
    - **page_size**: Recipes per page
    """
    try:
        from models.generated_recipe import GeneratedRecipe, ImageUrls
        
        recipe_service = RecipeGenerationService(db)
        
        skip = (page - 1) * page_size
        
        # Get total count
        total = await recipe_service.generated_recipes_collection.count_documents({
            "user_id": current_user.id,
            "is_favorite": True
        })
        
        # Get recipes
        cursor = recipe_service.generated_recipes_collection.find({
            "user_id": current_user.id,
            "is_favorite": True
        }).sort("timestamp", -1).skip(skip).limit(page_size)
        
        recipes = []
        async for doc in cursor:
            # Parse image URLs if present
            image_urls = None
            if doc.get("image_urls"):
                image_urls = ImageUrls(**doc["image_urls"])
            
            recipes.append(GeneratedRecipeResponse(
                id=str(doc["_id"]),
                recipe=GeneratedRecipe(**doc["generated_recipe"]),
                ingredients_used=doc["ingredients"],
                created_at=doc["timestamp"],
                is_favorite=True,
                image_urls=image_urls
            ))
        
        return RecipeHistoryResponse(
            recipes=recipes,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error fetching favorites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching favorite recipes"
        )