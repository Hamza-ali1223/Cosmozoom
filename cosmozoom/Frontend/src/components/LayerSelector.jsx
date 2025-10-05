// src/components/LayerSelector.jsx
import React from 'react';

function LayerSelector({ planet, selectedLayer, onLayerChange }) {
  // Only show layer selector for planets with multiple layers
  if (!planet.layers || planet.layers.length <= 1) {
    return null;
  }

  return (
    <div className="layer-selector">
      <label htmlFor="layer-select">Layer:</label>
      <select
        id="layer-select"
        value={selectedLayer || planet.layers[0].id}
        onChange={(e) => onLayerChange(e.target.value)}
        className="layer-dropdown"
      >
        {planet.layers.map((layer) => (
          <option key={layer.id} value={layer.id}>
            {layer.name}
          </option>
        ))}
      </select>
      <p className="layer-description">
        {planet.layers.find(l => l.id === (selectedLayer || planet.layers[0].id))?.description}
      </p>
    </div>
  );
}

export default LayerSelector;