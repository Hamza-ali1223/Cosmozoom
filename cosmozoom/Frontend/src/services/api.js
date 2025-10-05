// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'https://49cc9707d4ff.ngrok-free.app'; // Your FastAPI backend

/**
 * API service for communicating with NASA imagery backend
 */
class NasaImageryAPI {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 15000, // Reduced to 15 seconds for faster failure detection
      headers: {
        'ngrok-skip-browser-warning': 'true'
      }
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for logging and error handling
    this.client.interceptors.response.use(
      (response) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        const url = error.config?.url || 'unknown';
        const status = error.response?.status || 'no response';
        const message = error.response?.data?.detail || error.message;
        
        console.error(`❌ API Error: ${status} ${url} - ${message}`);
        
        // Enhanced error object with more context
        const enhancedError = {
          ...error,
          isNetworkError: !error.response,
          isServerError: error.response?.status >= 500,
          isClientError: error.response?.status >= 400 && error.response?.status < 500,
          isTileError: url.includes('/tile'),
          url,
          status,
          message
        };
        
        return Promise.reject(enhancedError);
      }
    );
  }

  /**
   * Retry logic for failed requests
   */
  async retryRequest(requestFn, maxRetries = 3, baseDelay = 1000) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        const isLastAttempt = attempt === maxRetries;
        const shouldRetry = error.isNetworkError || error.isServerError;
        
        if (isLastAttempt || !shouldRetry) {
          throw error;
        }
        
        const delay = baseDelay * Math.pow(2, attempt - 1); // Exponential backoff
        console.log(`🔄 Retrying in ${delay}ms (attempt ${attempt}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  /**
   * Health check for a specific planet service
   */
  async getHealth(planet) {
    return this.retryRequest(async () => {
      try {
        const response = await this.client.get(`/${planet}`);
        return {
          ...response.data,
          planet,
          timestamp: new Date().toISOString(),
          success: true
        };
      } catch (error) {
        console.error(`Health check failed for ${planet}:`, error);
        return {
          status: 'error',
          planet,
          timestamp: new Date().toISOString(),
          success: false,
          error: error.message
        };
      }
    });
  }

  /**
   * Get Moon tile
   * @param {number} z - Zoom level (0-8)
   * @param {number} x - Tile column
   * @param {number} y - Tile row
   * @param {string} format - Image format (jpg, png)
   */
  getMoonTileURL(z, x, y, format = 'jpg') {
    const url = `${this.baseURL}/moon/tile?z=${z}&x=${x}&y=${y}&format=${format}`;
    console.log(`🌙 Moon tile URL: ${url}`);
    return url;
  }

  /**
   * Get Mercury tile
   * @param {number} z - Zoom level (0-7)
   * @param {number} x - Tile column
   * @param {number} y - Tile row
   * @param {string} format - Image format (jpg)
   */
  getMercuryTileURL(z, x, y, format = 'jpg') {
    const url = `${this.baseURL}/mercury/tile?z=${z}&x=${x}&y=${y}&format=${format}`;
    console.log(`☿️ Mercury tile URL: ${url}`);
    return url;
  }

  /**
   * Get Earth tile
   * @param {number} z - Zoom level (0-9)
   * @param {number} x - Tile column
   * @param {number} y - Tile row
   * @param {string} date - Date in YYYY-MM-DD format
   * @param {string} layer - Layer name
   * @param {string} format - Image format (jpg, png)
   */
  getEarthTileURL(z, x, y, date, layer, format = 'jpg') {
    const url = `${this.baseURL}/earth/tile?z=${z}&x=${x}&y=${y}&date=${date}&layer=${layer}&format=${format}`;
    console.log(`🌍 Earth tile URL: ${url}`);
    return url;
  }

  // ⬇️ ADD MARS METHOD HERE ⬇️
  /**
   * Get Mars tile URL
   * @param {number} z - Zoom level (0-7)
   * @param {number} x - Tile column
   * @param {number} y - Tile row
   * @param {string} layer - Layer name (viking or mola)
   * @param {string} format - Image format (jpg, png)
   */
  getMarsTileURL(z, x, y, layer = 'viking', format = 'jpg') {
    const url = `${this.baseURL}/mars/tile?z=${z}&x=${x}&y=${y}&layer=${layer}&format=${format}`;
    console.log(`🔴 Mars tile URL: ${url}`);
    return url;
  }

  /**
   * Get capabilities for a planet
   */
  async getCapabilities(planet) {
    return this.retryRequest(async () => {
      try {
        const response = await this.client.get(`/${planet}/capabilities`);
        return response.data;
      } catch (error) {
        console.error(`Failed to get capabilities for ${planet}:`, error);
        throw error;
      }
    });
  }

  /**
   * Test tile endpoint to check if tiles are loading
   */
  async testTileEndpoint(planet, z = 1, x = 1, y = 1) {
    try {
      let url;
      switch (planet) {
        case 'moon':
          url = this.getMoonTileURL(z, x, y);
          break;
        case 'mercury':
          url = this.getMercuryTileURL(z, x, y);
          break;
        case 'earth':
          const yesterday = new Date();
          yesterday.setDate(yesterday.getDate() - 1);
          const dateStr = yesterday.toISOString().split('T')[0];
          url = this.getEarthTileURL(z, x, y, dateStr, 'MODIS_Terra_CorrectedReflectance_TrueColor');
          break;
        case 'mars':
          url = this.getMarsTileURL(z, x, y);
          break;
        default:
          throw new Error(`Unknown planet: ${planet}`);
      }

      const response = await fetch(url, { method: 'HEAD' });
      return {
        success: response.ok,
        status: response.status,
        url,
        planet
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        url: 'unknown',
        planet
      };
    }
  }
}

export default new NasaImageryAPI();