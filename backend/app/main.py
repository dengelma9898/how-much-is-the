from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, health
from app.core.config import settings

app = FastAPI(
    title="Preisvergleich API",
    description="API für die Preisvergleich-App zum Crawlen von Supermarkt-Preisen",
    version="1.0.0"
)

# CORS-Middleware konfigurieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion spezifische Origins verwenden
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router hinzufügen
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])

@app.get("/")
async def root():
    """Root endpoint mit API-Informationen"""
    return {
        "message": "Preisvergleich API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    } 