
"""
Mars Imagery Service - NASA Trek WMTS Tile Router

This module implements a FastAPI APIRouter for fetching Mars surface imagery tiles
from NASA Trek WMTS REST API.

RESTRICTIONS:
- Maximum zoom level: 7 (configurable via MARS_MAX_ZOOM env var)
- Supported layers: Only Viking Color Mosaic and MOLA Elevation
- Aliases accepted for layers (case-insensitive)

Router Prefix: /mars
Tag: Mars Tiles

Author: Hamza-ali1223
Last Modified: 2025-10-04 11:02:36 UTC
"""

import os
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
import httpx
from datetime import datetime
from typing import Optional

# Import configuration values
from config import (
    CONTENT_TYPE_MAP,
)

# ============================================================================
# MARS-SPECIFIC CONFIGURATION
# ============================================================================

# Base URL for NASA Mars Trek WMTS REST API
TREK_MARS_BASE_URL = "https://trek.nasa.gov/tiles/Mars/EQ"

# Default layer for Mars imagery (Viking Color Mosaic)
MARS_DEFAULT_LAYER = "Mars_Viking_MDIM21_ClrMosaic_global_232m"

# Default version for Mars imagery layers
MARS_DEFAULT_VERSION = "1.0.0"

# Default style for Mars imagery
MARS_DEFAULT_STYLE = "default"

# Default tile matrix set for Mars
MARS_DEFAULT_TMS = "default028mm"

# Default image format for Mars tiles
MARS_DEFAULT_FORMAT = "jpg"

# HTTP request timeout in seconds
MARS_REQUEST_TIMEOUT = 15.0

# Cache duration for Mars tiles (in seconds)
# 2592000 = 30 days (static imagery, doesn't change)
MARS_CACHE_MAX_AGE = 2592000


# ============================================================================
# ZOOM AND LAYER RESTRICTIONS
# ============================================================================

# Maximum zoom level (can be overridden via environment variable MARS_MAX_ZOOM)
# Default: 7 (supports zoom levels 0-7 inclusive)
MAX_ZOOM = int(os.getenv("MARS_MAX_ZOOM", "7"))

# Minimum zoom level (always 0)
MIN_ZOOM = 0

# Supported Mars imagery layers with canonical IDs and accepted aliases
# Only Viking Color Mosaic and MOLA Elevation are supported
SUPPORTED_LAYERS = {
    # Viking Color Mosaic - canonical and aliases (case-insensitive)
    "mars_viking_mdim21_clrmosaic_global_232m": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
    "viking": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
    "viking color mosaic": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
    "mars_viking": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
    
    # MOLA Elevation - canonical and aliases (case-insensitive)
    "mars_mgs_mola_megr_global_463m": "Mars_MGS_MOLA_MEGR_global_463m",
    "mola": "Mars_MGS_MOLA_MEGR_global_463m",
    "mola elevation": "Mars_MGS_MOLA_MEGR_global_463m",
    "mars_mgs_mola": "Mars_MGS_MOLA_MEGR_global_463m",
}

# Layer metadata for supported layers only
LAYER_METADATA = {
    "Mars_Viking_MDIM21_ClrMosaic_global_232m": {
        "id": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
        "title": "Viking Color Mosaic",
        "name": "Viking Color Mosaic",
        "resolution": "232 meters/pixel",
        "source": "Viking Orbiter 1 & 2",
        "type": "color mosaic",
        "coverage": "Global",
        "minZoom": MIN_ZOOM,
        "maxZoom": MAX_ZOOM,
        "formats": ["jpg", "png"],
        "aliases": ["viking", "Viking Color Mosaic", "Mars_Viking"],
        "description": "Global color mosaic of Mars surface from Viking missions"
    },
    "Mars_MGS_MOLA_MEGR_global_463m": {
        "id": "Mars_MGS_MOLA_MEGR_global_463m",
        "title": "MOLA Elevation",
        "name": "MOLA Elevation",
        "resolution": "463 meters/pixel",
        "source": "Mars Global Surveyor MOLA",
        "type": "elevation/topography",
        "coverage": "Global",
        "minZoom": MIN_ZOOM,
        "maxZoom": MAX_ZOOM,
        "formats": ["jpg", "png"],
        "aliases": ["mola", "MOLA Elevation", "Mars_MGS_MOLA"],
        "description": "Topographic elevation data from Mars Global Surveyor MOLA instrument"
    }
}


