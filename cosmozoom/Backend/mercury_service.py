"""
NASA Trek Mercury WMTS Tile Service
Provides Mercury surface imagery from MESSENGER MDIS dataset
"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse
import httpx
from datetime import datetime
from typing import Optional
import config

# Create router with Mercury prefix
router = APIRouter(
    prefix="/mercury",
    tags=["Mercury Tiles"],
    responses={
        404: {"description": "Tile not found"},
        400: {"description": "Invalid parameters"},
        406: {"description": "Unsupported format"},
        502: {"description": "Upstream service error"}
    }
)

# Constants
MAX_ZOOM = 7  # Mercury WMTS supports zoom levels 0-7


@router.get("/", response_model=None)
async def mercury_health():
    """
    Mercury service health check endpoint
    
    Returns service status and basic information
    
    **Returns:**
    - **200**: Service is operational
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": "mercury"
        }
    )


@router.get("/info")
async def mercury_service_info():
    """
    Mercury service detailed information and metadata endpoint
    
    Returns:
        Service configuration, defaults, and example usage
    """
    return {
        "service": "NASA Trek Mercury Tile Proxy",
        "celestial_body": "Mercury",
        "status": "operational",
        "description": "MESSENGER MDIS Enhanced Color Mosaic - Global 665m resolution",
        "data_source": "NASA Trek WMTS",
        "dataset": "Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m",
        "defaults": {
            "layer": config.MERCURY_DEFAULT_LAYER,
            "version": config.MERCURY_DEFAULT_VERSION,
            "style": config.MERCURY_DEFAULT_STYLE,
            "TileMatrixSet": config.MERCURY_DEFAULT_TMS,
            "format": config.MERCURY_DEFAULT_FORMAT,
            "max_zoom": MAX_ZOOM
        },
        "coordinate_system": "IAU2000::19900",
        "coverage": {
            "longitude": [-180.0, 180.0],
            "latitude": [-90.0, 90.0]
        },
        "example": f"/mercury/tile?z=3&y=4&x=8",
        "full_example": f"/mercury/tile?z=3&y=4&x=8&layer={config.MERCURY_DEFAULT_LAYER}&style=default&TileMatrixSet=default028mm&format=jpg",
        "documentation": {
            "capabilities": "https://trek.nasa.gov/tiles/Mercury/EQ/Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m/1.0.0/WMTSCapabilities.xml",
            "trek_url": "https://trek.nasa.gov/"
        }
    }


