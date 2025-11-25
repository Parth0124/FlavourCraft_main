"""
Recipe service - handles AI recipe generation and static recipe management
"""
from typing import List, Optional, Dict
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import time

from models.generated_recipe import (
    GeneratedRecipeRequest,
    GeneratedRecipe,
    GeneratedRecipeDocument,
    GeneratedRecipeResponse
)
from models.static_recipe import StaticRecipe, RecipeFilter
from config import get_settings
from utils.logger import get_logger

# MLOps imports
from services.mlflow_service import mlflow_manager
from services.prometheus_service import prometheus_metrics
from services.model_monitoring_service import model_monitor

settings = get_settings()
logger = get_logger(__name__)


class RecipeGenerationService:
    """Service for AI-powered recipe generation"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.generated_recipes_collection = db.generated_recipes
        self.openai_client = None
        
        if settings.OPENAI_API_KEY:
            self._initialize_openai()
        
        # MLOps: Set baseline for monitoring
        model_monitor.set_baseline("openai_recipe_generator", {
            "confidence_mean": 0.85,
            "confidence_std": 0.10,
            "latency_mean": 3.0,
            "latency_std": 1.0
        })
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import AsyncOpenAI
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized for recipe generation")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {str(e)}")
    
    async def generate_recipe_openai(
        self, 
        request: GeneratedRecipeRequest
    ) -> Optional[GeneratedRecipe]:
        """
        Generate recipe using OpenAI GPT
        
        Args:
            request: Recipe generation request
            
        Returns:
            Generated recipe or None
        """
        # MLOps: Start timing
        start_time = time.time()
        model_name = "openai_recipe_generator"
        
        if not self.openai_client:
            return None
        
        try:
            # Build prompt
            prompt = self._build_generation_prompt(request)
            
            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional chef and recipe creator. Generate creative, delicious, and practical recipes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=0.7
            )
            
            # Parse response
            content = response.choices[0].message.content
            recipe = self._parse_recipe_response(content, request)
            
            logger.info(f"Generated recipe using OpenAI: {recipe.title}")
            
            # MLOps: Track metrics
            processing_time = time.time() - start_time
            complexity = recipe.difficulty
            
            prometheus_metrics.track_recipe_generation(
                model="openai",
                status="success",
                duration=processing_time,
                complexity=complexity
            )
            
            prometheus_metrics.track_openai_api_call(
                operation="recipe_generation",
                status="success",
                latency=processing_time
            )
            
            model_monitor.record_prediction(
                model_name=model_name,
                prediction=recipe.title,
                confidence=0.85,  # OpenAI baseline
                latency=processing_time,
                input_features={
                    "num_ingredients": len(request.ingredients),
                    "has_dietary_prefs": bool(request.dietary_preferences),
                    "has_cuisine_type": bool(request.cuisine_type)
                }
            )
            
            mlflow_manager.log_recipe_generation(
                recipe_title=recipe.title,
                ingredients_used=request.ingredients,
                generation_model="openai_gpt",
                generation_time=processing_time,
                recipe_complexity=complexity
            )
            
            # Check for drift
            drift_result = model_monitor.detect_drift(model_name=model_name, drift_type="latency")
            if drift_result.get("drift_detected"):
                logger.warning(f"[MLOps] Drift detected in recipe generation: {drift_result['drift_score']:.4f}")
            
            logger.info(f"[MLOps] Recipe generation tracked: '{recipe.title}', {processing_time:.2f}s")
            
            return recipe
            
        except Exception as e:
            # MLOps: Track error
            processing_time = time.time() - start_time
            
            prometheus_metrics.track_recipe_generation(
                model="openai",
                status="error",
                duration=processing_time,
                complexity="unknown"
            )
            
            prometheus_metrics.track_openai_api_call(
                operation="recipe_generation",
                status="error",
                latency=processing_time
            )
            
            prometheus_metrics.track_model_error(
                model_name=model_name,
                error_type=type(e).__name__
            )
            
            logger.error(f"Error generating recipe with OpenAI: {str(e)}")
            logger.error(f"[MLOps] Recipe generation error tracked: {e}")
            return None
    
    def _build_generation_prompt(self, request: GeneratedRecipeRequest) -> str:
        """Build prompt for recipe generation"""
        ingredients_str = ", ".join(request.ingredients)
        
        prompt = f"""Create a recipe using these ingredients: {ingredients_str}

Requirements:
"""
        
        if request.dietary_preferences:
            dietary_str = ", ".join(request.dietary_preferences)
            prompt += f"- Must be {dietary_str}\n"
        
        if request.cuisine_type:
            prompt += f"- Cuisine type: {request.cuisine_type}\n"
        
        if request.cooking_time:
            prompt += f"- Maximum cooking time: {request.cooking_time} minutes\n"
        
        if request.difficulty:
            prompt += f"- Difficulty level: {request.difficulty}\n"
        
        prompt += """
Format your response EXACTLY like this:

TITLE: [Recipe name]

STEPS:
1. [First step]
2. [Second step]
3. [Third step]
[... more steps]

TIME: [total time in minutes as a number]

