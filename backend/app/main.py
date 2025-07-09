import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import search, health, admin
from app.core.config import settings
from app.core.database import create_db_and_tables, close_db, async_session_maker
from app.services.scheduler_service import scheduler_service
from app.services.database_service import DatabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    
    # Startup
    logger.info("Starting Preisvergleich API...")
    
    try:
        # Initialize database tables
        await create_db_and_tables()
        logger.info("Database tables created/verified")
        
        # Initialize default stores
        async with async_session_maker() as session:
            db_service = DatabaseService(session)
            await db_service.initialize_stores()
        logger.info("Default stores initialized")
        
        # Start scheduler
        await scheduler_service.start()
        logger.info("Scheduler service started")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        # Don't fail startup for database issues in development
        if not settings.debug:
            raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Preisvergleich API...")
    
    try:
        # Stop scheduler
        await scheduler_service.stop()
        logger.info("Scheduler service stopped")
        
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    
    logger.info("Application shutdown completed")


app = FastAPI(
    title=settings.api_title,
    description="API für die Preisvergleich-App zum Crawlen von Supermarkt-Preisen mit Datenbank-Integration",
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS-Middleware konfigurieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router hinzufügen
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

@app.get("/")
async def root():
    """Root endpoint mit API-Informationen"""
    return {
        "message": "Preisvergleich API",
        "version": settings.api_version,
        "debug": settings.debug,
        "database_enabled": True,
        "scheduler_enabled": settings.enable_scheduler,
        "docs": "/docs",
        "openapi": "/openapi.json"
    } 