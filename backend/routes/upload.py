"""
Upload routes - image upload and ingredient detection
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Dict

from models.user import UserResponse
from dependencies import get_current_user
from services.ingredient_service import ingredient_service
from services.cloudinary_service import cloudinary_service
from services.storage_service import file_storage
from utils.validators import validate_image_file, sanitize_filename
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/upload", tags=["Image Upload"])


@router.post("/", response_model=Dict)
async def upload_image(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Upload an image and detect ingredients
    
    - **file**: Image file (JPG, PNG, WEBP, max 10MB)
    
    Returns detected ingredients with confidence scores and image URLs
    """
    try:
        # Validate file
        is_valid, error_message = await validate_image_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Read file content
        content = await file.read()
        
        # Save to temporary storage
        safe_filename = sanitize_filename(file.filename)
        temp_path = await file_storage.save_temp_file(content, safe_filename)
        
        logger.info(f"Image uploaded by user {current_user.email}: {safe_filename}")
        
        # Upload to Cloudinary (non-blocking, continues even if fails)
        image_urls = None
        try:
            image_upload_result = await cloudinary_service.upload_image(
                image_bytes=content,
                user_id=current_user.id,
                filename=safe_filename,
                folder="ingredient_images"
            )
            
            if image_upload_result:
                image_urls = {
                    "url": image_upload_result["secure_url"],
                    "thumbnail_url": image_upload_result["thumbnail_url"],
                    "medium_url": image_upload_result["medium_url"],
                    "public_id": image_upload_result["public_id"]
                }
                logger.info(f"✅ Image uploaded to Cloudinary: {image_urls['url']}")
            else:
                logger.warning("⚠️  Cloudinary upload failed - continuing without image URL")
        except Exception as cloudinary_error:
            logger.error(f"Cloudinary upload error (non-critical): {str(cloudinary_error)}")
        
        # Detect ingredients
        detection_results = await ingredient_service.detect_ingredients(content)
        
        # Clean up temp file
        await file_storage.delete_file(temp_path)
        
        response = {
            "status": "success",
            "filename": file.filename,
            "ingredients": detection_results["ingredients"],
            "confidence": detection_results["confidence"],
            "source": detection_results["source"],
            "details": {
                "local_detected": detection_results["local_detected"],
                "openai_detected": detection_results["openai_detected"],
                "total_unique": detection_results["total_unique"]
            },
            "message": "Please review and verify the detected ingredients before generating a recipe",
            "requires_verification": True,
            "next_step": "Review ingredients, add/remove items, then call POST /recipes/generate",
            "image_urls": image_urls  # Include image URLs in response
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the image"
        )


@router.post("/multi", response_model=Dict)
async def upload_multiple_images(
    files: list[UploadFile] = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Upload multiple images and detect ingredients from all of them
    
    - **files**: List of image files (max 5 images)
    
    Returns combined detected ingredients with image URLs
    """
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 images allowed per upload"
        )
    
    try:
        all_ingredients = []
        total_confidence = 0.0
        results_details = []
        image_urls_list = []
        
        for file in files:
            # Validate each file
            is_valid, error_message = await validate_image_file(file)
            if not is_valid:
                logger.warning(f"Skipping invalid file {file.filename}: {error_message}")
                continue
            
            # Read and process
            content = await file.read()
            
            # Upload to Cloudinary
            image_urls = None
            try:
                safe_filename = sanitize_filename(file.filename)
                image_upload_result = await cloudinary_service.upload_image(
                    image_bytes=content,
                    user_id=current_user.id,
                    filename=safe_filename,
                    folder="ingredient_images"
                )
                
                if image_upload_result:
                    image_urls = {
                        "url": image_upload_result["secure_url"],
                        "thumbnail_url": image_upload_result["thumbnail_url"],
                        "medium_url": image_upload_result["medium_url"],
                        "public_id": image_upload_result["public_id"],
                        "filename": file.filename
                    }
                    image_urls_list.append(image_urls)
            except Exception as cloudinary_error:
                logger.error(f"Cloudinary upload error for {file.filename}: {str(cloudinary_error)}")
            
            # Detect ingredients
            detection_results = await ingredient_service.detect_ingredients(content)
            
            # Collect results
            all_ingredients.extend(detection_results["ingredients"])
            total_confidence += detection_results["confidence"]
            results_details.append({
                "filename": file.filename,
                "ingredients": detection_results["ingredients"],
                "confidence": detection_results["confidence"],
                "image_urls": image_urls
            })
        
        # Remove duplicates (case-insensitive)
        unique_ingredients = []
        seen = set()
        for ing in all_ingredients:
            ing_lower = ing.lower()
            if ing_lower not in seen:
                unique_ingredients.append(ing)
                seen.add(ing_lower)
        
        avg_confidence = total_confidence / len(files) if files else 0.0
        
        logger.info(f"Multi-upload by {current_user.email}: {len(unique_ingredients)} unique ingredients from {len(files)} images")
        
        return {
            "status": "success",
            "total_images": len(files),
            "ingredients": unique_ingredients,
            "average_confidence": round(avg_confidence, 2),
            "details": results_details,
            "image_urls_list": image_urls_list,  # All uploaded images
            "message": "Please review and verify the detected ingredients before generating a recipe",
            "requires_verification": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the images"
        )


@router.post("/verify", response_model=Dict)
async def verify_detected_ingredients(
    original_ingredients: list[str],
    verified_ingredients: list[str],
    added_ingredients: list[str] = [],
    removed_ingredients: list[str] = [],
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Submit user verification/corrections of detected ingredients
    
    This endpoint tracks user feedback to improve detection accuracy over time.
    
    - **original_ingredients**: What the AI detected
    - **verified_ingredients**: Final list after user review
    - **added_ingredients**: Items user manually added (AI missed these)
    - **removed_ingredients**: Items user removed (AI wrongly detected)
    
    Returns confirmation and statistics
    """
    try:
        # Calculate accuracy metrics
        total_original = len(original_ingredients)
        total_verified = len(verified_ingredients)
        correctly_detected = len(set(original_ingredients) & set(verified_ingredients))
        
        accuracy = (correctly_detected / total_original * 100) if total_original > 0 else 0
        
        # Log for analytics (in production, save to database)
        logger.info(f"User feedback from {current_user.email}:")
        logger.info(f"  - AI detected: {total_original} items")
        logger.info(f"  - User verified: {total_verified} items")
        logger.info(f"  - Accuracy: {accuracy:.1f}%")
        logger.info(f"  - Added by user: {added_ingredients}")
        logger.info(f"  - Removed by user: {removed_ingredients}")
        
        # TODO: In production, save this feedback to improve the model
        # await db.ingredient_feedback.insert_one({
        #     "user_id": current_user.id,
        #     "original": original_ingredients,
        #     "verified": verified_ingredients,
        #     "added": added_ingredients,
        #     "removed": removed_ingredients,
        #     "accuracy": accuracy,
        #     "timestamp": datetime.utcnow()
        # })
        
        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "statistics": {
                "original_count": total_original,
                "verified_count": total_verified,
                "correctly_detected": correctly_detected,
                "accuracy_percentage": round(accuracy, 1),
                "items_added": len(added_ingredients),
                "items_removed": len(removed_ingredients)
            },
            "verified_ingredients": verified_ingredients,
            "next_step": "Use these verified ingredients to generate a recipe"
        }
        
    except Exception as e:
        logger.error(f"Error processing ingredient verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing verification"
        )