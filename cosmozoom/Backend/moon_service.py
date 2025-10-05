# moon_service.py
"""
Moon Imagery Service - NASA Trek WMTS Tile Router

This module implements a FastAPI APIRouter for fetching Moon surface imagery tiles
from NASA Trek WMTS REST API.

Router Prefix: /moon
Tag: Moon Tiles
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
import httpx

# Import configuration values
from config import (
    TREK_MOON_BASE_URL,
    MOON_DEFAULT_LAYER,
    MOON_DEFAULT_VERSION,
    MOON_DEFAULT_STYLE,
    MOON_DEFAULT_TMS,
    MOON_DEFAULT_FORMAT,
    MOON_MAX_ZOOM,
    MOON_REQUEST_TIMEOUT,
    MOON_CACHE_MAX_AGE,
    CONTENT_TYPE_MAP,
)

# Create APIRouter instance with prefix and tag
# This router will be mounted at /moon in the main app
router = APIRouter(
    prefix="/moon",
    tags=["Moon Tiles"],
    responses={
        404: {"description": "Tile not found"},
        502: {"description": "Upstream service error"},
    }
)


@router.get("/tile")
async def get_moon_tile(
    z: int = Query(
        ...,
        ge=0,
        le=MOON_MAX_ZOOM,
        description=f"Zoom level (0-{MOON_MAX_ZOOM})",
        example=2
    ),
    y: int = Query(
        ...,
        ge=0,
        description="Tile row coordinate",
        example=1
    ),
    x: int = Query(
        ...,
        ge=0,
        description="Tile column coordinate",
        example=3
    ),
    layer: str = Query(
        default=MOON_DEFAULT_LAYER,
        description="Moon imagery layer name",
        example=MOON_DEFAULT_LAYER
    ),
    version: str = Query(
        default=MOON_DEFAULT_VERSION,
        description="Layer version",
        example=MOON_DEFAULT_VERSION
    ),
    style: str = Query(
        default=MOON_DEFAULT_STYLE,
        description="Style identifier",
        example=MOON_DEFAULT_STYLE
    ),
    tile_matrix_set: str = Query(
        default=MOON_DEFAULT_TMS,
        alias="TileMatrixSet",
        description="Tile matrix set identifier",
        example=MOON_DEFAULT_TMS
    ),
    format: str = Query(
        default=MOON_DEFAULT_FORMAT,
        regex="^(jpg|jpeg|png|tif|tiff)$",
        description="Image format (jpg, png, tif)",
        example="jpg"
    )
):
    """
    Fetch a Moon surface imagery tile from NASA Trek WMTS service
    
    This endpoint proxies requests to NASA Trek and returns the tile image bytes.
    
    **Note:** Moon imagery is static (no date parameter required).
    
    **WMTS URL Pattern:**
    ```
    https://trek.nasa.gov/tiles/Moon/EQ/
      {layer}/{version}/{style}/{TileMatrixSet}/{z}/{y}/{x}.{format}
    ```
    
    **Parameters:**
    - **z**: Zoom level 0-10 (required)
    - **y**: Tile row coordinate (required)
    - **x**: Tile column coordinate (required)
    - **layer**: Moon imagery layer (default: LRO_WAC_Mosaic_Global_303ppd_v02)
    - **version**: Layer version (default: 1.0.0)
    - **style**: Style identifier (default: default)
    - **TileMatrixSet**: Tile grid system (default: default028mm)
    - **format**: Image format - jpg, png, tif (default: jpg)
    
    **Returns:**
    - Binary image data with appropriate Content-Type header
    
    **Example Usage:**
    ```
    GET /moon/tile?z=2&y=1&x=3&format=jpg
    GET /moon/tile?z=5&y=10&x=15&layer=LRO_WAC_Mosaic_Global_303ppd_v02&format=png
    ```
    
    **Raises:**
    - **400**: Coordinates out of bounds for zoom level
    - **404**: Tile not found (check layer or coordinates)
    - **502**: Trek service unavailable or network error
    """
    
    # -------------------------------------------------------------------------
    # STEP 1: Validate tile coordinates are within bounds for zoom level
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
    # STEP 2: Construct NASA Trek Moon WMTS URL
    # -------------------------------------------------------------------------
    # URL pattern: {base}/{layer}/{version}/{style}/{TMS}/{z}/{y}/{x}.{format}
    tile_url = (
        f"{TREK_MOON_BASE_URL}/{layer}/{version}/{style}/"
        f"{tile_matrix_set}/{z}/{y}/{x}.{format}"
    )
    
    # -------------------------------------------------------------------------
    # STEP 3: Fetch tile from NASA Trek using async HTTP client
    # -------------------------------------------------------------------------
    async with httpx.AsyncClient(timeout=MOON_REQUEST_TIMEOUT) as client:
        try:
            # Make GET request to Trek
            response = await client.get(tile_url)
            
            # Handle 404 - tile not found
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Tile not found",
                        "message": "The requested tile does not exist. Check layer name or coordinates.",
                        "requested_url": tile_url,
                        "parameters": {
                            "layer": layer,
                            "z": z, "y": y, "x": x,
                            "format": format
                        }
                    }
                )
            
            # Raise exception for other HTTP errors (4xx, 5xx)
            response.raise_for_status()
            
            # -------------------------------------------------------------------------
            # STEP 4: Return tile image with proper Content-Type
            # -------------------------------------------------------------------------
            # Get content type from format, default to image/jpeg
            content_type = CONTENT_TYPE_MAP.get(format, "image/jpeg")
            
            return Response(
                content=response.content,  # Binary image data
                media_type=content_type,   # Content-Type header
                headers={
                    # Cache for 30 days (static imagery)
                    "Cache-Control": f"public, max-age={MOON_CACHE_MAX_AGE}",
                    # Custom headers for debugging/tracking
                    "X-Tile-Source": "NASA-Trek-Moon",
                    "X-Tile-Layer": layer,
                    "X-Zoom-Level": str(z),
                }
            )
            
        except httpx.HTTPStatusError as e:
            # HTTP error from Trek (non-404)
            raise HTTPException(
                status_code=e.response.status_code,
                detail={
                    "error": "Trek service error",
                    "message": f"NASA Trek returned HTTP {e.response.status_code}",
                    "requested_url": tile_url
                }
            )
        
        except httpx.HTTPError as e:
            # Network error (timeout, connection refused, etc.)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "Network error",
                    "message": f"Failed to connect to NASA Trek: {str(e)}",
                    "requested_url": tile_url
                }
            )


@router.get("/")
async def moon_service_info():
    """
    Get Moon imagery service information
    
    Returns metadata about the Moon tile service including
    available endpoints, default values, and usage examples.
    """
    return {
        "service": "NASA Trek Moon Tile Proxy",
        "celestial_body": "Moon",
        "status": "operational",
        "source": "NASA Trek WMTS",
        "base_url": TREK_MOON_BASE_URL,
        "note": "Moon imagery is static - no date parameter required",
        "defaults": {
            "layer": MOON_DEFAULT_LAYER,
            "version": MOON_DEFAULT_VERSION,
            "style": MOON_DEFAULT_STYLE,
            "tile_matrix_set": MOON_DEFAULT_TMS,
            "format": MOON_DEFAULT_FORMAT,
            "max_zoom": MOON_MAX_ZOOM
        },
        "endpoints": {
            "/moon": "Service information",
            "/moon/tile": "Fetch Moon surface tiles"
        },
        "example": f"/moon/tile?z=2&y=1&x=3&format=jpg"
    }