"""
User routes - profile management and user data
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.user import UserResponse, UserUpdate
from dependencies import get_current_user
from services.storage_service import get_database
from services.auth_service import AuthService
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current user's profile
    
    Returns complete user profile information
    """
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update current user's profile
    
    - **username**: New username (optional)
    - **preferences**: Updated preferences (optional)
      - dietary_restrictions: List of dietary restrictions
      - cuisine_preferences: List of preferred cuisines
      - cooking_skill: Skill level (beginner/intermediate/advanced)
    
    Returns updated user profile
    """
    try:
        auth_service = AuthService(db)
        
        # Prepare update data
        update_dict = {}
        
        if update_data.username:
            # Check if username is already taken by another user
            existing_user = await db.users.find_one({
                "username": update_data.username,
                "_id": {"$ne": current_user.id}
            })
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            
            update_dict["username"] = update_data.username
        
        if update_data.preferences:
            update_dict["preferences"] = update_data.preferences.model_dump()
        
        # Update user
        updated_user = await auth_service.update_user_profile(
            current_user.id,
            update_dict
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        logger.info(f"Profile updated for user {current_user.email}")
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating profile"
        )


@router.get("/history")
async def get_user_history(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get complete user cooking history
    
    Returns statistics about user's recipe generation activity
    """
    try:
        # Get total recipes generated
        total_recipes = await db.generated_recipes.count_documents({
            "user_id": current_user.id
        })
        
        # Get favorite count
        favorite_count = await db.generated_recipes.count_documents({
            "user_id": current_user.id,
            "is_favorite": True
        })
        
        # Get most used ingredients
        pipeline = [
            {"$match": {"user_id": current_user.id}},
            {"$unwind": "$ingredients"},
            {"$group": {
                "_id": "$ingredients",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        most_used_ingredients = []
        async for doc in db.generated_recipes.aggregate(pipeline):
            most_used_ingredients.append({
                "ingredient": doc["_id"],
                "count": doc["count"]
            })
        
        # Get preferred cuisines from generated recipes
        cuisine_pipeline = [
            {"$match": {"user_id": current_user.id, "cuisine_type": {"$ne": None}}},
            {"$group": {
                "_id": "$cuisine_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        cuisine_stats = []
        async for doc in db.generated_recipes.aggregate(cuisine_pipeline):
            cuisine_stats.append({
                "cuisine": doc["_id"],
                "count": doc["count"]
            })
        
        return {
            "total_recipes_generated": total_recipes,
            "favorite_recipes": favorite_count,
            "most_used_ingredients": most_used_ingredients,
            "cuisine_statistics": cuisine_stats,
            "user_preferences": current_user.preferences
        }
        
    except Exception as e:
        logger.error(f"Error fetching user history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user history"
        )


@router.get("/favorites")
async def get_user_favorites(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all favorite recipes for current user
    
    Returns list of favorite recipe IDs and basic info
    """
    try:
        cursor = db.generated_recipes.find({
            "user_id": current_user.id,
            "is_favorite": True
        }).sort("timestamp", -1)
        
        favorites = []
        async for doc in cursor:
            favorites.append({
                "id": str(doc["_id"]),
                "title": doc["generated_recipe"]["title"],
                "ingredients": doc["ingredients"],
                "created_at": doc["timestamp"],
                "difficulty": doc["generated_recipe"]["difficulty"]
            })
        
        return {
            "total": len(favorites),
            "favorites": favorites
        }
        
    except Exception as e:
        logger.error(f"Error fetching favorites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching favorites"
        )


@router.delete("/account")
async def delete_user_account(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete current user's account and all associated data
    
    WARNING: This action is irreversible!
    - Deletes user account
    - Deletes all generated recipes
    - Removes all user data
    """
    try:
        from bson import ObjectId
        
        # Delete all generated recipes
        await db.generated_recipes.delete_many({
            "user_id": current_user.id
        })
        
        # Delete user account
        result = await db.users.delete_one({
            "_id": ObjectId(current_user.id)
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User account deleted: {current_user.email}")
        
        return {
            "message": "Account successfully deleted",
            "email": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting account"
        )