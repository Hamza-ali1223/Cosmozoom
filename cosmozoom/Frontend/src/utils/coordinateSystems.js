// src/utils/coordinateSystems.js

/**
 * Coordinate system configurations for different celestial bodies
 */
export const COORDINATE_SYSTEMS = {
  earth: {
    name: "Geographic Coordinates",
    shortName: "Geographic",
    description: "Standard Earth latitude and longitude",
    latRange: [-90, 90],
    lngRange: [-180, 180],
    latLabel: "Latitude",
    lngLabel: "Longitude", 
    example: {
      lat: "40.7128",
      lng: "-74.0060",
      location: "New York City"
    },
    icon: "🌍"
  },
  moon: {
    name: "Selenographic Coordinates",
    shortName: "Selenographic",
    description: "Moon's latitude and longitude system",
    latRange: [-90, 90],
    lngRange: [-180, 180],
    latLabel: "Selenographic Latitude",
    lngLabel: "Selenographic Longitude",
    example: {
      lat: "0.674",
      lng: "23.473",
      location: "Apollo 11 Landing Site"
    },
    icon: "🌙"
  },
  mars: {
    name: "Areographic Coordinates", 
    shortName: "Areographic",
    description: "Mars latitude and longitude system",
    latRange: [-90, 90],
    lngRange: [-180, 180], // We'll normalize 0-360° to -180/180°
    latLabel: "Areographic Latitude",
    lngLabel: "Areographic Longitude",
    example: {
      lat: "18.65",
      lng: "-133.8",
      location: "Olympus Mons"
    },
    acceptsAltFormat: true,
    altFormatDesc: "Also accepts 0° to 360° longitude format",
    icon: "🔴"
  },
  mercury: {
    name: "Mercurian Coordinates",
    shortName: "Mercurian", 
    description: "Mercury's latitude and longitude system",
    latRange: [-90, 90],
    lngRange: [-180, 180],
    latLabel: "Mercurian Latitude",
    lngLabel: "Mercurian Longitude",
    example: {
      lat: "30.0",
      lng: "171.0", 
      location: "Caloris Basin"
    },
    icon: "☿️"
  }
};

/**
 * Get coordinate system configuration for a planet
 */
export function getCoordinateSystem(planetId) {
  return COORDINATE_SYSTEMS[planetId] || COORDINATE_SYSTEMS.earth;
}

/**
 * Validate coordinates for a specific planet
 */
export function validateCoordinates(planetId, lat, lng) {
  const system = getCoordinateSystem(planetId);
  const errors = [];

  // Validate latitude
  if (lat < system.latRange[0] || lat > system.latRange[1]) {
    errors.push(`${system.latLabel} must be between ${system.latRange[0]}° and ${system.latRange[1]}°`);
  }

  // Validate longitude
  let normalizedLng = lng;
  
  // Handle Mars special case: convert 0-360° to -180/180°
  if (planetId === 'mars' && lng >= 0 && lng <= 360) {
    normalizedLng = lng > 180 ? lng - 360 : lng;
  }

  if (normalizedLng < system.lngRange[0] || normalizedLng > system.lngRange[1]) {
    if (planetId === 'mars') {
      errors.push(`${system.lngLabel} must be between ${system.lngRange[0]}° and ${system.lngRange[1]}° or 0° to 360°`);
    } else {
      errors.push(`${system.lngLabel} must be between ${system.lngRange[0]}° and ${system.lngRange[1]}°`);
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    normalizedLng
  };
}

/**
 * Format coordinate examples for display
 */
export function getCoordinateExample(planetId) {
  const system = getCoordinateSystem(planetId);
  return `${system.example.lat}, ${system.example.lng} (${system.example.location})`;
}

/**
 * Get coordinate system help text
 */
export function getCoordinateHelp(planetId) {
  const system = getCoordinateSystem(planetId);
  let help = `${system.icon} ${system.name}: ${system.description}`;
  
  if (system.acceptsAltFormat) {
    help += `\n${system.altFormatDesc}`;
  }
  
  return help;
}