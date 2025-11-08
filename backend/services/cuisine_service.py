"""
Cuisine collection service - handles cuisine-based recipe queries
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import Counter
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from utils.logger import get_logger

logger = get_logger(__name__)


class CuisineCollectionService:
    """Service for cuisine-based recipe collections"""
    
    # Cuisine metadata with emojis and descriptions
    CUISINE_INFO = {
        "italian": {"emoji": "🇮🇹", "description": "Classic Italian cuisine with pasta, pizza, and Mediterranean flavors"},
        "mexican": {"emoji": "🇲🇽", "description": "Vibrant Mexican dishes with tacos, burritos, and bold spices"},
        "chinese": {"emoji": "🇨🇳", "description": "Traditional Chinese cooking with stir-fries, dumplings, and noodles"},
        "indian": {"emoji": "🇮🇳", "description": "Rich Indian flavors with curries, rice dishes, and aromatic spices"},
        "japanese": {"emoji": "🇯🇵", "description": "Elegant Japanese cuisine including sushi, ramen, and tempura"},
        "thai": {"emoji": "🇹🇭", "description": "Spicy and flavorful Thai food with curries, pad thai, and coconut"},
        "french": {"emoji": "🇫🇷", "description": "Sophisticated French cooking with pastries, sauces, and techniques"},
        "american": {"emoji": "🇺🇸", "description": "Classic American comfort food including burgers, BBQ, and more"},
        "mediterranean": {"emoji": "🌊", "description": "Healthy Mediterranean diet with olive oil, vegetables, and seafood"},
        "korean": {"emoji": "🇰🇷", "description": "Korean favorites including kimchi, bibimbap, and Korean BBQ"},
        "middle-eastern": {"emoji": "🕌", "description": "Middle Eastern flavors with hummus, falafel, and kebabs"},
        "spanish": {"emoji": "🇪🇸", "description": "Spanish cuisine with paella, tapas, and seafood"},
        "greek": {"emoji": "🇬🇷", "description": "Fresh Greek dishes with feta, olives, and Mediterranean herbs"},
        "vietnamese": {"emoji": "🇻🇳", "description": "Light Vietnamese food including pho, spring rolls, and vermicelli"},
        "other": {"emoji": "🌍", "description": "Other international cuisines and fusion dishes"}
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.generated_recipes
    
    async def get_all_cuisines(self, user_id: Optional[str] = None) -> Dict:
        """
        Get all available cuisines with recipe counts
        
        Args:
            user_id: Optional user ID to filter by user's recipes
            
        Returns:
            Dictionary with cuisine information
        """
        try:
            # Build query
            query = {}
            if user_id:
                query["user_id"] = user_id
            
            # Get all recipes with cuisine types
            pipeline = [
                {"$match": query},
                {"$match": {"cuisine_type": {"$exists": True, "$ne": None}}},
                {"$group": {
                    "_id": "$cuisine_type",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            
            results = await self.collection.aggregate(pipeline).to_list(length=None)
            
            # Format response
            cuisines = []
            total_recipes = 0
            
            for item in results:
                cuisine_type = item["_id"].lower()
                count = item["count"]
                total_recipes += count
                
                # Get metadata
                metadata = self.CUISINE_INFO.get(cuisine_type, {
                    "emoji": "🍽️",
                    "description": f"{cuisine_type.title()} cuisine"
                })
                
                cuisines.append({
                    "cuisine_type": cuisine_type,
                    "recipe_count": count,
                    "emoji": metadata.get("emoji", "🍽️"),
                    "description": metadata.get("description", "")
                })
            
            logger.info(f"Found {len(cuisines)} cuisines with {total_recipes} total recipes")
            
            return {
                "cuisines": cuisines,
                "total_cuisines": len(cuisines),
                "total_recipes": total_recipes
            }
            
        except Exception as e:
            logger.error(f"Error getting all cuisines: {str(e)}")
            raise
    
    async def get_cuisine_collection(
        self,
        cuisine_type: str,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Dict:
        """
        Get all recipes for a specific cuisine type
        
        Args:
            cuisine_type: Type of cuisine (e.g., "italian", "mexican")
            user_id: Optional user ID to filter
            skip: Pagination offset
            limit: Number of recipes to return
            
        Returns:
            Dictionary with cuisine collection data
        """
        try:
            # Build query
            query = {"cuisine_type": cuisine_type.lower()}
            if user_id:
                query["user_id"] = user_id
            
            # Get total count
            total_count = await self.collection.count_documents(query)
            
            # Get recipes
            recipes_cursor = self.collection.find(query).skip(skip).limit(limit).sort("timestamp", -1)
            recipes_raw = await recipes_cursor.to_list(length=limit)
            
            # Format recipes
            recipes = []
            for recipe_doc in recipes_raw:
                recipes.append({
                    "id": str(recipe_doc["_id"]),
                    "title": recipe_doc["generated_recipe"]["title"],
                    "estimated_time": recipe_doc["generated_recipe"]["estimated_time"],
                    "difficulty": recipe_doc["generated_recipe"]["difficulty"],
                    "servings": recipe_doc["generated_recipe"].get("servings", 4),
                    "ingredients": recipe_doc["ingredients"],
                    "created_at": recipe_doc["timestamp"].isoformat(),
                    "is_favorite": recipe_doc.get("is_favorite", False)
                })
            
            # Get statistics for this cuisine
            stats = await self._get_cuisine_stats(cuisine_type, user_id)
            
            logger.info(f"Retrieved {len(recipes)} recipes for cuisine: {cuisine_type}")
            
            return {
                "cuisine_type": cuisine_type,
                "total_recipes": total_count,
                "recipes": recipes,
                "popular_ingredients": stats.get("popular_ingredients", []),
                "avg_cooking_time": stats.get("avg_cooking_time"),
                "difficulty_breakdown": stats.get("difficulty_breakdown", {}),
                "page_info": {
                    "current_page": (skip // limit) + 1 if limit > 0 else 1,
                    "page_size": limit,
                    "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cuisine collection for {cuisine_type}: {str(e)}")
            raise
    
    async def _get_cuisine_stats(
        self,
        cuisine_type: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Get statistics for a specific cuisine
        
        Args:
            cuisine_type: Type of cuisine
            user_id: Optional user ID to filter
            
        Returns:
            Dictionary with cuisine statistics
        """
        try:
            query = {"cuisine_type": cuisine_type.lower()}
            if user_id:
                query["user_id"] = user_id
            
            # Get all recipes for this cuisine
            recipes = await self.collection.find(query).to_list(length=None)
            
            if not recipes:
                return {}
            
            # Calculate statistics
            all_ingredients = []
            cooking_times = []
            difficulties = {"easy": 0, "medium": 0, "hard": 0}
            
            for recipe in recipes:
                # Collect ingredients
                all_ingredients.extend(recipe.get("ingredients", []))
                
                # Collect cooking times
                time = recipe["generated_recipe"].get("estimated_time", 0)
                if time > 0:
                    cooking_times.append(time)
                
                # Count difficulties
                difficulty = recipe["generated_recipe"].get("difficulty", "medium")
                difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
            
            # Get most popular ingredients (top 10)
            ingredient_counts = Counter(all_ingredients)
            popular_ingredients = [ing for ing, _ in ingredient_counts.most_common(10)]
            
            # Calculate average cooking time
            avg_time = sum(cooking_times) / len(cooking_times) if cooking_times else None
            
            return {
                "popular_ingredients": popular_ingredients,
                "avg_cooking_time": round(avg_time, 1) if avg_time else None,
                "difficulty_breakdown": difficulties
            }
            
        except Exception as e:
            logger.error(f"Error calculating cuisine stats: {str(e)}")
            return {}
    
    async def get_cuisine_detailed_stats(
        self,
        cuisine_type: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Get detailed statistics for a cuisine type
        
        Args:
            cuisine_type: Type of cuisine
            user_id: Optional user ID to filter
            
        Returns:
            Detailed statistics dictionary
        """
        try:
            query = {"cuisine_type": cuisine_type.lower()}
            if user_id:
                query["user_id"] = user_id
            
            # Get all recipes
            recipes = await self.collection.find(query).to_list(length=None)
            
            if not recipes:
                return {
                    "cuisine_type": cuisine_type,
                    "total_recipes": 0,
                    "message": f"No recipes found for {cuisine_type} cuisine"
                }
            
            # Basic stats
            total_recipes = len(recipes)
            unique_users = len(set(str(r["user_id"]) for r in recipes))
            
            # Ingredient analysis
            all_ingredients = []
            for recipe in recipes:
                all_ingredients.extend(recipe.get("ingredients", []))
            
            ingredient_counts = Counter(all_ingredients)
            most_used_ingredients = [ing for ing, _ in ingredient_counts.most_common(10)]
            
            # Difficulty distribution
            difficulties = {"easy": 0, "medium": 0, "hard": 0}
            for recipe in recipes:
                difficulty = recipe["generated_recipe"].get("difficulty", "medium")
                difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
            
            # Time distribution
            time_distribution = {
                "under_30": 0,
                "30_60": 0,
                "over_60": 0
            }
            
            cooking_times = []
            for recipe in recipes:
                time = recipe["generated_recipe"].get("estimated_time", 0)
                if time > 0:
                    cooking_times.append(time)
                    if time < 30:
                        time_distribution["under_30"] += 1
                    elif time <= 60:
                        time_distribution["30_60"] += 1
                    else:
                        time_distribution["over_60"] += 1
            
            # Calculate average rating (if ratings exist)
            ratings = [r.get("rating", 0) for r in recipes if r.get("rating", 0) > 0]
            avg_rating = sum(ratings) / len(ratings) if ratings else None
            
            # Recent activity
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            created_this_week = sum(1 for r in recipes if r["timestamp"] >= week_ago)
            created_this_month = sum(1 for r in recipes if r["timestamp"] >= month_ago)
            
            return {
                "cuisine_type": cuisine_type,
                "total_recipes": total_recipes,
                "total_users": unique_users,
                "avg_rating": round(avg_rating, 2) if avg_rating else None,
                "most_used_ingredients": most_used_ingredients,
                "difficulty_distribution": difficulties,
                "time_distribution": time_distribution,
                "created_this_week": created_this_week,
                "created_this_month": created_this_month,
                "avg_cooking_time": round(sum(cooking_times) / len(cooking_times), 1) if cooking_times else None
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed cuisine stats: {str(e)}")
            raise
    
    async def search_by_cuisine_and_ingredients(
        self,
        cuisine_type: str,
        ingredients: List[str],
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search recipes by cuisine type and ingredients
        
        Args:
            cuisine_type: Type of cuisine
            ingredients: List of ingredients to search for
            user_id: Optional user ID to filter
            limit: Maximum number of results
            
        Returns:
            List of matching recipes
        """
        try:
            # Build query
            query = {
                "cuisine_type": cuisine_type.lower(),
                "ingredients": {"$all": [ing.lower() for ing in ingredients]}
            }
            
            if user_id:
                query["user_id"] = user_id
            
            # Execute search
            recipes_cursor = self.collection.find(query).limit(limit).sort("timestamp", -1)
            recipes_raw = await recipes_cursor.to_list(length=limit)
            
            # Format results
            recipes = []
            for recipe_doc in recipes_raw:
                recipes.append({
                    "id": str(recipe_doc["_id"]),
                    "title": recipe_doc["generated_recipe"]["title"],
                    "estimated_time": recipe_doc["generated_recipe"]["estimated_time"],
                    "difficulty": recipe_doc["generated_recipe"]["difficulty"],
                    "ingredients": recipe_doc["ingredients"],
                    "cuisine_type": recipe_doc["cuisine_type"],
                    "created_at": recipe_doc["timestamp"].isoformat()
                })
            
            logger.info(f"Found {len(recipes)} recipes for {cuisine_type} with ingredients: {ingredients}")
            
            return recipes
            
        except Exception as e:
            logger.error(f"Error searching by cuisine and ingredients: {str(e)}")
            raise
    
    async def get_trending_cuisines(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get trending cuisines based on recent recipe creation
        
        Args:
            days: Number of days to look back
            limit: Maximum number of cuisines to return
            
        Returns:
            List of trending cuisines
        """
        try:
            # Calculate date threshold
            date_threshold = datetime.utcnow() - timedelta(days=days)
            
            # Aggregation pipeline
            pipeline = [
                {"$match": {
                    "timestamp": {"$gte": date_threshold},
                    "cuisine_type": {"$exists": True, "$ne": None}
                }},
                {"$group": {
                    "_id": "$cuisine_type",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            
            results = await self.collection.aggregate(pipeline).to_list(length=limit)
            
            # Format response
            trending = []
            for item in results:
                cuisine_type = item["_id"].lower()
                metadata = self.CUISINE_INFO.get(cuisine_type, {
                    "emoji": "🍽️",
                    "description": f"{cuisine_type.title()} cuisine"
                })
                
                trending.append({
                    "cuisine_type": cuisine_type,
                    "recipe_count": item["count"],
                    "emoji": metadata.get("emoji", "🍽️"),
                    "description": metadata.get("description", "")
                })
            
            logger.info(f"Found {len(trending)} trending cuisines in last {days} days")
            
            return trending
            
        except Exception as e:
            logger.error(f"Error getting trending cuisines: {str(e)}")
            raise