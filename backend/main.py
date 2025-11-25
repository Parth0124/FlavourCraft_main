"""
FlavourCraft Backend - AI Recipe Generator
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
import importlib
from services.storage_service import db_manager, file_storage
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

'''
Routes imported
'''
auth = importlib.import_module("routes.auth")
upload = importlib.import_module("routes.upload")
recipes = importlib.import_module("routes.recipes")
users = importlib.import_module("routes.users")
cuisine = importlib.import_module("routes.cuisine")
mlops_monitoring = importlib.import_module("routes.mlops_monitoring")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown
    """
    # Startup
    logger.info("Starting FlavourCraft backend...")
    
    # Connect to database
    await db_manager.connect_to_database()
    logger.info("Database connected")
    
    # Cleanup old temporary files
    await file_storage.cleanup_temp_files(older_than_hours=24)
    logger.info("Temporary files cleaned up")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FlavourCraft backend...")
    
    # Close database connection
    await db_manager.close_database_connection()
    logger.info("Database connection closed")
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="FlavourCraft API",
    description="""
    🍳 **FlavourCraft** - AI-Powered Recipe Generator
    
    ## Features
    
    * 🔐 **JWT Authentication** - Secure user sessions
    * 📸 **Image Processing** - Upload ingredient images
    * 🤖 **AI Recipe Generation** - OpenAI & Local Models
    * 🌍 **Cuisine Collections** - Browse recipes by cuisine type
    * 📚 **Static Recipe Library** - Browse pre-loaded recipes
    * 📊 **User History** - Track your cooking journey
    * ⭐ **Favorites** - Save your best recipes
    
    ## Getting Started
    
    1. Register a new account at `/auth/register`
    2. Login to get your JWT token at `/auth/login`
    3. Upload ingredient images at `/upload`
    4. Generate recipes at `/recipes/generate`
    5. Browse by cuisine at `/cuisines`
    6. Browse static recipes at `/recipes/static`
    
    ## Authentication
    
    Most endpoints require authentication. Include your JWT token in the Authorization header:
    ```
    Authorization: Bearer <your_token>
    ```
    """,
    version="1.0.0",
    contact={
        "name": "FlavourCraft Team",
        "email": "support@flavourcraft.com",
    },
    license_info={
        "name": "MIT License",
    },
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["*"] if settings.CORS_METHODS == "*" else settings.CORS_METHODS.split(","),
    allow_headers=["*"] if settings.CORS_HEADERS == "*" else settings.CORS_HEADERS.split(","),
)

# Include routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(recipes.router)
app.include_router(users.router)
app.include_router(cuisine.router)
app.include_router(mlops_monitoring.router)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": "FlavourCraft API",
        "version": "1.0.0",
        "description": "AI-Powered Recipe Generator",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "online"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_manager.db else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development"
    )