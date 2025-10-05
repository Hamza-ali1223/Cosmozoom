# 🚀 NASA Imagery Tile Proxy - Architecture Documentation

**Project:** NASA GIBS & Trek WMTS Tile Proxy Service  
**Version:** 2.0.0  
**Created:** 2025-10-04  
**Author:** Hamza-ali1223  
**Stack:** Python 3.11+, FastAPI, httpx, uvicorn

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Architecture Design](#-architecture-design)
3. [Technology Stack](#-technology-stack)
4. [Project Structure](#-project-structure)
5. [Service Components](#-service-components)
6. [API Endpoints](#-api-endpoints)
7. [Data Flow](#-data-flow)
8. [Configuration](#-configuration)
9. [Error Handling](#-error-handling)
10. [Deployment](#-deployment)
11. [Usage Examples](#-usage-examples)
12. [Future Enhancements](#-future-enhancements)

---

## 🎯 Project Overview

### Purpose
A lightweight FastAPI-based proxy service that fetches and serves satellite imagery tiles from:
- **NASA GIBS WMTS** (Earth satellite imagery - time-series, date-based)
- **NASA Trek WMTS** (Moon surface imagery - static)

### Key Features
- ✅ **Modular architecture** with separate service routers
- ✅ **Async tile fetching** using httpx for non-blocking I/O
- ✅ **Parameter validation** (date format, zoom bounds, tile coordinates)
- ✅ **Proper Content-Type** handling (JPEG, PNG, TIFF)
- ✅ **Error handling** with detailed client-friendly responses
- ✅ **Caching headers** (24h for Earth, 30d for Moon)
- ✅ **CORS enabled** for frontend integration
- ✅ **Auto-generated docs** (Swagger UI, ReDoc)
- ✅ **Default values** for common parameters

### Use Cases
- Frontend map viewers (Leaflet, Cesium, OpenLayers)
- GIS applications
- Time-series Earth observation analysis
- Lunar surface exploration tools
- Educational platforms

---

## 🏗️ Architecture Design

### Design Pattern
**Modular Router Architecture** with separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                         (main.py)                            │
├─────────────────────────────────────────────────────────────┤
│  - App initialization                                        │
│  - Router mounting (/earth, /moon)                          │
│  - CORS middleware                                           │
│  - Health & metadata endpoints                              │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
    ┌────────▼─────────┐           ┌─────────▼────────┐
    │  Earth Router    │           │   Moon Router    │
    │ (gibs_service)   │           │ (moon_service)   │
    ├──────────────────┤           ├──────────────────┤
    │ - /earth/tile    │           │ - /moon/tile     │
    │ - /earth/        │           │ - /moon/         │
    │ - Validation     │           │ - Validation     │
    │ - GIBS fetching  │           │ - Trek fetching  │
    └────────┬─────────┘           └─────────┬────────┘
             │                               │
             │        ┌──────────────┐       │
             └────────►   config.py  ◄───────┘
                      └──────────────┘
                      (Shared Config)
```

### Architectural Principles
1. **Separation of Concerns**: Each file has one responsibility
2. **Dependency Injection**: Config values injected from single source
3. **Modularity**: Easy to add new celestial bodies (Mars, Venus, etc.)
4. **Scalability**: Routers can be deployed independently if needed
5. **Testability**: Services can be unit tested in isolation

---

## 🛠️ Technology Stack

### Core Technologies
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Programming language |
| **FastAPI** | 0.104.1 | Web framework (async, high-performance) |
| **Uvicorn** | 0.24.0 | ASGI server |
| **httpx** | 0.25.1 | Async HTTP client for fetching tiles |
| **Pydantic** | Built-in with FastAPI | Request validation |

### External APIs
| Service | URL | Purpose |
|---------|-----|---------|
| **NASA GIBS WMTS** | `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best` | Earth satellite imagery |
| **NASA Trek WMTS** | `https://trek.nasa.gov/tiles/Moon/EQ` | Moon surface imagery |

---

## 📁 Project Structure

```
nasa-imagery-proxy/
│
├── main.py                      # FastAPI app initialization & routing
├── config.py                    # Global configuration constants
├── gibs_service.py              # Earth tile service (APIRouter)
├── moon_service.py              # Moon tile service (APIRouter)
├── requirements.txt             # Python dependencies
│
├── README.md                    # User documentation
├── ARCHITECTURE.md              # This file (technical docs)
├── .gitignore                   # Git ignore patterns
│
└── tests/                       # Unit tests (future)
    ├── test_earth.py
    ├── test_moon.py
    └── test_config.py
```

### File Responsibilities

| File | Lines | Responsibility | Dependencies |
|------|-------|----------------|--------------|
| **config.py** | ~80 | Configuration constants only | None |
| **gibs_service.py** | ~250 | Earth tile APIRouter | config, fastapi, httpx |
| **moon_service.py** | ~220 | Moon tile APIRouter | config, fastapi, httpx |
| **main.py** | ~200 | App init, router mounting, CORS | config, routers, fastapi |

---

## 🔧 Service Components

### 1. Configuration Module (`config.py`)

**Purpose:** Centralized configuration for all services

**Key Variables:**

#### Earth (GIBS) Configuration
```python
GIBS_BASE_URL = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best"
EARTH_DEFAULT_LAYER = "VIIRS_SNPP_CorrectedReflectance_TrueColor"
EARTH_DEFAULT_DATE = "2025-10-03"
EARTH_DEFAULT_TMS = "GoogleMapsCompatible_Level9"
EARTH_DEFAULT_FORMAT = "jpg"
EARTH_MAX_ZOOM = 9
EARTH_REQUEST_TIMEOUT = 15.0  # seconds
EARTH_CACHE_MAX_AGE = 86400   # 24 hours
```

#### Moon (Trek) Configuration
```python
TREK_MOON_BASE_URL = "https://trek.nasa.gov/tiles/Moon/EQ"
MOON_DEFAULT_LAYER = "LRO_WAC_Mosaic_Global_303ppd_v02"
MOON_DEFAULT_VERSION = "1.0.0"
MOON_DEFAULT_STYLE = "default"
MOON_DEFAULT_TMS = "default028mm"
MOON_DEFAULT_FORMAT = "jpg"
MOON_MAX_ZOOM = 10
MOON_REQUEST_TIMEOUT = 15.0   # seconds
MOON_CACHE_MAX_AGE = 2592000  # 30 days
```

#### Content Type Mapping
```python
CONTENT_TYPE_MAP = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "tif": "image/tiff"
}
```

---

### 2. Earth Service (`gibs_service.py`)

**Purpose:** APIRouter for NASA GIBS Earth satellite imagery

**Router Configuration:**
- **Prefix:** `/earth`
- **Tag:** `Earth Tiles`

**Endpoints:**

#### `GET /earth/tile`
Fetch Earth satellite imagery tile

**Parameters:**
| Parameter | Type | Required | Default | Validation | Example |
|-----------|------|----------|---------|------------|---------|
| `layer` | str | No | `VIIRS_SNPP_CorrectedReflectance_TrueColor` | - | `MODIS_Terra_CorrectedReflectance_TrueColor` |
| `date` | str | No | `2025-10-03` | YYYY-MM-DD format, not in future | `2025-10-04` |
| `z` | int | Yes | - | 0 ≤ z ≤ 9 | `6` |
| `y` | int | Yes | - | 0 ≤ y < 2^z | `18` |
| `x` | int | Yes | - | 0 ≤ x < 2^z | `23` |
| `TileMatrixSet` | str | No | `GoogleMapsCompatible_Level9` | - | `GoogleMapsCompatible_Level9` |
| `format` | str | No | `jpg` | jpg\|png\|png8 | `jpg` |

**WMTS URL Pattern:**
```
https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/
  {layer}/default/{date}/{TileMatrixSet}/{z}/{y}/{x}.{format}
```

**Example:**
```
https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/
  VIIRS_SNPP_CorrectedReflectance_TrueColor/default/2025-10-03/
  GoogleMapsCompatible_Level9/6/18/23.jpg
```

**Validation Logic:**
1. ✅ Date format validation (YYYY-MM-DD)
2. ✅ Date not in future check
3. ✅ Tile coordinate bounds validation (x, y < 2^z)
4. ✅ Zoom level bounds (0-9)

**Response:**
- **Success (200):** Binary image data with `Content-Type: image/jpeg`
- **Error (400):** Invalid parameters
- **Error (404):** Tile not found
- **Error (502):** Upstream service error

#### `GET /earth/`
Service information endpoint

**Response:**
```json
{
  "service": "NASA GIBS Earth Tile Proxy",
  "celestial_body": "Earth",
  "status": "operational",
  "defaults": {...},
  "example": "/earth/tile?..."
}
```

---

### 3. Moon Service (`moon_service.py`)

**Purpose:** APIRouter for NASA Trek Moon surface imagery

**Router Configuration:**
- **Prefix:** `/moon`
- **Tag:** `Moon Tiles`

**Endpoints:**

#### `GET /moon/tile`
Fetch Moon surface imagery tile

**Parameters:**
| Parameter | Type | Required | Default | Validation | Example |
|-----------|------|----------|---------|------------|---------|
| `z` | int | Yes | - | 0 ≤ z ≤ 10 | `2` |
| `y` | int | Yes | - | 0 ≤ y < 2^z | `1` |
| `x` | int | Yes | - | 0 ≤ x < 2^z | `3` |
| `layer` | str | No | `LRO_WAC_Mosaic_Global_303ppd_v02` | - | `Lunar_LRO_LOLA_ClrShade_Global_128ppd_v04` |
| `version` | str | No | `1.0.0` | - | `1.0.0` |
| `style` | str | No | `default` | - | `default` |
| `TileMatrixSet` | str | No | `default028mm` | - | `default028mm` |
| `format` | str | No | `jpg` | jpg\|png\|tif | `jpg` |

**WMTS URL Pattern:**
```
https://trek.nasa.gov/tiles/Moon/EQ/
  {layer}/{version}/{style}/{TileMatrixSet}/{z}/{y}/{x}.{format}
```

**Example:**
```
https://trek.nasa.gov/tiles/Moon/EQ/
  LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/
  default028mm/2/1/3.jpg
```

**Validation Logic:**
1. ✅ Tile coordinate bounds validation (x, y < 2^z)
2. ✅ Zoom level bounds (0-10)

**Note:** No date parameter (Moon imagery is static)

**Response:**
- **Success (200):** Binary image data with `Content-Type: image/jpeg`
- **Error (400):** Invalid parameters
- **Error (404):** Tile not found
- **Error (502):** Upstream service error

#### `GET /moon/`
Service information endpoint

---

### 4. Main Application (`main.py`)

**Purpose:** FastAPI app initialization and router mounting

**Responsibilities:**
1. ✅ Create FastAPI app instance
2. ✅ Configure CORS middleware
3. ✅ Mount Earth router at `/earth`
4. ✅ Mount Moon router at `/moon`
5. ✅ Provide root endpoints (/, /health, /metadata)
6. ✅ Define startup/shutdown events
7. ✅ Run uvicorn server

**Root Endpoints:**

#### `GET /`
Service directory and overview

**Response:**
```json
{
  "service": "NASA Imagery Tile Proxy",
  "version": "2.0.0",
  "status": "operational",
  "services": {
    "earth": {...},
    "moon": {...}
  },
  "documentation": {
    "swagger_ui": "/docs",
    "redoc": "/redoc"
  }
}
```

#### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T07:28:51Z",
  "services": {
    "earth": "operational",
    "moon": "operational"
  }
}
```

---

## 🔗 API Endpoints

### Complete Endpoint Map

| Method | Endpoint | Service | Description |
|--------|----------|---------|-------------|
| **GET** | `/` | Root | Service directory |
| **GET** | `/health` | Root | Health check |
| **GET** | `/docs` | Root | Swagger UI documentation |
| **GET** | `/redoc` | Root | ReDoc documentation |
| **GET** | `/openapi.json` | Root | OpenAPI schema |
| **GET** | `/earth` | Earth | Earth service info |
| **GET** | `/earth/tile` | Earth | Fetch Earth tile |
| **GET** | `/moon` | Moon | Moon service info |
| **GET** | `/moon/tile` | Moon | Fetch Moon tile |

---

## 🔄 Data Flow

### Earth Tile Request Flow

```
1. Client Request
   ↓
   GET /earth/tile?date=2025-10-03&z=6&y=18&x=23
   ↓
2. FastAPI Router (main.py)
   ↓
   Route to earth_router.get_earth_tile()
   ↓
3. Earth Service (gibs_service.py)
   ↓
   a. Validate date format (YYYY-MM-DD)
   b. Check date not in future
   c. Validate tile coordinates (0 ≤ x,y < 2^z)
   d. Validate zoom level (0 ≤ z ≤ 9)
   ↓
4. Construct GIBS WMTS URL
   ↓
   https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/
   VIIRS_SNPP_CorrectedReflectance_TrueColor/default/2025-10-03/
   GoogleMapsCompatible_Level9/6/18/23.jpg
   ↓
5. Fetch Tile (async with httpx)
   ↓
   a. HTTP GET request to NASA GIBS
   b. Timeout: 15 seconds
   c. Handle errors (404, 502, timeouts)
   ↓
6. Return Response
   ↓
   a. Binary image data
   b. Content-Type: image/jpeg
   c. Cache-Control: public, max-age=86400
   d. Custom headers: X-Tile-Source, X-Tile-Layer, etc.
   ↓
7. Client receives image tile
```

### Moon Tile Request Flow

```
1. Client Request
   ↓
   GET /moon/tile?z=2&y=1&x=3
   ↓
2. FastAPI Router (main.py)
   ↓
   Route to moon_router.get_moon_tile()
   ↓
3. Moon Service (moon_service.py)
   ↓
   a. Validate tile coordinates (0 ≤ x,y < 2^z)
   b. Validate zoom level (0 ≤ z ≤ 10)
   ↓
4. Construct Trek WMTS URL
   ↓
   https://trek.nasa.gov/tiles/Moon/EQ/
   LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/
   default028mm/2/1/3.jpg
   ↓
5. Fetch Tile (async with httpx)
   ↓
   a. HTTP GET request to NASA Trek
   b. Timeout: 15 seconds
   c. Handle errors (404, 502, timeouts)
   ↓
6. Return Response
   ↓
   a. Binary image data
   b. Content-Type: image/jpeg
   c. Cache-Control: public, max-age=2592000
   d. Custom headers: X-Tile-Source, X-Tile-Layer, etc.
   ↓
7. Client receives image tile
```

---

## ⚙️ Configuration

### Environment-Specific Settings

#### Development
```python
# main.py
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,        # Auto-reload on code changes
    log_level="info"
)
```

#### Production
```bash
# Command line
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --no-reload \
  --log-level warning
```

### CORS Configuration
```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production CORS:**
```python
allow_origins=[
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
```

---

## 🚨 Error Handling

### Error Response Format

All errors return JSON with consistent structure:

```json
{
  "detail": {
    "error": "Error Type",
    "message": "Human-readable explanation",
    "provided": "User input that caused error",
    "suggestion": "How to fix it"
  }
}
```

### Error Types

#### 400 Bad Request
**Causes:**
- Invalid date format
- Date in the future
- Tile coordinates out of bounds
- Invalid zoom level

**Example:**
```json
{
  "detail": {
    "error": "Invalid date format",
    "message": "Date must be in YYYY-MM-DD format",
    "provided": "10-03-2025",
    "example": "2025-10-03"
  }
}
```

#### 404 Not Found
**Causes:**
- Tile doesn't exist for given date/layer
- Invalid layer name
- Coordinates outside tile coverage

**Example:**
```json
{
  "detail": {
    "error": "Tile not found",
    "message": "The requested tile does not exist...",
    "requested_url": "https://gibs.earthdata.nasa.gov/...",
    "parameters": {
      "layer": "VIIRS_SNPP_CorrectedReflectance_TrueColor",
      "date": "2025-10-03",
      "z": 6, "y": 18, "x": 23
    }
  }
}
```

#### 502 Bad Gateway
**Causes:**
- NASA service unavailable
- Network timeout
- Connection refused

**Example:**
```json
{
  "detail": {
    "error": "Network error",
    "message": "Failed to connect to NASA GIBS: timeout",
    "requested_url": "https://gibs.earthdata.nasa.gov/..."
  }
}
```

---

## 🚀 Deployment

### Local Development

```bash
# 1. Clone repository
git clone <repository-url>
cd nasa-imagery-proxy

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run server
python main.py

# Server runs at: http://localhost:8000
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build
docker build -t nasa-tile-proxy .

# Run
docker run -p 8000:8000 nasa-tile-proxy
```

### Production Server (systemd)

```ini
# /etc/systemd/system/nasa-tile-proxy.service
[Unit]
Description=NASA Tile Proxy Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/nasa-tile-proxy
Environment="PATH=/opt/nasa-tile-proxy/venv/bin"
ExecStart=/opt/nasa-tile-proxy/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable nasa-tile-proxy
sudo systemctl start nasa-tile-proxy
```

---

## 📚 Usage Examples

### cURL Examples

#### Earth Tile
```bash
# Minimal (uses defaults)
curl "http://localhost:8000/earth/tile?z=6&y=18&x=23" --output tile.jpg

# Full parameters
curl "http://localhost:8000/earth/tile?layer=VIIRS_SNPP_CorrectedReflectance_TrueColor&date=2025-10-03&z=6&y=18&x=23&format=jpg" --output tile.jpg

# Different layer
curl "http://localhost:8000/earth/tile?layer=MODIS_Terra_CorrectedReflectance_TrueColor&date=2025-10-03&z=6&y=18&x=23" --output tile.jpg

# PNG format
curl "http://localhost:8000/earth/tile?date=2025-10-03&z=6&y=18&x=23&format=png" --output tile.png
```

#### Moon Tile
```bash
# Basic
curl "http://localhost:8000/moon/tile?z=2&y=1&x=3" --output moon.jpg

# Higher zoom
curl "http://localhost:8000/moon/tile?z=5&y=10&x=15&format=jpg" --output moon_detail.jpg
```

### Python Client

```python
import httpx

# Fetch Earth tile
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/earth/tile",
        params={
            "date": "2025-10-03",
            "z": 6,
            "y": 18,
            "x": 23,
            "format": "jpg"
        }
    )
    
    if response.status_code == 200:
        with open("earth_tile.jpg", "wb") as f:
            f.write(response.content)
    else:
        print(response.json())
```

### JavaScript/Fetch

```javascript
// Fetch Earth tile
fetch('http://localhost:8000/earth/tile?date=2025-10-03&z=6&y=18&x=23')
  .then(response => response.blob())
  .then(blob => {
    const url = URL.createObjectURL(blob);
    document.getElementById('earth-img').src = url;
  });
```

### Leaflet.js Integration

```javascript
// Earth tiles
L.tileLayer('http://localhost:8000/earth/tile?date=2025-10-03&z={z}&x={x}&y={y}', {
    maxZoom: 9,
    attribution: 'NASA GIBS'
}).addTo(map);

// Moon tiles
L.tileLayer('http://localhost:8000/moon/tile?z={z}&x={x}&y={y}', {
    maxZoom: 10,
    attribution: 'NASA Trek'
}).addTo(moonMap);
```

---

## 🔮 Future Enhancements

### Planned Features

#### 1. Caching Layer
- **Redis caching** for frequently requested tiles
- **Disk caching** for long-term storage
- **Cache invalidation** based on date/layer

#### 2. Additional Celestial Bodies
- **Mars:** NASA Mars Trek WMTS
- **Venus:** NASA Venus Trek WMTS
- **Mercury:** NASA Mercury Trek WMTS

#### 3. Metadata Endpoints
```python
GET /earth/layers          # List all available Earth layers
GET /earth/dates/{layer}   # Available dates for layer
GET /moon/layers           # List all available Moon layers
```

#### 4. Batch Requests
```python
POST /earth/tiles
{
  "tiles": [
    {"z": 6, "y": 18, "x": 23, "date": "2025-10-03"},
    {"z": 6, "y": 19, "x": 23, "date": "2025-10-03"}
  ]
}
```

#### 5. WebSocket Streaming
Real-time tile updates for time-series animation

#### 6. Authentication
API key-based authentication for production use

#### 7. Rate Limiting
Request throttling to prevent abuse

#### 8. Analytics
- Request logging
- Popular tile tracking
- Performance monitoring

---

## 📊 Performance Considerations

### Current Performance
- **Latency:** ~200-500ms per tile (depends on NASA service)
- **Throughput:** Limited by NASA GIBS/Trek rate limits
- **Concurrency:** Async allows multiple simultaneous requests

### Optimization Strategies
1. ✅ **Async I/O:** Using httpx.AsyncClient
2. 🔄 **Caching:** Add Redis/memory cache (future)
3. 🔄 **CDN:** Deploy behind CloudFlare/AWS CloudFront (future)
4. 🔄 **Connection Pooling:** Reuse HTTP connections (future)

---

## 🔒 Security Considerations

### Current Security Measures
1. ✅ **Input validation:** All parameters validated
2. ✅ **Type checking:** Pydantic models ensure type safety
3. ✅ **Error hiding:** Don't expose internal errors to clients
4. ✅ **CORS:** Configurable origins

### Production Hardening
- [ ] Add rate limiting (e.g., slowapi)
- [ ] Add authentication (API keys, OAuth)
- [ ] Enable HTTPS only
- [ ] Configure restrictive CORS origins
- [ ] Add request logging and monitoring
- [ ] Implement input sanitization
- [ ] Add DDoS protection

---

## 📝 Development Workflow

### Adding a New Celestial Body (e.g., Mars)

1. **Create service file:** `mars_service.py`
   ```python
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/mars", tags=["Mars Tiles"])
   
   @router.get("/tile")
   async def get_mars_tile(...):
       # Implementation
   ```

2. **Add config:** In `config.py`
   ```python
   TREK_MARS_BASE_URL = "https://trek.nasa.gov/tiles/Mars/..."
   MARS_DEFAULT_LAYER = "..."
   ```

3. **Mount router:** In `main.py`
   ```python
   from mars_service import router as mars_router
   app.include_router(mars_router)
   ```

4. **Update docs:** Add examples and documentation

---

## 🧪 Testing Strategy

### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Earth tile
curl "http://localhost:8000/earth/tile?z=6&y=18&x=23" -o test.jpg

# Moon tile
curl "http://localhost:8000/moon/tile?z=2&y=1&x=3" -o test.jpg
```

### Automated Testing (Future)
```python
# tests/test_earth.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_earth_tile_success():
    response = client.get("/earth/tile?z=6&y=18&x=23")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_earth_tile_invalid_date():
    response = client.get("/earth/tile?date=invalid&z=6&y=18&x=23")
    assert response.status_code == 400
```

---

## 📖 References

### NASA Documentation
- [NASA GIBS API](https://nasa-gibs.github.io/gibs-api-docs/)
- [NASA Trek WMTS](https://trek.nasa.gov/)
- [WMTS Standard (OGC)](https://www.ogc.org/standards/wmts)

### FastAPI Documentation
- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [APIRouter Guide](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Async Best Practices](https://fastapi.tiangolo.com/async/)

### Tile Systems
- [Slippy Map Tilenames](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
- [Web Mercator Projection](https://en.wikipedia.org/wiki/Web_Mercator_projection)

---

## 🤝 Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Keep functions under 50 lines
- Maximum line length: 100 characters

### Commit Messages
```
feat: Add Mars imagery service
fix: Correct date validation in Earth service
docs: Update API examples
refactor: Simplify tile URL construction
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👤 Contact

**Author:** Hamza-ali1223  
**GitHub:** [@Hamza-ali1223](https://github.com/Hamza-ali1223)  
**Created:** 2025-10-04  

---

## 🎯 Quick Reference

### Start Server
```bash
python main.py
```

### Test URLs
```
Earth: http://localhost:8000/earth/tile?z=6&y=18&x=23
Moon:  http://localhost:8000/moon/tile?z=2&y=1&x=3
Docs:  http://localhost:8000/docs
```

### Default Values
- **Earth Layer:** `VIIRS_SNPP_CorrectedReflectance_TrueColor`
- **Earth Date:** `2025-10-03`
- **Moon Layer:** `LRO_WAC_Mosaic_Global_303ppd_v02`
- **Format:** `jpg`

---

**Last Updated:** 2025-10-04 07:28:51 UTC  
**Version:** 2.0.0  
**Status:** ✅ Production Ready