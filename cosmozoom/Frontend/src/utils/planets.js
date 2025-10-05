// src/utils/planets.js

export const PLANETS = {
  moon: {
    id: 'moon',
    name: 'Moon',
    icon: '🌙',
    maxZoom: 8,
    minZoom: 0,
    defaultZoom: 2,
    center: [0, 0], // Lat, Lng for Leaflet
    defaultLayer: 'LRO_WAC_Mosaic_Global_303ppd_v02',
    format: 'jpg',
    attribution: 'NASA Trek - Lunar Reconnaissance Orbiter',
    description: 'Lunar surface imagery from LRO',
  },
  mercury: {
    id: 'mercury',
    name: 'Mercury',
    icon: '☿️',
    maxZoom: 7,
    minZoom: 0,
    defaultZoom: 2,
    center: [0, 0],
    defaultLayer: 'Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m',
    format: 'jpg',
    attribution: 'NASA Trek - MESSENGER MDIS',
    description: 'Mercury surface imagery from MESSENGER',
  },
  earth: {
    id: 'earth',
    name: 'Earth',
    icon: '🌍',
    maxZoom: 9,
    minZoom: 0,
    defaultZoom: 3,
    center: [20, 0],
    defaultLayer: 'VIIRS_SNPP_CorrectedReflectance_TrueColor',
    format: 'jpg',
    attribution: 'NASA GIBS',
    description: 'Earth satellite imagery (date-based)',
    requiresDate: true,
    layers: [
      {
        id: 'VIIRS_SNPP_CorrectedReflectance_TrueColor',
        name: 'VIIRS True Color',
        description: 'Daily true color imagery'
      },
      {
        id: 'MODIS_Terra_CorrectedReflectance_TrueColor',
        name: 'MODIS Terra True Color',
        description: 'Terra satellite true color'
      },
      {
        id: 'MODIS_Aqua_CorrectedReflectance_TrueColor',
        name: 'MODIS Aqua True Color',
        description: 'Aqua satellite true color'
      }
    ]
  },
   // ⬇️ ADD MARS HERE ⬇️
  mars: {
    id: 'mars',
    name: 'Mars',
    icon: '🔴',
    maxZoom: 7,
    minZoom: 0,
    defaultZoom: 2,
    center: [0, 0],
    defaultLayer: 'Mars_Viking_MDIM21_ClrMosaic_global_232m',
    format: 'jpg',
    attribution: 'NASA Trek - Viking Orbiter',
    description: 'Mars surface imagery from Viking missions',
    layers: [
      {
        id: 'viking',
        name: 'Viking Color Mosaic',
        description: 'Global color mosaic - 232m/pixel'
      },
      {
        id: 'mola',
        name: 'MOLA Elevation',
        description: 'Topographic elevation data - 463m/pixel'
      }
    ]
  }
};

/**
 * Get today's date in YYYY-MM-DD format
 */
export function getTodayDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Get yesterday's date (GIBS might not have today yet)
 */
export function getYesterdayDate() {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const year = yesterday.getFullYear();
  const month = String(yesterday.getMonth() + 1).padStart(2, '0');
  const day = String(yesterday.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}