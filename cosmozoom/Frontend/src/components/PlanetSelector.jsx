// src/components/PlanetSelector.jsx
import React from 'react';
import { PLANETS } from '../utils/planets';

function PlanetSelector({ selectedPlanet, onPlanetChange }) {
  return (
    <div className="planet-selector">
      <label htmlFor="planet-select">Select Celestial Body:</label>
      <select
        id="planet-select"
        value={selectedPlanet}
        onChange={(e) => onPlanetChange(e.target.value)}
        className="planet-dropdown"
      >
        {Object.values(PLANETS).map((planet) => (
          <option key={planet.id} value={planet.id}>
            {planet.icon} {planet.name}
          </option>
        ))}
      </select>
      <p className="planet-description">
        {PLANETS[selectedPlanet].description}
      </p>
    </div>
  );
}

export default PlanetSelector;