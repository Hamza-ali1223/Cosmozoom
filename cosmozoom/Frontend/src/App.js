// src/App.jsx
import React, { useState, useEffect } from 'react';
import Map from './components/Map';
import PlanetSelector from './components/PlanetSelector';
import { PLANETS, getYesterdayDate } from './utils/planets';
import api from './services/api';
import APIDiagnostics from './utils/diagnostics';
import './App.css';
import LayerSelector from './components/LayerSelector'; // ⬅️ Import LayerSelector
function App() {
  const [selectedPlanetId, setSelectedPlanetId] = useState('moon');
  const [selectedDate, setSelectedDate] = useState(getYesterdayDate());
  const [sidebarOpen, setSidebarOpen] = useState(true); // Add sidebar toggle state
  
  const [isHealthy, setIsHealthy] = useState(null);
  const [loading, setLoading] = useState(false);

  const currentPlanet = PLANETS[selectedPlanetId];

  // Health check when planet changes
  useEffect(() => {
    checkHealth();
     
  }, [selectedPlanetId]);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const health = await api.getHealth(selectedPlanetId);
      const isHealthy = health.success && (health.status === 'ok' || health.status === 'operational');
      setIsHealthy(isHealthy);
      
      console.log(`${selectedPlanetId} health:`, health);
      
      // Test tile endpoint as well
      if (isHealthy) {
        const tileTest = await api.testTileEndpoint(selectedPlanetId);
        console.log(`${selectedPlanetId} tile test:`, tileTest);
        if (!tileTest.success) {
          console.warn(`Tiles may not be loading properly for ${selectedPlanetId}`);
        }
      }
    } catch (error) {
      setIsHealthy(false);
      console.error('Health check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanetChange = (planetId) => {
    setSelectedPlanetId(planetId);
  };

  const handleDateChange = (date) => {
    setSelectedDate(date);
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <button className="drawer-toggle" onClick={toggleSidebar}>
            {sidebarOpen ? '⮨' : '⮧'}
          </button>
          <h1>🌌 Cosmo Zoom</h1>
          <p className="subtitle">Explore Planetary Surfaces</p>
        </div>
      </header>

      <div className="app-container">
        <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <PlanetSelector
            selectedPlanet={selectedPlanetId}
            onPlanetChange={handlePlanetChange}
          />
          <div className="status-indicator">
            {loading ? (
              <span className="status loading">Checking...</span>
            ) : isHealthy === true ? (
              <span className="status healthy">Service Operational</span>
            ) : isHealthy === false ? (
              <span className="status unhealthy">Service Unavailable</span>
            ) : null}
          </div>

          <div className="info-section">
            <h3>About {currentPlanet.name}</h3>
            <ul>
              <li><strong>Max Zoom:</strong> {currentPlanet.maxZoom}</li>
              <li><strong>Format:</strong> {currentPlanet.format.toUpperCase()}</li>
              <li><strong>Source:</strong> {currentPlanet.attribution}</li>
            </ul>
          </div>
        </aside>

        <main className="map-container">
          {isHealthy === false ? (
            <div className="error-state">
              <h2>Service Unavailable</h2>
              <p>Unable to connect to {currentPlanet.name} tile service.</p>
              <button onClick={checkHealth} className="retry-btn">
                Retry
              </button>
            </div>
          ) : (
            <Map
              planet={currentPlanet}
              selectedDate={selectedDate}
              onDateChange={handleDateChange}
              
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;