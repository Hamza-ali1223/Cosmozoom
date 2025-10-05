# 🛰️ Cosmozoom Backend

Cosmozoom Backend is a powerful **FastAPI**-based service acting as a proxy and metadata provider for planetary surface imagery from NASA's **WMTS services** (Trek, GIBS, etc). This backend is the core API layer supporting the [Cosmozoom Frontend](https://github.com/your-org/cosmozoom), enabling interactive exploration of **Earth**, **Mars**, **Moon**, and **Mercury**.

---

## ⚡ Features

- 🪐 Unified tile proxying from NASA WMTS services
- 🔍 Dynamic info endpoints for layers and capabilities
- 🛠️ Coordinate-based tile retrieval
- 🧪 Health monitoring endpoints
- 🔌 Built with FastAPI for performance and simplicity

---

## 📦 Tech Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Docs**: Auto-generated via Swagger/OpenAPI
- **Dependencies**: Uvicorn, HTTPX, FastAPI

---

## 🚀 Getting Started


### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python ./main.py
```

The server will start on [http://localhost:8000](http://localhost:8000)

---

## 🔧 API Reference

> Full Swagger documentation available at: `http://localhost:8000/docs`

### 📍 Root & Health

* `GET /`
  Returns API metadata and structure.

* `GET /health`
  Simple health check to confirm service status.

---

### 🌍 Earth Tile Endpoints

* `GET /earth/tile/{z}/{x}/{y}.{format}`
  Fetch Earth tiles using NASA GIBS (MODIS or VIIRS) services.
  Parameters include: `layer`, `date`, `tileMatrixSet`, `format` (e.g. png, jpg)

* `GET /earth/info`
  Returns available layers, supported formats, defaults, etc.

---

### 🌕 Moon Tile Endpoints

* `GET /moon/tile/{z}/{x}/{y}.{format}`
  Fetch Moon surface tiles from NASA Trek WMTS.
  Parameters include `layer`, `version`, `tileMatrixSet`, `format`, etc.

* `GET /moon/info`
  Returns metadata and available layers for Moon imagery.

---

### 🔴 Mars Tile Endpoints

* `GET /mars/tile/{z}/{x}/{y}.{format}`
  Retrieve tiles from Mars Trek WMTS service.
  Supports layers like `Mars_Viking_MDIM21_ClrMosaic_global_232m`.

* `GET /mars/info`
  Returns information about available Mars tiles and supported formats.

* `GET /mars/layers`
  Lists all supported Mars layers (Viking, MOLA hillshade, etc.)

---

### 🟡 Mercury Tile Endpoints

* `GET /mercury/tile/{z}/{x}/{y}.{format}`
  Fetch Mercury tiles from NASA Mercury Trek service.
  Supports layers such as `MESSENGER_MDIS_Basemap`, `EnhancedColor`.

* `GET /mercury/info`
  Returns info and supported layers.

* `GET /mercury/capabilities`
  Exposes WMTS capabilities (bounds, zoom levels, tileMatrix info).

---

## 📌 Notes

* WMTS tile access is based on `{z}/{x}/{y}` coordinates and optional query parameters (layer, version, format).
* Services act as a **proxy** to NASA's WMTS endpoints and return tiles in `png` or `jpg`.
* Each celestial body (Earth, Moon, Mars, Mercury) has its own set of valid layers and tileMatrix configurations.

---

## 📂 Example Request

```http
GET /mars/tile/4/8/5.jpg?layer=Mars_Viking_MDIM21_ClrMosaic_global_232m
```

Returns the Mars tile from Viking mosaic at zoom level 4, tile (8, 5).

---

## ✅ Status Codes

* `200 OK` – Successful tile or metadata response
* `400 Bad Request` – Validation or parameter issues
* `404 Not Found` – Tile not available or out of bounds
* `502 Upstream Error` – Error from NASA WMTS

---

## 📄 License

MIT License © 2025

---

## 🤝 Acknowledgements

* [NASA GIBS](https://earthdata.nasa.gov/gibs) & [NASA Trek WMTS](https://trek.nasa.gov/)
* [FastAPI](https://fastapi.tiangolo.com/)
* [OpenPlanetary](https://openplanetary.org/)

---

> Built for planetary exploration with open data and open minds. 🌌


