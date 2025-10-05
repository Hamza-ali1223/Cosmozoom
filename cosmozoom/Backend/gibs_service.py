# gibs_service.py
"""
Earth Imagery Service - NASA GIBS WMTS Tile Router

This module implements a FastAPI APIRouter for fetching Earth satellite imagery tiles
from NASA GIBS (Global Imagery Browse Services) WMTS REST API.

Router Prefix: /earth
Tag: Earth Tiles
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
import httpx
from datetime import datetime

# Import configuration values
from config import (
    GIBS_BASE_URL,
    EARTH_DEFAULT_LAYER,
    EARTH_DEFAULT_DATE,
    EARTH_DEFAULT_TMS,
    EARTH_DEFAULT_FORMAT,
    EARTH_MAX_ZOOM,
    EARTH_REQUEST_TIMEOUT,
    EARTH_CACHE_MAX_AGE,
    CONTENT_TYPE_MAP,
)

# Create APIRouter instance with prefix and tag
# This router will be mounted at /earth in the main app
router = APIRouter(
    prefix="/earth",
    tags=["Earth Tiles"],
    responses={
        404: {"description": "Tile not found"},
        502: {"description": "Upstream service error"},
    }
)


@router.get("/tile")
async def get_earth_tile(
    layer: str = Query(
        default=EARTH_DEFAULT_LAYER,
        description="GIBS layer name (e.g., VIIRS_SNPP_CorrectedReflectance_TrueColor)",
        example=EARTH_DEFAULT_LAYER
    ),
    date: str = Query(
        default=EARTH_DEFAULT_DATE,
        description="Date in YYYY-MM-DD format",
        example=EARTH_DEFAULT_DATE,
        regex=r"^\d{4}-\d{2}-\d{2}$"
    ),
    z: int = Query(
        ...,
        ge=0,
        le=EARTH_MAX_ZOOM,
        description=f"Zoom level (0-{EARTH_MAX_ZOOM})",
        example=6
    ),
    y: int = Query(
        ...,
        ge=0,
        description="Tile row coordinate",
        example=18
    ),
    x: int = Query(
        ...,
        ge=0,
        description="Tile column coordinate",
        example=23
    ),
    tile_matrix_set: str = Query(
        default=EARTH_DEFAULT_TMS,
        alias="TileMatrixSet",
        description="Tile matrix set identifier",
        example=EARTH_DEFAULT_TMS
    ),
    format: str = Query(
        default=EARTH_DEFAULT_FORMAT,
        regex="^(jpg|jpeg|png|png8)$",
        description="Image format (jpg, png, png8)",
        example="jpg"
    )
):
    """
    Fetch an Earth satellite imagery tile from NASA GIBS WMTS service
    
    This endpoint proxies requests to NASA GIBS and returns the tile image bytes.
    
    **WMTS URL Pattern:**
    ```
    https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/
      {layer}/default/{date}/{TileMatrixSet}/{z}/{y}/{x}.{format}
    ```
    
    **Parameters:**
    - **layer**: Satellite imagery layer identifier (default: VIIRS True Color)
    - **date**: Image date in YYYY-MM-DD format (default: 2025-10-03)
    - **z**: Zoom level 0-9 (required)
    - **y**: Tile row coordinate (required)
    - **x**: Tile column coordinate (required)
    - **TileMatrixSet**: Tile grid system (default: GoogleMapsCompatible_Level9)
    - **format**: Image format - jpg, png, png8 (default: jpg)
    
    **Returns:**
    - Binary image data with appropriate Content-Type header
    
    **Example Usage:**
    ```
    GET /earth/tile?layer=VIIRS_SNPP_CorrectedReflectance_TrueColor&date=2025-10-03&z=6&y=18&x=23&format=jpg
    ```
    
    **Raises:**
    - **400**: Invalid date format or coordinates out of bounds
    - **404**: Tile not found (check layer, date, or coordinates)
    - **502**: GIBS service unavailable or network error
    """
    
    # -------------------------------------------------------------------------
    # STEP 1: Validate date format
    # -------------------------------------------------------------------------
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        
        # Check if date is not in the future
        if parsed_date > datetime.utcnow():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid date",
                    "message": f"Date cannot be in the future. Current UTC date: {datetime.utcnow().strftime('%Y-%m-%d')}",
                    "provided": date
                }
            )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid date format",
                "message": "Date must be in YYYY-MM-DD format",
                "provided": date,
                "example": "2025-10-03"
            }
        )
    
    # -------------------------------------------------------------------------
    # STEP 2: Validate tile coordinates are within bounds for zoom level
    # -------------------------------------------------------------------------
    max_tiles = 2 ** z  # At zoom level z, there are 2^z tiles in each dimension
    
    if x >= max_tiles or y >= max_tiles or x < 0 or y < 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Tile coordinates out of bounds",
                "message": f"At zoom level {z}, tile indices must be 0 to {max_tiles - 1}",
                "provided": {"x": x, "y": y, "z": z},
                "valid_range": f"0 to {max_tiles - 1}"
            }
        )
    
    # -------------------------------------------------------------------------
    # STEP 3: Construct NASA GIBS WMTS URL
    # -------------------------------------------------------------------------
    # URL pattern: {base}/{layer}/default/{date}/{TMS}/{z}/{y}/{x}.{format}
    tile_url = (
        f"{GIBS_BASE_URL}/{layer}/default/{date}/"
        f"{tile_matrix_set}/{z}/{y}/{x}.{format}"
    )
    
    # -------------------------------------------------------------------------
    # STEP 4: Fetch tile from NASA GIBS using async HTTP client
    # -------------------------------------------------------------------------
    async with httpx.AsyncClient(timeout=EARTH_REQUEST_TIMEOUT) as client:
        try:
            # Make GET request to GIBS
            response = await client.get(tile_url)
            
            # Handle 404 - tile not found
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Tile not found",
                        "message": "The requested tile does not exist. Check layer name, date, or coordinates.",
                        "requested_url": tile_url,
                        "parameters": {
                            "layer": layer,
                            "date": date,
                            "z": z, "y": y, "x": x,
                            "format": format
                        }
                    }
                )
            
            # Raise exception for other HTTP errors (4xx, 5xx)
            response.raise_for_status()
            
            # -------------------------------------------------------------------------
            # STEP 5: Return tile image with proper Content-Type
            # -------------------------------------------------------------------------
            # Get content type from format, default to image/jpeg
            content_type = CONTENT_TYPE_MAP.get(format, "image/jpeg")
            
            return Response(
                content=response.content,  # Binary image data
                media_type=content_type,   # Content-Type header
                headers={
                    # Cache for 24 hours (daily imagery)
                    "Cache-Control": f"public, max-age={EARTH_CACHE_MAX_AGE}",
                    # Custom headers for debugging/tracking
                    "X-Tile-Source": "NASA-GIBS",
                    "X-Tile-Layer": layer,
                    "X-Tile-Date": date,
                    "X-Zoom-Level": str(z),
                }
            )
            
        except httpx.HTTPStatusError as e:
            # HTTP error from GIBS (non-404)
            raise HTTPException(
                status_code=e.response.status_code,
                detail={
                    "error": "GIBS service error",
                    "message": f"NASA GIBS returned HTTP {e.response.status_code}",
                    "requested_url": tile_url
                }
            )
        
        except httpx.HTTPError as e:
            # Network error (timeout, connection refused, etc.)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "Network error",
                    "message": f"Failed to connect to NASA GIBS: {str(e)}",
                    "requested_url": tile_url
                }
            )


@router.get("/")
async def earth_service_info():
    """
    Get Earth imagery service information
    
    Returns metadata about the Earth tile service including
    available endpoints, default values, and usage examples.
    """
    return {
        "service": "NASA GIBS Earth Tile Proxy",
        "celestial_body": "Earth",
        "status": "operational",
        "source": "NASA GIBS WMTS",
        "base_url": GIBS_BASE_URL,
        "defaults": {
            "layer": EARTH_DEFAULT_LAYER,
            "date": EARTH_DEFAULT_DATE,
            "tile_matrix_set": EARTH_DEFAULT_TMS,
            "format": EARTH_DEFAULT_FORMAT,
            "max_zoom": EARTH_MAX_ZOOM
        },
        "endpoints": {
            "/earth": "Service information",
            "/earth/tile": "Fetch Earth satellite tiles"
        },
        "example": f"/earth/tile?layer={EARTH_DEFAULT_LAYER}&date={EARTH_DEFAULT_DATE}&z=6&y=18&x=23&format=jpg"
    }