# ============================================================================
# FASTAPI ROUTER SETUP
# ============================================================================

# Create APIRouter instance with prefix and tag
# This router will be mounted at /mars in the main app
router = APIRouter(
    prefix="/mars",
    tags=["Mars Tiles"],
    responses={
        400: {"description": "Invalid zoom level or coordinates out of bounds"},
        404: {"description": "Tile not found"},
        422: {"description": "Unsupported layer"},
        502: {"description": "Upstream service error"},
    }
)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_zoom_level(z: int) -> None:
    """
    Validate zoom level is within allowed range [MIN_ZOOM, MAX_ZOOM]
    
    This enforces the global zoom restriction for Mars tiles.
    
    Args:
        z: Zoom level to validate
        
    Raises:
        HTTPException: 400 if zoom is out of range
        
    Example:
        >>> validate_zoom_level(5)  # OK
        >>> validate_zoom_level(9)  # Raises HTTPException with 400
    """
    if z < MIN_ZOOM or z > MAX_ZOOM:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_zoom",
                "message": f"z must be between {MIN_ZOOM} and {MAX_ZOOM} for Mars tiles.",
                "maxZoom": MAX_ZOOM,
                "minZoom": MIN_ZOOM,
                "provided": z
            }
        )


def normalize_layer(layer: str) -> str:
    """
    Normalize and validate layer name, resolving aliases to canonical ID
    
    Accepts layer names case-insensitively and resolves common aliases
    (e.g., "viking", "VIKING", "Viking Color Mosaic") to the canonical
    layer identifier.
    
    Args:
        layer: Layer name or alias (case-insensitive, whitespace-trimmed)
        
    Returns:
        str: Canonical layer ID
        
    Raises:
        HTTPException: 422 if layer is not in the supported list
        
    Example:
        >>> normalize_layer("viking")
        "Mars_Viking_MDIM21_ClrMosaic_global_232m"
        
        >>> normalize_layer("MOLA")
        "Mars_MGS_MOLA_MEGR_global_463m"
        
        >>> normalize_layer("CTX")  # Not supported
        HTTPException(status_code=422, ...)
    """
    # Normalize: strip whitespace and convert to lowercase
    normalized = layer.strip().lower()
    
    # Resolve alias to canonical ID
    canonical_id = SUPPORTED_LAYERS.get(normalized)
    
    if canonical_id is None:
        # Layer not supported - return error with list of valid options
        raise HTTPException(
            status_code=422,
            detail={
                "error": "unsupported_layer",
                "message": "Only Viking Color Mosaic and MOLA Elevation are supported.",
                "provided": layer,
                "supported": [
                    LAYER_METADATA["Mars_Viking_MDIM21_ClrMosaic_global_232m"],
                    LAYER_METADATA["Mars_MGS_MOLA_MEGR_global_463m"]
                ]
            }
        )
    
    return canonical_id


def validate_tile_coordinates(z: int, x: int, y: int) -> None:
    """
    Validate tile coordinates are within bounds for the given zoom level
    
    At zoom level z, valid tile indices are 0 to (2^z - 1) inclusive.
    
    Args:
        z: Zoom level
        x: Tile column coordinate
        y: Tile row coordinate
        
    Raises:
        HTTPException: 400 if coordinates are out of bounds
        
    Example:
        >>> validate_tile_coordinates(z=3, x=5, y=2)  # OK (max is 7 at z=3)
        >>> validate_tile_coordinates(z=3, x=10, y=2)  # Raises 400
    """
    max_tiles = 2 ** z  # At zoom level z, there are 2^z tiles in each dimension
    
    if x >= max_tiles or y >= max_tiles or x < 0 or y < 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "coordinates_out_of_bounds",
                "message": f"At zoom level {z}, tile indices must be 0 to {max_tiles - 1}",
                "provided": {"x": x, "y": y, "z": z},
                "valid_range": {
                    "min": 0,
                    "max": max_tiles - 1,
                    "tiles_per_dimension": max_tiles
                },
                "celestial_body": "Mars"
            }
        )


