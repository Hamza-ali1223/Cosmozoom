# config.py
"""
Configuration module for NASA Imagery Tile Proxy

This file contains all global configuration variables used across the application.
No API routes or business logic should be placed here.
"""

# ============================================================================
# EARTH (NASA GIBS) CONFIGURATION
# ============================================================================

# Base URL for NASA GIBS WMTS REST API
# Used to fetch Earth satellite imagery tiles
GIBS_BASE_URL = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best"

# Default layer for Earth imagery
# VIIRS_SNPP_CorrectedReflectance_TrueColor provides daily true-color satellite imagery
EARTH_DEFAULT_LAYER = "VIIRS_SNPP_CorrectedReflectance_TrueColor"

# Default date for Earth imagery (YYYY-MM-DD format)
# Falls back to this date if user doesn't provide one
EARTH_DEFAULT_DATE = "2025-10-03"

# Default tile matrix set for Earth
# GoogleMapsCompatible_Level9 is the standard Web Mercator grid
EARTH_DEFAULT_TMS = "GoogleMapsCompatible_Level9"

# Default image format for Earth tiles
EARTH_DEFAULT_FORMAT = "jpg"

# Maximum zoom level supported by GIBS
EARTH_MAX_ZOOM = 9

# HTTP request timeout in seconds
EARTH_REQUEST_TIMEOUT = 15.0

# Cache duration for Earth tiles (in seconds)
# 86400 = 24 hours (daily imagery updates)
EARTH_CACHE_MAX_AGE = 86400


# ============================================================================
# MOON (NASA TREK) CONFIGURATION
# ============================================================================

# Base URL for NASA Moon Trek WMTS REST API
# Used to fetch Moon surface imagery tiles
TREK_MOON_BASE_URL = "https://trek.nasa.gov/tiles/Moon/EQ"

# Default layer for Moon imagery
# LRO_WAC_Mosaic_Global_303ppd_v02 is the Wide Angle Camera mosaic
MOON_DEFAULT_LAYER = "LRO_WAC_Mosaic_Global_303ppd_v02"

# Default version for Moon imagery layers
MOON_DEFAULT_VERSION = "1.0.0"

# Default style for Moon imagery
MOON_DEFAULT_STYLE = "default"

# Default tile matrix set for Moon
MOON_DEFAULT_TMS = "default028mm"

# Default image format for Moon tiles
MOON_DEFAULT_FORMAT = "jpg"

# Maximum zoom level supported by Trek
MOON_MAX_ZOOM = 10

# HTTP request timeout in seconds
MOON_REQUEST_TIMEOUT = 15.0

# Cache duration for Moon tiles (in seconds)
# 2592000 = 30 days (static imagery, doesn't change)
MOON_CACHE_MAX_AGE = 2592000


# ============================================================================
# CONTENT TYPE MAPPINGS
# ============================================================================

# Map file format to HTTP Content-Type header
CONTENT_TYPE_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "png8": "image/png",
    "tif": "image/tiff",
    "tiff": "image/tiff",
}



# ============================================================================
# MARS (TREK) CONFIGURATION
# ============================================================================

# Base URL for NASA Mars Trek WMTS REST API
# Used to fetch Mars surface imagery tiles
TREK_MARS_BASE_URL = "https://trek.nasa.gov/tiles/Mars/EQ"

# Default layer for Mars imagery
# Viking MDIM21 provides global color mosaic of Mars
MARS_DEFAULT_LAYER = "Mars_Viking_MDIM21_ClrMosaic_global_232m"

# Default version for Mars imagery layers
MARS_DEFAULT_VERSION = "1.0.0"

# Default style for Mars imagery
MARS_DEFAULT_STYLE = "default"

# Default tile matrix set for Mars
MARS_DEFAULT_TMS = "default028mm"

# Default image format for Mars tiles
MARS_DEFAULT_FORMAT = "jpg"

# Maximum zoom level supported by Mars Trek
MARS_MAX_ZOOM = 10

# HTTP request timeout in seconds
MARS_REQUEST_TIMEOUT = 15.0

# Cache duration for Mars tiles (in seconds)
# 2592000 = 30 days (static imagery, doesn't change)
MARS_CACHE_MAX_AGE = 2592000

# Available Mars Layers (Trek)
MARS_LAYERS = {
    "Mars_Viking_MDIM21_ClrMosaic_global_232m": "Viking Color Mosaic (232m/px)",
    "Mars_MGS_MOLA_ClrShade_merge_global_463m": "MOLA Elevation Shaded Relief (463m/px)",
    "Mars_MRO_CTX_mosaic_global_25m": "Context Camera Mosaic (25m/px, high-res)",
    "Mars_MEX_HRSC_MOLA_BlendShade_Global_200m": "HRSC/MOLA Blended Shade (200m/px)",
}

# ============================================
# MERCURY (NASA TREK) CONFIGURATION
# ============================================
TREK_MERCURY_BASE_URL = "https://trek.nasa.gov/tiles/Mercury/EQ"
MERCURY_DEFAULT_LAYER = "Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m"
MERCURY_DEFAULT_VERSION = "1.0.0"
MERCURY_DEFAULT_STYLE = "default"
MERCURY_DEFAULT_TMS = "default028mm"
MERCURY_DEFAULT_FORMAT = "jpg"
MERCURY_MAX_ZOOM = 7  # Based on XML capabilities (0-7)
MERCURY_REQUEST_TIMEOUT = 15.0  # seconds
MERCURY_CACHE_MAX_AGE = 2592000  # 30 days (static imagery)