"""
Ingredient detection service - handles image processing and ingredient identification

Strategy:
1. Local Open-Source Models (Primary) - FREE, fast, reasonable accuracy
   - Uses CLIP for zero-shot classification of common ingredients
2. OpenAI Vision API (Fallback) - High accuracy when local confidence is low
3. Hybrid approach for best results

Models Used:
- CLIP (openai/clip-vit-base-patch32) - Zero-shot image classification
- Can detect ingredients by comparing image to text labels
"""
from typing import List, Dict, Tuple
import io
from PIL import Image
import asyncio
import torch
import numpy as np

from config import get_settings
from utils.logger import get_logger
from utils.validators import validate_ingredients

settings = get_settings()
logger = get_logger(__name__)


class IngredientDetectionService:
    """Service for detecting ingredients from images"""
    
    def __init__(self):
        self.use_local_models = settings.USE_LOCAL_MODELS
        self.local_model = None
        self.clip_processor = None
        self.openai_client = None
        
        # Initialize local models first (if enabled)
        if self.use_local_models:
            self._initialize_local_model()
        
        # Initialize OpenAI as fallback
        if settings.OPENAI_API_KEY:
            self._initialize_openai_client()
    
    def _initialize_local_model(self):
        """
        Initialize CLIP model for zero-shot ingredient classification
        
        CLIP can classify images against text descriptions, making it perfect
        for ingredient detection. We'll use a predefined list of common ingredients.
        
        Model: openai/clip-vit-base-patch32
        Size: ~600MB
        Accuracy: 60-75% for common ingredients
        Speed: 1-2s on CPU, <0.5s on GPU
        """
        try:
            from transformers import CLIPProcessor, CLIPModel
            
            logger.info("Initializing CLIP model for ingredient detection...")
            
            # Check if CUDA is available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")
            
            # Load CLIP model and processor
            model_name = "openai/clip-vit-base-patch32"
            logger.info(f"Loading model: {model_name} (this may take a minute on first run...)")
            
            self.clip_processor = CLIPProcessor.from_pretrained(model_name)
            self.local_model = CLIPModel.from_pretrained(model_name).to(self.device)
            
            logger.info("✅ CLIP model initialized successfully!")
            logger.info(f"Device: {self.device}, Model: {model_name}")
            
            # Common ingredients for zero-shot classification
            self.ingredient_labels = [
                # Vegetables
                "tomatoes", "onions", "garlic", "potatoes", "carrots", "bell peppers",
                "green beans", "broccoli", "cauliflower", "spinach", "lettuce", "cabbage",
                "cucumber", "zucchini", "eggplant", "celery", "mushrooms", "corn",
                
                # Fruits
                "apples", "bananas", "oranges", "lemons", "limes", "strawberries",
                "blueberries", "grapes", "watermelon", "pineapple", "mango", "avocado",
                
                # Proteins
                "chicken", "beef", "pork", "fish", "shrimp", "eggs", "tofu",
                "salmon", "tuna", "bacon", "ground meat",
                
                # Dairy
                "milk", "cheese", "butter", "yogurt", "cream", "mozzarella", "cheddar",
                
                # Grains & Staples
                "rice", "pasta", "bread", "flour", "noodles", "quinoa", "oats",
                
                # Herbs & Spices
                "basil", "cilantro", "parsley", "rosemary", "thyme", "oregano",
                "ginger", "chili peppers", "black pepper", "salt",
                
                # Oils & Condiments
                "olive oil", "vegetable oil", "soy sauce", "vinegar", "ketchup",
                "mayonnaise", "mustard", "honey",
                
                # Canned & Packaged
                "canned tomatoes", "tomato sauce", "beans", "chickpeas", "coconut milk"
            ]
            
            logger.info(f"Loaded {len(self.ingredient_labels)} ingredient categories for detection")
            
        except Exception as e:
            logger.error(f"Failed to initialize CLIP model: {str(e)}")
            logger.info("Will fall back to OpenAI Vision API if available")
            self.local_model = None
            self.clip_processor = None
    
    def _initialize_openai_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import AsyncOpenAI
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    
    async def detect_ingredients_local(
        self, 
        image_bytes: bytes
    ) -> Tuple[List[str], float]:
        """
        Detect ingredients using CLIP zero-shot classification
        
        CLIP compares the image against text descriptions of ingredients
        and returns similarity scores. We select ingredients with high confidence.
        
        Args:
            image_bytes: Image content as bytes
            
        Returns:
            Tuple of (ingredients list, confidence score)
        """
        if not self.local_model or not self.clip_processor:
            logger.info("Local CLIP model not available, skipping local detection")
            return [], 0.0
        
        try:
            # Open and prepare image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Prepare inputs for CLIP
            # We'll compare the image against all ingredient labels
            inputs = self.clip_processor(
                text=self.ingredient_labels,
                images=image,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            # Run inference in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def run_clip():
                with torch.no_grad():
                    outputs = self.local_model(**inputs)
                    # Get similarity scores between image and each text label
                    logits_per_image = outputs.logits_per_image
                    probs = logits_per_image.softmax(dim=1)
                return probs.cpu().numpy()[0]
            
            probabilities = await loop.run_in_executor(None, run_clip)
            
            # Get top predictions
            # We'll use a threshold to only include confident predictions
            confidence_threshold = 0.15  # 15% confidence minimum
            
            ingredients = []
            scores = []
            
            for idx, prob in enumerate(probabilities):
                if prob > confidence_threshold:
                    ingredient = self.ingredient_labels[idx]
                    ingredients.append(ingredient)
                    scores.append(float(prob))
            
            # Sort by confidence
            if ingredients:
                sorted_pairs = sorted(zip(ingredients, scores), key=lambda x: x[1], reverse=True)
                ingredients = [ing for ing, _ in sorted_pairs[:10]]  # Top 10 max
                avg_confidence = sum(scores) / len(scores)
            else:
                avg_confidence = 0.0
            
            if ingredients:
                logger.info(f"🎯 CLIP detected {len(ingredients)} ingredients: {', '.join(ingredients[:5])}...")
                logger.info(f"   Average confidence: {avg_confidence:.2%}")
            else:
                logger.info("⚠️  CLIP did not detect any ingredients above confidence threshold")
            
            return ingredients, avg_confidence
            
        except Exception as e:
            logger.error(f"Error in CLIP ingredient detection: {str(e)}")
            return [], 0.0
    
    async def detect_ingredients_openai(
        self, 
        image_bytes: bytes
    ) -> Tuple[List[str], float]:
        """
        Detect ingredients using OpenAI Vision API
        
        Args:
            image_bytes: Image content as bytes
            
        Returns:
            Tuple of (ingredients list, confidence score)
        """
        if not self.openai_client:
            return [], 0.0
        
        try:
            import base64
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Call OpenAI Vision API
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this image and list all food ingredients you can identify. 
                                Return ONLY a comma-separated list of ingredients, nothing else. 
                                Be specific and include quantities if visible.
                                Example: tomato, onion, garlic, rice, chicken"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Split by comma and clean
            ingredients = [
                ing.strip() 
                for ing in content.split(',') 
                if ing.strip()
            ]
            
            # OpenAI typically has high confidence, use 0.85 as baseline
            confidence = 0.85
            
            logger.info(f"OpenAI detected {len(ingredients)} ingredients")
            
            return ingredients, confidence
            
        except Exception as e:
            logger.error(f"Error in OpenAI ingredient detection: {str(e)}")
            return [], 0.0
    
    def merge_detection_results(
        self,
        local_results: Tuple[List[str], float],
        openai_results: Tuple[List[str], float]
    ) -> Dict[str, any]:
        """
        Merge results from local and OpenAI models
        
        Args:
            local_results: Tuple of (ingredients, confidence) from local model
            openai_results: Tuple of (ingredients, confidence) from OpenAI
            
        Returns:
            Dictionary with merged results
        """
        local_ingredients, local_confidence = local_results
        openai_ingredients, openai_confidence = openai_results
        
        # Combine and deduplicate ingredients
        all_ingredients = local_ingredients + openai_ingredients
        unique_ingredients = validate_ingredients(all_ingredients)
        
        # Calculate weighted confidence
        if local_confidence > 0 and openai_confidence > 0:
            # Both models provided results
            total_confidence = (local_confidence + openai_confidence) / 2
            source = "hybrid"
        elif openai_confidence > 0:
            total_confidence = openai_confidence
            source = "openai"
        elif local_confidence > 0:
            total_confidence = local_confidence
            source = "local"
        else:
            total_confidence = 0.0
            source = "none"
        
        return {
            "ingredients": unique_ingredients,
            "confidence": round(total_confidence, 2),
            "source": source,
            "local_detected": len(local_ingredients),
            "openai_detected": len(openai_ingredients),
            "total_unique": len(unique_ingredients)
        }
    
    async def detect_ingredients(self, image_bytes: bytes) -> Dict[str, any]:
        """
        Main method to detect ingredients from image
        
        Strategy (OPEN-SOURCE FIRST):
        1. Try local CLIP model first (FREE, 60-75% accuracy)
        2. If confidence is low (<40%), use OpenAI as backup
        3. If no OpenAI key, return local results regardless
        4. Merge results if both are used
        
        Args:
            image_bytes: Image content as bytes
            
        Returns:
            Dictionary with detection results
        """
        logger.info("🚀 Starting ingredient detection with OPEN-SOURCE MODELS...")
        
        local_results = ([], 0.0)
        openai_results = ([], 0.0)
        
        # Step 1: Try local CLIP model first
        if self.local_model and self.use_local_models:
            logger.info("📊 Step 1: Using local CLIP model (FREE)")
            local_results = await self.detect_ingredients_local(image_bytes)
            local_ingredients, local_confidence = local_results
            
            logger.info(f"   ✓ Local model found {len(local_ingredients)} ingredients")
            logger.info(f"   ✓ Confidence: {local_confidence:.2%}")
            
            # Step 2: Decide if we need OpenAI backup
            if local_confidence >= 0.40 and len(local_ingredients) > 0:
                # Good confidence - use local results
                logger.info("   ✅ Local confidence is GOOD (≥40%) - using local results!")
                logger.info("   💰 Saved $0.001 by not using OpenAI!")
                openai_results = ([], 0.0)
                
            elif self.openai_client:
                # Low confidence - enhance with OpenAI
                logger.info(f"   ⚠️  Local confidence is LOW (<40%) - enhancing with OpenAI...")
                openai_results = await self.detect_ingredients_openai(image_bytes)
                openai_ingredients, openai_confidence = openai_results
                logger.info(f"   ✓ OpenAI found {len(openai_ingredients)} ingredients")
                
            else:
                # No OpenAI available - use local results anyway
                logger.warning("   ⚠️  Low confidence but no OpenAI key - using local results")
                logger.info("   💡 Tip: Add OPENAI_API_KEY for better accuracy on unclear images")
                
        elif self.openai_client:
            # No local model - use OpenAI only
            logger.info("📊 Step 1: Local models disabled - using OpenAI Vision")
            openai_results = await self.detect_ingredients_openai(image_bytes)
            
        else:
            # No models available at all
            logger.error("❌ No detection models available! Enable local models or add OpenAI key")
            return {
                "ingredients": [],
                "confidence": 0.0,
                "source": "none",
                "local_detected": 0,
                "openai_detected": 0,
                "total_unique": 0,
                "message": "No AI models configured. Please set USE_LOCAL_MODELS=true or add OPENAI_API_KEY"
            }
        
        # Merge results
        merged_results = self.merge_detection_results(local_results, openai_results)
        
        # Add helpful message if no ingredients detected
        if merged_results['total_unique'] == 0:
            logger.warning("⚠️  No ingredients detected in image")
            merged_results['message'] = "No ingredients detected. Try: 1) Better lighting, 2) Close-up photos, 3) Clear individual ingredients"
        else:
            logger.info(f"✅ Detection complete: {merged_results['total_unique']} unique ingredients found")
            logger.info(f"   Source: {merged_results['source']}")
        
        return merged_results


# Global ingredient detection service instance
ingredient_service = IngredientDetectionService()