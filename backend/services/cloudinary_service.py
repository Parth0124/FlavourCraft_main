"""
Cloudinary image hosting service
Handles uploading and managing images on Cloudinary
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
        Upload image to Cloudinary
        
        Args:
            image_bytes: Image content as bytes
            user_id: User ID for organizing uploads
            filename: Original filename
            folder: Cloudinary folder (default: "ingredient_images")
            
        Returns:
            Dictionary with image URLs or None if upload fails
            {
                "url": "https://res.cloudinary.com/.../image.jpg",
                "secure_url": "https://res.cloudinary.com/.../image.jpg",
                "public_id": "ingredient_images/user_123/abc123",
                "thumbnail_url": "https://res.cloudinary.com/.../c_thumb,w_200/image.jpg"
            }
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
            
            logger.info(f"Uploading image to Cloudinary: {public_id}")
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_bytes,
                public_id=public_id,
                folder=folder,
                resource_type="image",
                overwrite=False,
                quality="auto",  # Automatic quality optimization
                fetch_format="auto",  # Automatic format optimization
                tags=[user_id, "ingredient"]  # Add tags for easy filtering
            )
            
            # Extract URLs
            secure_url = upload_result.get("secure_url")
            public_id_full = upload_result.get("public_id")
            
            # Generate thumbnail URL (200x200)
            thumbnail_url = cloudinary.CloudinaryImage(public_id_full).build_url(
                transformation=[
                    {"width": 200, "height": 200, "crop": "thumb", "gravity": "auto"},
                    {"quality": "auto", "fetch_format": "auto"}
                ]
            )
            
            # Generate medium-sized URL (600x600)
            medium_url = cloudinary.CloudinaryImage(public_id_full).build_url(
                transformation=[
                    {"width": 600, "height": 600, "crop": "limit"},
                    {"quality": "auto", "fetch_format": "auto"}
                ]
            )
            
            logger.info(f"✅ Image uploaded successfully: {secure_url}")
            
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
            logger.error(f"Failed to upload image to Cloudinary: {str(e)}")
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
                logger.warning(f"Failed to delete image: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting image from Cloudinary: {str(e)}")
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
            logger.error(f"Error fetching user images: {str(e)}")
            return []


# Global Cloudinary service instance
cloudinary_service = CloudinaryService()