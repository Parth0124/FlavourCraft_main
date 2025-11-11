"""
Cloudinary image hosting service - FIXED VERSION
Handles uploading and managing images on Cloudinary with proper transformations
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Optional, Dict
from io import BytesIO

from config import get_settings
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class CloudinaryService:
    """Service for managing images on Cloudinary"""
    
    def __init__(self):
        """Initialize Cloudinary configuration"""
        self.is_configured = False
        
        if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
            try:
                cloudinary.config(
                    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                    api_key=settings.CLOUDINARY_API_KEY,
                    api_secret=settings.CLOUDINARY_API_SECRET,
                    secure=True
                )
                self.is_configured = True
                logger.info("✅ Cloudinary configured successfully")
            except Exception as e:
                logger.error(f"Failed to configure Cloudinary: {str(e)}")
                self.is_configured = False
        else:
            logger.warning("⚠️  Cloudinary not configured - image URLs will not be stored")
            logger.info("Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to .env")
    
    async def upload_image(
        self,
        image_bytes: bytes,
        user_id: str,
        filename: str,
        folder: str = "ingredient_images"
    ) -> Optional[Dict[str, str]]:
        """
        Upload image to Cloudinary with optimized transformations
        
        Args:
            image_bytes: Image content as bytes
            user_id: User ID for organizing uploads
            filename: Original filename
            folder: Cloudinary folder (default: "ingredient_images")
            
        Returns:
            Dictionary with image URLs or None if upload fails
        """
        if not self.is_configured:
            logger.warning("Cloudinary not configured - skipping upload")
            return None
        
        try:
            # Create a unique public_id with user folder structure
            import uuid
            from pathlib import Path
            
            # Extract file extension
            file_ext = Path(filename).suffix.lower().replace('.', '')
            if not file_ext:
                file_ext = 'jpg'
            
            # Generate unique ID
            unique_id = str(uuid.uuid4())[:8]
            
            # Construct public_id: folder/user_id/unique_id
            public_id = f"{folder}/{user_id}/{unique_id}"
            
            logger.info(f"📤 Uploading image to Cloudinary: {public_id}")
            
            # ✅ FIX: Upload with eager transformations to generate URLs immediately
            upload_result = cloudinary.uploader.upload(
                image_bytes,
                public_id=public_id,
                folder=folder,
                resource_type="image",
                overwrite=False,
                quality="auto:good",  # Better quality than just "auto"
                fetch_format="auto",
                tags=[user_id, "ingredient"],
                # ✅ Generate transformations eagerly so they're ready immediately
                eager=[
                    # Thumbnail: 200x200 crop with face/auto focus
                    {
                        "width": 200,
                        "height": 200,
                        "crop": "fill",  # Changed from "thumb" to "fill"
                        "gravity": "auto",
                        "quality": "auto:good",
                        "fetch_format": "auto"
                    },
                    # Medium: 600x600 limit
                    {
                        "width": 600,
                        "height": 600,
                        "crop": "limit",
                        "quality": "auto:good",
                        "fetch_format": "auto"
                    }
                ],
                eager_async=False,  # Wait for transformations to complete
            )
            
            # Extract URLs
            secure_url = upload_result.get("secure_url")
            public_id_full = upload_result.get("public_id")
            
            logger.info(f"✅ Image uploaded successfully")
            logger.info(f"   Public ID: {public_id_full}")
            logger.info(f"   URL: {secure_url}")
            
            # ✅ FIX: Build transformation URLs manually for consistency
            # This ensures they match the eager transformations
            base_url = f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/image/upload"
            
            # Thumbnail URL with fill crop (better than thumb for grid display)
            thumbnail_url = f"{base_url}/c_fill,g_auto,h_200,w_200,q_auto:good,f_auto/{public_id_full}"
            
            # Medium URL with limit crop
            medium_url = f"{base_url}/c_limit,h_600,w_600,q_auto:good,f_auto/{public_id_full}"
            
            logger.info(f"📸 Generated URLs:")
            logger.info(f"   Full: {secure_url}")
            logger.info(f"   Medium: {medium_url}")
            logger.info(f"   Thumbnail: {thumbnail_url}")
            
            return {
                "url": secure_url,
                "secure_url": secure_url,
                "public_id": public_id_full,
                "thumbnail_url": thumbnail_url,
                "medium_url": medium_url,
                "format": upload_result.get("format"),
                "width": upload_result.get("width"),
                "height": upload_result.get("height"),
                "bytes": upload_result.get("bytes")
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload image to Cloudinary: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def delete_image(self, public_id: str) -> bool:
        """
        Delete image from Cloudinary
        
        Args:
            public_id: Cloudinary public_id of the image
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured:
            return False
        
        try:
            result = cloudinary.uploader.destroy(public_id)
            
            if result.get("result") == "ok":
                logger.info(f"✅ Image deleted from Cloudinary: {public_id}")
                return True
            else:
                logger.warning(f"⚠️  Failed to delete image: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting image from Cloudinary: {str(e)}")
            return False
    
    async def get_user_images(self, user_id: str, max_results: int = 100) -> list:
        """
        Get all images uploaded by a user
        
        Args:
            user_id: User ID
            max_results: Maximum number of images to return
            
        Returns:
            List of image resources
        """
        if not self.is_configured:
            return []
        
        try:
            result = cloudinary.api.resources_by_tag(
                user_id,
                max_results=max_results,
                resource_type="image"
            )
            
            return result.get("resources", [])
            
        except Exception as e:
            logger.error(f"❌ Error fetching user images: {str(e)}")
            return []


# Global Cloudinary service instance
cloudinary_service = CloudinaryService()