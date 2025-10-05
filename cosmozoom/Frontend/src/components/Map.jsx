// src/components/Map.jsx
import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import { CRS } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import api from '../services/api';
import Controls from './Controls';

/**
 * Component to update map view when planet changes
 */
function MapViewController({ planet }) {
  const map = useMap();

  useEffect(() => {
    map.setView(planet.center, planet.defaultZoom);
    map.setMaxZoom(planet.maxZoom);
    map.setMinZoom(planet.minZoom);
  }, [planet, map]);

  return null;
}

function Map({ planet, selectedDate, onDateChange }) {
  const [tileLayerKey, setTileLayerKey] = useState(0);
  const [tileErrors, setTileErrors] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  
  // Comparison mode state
  const [isComparisonMode, setIsComparisonMode] = useState(false);
  const [comparisonDate, setComparisonDate] = useState(selectedDate);

  // Force tile layer refresh when planet or date changes
  useEffect(() => {
    setTileLayerKey(prev => prev + 1);
    setTileErrors(0);
    setIsLoading(true);
    // Reset comparison mode when switching planets
    if (planet.id !== 'earth') {
      setIsComparisonMode(false);
    }
  }, [planet.id, selectedDate]);

  // Handle tile loading events
  const handleTileLoadStart = () => {
    setIsLoading(true);
  };

  const handleTileLoad = () => {
    setIsLoading(false);
  };

  const handleTileError = (error) => {
    console.error('Tile loading error:', error);
    setTileErrors(prev => prev + 1);
    setIsLoading(false);
  };

  // Generate tile URL based on planet
  const getTileUrl = () => {
    switch (planet.id) {
      case 'moon':
        return api.getMoonTileURL('{z}', '{x}', '{y}', planet.format);
      case 'mercury':
        return api.getMercuryTileURL('{z}', '{x}', '{y}', planet.format);
      case 'earth':
        return api.getEarthTileURL(
          '{z}',
          '{x}',
          '{y}',
          selectedDate,
          planet.defaultLayer,
          planet.format
        );
         // ⬇️ ADD MARS CASE HERE ⬇️
      case 'mars':
        return api.getMarsTileURL(
          '{z}',
          '{x}',
          '{y}',
         'viking', // Use selected layer or default to viking
          planet.format
        );
      default:
        return '';
    }
  };

  return (
    <div className="map-wrapper">
      {tileErrors > 10 && (
        <div className="tile-error-warning">
          ⚠️ Some map tiles failed to load. The server might be experiencing issues.
        </div>
      )}
      
      {isLoading && (
        <div className="loading-indicator">
          🔄 Loading map tiles...
        </div>
      )}
      
      {planet.id === 'earth' && isComparisonMode ? (
        // Comparison mode: two maps side by side
        <div className="comparison-maps">
          <div className="comparison-map-container">
            <div className="comparison-map-label">
              {selectedDate}
            </div>
            <MapContainer
              center={planet.center}
              zoom={planet.defaultZoom}
              minZoom={planet.minZoom}
              maxZoom={planet.maxZoom}
              crs={CRS.EPSG3857}
              style={{ height: '100%', width: '100%' }}
              zoomControl={false}
            >
              <MapViewController planet={planet} />
              <TileLayer
                key={`main-${tileLayerKey}`}
                url={getTileUrl()}
                attribution={planet.attribution}
                maxZoom={planet.maxZoom}
                minZoom={planet.minZoom}
                tileSize={256}
                noWrap={false}
                eventHandlers={{
                  loading: handleTileLoadStart,
                  load: handleTileLoad,
                  tileerror: handleTileError,
                }}
              />
            </MapContainer>
          </div>
          
          <div className="comparison-map-container">
            <div className="comparison-map-label">
              {comparisonDate}
            </div>
            <MapContainer
              center={planet.center}
              zoom={planet.defaultZoom}
              minZoom={planet.minZoom}
              maxZoom={planet.maxZoom}
              crs={CRS.EPSG3857}
              style={{ height: '100%', width: '100%' }}
              zoomControl={false}
            >
              <MapViewController planet={planet} />
              <TileLayer
                key={`comparison-${tileLayerKey}`}
                url={api.getEarthTileURL('{z}', '{x}', '{y}', comparisonDate, planet.defaultLayer, planet.format)}
                attribution={planet.attribution}
                maxZoom={planet.maxZoom}
                minZoom={planet.minZoom}
                tileSize={256}
                noWrap={false}
                eventHandlers={{
                  loading: handleTileLoadStart,
                  load: handleTileLoad,
                  tileerror: handleTileError,
                }}
              />
            </MapContainer>
          </div>
        </div>
      ) : (
        // Normal mode: single map
        <MapContainer
          center={planet.center}
          zoom={planet.defaultZoom}
          minZoom={planet.minZoom}
          maxZoom={planet.maxZoom}
          crs={CRS.EPSG3857}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          <MapViewController planet={planet} />
          
          <TileLayer
            key={tileLayerKey}
            url={getTileUrl()}
            attribution={planet.attribution}
            maxZoom={planet.maxZoom}
            minZoom={planet.minZoom}
            tileSize={256}
            noWrap={false}
            eventHandlers={{
              loading: handleTileLoadStart,
              load: handleTileLoad,
              tileerror: handleTileError,
            }}
          />

          <Controls
            planet={planet}
            onDateChange={onDateChange}
            selectedDate={selectedDate}
            isComparisonMode={isComparisonMode}
            onComparisonModeChange={setIsComparisonMode}
            comparisonDate={comparisonDate}
            onComparisonDateChange={setComparisonDate}
          />
        </MapContainer>
      )}
      
      {/* Controls for comparison mode (outside MapContainer to avoid hook issues) */}
      {planet.id === 'earth' && isComparisonMode && (
        <div className="map-controls">
          <div className="control-group comparison-control">
            <button 
              onClick={() => setIsComparisonMode(false)} 
              className="control-btn comparison-btn active"
            >
              🔄 Exit Comparison
            </button>
            
            <div className="comparison-date-control">
              <label htmlFor="comparison-date-picker-external">Compare with:</label>
              <input
                id="comparison-date-picker-external"
                type="date"
                value={comparisonDate}
                onChange={(e) => setComparisonDate(e.target.value)}
                max={new Date().toISOString().split('T')[0]}
                className="date-input"
              />
            </div>
          </div>

          <div className="control-group date-control">
            <label htmlFor="date-picker-external">Main Date:</label>
            <input
              id="date-picker-external"
              type="date"
              value={selectedDate}
              onChange={(e) => onDateChange(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              className="date-input"
            />
          </div>

          <div className="info-panel">
            <p>Max Zoom: {planet.maxZoom}</p>
            <p>Attribution: {planet.attribution}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Map;