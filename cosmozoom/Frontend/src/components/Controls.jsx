
import React, { useState } from 'react';
import { useMap } from 'react-leaflet';
import { getCoordinateSystem, validateCoordinates, getCoordinateExample, getCoordinateHelp } from '../utils/coordinateSystems';

function Controls({ 
  planet, 
  onDateChange, 
  selectedDate, 
  isComparisonMode, 
  onComparisonModeChange, 
  comparisonDate, 
  onComparisonDateChange 
}) {
  const map = useMap();
  const planetConfig = planet;
  const coordSystem = getCoordinateSystem(planetConfig.id);
  
  // State for latitude/longitude search
  const [searchLat, setSearchLat] = useState('');
  const [searchLng, setSearchLng] = useState('');
  const [searchError, setSearchError] = useState('');

  const handleZoomIn = () => {
    map.zoomIn();
  };

  const handleZoomOut = () => {
    map.zoomOut();
  };

  const handleReset = () => {
    map.setView(planetConfig.center, planetConfig.defaultZoom);
  };

  const handleCoordinateSearch = () => {
    // Clear previous errors
    setSearchError('');
    
    // Validate inputs
    const lat = parseFloat(searchLat);
    const lng = parseFloat(searchLng);
    
    // Check if values are valid numbers
    if (isNaN(lat) || isNaN(lng)) {
      setSearchError(`Please enter valid numbers for both ${coordSystem.latLabel.toLowerCase()} and ${coordSystem.lngLabel.toLowerCase()}`);
      return;
    }
    
    // Use planet-specific validation
    const validation = validateCoordinates(planetConfig.id, lat, lng);
    
    if (!validation.isValid) {
      setSearchError(validation.errors[0]); // Show first error
      return;
    }
    
    // Use normalized longitude for Mars if needed
    const normalizedLng = validation.normalizedLng;
    
    // Navigate to the coordinates with a reasonable zoom level
    const zoomLevel = Math.min(planetConfig.maxZoom - 2, 8);
    map.setView([lat, normalizedLng], zoomLevel);
    
    // Clear search fields after successful search
    setSearchLat('');
    setSearchLng('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleCoordinateSearch();
    }
  };

  const toggleComparisonMode = () => {
    onComparisonModeChange(!isComparisonMode);
  };

  return (
    <div className="map-controls">
      <div className="control-group">
        <button onClick={handleZoomIn} className="control-btn">
          ➕ Zoom In
        </button>
        <button onClick={handleZoomOut} className="control-btn">
          ➖ Zoom Out
        </button>
        <button onClick={handleReset} className="control-btn">
          Reset View
        </button>
      </div>

      {/* Coordinate Search Section */}
      <div className="control-group search-controls">
        <h4>{coordSystem.icon} {coordSystem.shortName} Search</h4>
        <div className="coordinate-system-info">
          <small>{coordSystem.description}</small>
          {coordSystem.acceptsAltFormat && (
            <small className="alt-format">{coordSystem.altFormatDesc}</small>
          )}
        </div>
        <div className="coordinate-inputs">
          <div className="input-group">
            <label htmlFor="latitude">{coordSystem.latLabel}:</label>
            <input
              id="latitude"
              type="number"
              value={searchLat}
              onChange={(e) => setSearchLat(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={coordSystem.example.lat}
              step="any"
              min={coordSystem.latRange[0]}
              max={coordSystem.latRange[1]}
              className="coordinate-input"
            />
          </div>
          <div className="input-group">
            <label htmlFor="longitude">{coordSystem.lngLabel}:</label>
            <input
              id="longitude"
              type="number"
              value={searchLng}
              onChange={(e) => setSearchLng(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={coordSystem.example.lng}
              step="any"
              min={planetConfig.id === 'mars' ? 0 : coordSystem.lngRange[0]}
              max={planetConfig.id === 'mars' ? 360 : coordSystem.lngRange[1]}
              className="coordinate-input"
            />
          </div>
        </div>
        <div className="coordinate-example">
          <small>📍 Example: {getCoordinateExample(planetConfig.id)}</small>
        </div>
        <button 
          onClick={handleCoordinateSearch} 
          className="control-btn search-btn"
          disabled={!searchLat || !searchLng}
        >
          🎯 Go to Coordinates
        </button>
        {searchError && (
          <div className="error-message">
            ⚠️ {searchError}
          </div>
        )}
      </div>

      {planetConfig.requiresDate && (
        <div className="control-group date-control">
          <label htmlFor="date-picker">Date:</label>
          <input
            id="date-picker"
            type="date"
            value={selectedDate}
            onChange={(e) => onDateChange(e.target.value)}
            max={new Date().toISOString().split('T')[0]}
            className="date-input"
          />
        </div>
      )}

      {/* Earth Comparison Mode */}
      {planetConfig.id === 'earth' && (
        <div className="control-group comparison-control">
          <button 
            onClick={toggleComparisonMode} 
            className={`control-btn comparison-btn ${isComparisonMode ? 'active' : ''}`}
          >
            {isComparisonMode ? '🔄 Exit Comparison' : '🔍 Compare Images'}
          </button>
          
          {isComparisonMode && (
            <div className="comparison-date-control">
              <label htmlFor="comparison-date-picker">Compare with:</label>
              <input
                id="comparison-date-picker"
                type="date"
                value={comparisonDate}
                onChange={(e) => onComparisonDateChange(e.target.value)}
                max={new Date().toISOString().split('T')[0]}
                className="date-input"
              />
            </div>
          )}
        </div>
      )}

      <div className="info-panel">
        <p>Max Zoom: {planetConfig.maxZoom}</p>
        <p>Attribution: {planetConfig.attribution}</p>
      </div>
    </div>
  );
}

export default Controls;