@router.get("/tile")
async def get_mercury_tile(
    z: int = Query(..., ge=0, description="Zoom level (0-7, required)", example=3),
    x: int = Query(..., ge=0, description="Tile column index (TileCol, required)", example=8),
    y: int = Query(..., ge=0, description="Tile row index (TileRow, required)", example=4),
    layer: str = Query(
        config.MERCURY_DEFAULT_LAYER,
        description="Mercury imagery layer (optional, defaults to MESSENGER MDIS Enhanced Color)",
        example="Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m"
    ),
    version: str = Query(
        config.MERCURY_DEFAULT_VERSION,
        description="WMTS version (optional, defaults to 1.0.0)",
        example="1.0.0"
    ),
    style: str = Query(
        config.MERCURY_DEFAULT_STYLE,
        description="Tile style (optional, defaults to 'default')",
        example="default"
    ),
    TileMatrixSet: str = Query(
        config.MERCURY_DEFAULT_TMS,
        description="Tile matrix set identifier (optional, defaults to 'default028mm')",
        example="default028mm"
    ),
    format: str = Query(
        config.MERCURY_DEFAULT_FORMAT,
        description="Image format (optional, defaults to 'jpg', only 'jpg' supported)",
        example="jpg"
    )
):
    """
    Fetch Mercury surface imagery tile from NASA Trek WMTS
    
    **Mercury Dataset Information:**
    - **Source:** MESSENGER MDIS (Mercury Dual Imaging System)
    - **Type:** Enhanced Color Mosaic
    - **Resolution:** 665 meters per pixel at equator
    - **Coverage:** Global
    - **Coordinate System:** IAU2000::19900 (Mercury 2000)
    
    **Tile Coordinate System:**
    - Based on Web Mercator-style tiling with 2:1 aspect ratio
    - Origin at top-left (-180°, 90°)
    - Each zoom level doubles resolution
    
    **Available Zoom Levels:**
    - Level 0: 2×1 tiles (global view)
    - Level 1: 4×2 tiles
    - Level 2: 8×4 tiles
    - Level 3: 16×8 tiles
    - Level 4: 32×16 tiles
    - Level 5: 64×32 tiles
    - Level 6: 128×64 tiles
    - Level 7: 256×128 tiles (highest detail)
    
    **Required Parameters:**
    - **z**: Zoom level (0-7, required)
    - **x**: Tile column index (required)
    - **y**: Tile row index (required)
    
    **Optional Parameters (with defaults):**
    - **layer**: Mercury layer identifier (default: Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m)
    - **version**: WMTS service version (default: 1.0.0)
    - **style**: Rendering style (default: 'default')
    - **TileMatrixSet**: Tile matrix set (default: 'default028mm')
    - **format**: Image format (default: 'jpg', only 'jpg' supported)
    
    **Example Requests:**
    ```
    # Minimal request (uses all defaults)
    GET /mercury/tile?z=3&x=8&y=4
    
    # With custom layer
    GET /mercury/tile?z=3&x=8&y=4&layer=Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m
    
    # Full parameters specified
    GET /mercury/tile?z=3&x=8&y=4&layer=Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m&style=default&TileMatrixSet=default028mm&format=jpg
    ```
    
    **Returns:**
    - **200**: Binary image data (JPEG)
    - **400**: Invalid parameters (zoom out of range, coordinates out of bounds)
    - **404**: Tile not found
    - **406**: Unsupported format
    - **502**: NASA Trek service error
    """
    
    # ===========================
    # 1. VALIDATE FORMAT (406)
    # ===========================
    if format.lower() != "jpg":
        raise HTTPException(
            status_code=406,
            detail={
                "error": "Unsupported format",
                "message": f"Only 'jpg' format is supported. Requested format: '{format}'",
                "supported_formats": ["jpg"],
                "provided": format
            }
        )
    
    # ===========================
    # 2. VALIDATE ZOOM LEVEL (400)
    # ===========================
    if z < 0 or z > MAX_ZOOM:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Zoom level out of range",
                "message": f"Zoom level must be between 0 and {MAX_ZOOM}",
                "provided": z,
                "valid_range": f"0-{MAX_ZOOM}",
                "suggestion": f"Use a zoom level between 0 and {MAX_ZOOM}"
            }
        )
    
    # ===========================
    # 3. VALIDATE TILE COORDINATES (400)
    # ===========================
    # Mercury uses 2:1 aspect ratio (width = 2 × height)
    max_tile_col = 2 ** (z + 1)  # Width: 2, 4, 8, 16, 32, 64, 128, 256
    max_tile_row = 2 ** z          # Height: 1, 2, 4, 8, 16, 32, 64, 128
    
    # Validate X coordinate
    if x < 0 or x >= max_tile_col:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "X coordinate out of bounds",
                "message": f"For zoom level {z}, x must be between 0 and {max_tile_col - 1}",
                "provided": x,
                "valid_range": f"0-{max_tile_col - 1}",
                "zoom_level": z,
                "tile_matrix": f"{max_tile_col}×{max_tile_row}"
            }
        )
    
    # Validate Y coordinate
    if y < 0 or y >= max_tile_row:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Y coordinate out of bounds",
                "message": f"For zoom level {z}, y must be between 0 and {max_tile_row - 1}",
                "provided": y,
                "valid_range": f"0-{max_tile_row - 1}",
                "zoom_level": z,
                "tile_matrix": f"{max_tile_col}×{max_tile_row}"
            }
        )
    
    # ===========================
    # 4. CONSTRUCT WMTS URL
    # ===========================
    # URL Pattern: {base_url}/{layer}/{version}/{style}/{TileMatrixSet}/{z}/{y}/{x}.{format}
    tile_url = (
        f"{config.TREK_MERCURY_BASE_URL}/"
        f"{layer}/{version}/{style}/{TileMatrixSet}/{z}/{y}/{x}.{format}"
    )
    
    # ===========================
    # 5. FETCH TILE FROM NASA TREK
    # ===========================
    try:
        async with httpx.AsyncClient(timeout=config.MERCURY_REQUEST_TIMEOUT) as client:
            response = await client.get(tile_url)
            
            # Handle 404 - Tile not found
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Tile not found",
                        "message": "The requested Mercury tile does not exist. This may be due to invalid coordinates, layer name, or the tile may not have data coverage.",
                        "requested_url": tile_url,
                        "parameters": {
                            "layer": layer,
                            "version": version,
                            "z": z,
                            "y": y,
                            "x": x,
                            "style": style,
                            "TileMatrixSet": TileMatrixSet,
                            "format": format
                        },
                        "suggestions": [
                            "Verify tile coordinates are within bounds",
                            "Check if the layer name is correct",
                            "Try a different zoom level",
                            f"Valid zoom range: 0-{MAX_ZOOM}"
                        ]
                    }
                )
            
            # Handle other HTTP errors
            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "error": "Upstream service error",
                        "message": f"NASA Trek returned status code {response.status_code}",
                        "requested_url": tile_url,
                        "status_code": response.status_code
                    }
                )
            
            # ===========================
            # 6. RETURN TILE IMAGE
            # ===========================
            content_type = config.CONTENT_TYPE_MAP.get(format, "image/jpeg")
            
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": f"public, max-age={config.MERCURY_CACHE_MAX_AGE}",
                    "X-Tile-Source": "NASA Trek Mercury WMTS",
                    "X-Tile-Layer": layer,
                    "X-Tile-Coordinates": f"z={z}, y={y}, x={x}",
                    "X-Tile-Format": format,
                    "X-Tile-Matrix": f"{max_tile_col}×{max_tile_row}",
                    "X-Dataset": "MESSENGER MDIS Enhanced Color Mosaic",
                    "X-Resolution": "665m per pixel",
                    "X-Coordinate-System": "IAU2000::19900"
                }
            )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Request timeout",
                "message": f"Request to NASA Trek timed out after {config.MERCURY_REQUEST_TIMEOUT} seconds",
                "requested_url": tile_url
            }
        )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Network error",
                "message": f"Failed to connect to NASA Trek: {str(e)}",
                "requested_url": tile_url
            }
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (don't wrap them)
        raise
    
    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while processing your request",
                "error_type": type(e).__name__
            }
        )