# ============================================================================
# TILE ENDPOINT
# ============================================================================

@router.get("/tile")
async def get_mars_tile(
    z: int = Query(
        ...,
        ge=MIN_ZOOM,
        description=f"Zoom level ({MIN_ZOOM}-{MAX_ZOOM})",
        example=3
    ),
    y: int = Query(
        ...,
        ge=0,
        description="Tile row coordinate (0 to 2^z - 1)",
        example=2
    ),
    x: int = Query(
        ...,
        ge=0,
        description="Tile column coordinate (0 to 2^z - 1)",
        example=5
    ),
    layer: str = Query(
        default=MARS_DEFAULT_LAYER,
        description="Mars imagery layer (viking or mola). Aliases accepted (case-insensitive).",
        example="viking"
    ),
    version: str = Query(
        default=MARS_DEFAULT_VERSION,
        description="Layer version",
        example=MARS_DEFAULT_VERSION
    ),
    style: str = Query(
        default=MARS_DEFAULT_STYLE,
        description="Style identifier",
        example=MARS_DEFAULT_STYLE
    ),
    tile_matrix_set: str = Query(
        default=MARS_DEFAULT_TMS,
        alias="TileMatrixSet",
        description="Tile matrix set identifier",
        example=MARS_DEFAULT_TMS
    ),
    format: str = Query(
        default=MARS_DEFAULT_FORMAT,
        regex="^(jpg|jpeg|png|tif|tiff)$",
        description="Image format (jpg, png, tif)",
        example="jpg"
    )
):
    """
    Fetch a Mars surface imagery tile from NASA Trek WMTS service
    
    **Restrictions:**
    - Maximum zoom level: 7 (configurable via MARS_MAX_ZOOM environment variable)
    - Supported layers: Viking Color Mosaic, MOLA Elevation only
    - Case-insensitive layer aliases accepted (e.g., "viking", "MOLA")
    
    **WMTS URL Pattern:**
    ```
    https://trek.nasa.gov/tiles/Mars/EQ/
      {layer}/{version}/{style}/{TileMatrixSet}/{z}/{y}/{x}.{format}
    ```
    
    **Parameters:**
    - **z**: Zoom level 0-7 (required, enforced globally)
    - **y**: Tile row coordinate (required, 0 to 2^z - 1)
    - **x**: Tile column coordinate (required, 0 to 2^z - 1)
    - **layer**: Mars imagery layer (default: Viking Color Mosaic)
              Supported: Viking Color Mosaic, MOLA Elevation
              Aliases (case-insensitive): viking, mola
    - **version**: Layer version (default: 1.0.0)
    - **style**: Style identifier (default: default)
    - **TileMatrixSet**: Tile grid system (default: default028mm)
    - **format**: Image format - jpg, png, tif (default: jpg)
    
    **Returns:**
    - Binary image data with appropriate Content-Type header
    - HTTP 200 on success
    
    **Example Usage:**
    ```
    # Using default Viking layer
    GET /mars/tile?z=3&y=2&x=5&format=jpg
    
    # Using layer alias
    GET /mars/tile?layer=viking&z=5&y=10&x=15&format=png
    
    # Using MOLA elevation
    GET /mars/tile?layer=mola&z=4&y=7&x=9&format=jpg
    ```
    
    **Supported Mars Layers:**
    - **Viking Color Mosaic** (232m/pixel)
      - Canonical ID: `Mars_Viking_MDIM21_ClrMosaic_global_232m`
      - Aliases: `viking`, `Viking Color Mosaic`, `Mars_Viking`
    - **MOLA Elevation** (463m/pixel)
      - Canonical ID: `Mars_MGS_MOLA_MEGR_global_463m`
      - Aliases: `mola`, `MOLA Elevation`, `Mars_MGS_MOLA`
    
    **Error Responses:**
    - **400 invalid_zoom**: Zoom level out of range (not 0-7)
    - **400 coordinates_out_of_bounds**: x or y coordinates invalid for zoom level
    - **422 unsupported_layer**: Layer not in supported list
    - **404**: Tile not found at NASA Trek (may not exist for this location)
    - **502**: Network error or NASA Trek service unavailable
    
    **Raises:**
    - HTTPException(400): Invalid zoom level or coordinates
    - HTTPException(422): Unsupported layer
    - HTTPException(404): Tile not found
    - HTTPException(502): Upstream service error
    """
    
    # -------------------------------------------------------------------------
    # STEP 0: Validate zoom level and layer BEFORE making any requests
    # -------------------------------------------------------------------------
    # This ensures we don't waste bandwidth on invalid requests
    validate_zoom_level(z)
    canonical_layer = normalize_layer(layer)
    
    # -------------------------------------------------------------------------
    # STEP 1: Validate tile coordinates are within bounds for zoom level
    # -------------------------------------------------------------------------
    validate_tile_coordinates(z, x, y)
    
    # -------------------------------------------------------------------------
    # STEP 2: Construct NASA Trek Mars WMTS URL
    # -------------------------------------------------------------------------
    # URL pattern: {base}/{canonical_layer}/{version}/{style}/{TMS}/{z}/{y}/{x}.{format}
    tile_url = (
        f"{TREK_MARS_BASE_URL}/{canonical_layer}/{version}/{style}/"
        f"{tile_matrix_set}/{z}/{y}/{x}.{format}"
    )
    
    # -------------------------------------------------------------------------
    # STEP 3: Fetch tile from NASA Trek using async HTTP client
    # -------------------------------------------------------------------------
    async with httpx.AsyncClient(timeout=MARS_REQUEST_TIMEOUT) as client:
        try:
            # Make GET request to Trek
            response = await client.get(tile_url)
            
            # Handle 404 - tile not found
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "tile_not_found",
                        "message": "The requested Mars tile does not exist. Check layer name or coordinates.",
                        "requested_url": tile_url,
                        "parameters": {
                            "layer": canonical_layer,
                            "z": z,
                            "y": y,
                            "x": x,
                            "format": format
                        },
                        "celestial_body": "Mars",
                        "suggestion": "Try a different zoom level or verify the coordinates are within Mars coverage"
                    }
                )
            
            # Raise exception for other HTTP errors (4xx, 5xx)
            response.raise_for_status()
            
            # -------------------------------------------------------------------------
            # STEP 4: Return tile image with proper Content-Type and headers
            # -------------------------------------------------------------------------
            # Get content type from format, default to image/jpeg
            content_type = CONTENT_TYPE_MAP.get(format, "image/jpeg")
            
            return Response(
                content=response.content,  # Binary image data
                media_type=content_type,   # Content-Type header
                headers={
                    # Cache for 30 days (static imagery, won't change)
                    "Cache-Control": f"public, max-age={MARS_CACHE_MAX_AGE}",
                    # Custom headers for debugging/tracking
                    "X-Tile-Source": "NASA-Trek-Mars",
                    "X-Tile-Layer": canonical_layer,
                    "X-Celestial-Body": "Mars",
                    "X-Zoom-Level": str(z),
                    "X-Tile-Coordinates": f"z={z},x={x},y={y}",
                    # Additional metadata
                    "X-Max-Zoom": str(MAX_ZOOM),
                    "X-Service-Version": "2.0.0",
                    "X-User": "Hamza-ali1223"
                }
            )
            
        except httpx.HTTPStatusError as e:
            # HTTP error from Trek (non-404)
            raise HTTPException(
                status_code=e.response.status_code,
                detail={
                    "error": "trek_service_error",
                    "message": f"NASA Trek returned HTTP {e.response.status_code}",
                    "requested_url": tile_url,
                    "celestial_body": "Mars"
                }
            )
        
        except httpx.HTTPError as e:
            # Network error (timeout, connection refused, etc.)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "network_error",
                    "message": f"Failed to connect to NASA Trek: {str(e)}",
                    "requested_url": tile_url,
                    "celestial_body": "Mars"
                }
            )


