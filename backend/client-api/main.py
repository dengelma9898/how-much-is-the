import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import search, health
from shared.core.config import settings
from shared.core.database import create_db_and_tables, close_db, async_session_maker_ro
from shared.services.database_service import DatabaseService

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
    logger.info("Starting Preisvergleich Client API...")
    
    try:
        # Verify database tables exist (read-only, no creation)
        logger.info("Verifying database connection...")
        
        # Test read-only database connection
        async with async_session_maker_ro() as session:
            db_service = DatabaseService(session)
            stores = await db_service.stores.get_all_enabled()
            logger.info(f"Database connection verified - found {len(stores)} stores")
        
        logger.info("Client API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        # Don't fail startup for database issues in development
        if not settings.debug:
            raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Preisvergleich Client API...")
    
    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    
    logger.info("Client API shutdown completed")


app = FastAPI(
    title=f"{settings.api_title} - Client API",
    description="Read-only API für mobile Apps und Web-Clients zum Suchen von Produkten",
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS-Middleware konfigurieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Nur GET und POST, kein DELETE/PUT
    allow_headers=["*"],
)

# Router hinzufügen - nur read-only Endpoints
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])

@app.get("/")
async def root():
    """Root endpoint mit API-Informationen"""
    return {
        "message": "Preisvergleich Client API",
        "version": settings.api_version,
        "debug": settings.debug,
        "type": "client-api",
        "access": "read-only",
        "docs": "/docs",
        "openapi": "/openapi.json"
    } 