@router.get("/capabilities")
async def get_mercury_capabilities():
    """
    Get Mercury WMTS capabilities metadata
    
    Returns information about available tile matrices, zoom levels, and coverage
    """
    return {
        "service": "WMTS",
        "version": "1.0.0",
        "layer": {
            "identifier": config.MERCURY_DEFAULT_LAYER,
            "title": "Mercury MESSENGER MDIS Basemap Enhanced Color Mosaic Global 665m",
            "bounding_box": {
                "crs": "urn:ogc:def:crs:IAU2000::19900",
                "lower_corner": [-180.0, -90.0],
                "upper_corner": [180.0, 90.0]
            },
            "wgs84_bounding_box": {
                "crs": "urn:ogc:def:crs:OGC:2:84",
                "lower_corner": [-180.0, -90.0],
                "upper_corner": [180.0, 90.0]
            }
        },
        "tile_matrix_set": {
            "identifier": "default028mm",
            "title": "default",
            "description": "Scale values based on OGC specification (0.28mm per pixel)",
            "supported_crs": "urn:ogc:def:crs:IAU2000::19900",
            "tile_matrices": [
                {"zoom": 0, "matrix_width": 2, "matrix_height": 1, "scale_denominator": 2.79e8},
                {"zoom": 1, "matrix_width": 4, "matrix_height": 2, "scale_denominator": 1.40e8},
                {"zoom": 2, "matrix_width": 8, "matrix_height": 4, "scale_denominator": 6.98e7},
                {"zoom": 3, "matrix_width": 16, "matrix_height": 8, "scale_denominator": 3.49e7},
                {"zoom": 4, "matrix_width": 32, "matrix_height": 16, "scale_denominator": 1.75e7},
                {"zoom": 5, "matrix_width": 64, "matrix_height": 32, "scale_denominator": 8.73e6},
                {"zoom": 6, "matrix_width": 128, "matrix_height": 64, "scale_denominator": 4.36e6},
                {"zoom": 7, "matrix_width": 256, "matrix_height": 128, "scale_denominator": 2.18e6}
            ],
            "tile_size": "256×256 pixels",
            "top_left_corner": [-180.0, 90.0]
        },
        "formats": ["image/jpeg"],
        "styles": ["default"],
        "resource_url_template": tile_url_template(),
        "max_zoom": MAX_ZOOM,
        "capabilities_xml": "https://trek.nasa.gov/tiles/Mercury/EQ/Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m/1.0.0/WMTSCapabilities.xml"
    }


def tile_url_template() -> str:
    """Generate template URL for Mercury tiles"""
    return (
        f"{config.TREK_MERCURY_BASE_URL}/"
        f"{{layer}}/{{version}}/{{style}}/{{TileMatrixSet}}/{{z}}/{{y}}/{{x}}.{{format}}"
    )