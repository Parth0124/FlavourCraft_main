"""
FlavourCraft Backend - AI Recipe Generator
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import importlib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from services.storage_service import db_manager, file_storage
from utils.logger import get_logger

from fastapi.responses import Response
from services.prometheus_service import prometheus_metrics

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

# Read CORS configuration directly from environment variables
cors_origins = os.getenv('CORS_ORIGINS', '*')
cors_credentials = os.getenv('CORS_CREDENTIALS', 'true').lower() == 'true'
cors_methods = os.getenv('CORS_METHODS', '*')
cors_headers = os.getenv('CORS_HEADERS', '*')

# Parse CORS origins list
cors_origins_list = [origin.strip() for origin in cors_origins.split(',')] if cors_origins != '*' else ['*']

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=cors_credentials,
    allow_methods=["*"] if cors_methods == "*" else [method.strip() for method in cors_methods.split(",")],
    allow_headers=["*"] if cors_headers == "*" else [header.strip() for header in cors_headers.split(",")],
)

# Include routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(recipes.router)
app.include_router(users.router)
app.include_router(cuisine.router)
app.include_router(mlops_monitoring.router)

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    metrics_data = prometheus_metrics.get_metrics()
    return Response(
        content=metrics_data,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )

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
    Comprehensive health check endpoint for production monitoring
    """
    import psutil
    from datetime import datetime, timezone


    # Read environment directly from environment variable
    environment = os.getenv('ENVIRONMENT', 'development')

    # Check database connectivity
    db_status = "connected" if db_manager.db is not None else "disconnected"
    db_healthy = db_manager.db is not None

    # Check disk space (uploads directory)
    try:
        disk_usage = psutil.disk_usage('/')
        disk_healthy = disk_usage.percent < 90  # Alert if disk > 90%
        disk_info = {
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "used_gb": round(disk_usage.used / (1024**3), 2),
            "free_gb": round(disk_usage.free / (1024**3), 2),
            "percent_used": disk_usage.percent
        }
    except Exception as e:
        disk_healthy = False
        disk_info = {"error": str(e)}

    # Check memory usage
    try:
        memory = psutil.virtual_memory()
        memory_healthy = memory.percent < 90  # Alert if memory > 90%
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent
        }
    except Exception as e:
        memory_healthy = False
        memory_info = {"error": str(e)}

    # Overall health status
    overall_healthy = db_healthy and disk_healthy and memory_healthy

    response = {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": environment,
        "checks": {
            "database": {
                "status": db_status,
                "healthy": db_healthy
            },
            "disk": {
                "healthy": disk_healthy,
                **disk_info
            },
            "memory": {
                "healthy": memory_healthy,
                **memory_info
            }
        }
    }

    # Return 503 if unhealthy (useful for load balancers)
    if not overall_healthy:
        from fastapi import status
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response
        )

    return response


if __name__ == "__main__":
    import uvicorn
    
    # Read credentials directly from environment variables
    api_host = os.getenv('API_HOST', '0.0.0.0')
    api_port = int(os.getenv('API_PORT', '8000'))
    environment = os.getenv('ENVIRONMENT', 'development')
    
    uvicorn.run(
        "main:app",
        host=api_host,
        port=api_port,
        reload=environment == "development"
    )