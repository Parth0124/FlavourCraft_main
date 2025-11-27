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
import time
import os

from utils.logger import get_logger

# MLOps imports - with lazy loading to avoid circular imports
_mlflow_manager = None
_prometheus_metrics = None
_model_monitor = None


def _get_mlflow():
    global _mlflow_manager
    if _mlflow_manager is None:
        from services.mlflow_service import mlflow_manager
        _mlflow_manager = mlflow_manager
    return _mlflow_manager


def _get_prometheus():
    global _prometheus_metrics
    if _prometheus_metrics is None:
        from services.prometheus_service import prometheus_metrics
        _prometheus_metrics = prometheus_metrics
    return _prometheus_metrics


def _get_monitor():
    global _model_monitor
    if _model_monitor is None:
        from services.model_monitoring_service import model_monitor
        _model_monitor = model_monitor
    return _model_monitor


logger = get_logger(__name__)


class IngredientDetectionService:
    """Service for detecting ingredients from images"""
    
    def __init__(self):
        # Read credentials directly from environment variables
        self.use_local_models = os.getenv('USE_LOCAL_MODELS', 'true').lower() == 'true'
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.prometheus_enabled = os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true'
        self.enable_drift_detection = os.getenv('ENABLE_DRIFT_DETECTION', 'true').lower() == 'true'
        
        self.local_model = None
        self.clip_processor = None
        self.openai_client = None
        
        # Initialize local models first (if enabled)
        if self.use_local_models:
            self._initialize_local_model()
        
        # Initialize OpenAI as fallback
        if self.openai_api_key:
            self._initialize_openai_client()
    
    def _initialize_local_model(self):
        """
        Initialize CLIP model for zero-shot ingredient classification
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
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    
    async def detect_ingredients_local(
        self, 
        image_bytes: bytes
    ) -> Tuple[List[str], float]:
        """
        Detect ingredients using CLIP zero-shot classification
        """
        if not self.local_model or not self.clip_processor:
            logger.info("Local CLIP model not available, skipping local detection")
            return [], 0.0
        
        start_time = time.time()
        ingredients = []
        scores = []
        avg_confidence = 0.0
        
        # STEP 1: DETECTION (Critical - must complete)
        try:
            # Open and prepare image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Prepare inputs for CLIP
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
                    logits_per_image = outputs.logits_per_image
                    probs = logits_per_image.softmax(dim=1)
                return probs.cpu().numpy()[0]
            
            probabilities = await loop.run_in_executor(None, run_clip)
            
            # Get top predictions
            confidence_threshold = 0.15  # 15% confidence minimum
            
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
            
            processing_time = time.time() - start_time
            
            if ingredients:
                logger.info(f"🎯 CLIP detected {len(ingredients)} ingredients: {', '.join(ingredients[:5])}...")
                logger.info(f"   Average confidence: {avg_confidence:.2%}")
            else:
                logger.info("⚠️  CLIP did not detect any ingredients above confidence threshold")
                
        except Exception as e:
            logger.error(f"Error in CLIP ingredient detection: {str(e)}")
            processing_time = time.time() - start_time
            return [], 0.0
        
        # STEP 2: MLOPS TRACKING (Non-critical - can fail safely)
        if self.prometheus_enabled:
            try:
                prometheus = _get_prometheus()
                prometheus.track_ingredient_detection(
                    model_name="clip_ingredient_detector",
                    num_ingredients=len(ingredients),
                    confidence_score=avg_confidence,
                    processing_time=processing_time,
                    success=len(ingredients) > 0
                )
                
                monitor = _get_monitor()
                monitor.record_prediction(
                    model_name="clip_ingredient_detector",
                    prediction=ingredients,
                    confidence=avg_confidence,
                    latency=processing_time,
                    input_features={"num_ingredients": len(ingredients)}
                )
                
                mlflow = _get_mlflow()
                mlflow.log_ingredient_detection(
                    ingredients=ingredients,
                    confidence_scores=dict(zip(ingredients, scores)) if ingredients else {},
                    detection_method="clip_local",
                    processing_time=processing_time,
                    image_metadata={"model": "clip-vit-base-patch32"}
                )
                
                logger.debug(f"[MLOps] CLIP detection tracked: {len(ingredients)} ingredients")
                
            except Exception as e:
                # MLOps tracking failed - just log it, don't affect results
                logger.error(f"[MLOps] Tracking failed (non-critical): {str(e)}")
        
        # STEP 3: ALWAYS RETURN DETECTION RESULTS
        return ingredients, avg_confidence
    
    async def detect_ingredients_openai(
        self, 
        image_bytes: bytes
    ) -> Tuple[List[str], float]:
        """
        Detect ingredients using OpenAI Vision API
        """
        if not self.openai_client:
            return [], 0.0
        
        start_time = time.time()
        ingredients = []
        confidence = 0.0
        content = ""
        
        # STEP 1: DETECTION (Critical - must complete)
        try:
            import base64
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Call OpenAI Vision API
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
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
                max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
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
            
            processing_time = time.time() - start_time
            
            logger.info(f"OpenAI detected {len(ingredients)} ingredients")
            
        except Exception as e:
            logger.error(f"Error in OpenAI ingredient detection: {str(e)}")
            processing_time = time.time() - start_time
            return [], 0.0
        
        # STEP 2: MLOPS TRACKING (Non-critical - can fail safely)
        if self.prometheus_enabled:
            try:
                prometheus = _get_prometheus()
                prometheus.track_ingredient_detection(
                    model_name="openai_vision",
                    num_ingredients=len(ingredients),
                    confidence_score=confidence,
                    processing_time=processing_time,
                    success=len(ingredients) > 0
                )
                
                prometheus.track_openai_api_call(
                    operation="vision_ingredient_detection",
                    status="success",
                    latency=processing_time,
                    tokens_used=len(content.split()) if content else 0,
                    cost_estimate=0.001
                )
                
                monitor = _get_monitor()
                monitor.record_prediction(
                    model_name="openai_vision",
                    prediction=ingredients,
                    confidence=confidence,
                    latency=processing_time,
                    input_features={"num_ingredients": len(ingredients)}
                )
                
                mlflow = _get_mlflow()
                mlflow.log_ingredient_detection(
                    ingredients=ingredients,
                    confidence_scores={ing: confidence for ing in ingredients},
                    detection_method="openai_vision",
                    processing_time=processing_time,
                    image_metadata={"model": self.openai_model}
                )
                
                logger.debug(f"[MLOps] OpenAI detection tracked: {len(ingredients)} ingredients")
                
            except Exception as e:
                # MLOps tracking failed - just log it, don't affect results
                logger.error(f"[MLOps] Tracking failed (non-critical): {str(e)}")
        
        # STEP 3: ALWAYS RETURN DETECTION RESULTS
        return ingredients, confidence
    
    def merge_detection_results(
        self,
        local_results: Tuple[List[str], float],
        openai_results: Tuple[List[str], float]
    ) -> Dict[str, any]:
        """
        Merge results from local and OpenAI models
        """
        from utils.validators import validate_ingredients
        
        local_ingredients, local_confidence = local_results
        openai_ingredients, openai_confidence = openai_results
        
        # Combine and deduplicate ingredients
        all_ingredients = local_ingredients + openai_ingredients
        unique_ingredients = validate_ingredients(all_ingredients)
        
        # Calculate weighted confidence
        if local_confidence > 0 and openai_confidence > 0:
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
        """
        pipeline_start = time.time()
        
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
        
        pipeline_time = time.time() - pipeline_start
        
        # Track full pipeline (non-critical)
        if self.prometheus_enabled:
            try:
                prometheus = _get_prometheus()
                prometheus.track_ingredient_detection(
                    model_name="ingredient_detection_pipeline",
                    num_ingredients=merged_results['total_unique'],
                    confidence_score=merged_results['confidence'],
                    processing_time=pipeline_time,
                    success=merged_results['total_unique'] > 0
                )
                
                # Check for drift
                if self.enable_drift_detection:
                    monitor = _get_monitor()
                    drift_result = monitor.check_drift(
                        model_name="ingredient_detection_pipeline",
                        current_metrics={
                            "confidence": merged_results['confidence'],
                            "latency": pipeline_time
                        }
                    )
                    if drift_result and drift_result.get('drift_detected'):
                        logger.warning(f"⚠️  Model drift detected! Score: {drift_result.get('drift_score', 0):.3f}")
                        merged_results['drift_detected'] = True
                        merged_results['drift_score'] = drift_result.get('drift_score', 0)
                
                logger.info(f"[MLOps] Full detection pipeline tracked: {merged_results['total_unique']} ingredients, {pipeline_time:.2f}s")
                
            except Exception as e:
                logger.error(f"[MLOps] Pipeline tracking failed (non-critical): {str(e)}")
                # Don't affect results
        
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