
# 🌌 Cosmozoom

**Cosmozoom** is an open-source, multi-planetary map exploration tool inspired by Google Maps — but for space. It allows users to **explore the surface of Earth, Mars, Moon, and Mercury** using high-resolution tiles provided by **NASA** and **Google Jeep** services. The project consists of:

- 🌐 A modern **React + Leaflet.js** frontend
- 🛰️ A fast **FastAPI** backend that proxies and serves planetary imagery tiles via NASA WMTS services

---



## 📸 Preview

![Cosmozoom Mars View](./cosmozoom/frontend/image.png)  
*Mars surface imagery from NASA Trek - Viking Orbiter*

---

## 📁 Project Structure

```bash
cosmozoom/
├── frontend/      # React + Leaflet.js planetary map viewer
├── backend/       # FastAPI tile proxy for NASA WMTS APIs
└── README.md      # You're here!
````

---

## 🛰️ Features

* Interactive exploration of **Mars**, **Earth**, **Moon**, and **Mercury**
* High-res tiles served from **NASA GIBS** and **Trek WMTS**
* Leaflet-based zoom, pan, and aerographic search
* Custom planetary metadata and dynamic tile fetching
* API proxy layer handles upstream services securely and reliably

---

## 🖥️ Frontend Setup (`frontend/`)

### Tech Stack

* React + Vite
* Leaflet.js
* Axios

### Steps

```bash
cd frontend
npm install
```

Before running, **update the backend base URL** in:

```js
// src/services/api.js

const BASE_URL = 'http://localhost:8000'; // 🔧 Change this to your backend URL
```

Then start the dev server:

```bash
npm run dev
```

> App runs on: `http://localhost:3000`

---

## 🔧 Backend Setup (`backend/`)

### Tech Stack

* FastAPI (Python)
* HTTPX / Uvicorn

### Steps

```bash
cd backend
pip install -r requirements.txt
python ./main.py
```

> API available at: `http://localhost:8000`
> Swagger Docs: `http://localhost:8000/docs`

### Main Endpoints

| Method | Endpoint                    | Description                    |
| ------ | --------------------------- | ------------------------------ |
| GET    | `/health`                   | Health check                   |
| GET    | `/earth/tile/{z}/{x}/{y}`   | Earth tile via GIBS            |
| GET    | `/mars/tile/{z}/{x}/{y}`    | Mars tile via Trek             |
| GET    | `/moon/tile/{z}/{x}/{y}`    | Moon tile                      |
| GET    | `/mercury/tile/{z}/{x}/{y}` | Mercury tile                   |
| GET    | `/[planet]/info`            | Available layers for each body |

For full API reference, visit: `http://localhost:8000/docs`

---

## ✅ Environment Requirements

* Node.js (v18+ recommended)
* Python 3.10+
* Git & pip

---

## 🛠️ Development Notes

* Coordinate system uses **aerographic latitude/longitude** for Mars/Moon
* Accepts both `0° - 360°` and `-180° to 180°` longitude formats
* All tiles are fetched on demand and rendered via Leaflet

---
