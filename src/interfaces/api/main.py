"""
Open Data Monitoring API

Point d'entrée principal de l'API REST qui expose les fonctionnalités de la CLI
via des endpoints HTTP. Suit les principes DDD en réutilisant les handlers existants.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interfaces.api.routers import common, platforms, datasets
from settings import ENV

# Configuration de l'application FastAPI
api_app = FastAPI(
    title="Open Data Monitoring API",
    description="API REST pour le monitoring des plateformes Open Data",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "common",
            "description": "Opérations communes et utilitaires"
        },
        {
            "name": "platforms", 
            "description": "Gestion des plateformes Open Data"
        },
        {
            "name": "datasets",
            "description": "Gestion des datasets"
        }
    ]
)

# Configuration CORS pour le développement
if ENV in ["DEV", "TEST"]:
    api_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # À restreindre en production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Enregistrement des routers
api_app.include_router(common.router, prefix="/api/v1")
api_app.include_router(platforms.router, prefix="/api/v1") 
api_app.include_router(datasets.router, prefix="/api/v1")

# Health check endpoint
@api_app.get("/health")
async def health_check():
    """Point de contrôle de santé de l'API"""
    return {
        "status": "healthy",
        "environment": ENV,
        "version": "1.0.0"
    } 