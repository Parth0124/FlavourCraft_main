"""
Database storage and file management service
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
import aiofiles
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """MongoDB database manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect_to_database(self):
        """Connect to MongoDB"""
        try:
            # Read credentials directly from environment variables
            mongodb_uri = os.getenv('MONGODB_URI')
            mongodb_db_name = os.getenv('MONGODB_DB_NAME', 'FlavourCraft')
            
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable is not set")
            
            self.client = AsyncIOMotorClient(mongodb_uri)
            self.db = self.client[mongodb_db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {mongodb_db_name}")
            
            # Create indexes
            await self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    async def close_database_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
    
    async def create_indexes(self):
        """Create database indexes for optimal query performance"""
        try:
            # Users collection indexes
            await self.db.users.create_index("email", unique=True)
            await self.db.users.create_index("username", unique=True)
            await self.db.users.create_index("created_at")
            
            # Static recipes collection indexes
            await self.db.static_recipes.create_index("tags")
            await self.db.static_recipes.create_index("ingredients")
            await self.db.static_recipes.create_index("difficulty")
            await self.db.static_recipes.create_index("title")
            
            # Generated recipes collection indexes
            await self.db.generated_recipes.create_index("user_id")
            await self.db.generated_recipes.create_index("timestamp")
            await self.db.generated_recipes.create_index("is_favorite")
            await self.db.generated_recipes.create_index(
                [("user_id", 1), ("timestamp", -1)]
            )
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if self.db is None:
            raise RuntimeError("Database not initialized. Call connect_to_database first.")
        return self.db


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency to get database instance
    
    Returns:
        MongoDB database instance
    """
    return db_manager.get_database()


class FileStorageManager:
    """File storage manager for uploads and temporary files"""
    
    def __init__(self):
        # Read credentials directly from environment variables
        upload_dir = os.getenv('UPLOAD_DIR', './uploads')
        temp_dir = os.getenv('TEMP_DIR', './temp')
        
        self.upload_dir = Path(upload_dir)
        self.temp_dir = Path(temp_dir)
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_upload_file(
        self, 
        file_content: bytes, 
        filename: str,
        directory: str = "images"
    ) -> str:
        """
        Save uploaded file to storage
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            directory: Subdirectory to save file in
            
        Returns:
            Full file path
        """
        # Create subdirectory if it doesn't exist
        save_dir = self.upload_dir / directory
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        
        file_path = save_dir / unique_filename
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            logger.info(f"File saved successfully: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise
    
    async def save_temp_file(self, file_content: bytes, filename: str) -> str:
        """
        Save temporary file
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            
        Returns:
            Full file path
        """
        file_path = self.temp_dir / filename
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving temp file: {str(e)}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    async def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        Clean up temporary files older than specified hours
        
        Args:
            older_than_hours: Delete files older than this many hours
        """
        try:
            current_time = datetime.now().timestamp()
            threshold = older_than_hours * 3600  # Convert hours to seconds
            
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > threshold:
                        file_path.unlink()
                        logger.info(f"Cleaned up old temp file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")


# Global file storage manager instance
file_storage = FileStorageManager()