DIFFICULTY: [easy/medium/hard]

TIPS: [Optional cooking tips]

SERVINGS: [number of servings]
"""
        
        return prompt
    
    def _parse_recipe_response(
        self, 
        content: str, 
        request: GeneratedRecipeRequest
    ) -> GeneratedRecipe:
        """Parse OpenAI response into GeneratedRecipe object"""
        lines = content.strip().split('\n')
        
        title = "Custom Recipe"
        steps = []
        estimated_time = request.cooking_time or 30
        difficulty = request.difficulty or "medium"
        tips = None
        servings = 4
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
            elif line.startswith('STEPS:'):
                current_section = 'steps'
            elif line.startswith('TIME:'):
                try:
                    time_str = line.replace('TIME:', '').strip()
                    estimated_time = int(''.join(filter(str.isdigit, time_str)))
                except:
                    pass
            elif line.startswith('DIFFICULTY:'):
                diff = line.replace('DIFFICULTY:', '').strip().lower()
                if diff in ['easy', 'medium', 'hard']:
                    difficulty = diff
            elif line.startswith('TIPS:'):
                tips = line.replace('TIPS:', '').strip()
            elif line.startswith('SERVINGS:'):
                try:
                    servings = int(''.join(filter(str.isdigit, line)))
                except:
                    pass
            elif current_section == 'steps' and line[0].isdigit():
                # Remove step number
                step = line.split('.', 1)[-1].strip()
                if step:
                    steps.append(step)
        
        # Ensure we have at least 3 steps
        if len(steps) < 3:
            steps = [
                f"Prepare all ingredients: {', '.join(request.ingredients)}",
                "Follow the cooking process carefully",
                "Serve hot and enjoy!"
            ]
        
        return GeneratedRecipe(
            title=title,
            steps=steps,
            estimated_time=estimated_time,
            difficulty=difficulty,
            tips=tips,
            servings=servings
        )
    
    async def generate_recipe_fallback(
        self, 
        request: GeneratedRecipeRequest
    ) -> GeneratedRecipe:
        """
        Fallback rule-based recipe generation
        Used when AI services are unavailable
        
        Args:
            request: Recipe generation request
            
        Returns:
            Basic generated recipe
        """
        ingredients_str = ", ".join(request.ingredients)
        
        # Simple template-based generation
        title = f"Custom Recipe with {request.ingredients[0].title()}"
        
        steps = [
            f"Gather all ingredients: {ingredients_str}",
            "Prepare and clean all ingredients thoroughly",
            "Heat a pan or pot with some oil",
            "Add the main ingredients and cook as needed",
            "Season with salt, pepper, and spices to taste",
            "Cook until everything is well done",
            "Serve hot and enjoy your meal!"
        ]
        
        return GeneratedRecipe(
            title=title,
            steps=steps,
            estimated_time=request.cooking_time or 30,
            difficulty=request.difficulty or "medium",
            tips="Adjust cooking time based on your ingredients and preferences",
            servings=4
        )
    
    async def generate_and_save_recipe(
        self,
        user_id: str,
        username: str,
        request: GeneratedRecipeRequest,
        image_urls: Optional[Dict] = None
    ) -> GeneratedRecipeResponse:
        """
        Generate recipe and save to database
        
        Args:
            user_id: User ID
            username: Username
            request: Recipe generation request
            image_urls: Optional dictionary with image URLs from Cloudinary
            
        Returns:
            Generated recipe response
        """
        # MLOps: Start timing full pipeline
        pipeline_start_time = time.time()
        
        # Try OpenAI first
        recipe = await self.generate_recipe_openai(request)
        source = "openai"
        confidence = 0.85
        
        # Fallback to rule-based if OpenAI fails
        if not recipe:
            logger.warning("OpenAI generation failed, using fallback method")
            recipe = await self.generate_recipe_fallback(request)
            source = "fallback"
            confidence = 0.5
        
        # Create document
        recipe_doc = {
            "user_id": user_id,
            "ingredients": request.ingredients,
            "generated_recipe": recipe.model_dump(),
            "source": source,
            "confidence_score": confidence,
            "is_favorite": False,
            "timestamp": datetime.utcnow(),
            "dietary_preferences": request.dietary_preferences or [],
            "cuisine_type": request.cuisine_type,
            "image_urls": image_urls  # Store Cloudinary image URLs
        }
        
        # Save to database
        db_start = time.time()
        result = await self.generated_recipes_collection.insert_one(recipe_doc)
        db_duration = time.time() - db_start
        
        logger.info(f"Recipe saved for user {user_id}: {recipe.title}")
        
        # MLOps: Track full pipeline
        pipeline_duration = time.time() - pipeline_start_time
        
        prometheus_metrics.track_database_operation(
            operation="insert",
            collection="generated_recipes",
            status="success",
            duration=db_duration
        )
        
        mlflow_manager.log_metrics({
            "recipe_generation_pipeline_duration": pipeline_duration,
            "recipe_saved_successfully": 1.0
        })
        
        logger.info(f"[MLOps] Full recipe pipeline tracked: {pipeline_duration:.2f}s")
        
        # Parse image URLs for response
        from models.generated_recipe import ImageUrls
        parsed_image_urls = None
        if image_urls:
            parsed_image_urls = ImageUrls(**image_urls)
        
        return GeneratedRecipeResponse(
            id=str(result.inserted_id),
            recipe=recipe,
            ingredients_used=request.ingredients,
            created_at=recipe_doc["timestamp"],
            is_favorite=False,
            image_urls=parsed_image_urls,
            username=username,
            cuisine_type=request.cuisine_type or "",
            dietary_preferences=request.dietary_preferences or []
        )
    
    async def get_all_generated_recipes(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        Get ALL generated recipes from ALL users (public access)
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of recipes per page
            
        Returns:
            Dictionary with recipes and pagination info
        """
        skip = (page - 1) * page_size
        
        # Get total count
        total = await self.generated_recipes_collection.count_documents({})
        
        # Get recipes
        cursor = self.generated_recipes_collection.find(
            {}
        ).sort("timestamp", -1).skip(skip).limit(page_size)
        
        from models.generated_recipe import ImageUrls
        
        recipes = []
        async for doc in cursor:
            # Get username from users collection
            user = await self.db.users.find_one({"_id": doc["user_id"]})
            username = user.get("username", "Anonymous") if user else "Anonymous"
            
            # Parse image URLs if present
            image_urls = None
            if doc.get("image_urls"):
                image_urls = ImageUrls(**doc["image_urls"])
            
            recipes.append(GeneratedRecipeResponse(
                id=str(doc["_id"]),
                recipe=GeneratedRecipe(**doc["generated_recipe"]),
                ingredients_used=doc["ingredients"],
                created_at=doc["timestamp"],
                is_favorite=doc.get("is_favorite", False),
                image_urls=image_urls,
                username=username,
                cuisine_type=doc.get("cuisine_type", ""),
                dietary_preferences=doc.get("dietary_preferences", [])
            ))
        
        return {
            "recipes": recipes,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def get_user_recipe_history(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict:
        """
        Get user's recipe generation history
        
        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of recipes per page
            
        Returns:
            Dictionary with recipes and pagination info
        """
        skip = (page - 1) * page_size
        
        # Get total count
        total = await self.generated_recipes_collection.count_documents(
            {"user_id": user_id}
        )
        
        # Get username
        user = await self.db.users.find_one({"_id": user_id})
        username = user.get("username", "Anonymous") if user else "Anonymous"
        
        # Get recipes
        cursor = self.generated_recipes_collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).skip(skip).limit(page_size)
        
        from models.generated_recipe import ImageUrls
        
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
                is_favorite=doc.get("is_favorite", False),
                image_urls=image_urls,
                username=username,
                cuisine_type=doc.get("cuisine_type", ""),
                dietary_preferences=doc.get("dietary_preferences", [])
            ))
        
        return {
            "recipes": recipes,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def toggle_favorite(self, recipe_id: str, user_id: str) -> bool:
        """
        Toggle favorite status of a recipe
        
        Args:
            recipe_id: Recipe ID
            user_id: User ID (for security)
            
        Returns:
            True if successful
        """
        try:
            recipe = await self.generated_recipes_collection.find_one({
                "_id": ObjectId(recipe_id),
                "user_id": user_id
            })
            
            if not recipe:
                return False
            
            new_favorite_status = not recipe.get("is_favorite", False)
            
            await self.generated_recipes_collection.update_one(
                {"_id": ObjectId(recipe_id)},
                {"$set": {"is_favorite": new_favorite_status}}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error toggling favorite: {str(e)}")
            return False


class StaticRecipeService:
    """Service for managing static recipes"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.recipes_collection = db.static_recipes
    
    async def search_recipes(
        self,
        filters: RecipeFilter,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        Search static recipes with filters
        
        Args:
            filters: Search filters
            page: Page number
            page_size: Recipes per page
            
        Returns:
            Dictionary with recipes and pagination
        """
        query = {}
        
        # Build query
        if filters.tags:
            query["tags"] = {"$in": filters.tags}
        
        if filters.ingredients:
            query["ingredients"] = {
                "$all": [
                    {"$regex": ing, "$options": "i"} 
                    for ing in filters.ingredients
                ]
            }
        
        if filters.difficulty:
            query["difficulty"] = filters.difficulty
        
        if filters.max_prep_time:
            query["prep_time"] = {"$lte": filters.max_prep_time}
        
        if filters.max_cook_time:
            query["cook_time"] = {"$lte": filters.max_cook_time}
        
        # Get total count
        total = await self.recipes_collection.count_documents(query)
        
        # Get recipes
        skip = (page - 1) * page_size
        cursor = self.recipes_collection.find(query).skip(skip).limit(page_size)
        
        recipes = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            recipes.append(StaticRecipe(**doc))
        
        return {
            "recipes": recipes,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def get_recipe_by_id(self, recipe_id: str) -> Optional[StaticRecipe]:
        """Get static recipe by ID"""
        try:
            doc = await self.recipes_collection.find_one({"_id": ObjectId(recipe_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return StaticRecipe(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting recipe: {str(e)}")
            return None