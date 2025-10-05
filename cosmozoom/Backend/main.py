# main.py
"""
NASA Imagery Tile Proxy - Main Application

This is the entry point for the FastAPI application.
It creates the root app and mounts all service routers (Earth, Moon).

No tile fetching logic should be in this file - only app initialization,
router mounting, middleware configuration, and startup/shutdown events.
"""

from fastapi import FastAPI,Query,Response,HTTPException
import httpx
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import config
import uvicorn

# Import routers from service modules
from gibs_service import router as earth_router
from moon_service import router as moon_router
from mars_service import router as mars_router
from mercury_service import router as mercury_router

# Import config for metadata
from config import (
    EARTH_DEFAULT_LAYER,
    EARTH_DEFAULT_DATE,
    MOON_DEFAULT_LAYER,
    MARS_DEFAULT_LAYER,
)

# ============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ============================================================================

app = FastAPI(
    title="NASA Imagery Tile Proxy",
    description="Unified proxy service for NASA GIBS (Earth) and Trek (Moon) WMTS imagery tiles",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Root",
            "description": "Service directory and health endpoints"
        },
        {
            "name": "Earth Tiles",
            "description": "NASA GIBS Earth satellite imagery tile operations"
        },
        {
            "name": "Moon Tiles",
            "description": "NASA Trek Moon surface imagery tile operations"
        }
    ]
)

# ============================================================================
# CORS MIDDLEWARE CONFIGURATION
# ============================================================================

# Enable Cross-Origin Resource Sharing (CORS)
# This allows frontend applications from different domains to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins like ["https://yourfrontend.com"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"] # Expose all headers to the client
)

# ============================================================================
# MOUNT SERVICE ROUTERS
# ============================================================================

# Mount Earth imagery router at /earth prefix
# All routes in earth_router will be accessible at /earth/*
app.include_router(earth_router)

# Mount Moon imagery router at /moon prefix
# All routes in moon_router will be accessible at /moon/*
app.include_router(moon_router)

#Mount Mars Imagery router at /mars prefix
# All routes in mars_route will be accessible at /mars*
app.include_router(mars_router)

# Mount Mercury Imagery router at /mercury prefix
# All routes in mercury_service will be accessible at /mercury*
app.include_router(mercury_router)
# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Service directory and API overview
    
    Returns information about all available services, endpoints, and examples.
    This is the main entry point for discovering the API structure.
    """
    return {
        "service": "NASA Imagery Tile Proxy",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "description": "Unified proxy for NASA GIBS Earth and Trek Moon WMTS tile services",
        "services": {
            "earth": {
                "name": "NASA GIBS Earth Satellite Imagery",
                "celestial_body": "Earth",
                "source": "NASA GIBS WMTS",
                "requires_date": True,
                "endpoints": {
                    "info": "/earth",
                    "tile": "/earth/tile"
                },
                "example": f"/earth/tile?layer={EARTH_DEFAULT_LAYER}&date={EARTH_DEFAULT_DATE}&z=6&y=18&x=23&format=jpg"
            },
            "moon": {
                "name": "NASA Trek Moon Surface Imagery",
                "celestial_body": "Moon",
                "source": "NASA Trek WMTS",
                "requires_date": False,
                "endpoints": {
                    "info": "/moon",
                    "tile": "/moon/tile"
                },
                "example": f"/moon/tile?z=2&y=1&x=3&format=jpg"
            }
        },
        "mars": {  # ✅ ADD THIS BLOCK
                "name": "NASA Trek Mars Surface Imagery",
                "celestial_body": "Mars",
                "source": "NASA Trek WMTS",
                "requires_date": False,
                "endpoints": {
                    "info": "/mars",
                    "tile": "/mars/tile",
                    "layers": "/mars/layers"
                },
                "example": f"/mars/tile?z=3&y=2&x=5&format=jpg"
            },

            "mercury": {  # ← NEW SERVICE
                "endpoint": "/mercury",
                "tile_endpoint": "/mercury/tile",
                "description": "NASA Trek Mercury surface imagery (static)",
                "data_source": "Trek WMTS - MESSENGER MDIS",
                "features": ["enhanced color", "global mosaic", "665m resolution"],
                "default_layer": config.MERCURY_DEFAULT_LAYER,
                "max_zoom": config.MERCURY_MAX_ZOOM,
                "dataset": "MESSENGER MDIS Basemap Enhanced Color Mosaic",
                "resolution": "665 meters per pixel",
                "example": "/mercury/tile?z=3&y=4&x=8"
            },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "quick_links": {
            "health": "/health",
            "earth_service": "/earth",
            "moon_service": "/moon",
            "mar_service": "/mars"
        }
    }


@app.get("/proxy/earth/tile")
async def proxy_earth_tile(
    z: int = Query(...),
    x: int = Query(...),
    y: int = Query(...),
    date: str = Query(...),
    layer: str = Query(...),
    format: str = Query("jpg")
):
    """
    Proxy Earth tiles to avoid CORS issues in split-screen mode
    """
    # Build the actual NASA GIBS URL
    base_url = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best"
    tile_url = f"{base_url}/{layer}/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.{format}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(tile_url)
            response.raise_for_status()
            
            # Return the image with proper headers
            return Response(
                content=response.content,
                media_type=f"image/{format}",
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")


@app.get("/health", tags=["Root"])
async def health_check():
    """
    Health check endpoint
    
    Returns the operational status of all services.
    Useful for monitoring, load balancers, and uptime checks.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "earth": "operational",
            "moon": "operational",
            "mars": "operational",
            "mercury":"operational",
        },
        "uptime": "Service is running"
    }


# ============================================================================
# APPLICATION LIFECYCLE EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts
    
    Use this for initialization tasks like:
    - Opening database connections
    - Loading models or cache
    - Starting background tasks
    """
    print("🚀 NASA Imagery Tile Proxy is starting...")
    print("=" * 70)
    print("🌍 Earth Service:  /earth")
    print("🌙 Moon Service:   /moon")
    print("🔴 Mar Service: /mars")
    print("☿️  Mercury service: /mercury")
    print("📚 Documentation:  /docs")
    print("💚 Health Check:   /health")
    print("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when the application shuts down
    
    Use this for cleanup tasks like:
    - Closing database connections
    - Flushing caches
    - Stopping background tasks
    """
    print("🛑 NASA Imagery Tile Proxy is shutting down...")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Run the FastAPI application using Uvicorn ASGI server
    # This block only executes when running: python main.py
    
    print("=" * 70)
    print("🚀 Starting NASA Imagery Tile Proxy Server")
    print("=" * 70)
    print("📦 Service: NASA Imagery Tile Proxy")
    print("🔢 Version: 2.0.0")
    print("👤 User: Hamza-ali1223")
    print("📅 Date: 2025-10-04 07:11:40 UTC")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",           # Module:app reference
        host="0.0.0.0",       # Listen on all network interfaces
        port=8000,            # Port number
        reload=True,          # Auto-reload on code changes (development only)
        log_level="info"      # Logging verbosity
    )