# ============================================================================
# METADATA ENDPOINTS
# ============================================================================

@router.get("/")
async def mars_service_info():
    """
    Get Mars imagery service information
    
    Returns comprehensive metadata about the Mars tile service including:
    - Service status and version
    - Supported layers (only 2: Viking and MOLA)
    - Zoom level restrictions
    - Available endpoints
    - Usage examples
    - Points of interest on Mars
    
    **Returns:**
    - JSON object with service metadata
    
    **Example Response:**
    ```json
    {
      "service": "NASA Trek Mars Tile Proxy",
      "status": "operational",
      "maxZoom": 7,
      "supported_layers": [
        {
          "id": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
          "name": "Viking Color Mosaic",
          "minZoom": 0,
          "maxZoom": 7,
          "formats": ["jpg", "png"],
          "aliases": ["viking", "Viking Color Mosaic", "Mars_Viking"]
        },
        {
          "id": "Mars_MGS_MOLA_MEGR_global_463m",
          "name": "MOLA Elevation",
          "minZoom": 0,
          "maxZoom": 7,
          "formats": ["jpg", "png"],
          "aliases": ["mola", "MOLA Elevation", "Mars_MGS_MOLA"]
        }
      ]
    }
    ```
    """
    return {
        "service": "NASA Trek Mars Tile Proxy",
        "celestial_body": "Mars",
        "status": "operational",
        "version": "2.0.0",
        "source": "NASA Trek WMTS",
        "base_url": TREK_MARS_BASE_URL,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user": "Hamza-ali1223",
        "restrictions": {
            "max_zoom": MAX_ZOOM,
            "min_zoom": MIN_ZOOM,
            "supported_layers_count": 2,
            "note": "Mars imagery is static - no date parameter required. Only Viking and MOLA layers supported."
        },
        "defaults": {
            "layer": MARS_DEFAULT_LAYER,
            "version": MARS_DEFAULT_VERSION,
            "style": MARS_DEFAULT_STYLE,
            "tile_matrix_set": MARS_DEFAULT_TMS,
            "format": MARS_DEFAULT_FORMAT,
            "max_zoom": MAX_ZOOM
        },
        "supported_layers": [
            {
                "id": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
                "name": "Viking Color Mosaic",
                "resolution": "232 meters/pixel",
                "source": "Viking Orbiter 1 & 2",
                "type": "color mosaic",
                "coverage": "Global",
                "minZoom": MIN_ZOOM,
                "maxZoom": MAX_ZOOM,
                "formats": ["jpg", "png"],
                "aliases": ["viking", "Viking Color Mosaic", "Mars_Viking"],
                "description": "Global color mosaic of Mars surface from Viking missions"
            },
            {
                "id": "Mars_MGS_MOLA_MEGR_global_463m",
                "name": "MOLA Elevation",
                "resolution": "463 meters/pixel",
                "source": "Mars Global Surveyor MOLA",
                "type": "elevation/topography",
                "coverage": "Global",
                "minZoom": MIN_ZOOM,
                "maxZoom": MAX_ZOOM,
                "formats": ["jpg", "png"],
                "aliases": ["mola", "MOLA Elevation", "Mars_MGS_MOLA"],
                "description": "Topographic elevation data from Mars Global Surveyor MOLA instrument"
            }
        ],
        "endpoints": {
            "/mars": "Service information (this endpoint)",
            "/mars/tile": "Fetch Mars surface tiles",
            "/mars/layers": "List supported layers with metadata"
        },
        "examples": {
            "simple": "/mars/tile?z=3&y=2&x=5",
            "with_layer_alias": "/mars/tile?layer=viking&z=5&y=12&x=8&format=jpg",
            "mola_elevation": "/mars/tile?layer=mola&z=4&y=7&x=5&format=png",
            "full_parameters": f"/mars/tile?layer={MARS_DEFAULT_LAYER}&z=3&y=2&x=5&format=jpg"
        },
        "interesting_locations": {
            "Olympus_Mons": {
                "description": "Largest volcano in the solar system (21 km high)",
                "coordinates": {"z": 5, "y": 10, "x": 8},
                "url": "/mars/tile?layer=viking&z=5&y=10&x=8"
            },
            "Valles_Marineris": {
                "description": "Massive canyon system (4,000 km long)",
                "coordinates": {"z": 5, "y": 11, "x": 12},
                "url": "/mars/tile?layer=viking&z=5&y=11&x=12"
            },
            "Gale_Crater": {
                "description": "Curiosity rover landing site",
                "coordinates": {"z": 6, "y": 26, "x": 23},
                "url": "/mars/tile?layer=viking&z=6&y=26&x=23"
            },
            "Jezero_Crater": {
                "description": "Perseverance rover landing site (ancient lake bed)",
                "coordinates": {"z": 6, "y": 24, "x": 21},
                "url": "/mars/tile?layer=viking&z=6&y=24&x=21"
            }
        }
    }


@router.get("/layers")
async def mars_layers():
    """
    List all supported Mars imagery layers
    
    Returns only the two supported Mars imagery layers (Viking and MOLA)
    with complete metadata including:
    - Layer IDs and names
    - Resolution and data source
    - Zoom level ranges (minZoom: 0, maxZoom: 7)
    - Supported image formats
    - Accepted aliases (case-insensitive)
    - Example URLs
    
    **Returns:**
    - JSON object with layer list
    
    **Example Response:**
    ```json
    {
      "service": "Mars Imagery Layers",
      "total": 2,
      "maxZoom": 7,
      "layers": [
        {
          "id": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
          "name": "Viking Color Mosaic",
          "minZoom": 0,
          "maxZoom": 7,
          "formats": ["jpg", "png"],
          "aliases": ["viking", "Viking Color Mosaic", "Mars_Viking"]
        },
        {
          "id": "Mars_MGS_MOLA_MEGR_global_463m",
          "name": "MOLA Elevation",
          "minZoom": 0,
          "maxZoom": 7,
          "formats": ["jpg", "png"],
          "aliases": ["mola", "MOLA Elevation", "Mars_MGS_MOLA"]
        }
      ]
    }
    ```
    """
    return {
        "service": "Mars Imagery Layers",
        "celestial_body": "Mars",
        "total": 2,
        "default": MARS_DEFAULT_LAYER,
        "maxZoom": MAX_ZOOM,
        "minZoom": MIN_ZOOM,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "note": "Only Viking Color Mosaic and MOLA Elevation are supported. Layer aliases are case-insensitive.",
        "layers": [
            {
                "id": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
                "name": "Viking Color Mosaic",
                "resolution": "232 meters/pixel",
                "source": "Viking Orbiter 1 & 2",
                "type": "color mosaic",
                "coverage": "Global",
                "minZoom": MIN_ZOOM,
                "maxZoom": MAX_ZOOM,
                "formats": ["jpg", "png"],
                "aliases": ["viking", "Viking Color Mosaic", "Mars_Viking"],
                "description": "Global color mosaic of Mars surface",
                "url_example": "/mars/tile?layer=viking&z=3&y=2&x=5"
            },
            {
                "id": "Mars_MGS_MOLA_MEGR_global_463m",
                "name": "MOLA Elevation",
                "resolution": "463 meters/pixel",
                "source": "Mars Global Surveyor MOLA",
                "type": "elevation/topography",
                "coverage": "Global",
                "minZoom": MIN_ZOOM,
                "maxZoom": MAX_ZOOM,
                "formats": ["jpg", "png"],
                "aliases": ["mola", "MOLA Elevation", "Mars_MGS_MOLA"],
                "description": "Topographic elevation data",
                "url_example": "/mars/tile?layer=mola&z=4&y=5&x=7"
            }
        ]
    }