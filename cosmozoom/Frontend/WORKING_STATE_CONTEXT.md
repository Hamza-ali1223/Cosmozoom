# Cosmo Zoom - Working State Context

## Current Working Features (DO NOT BREAK)

### Core Functionality
- ✅ **Coordinate Search**: Latitude/longitude search with validation
- ✅ **Map Navigation**: Zoom in, zoom out, reset view controls
- ✅ **Planet Switching**: Works across Moon, Mercury, Earth, Mars
- ✅ **Date Selection**: For Earth imagery with date picker
- ✅ **Earth Comparison Mode**: Side-by-side image comparison for Earth only

### Technical Implementation
- ✅ **API Integration**: Enhanced error handling with retry logic
- ✅ **Tile Loading**: With error handling and loading indicators
- ✅ **State Management**: Proper state lifting for comparison mode
- ✅ **Component Structure**: Map, Controls, PlanetSelector all working

### Earth Comparison Feature (CRITICAL)
- ✅ **Toggle Button**: "🔍 Compare Images" / "🔄 Exit Comparison"
- ✅ **Side-by-Side View**: Two maps displayed when in comparison mode
- ✅ **Date Labels**: Shows dates on each map in comparison
- ✅ **External Controls**: Controls outside MapContainer in comparison mode
- ✅ **State Communication**: Map manages comparison state, Controls receives props

### File Structure (DO NOT MODIFY CORE LOGIC)
```
src/
├── App.js - Main app with health checks and state
├── App.css - Styling (can modify colors/UI only)
├── components/
│   ├── Map.jsx - Conditional rendering for single/comparison mode
│   ├── Controls.jsx - Search + comparison controls
│   ├── PlanetSelector.jsx - Planet selection
│   └── LayerSelector.jsx - Layer selection
├── services/
│   └── api.js - Enhanced with retry logic and error handling
└── utils/
    ├── planets.js - Planet configurations
    └── diagnostics.js - API diagnostics utility
```

### Component Props (MAINTAIN INTERFACES)
```javascript
// Map.jsx
<Map planet={planet} selectedDate={selectedDate} onDateChange={onDateChange} />

// Controls.jsx (inside MapContainer)
<Controls 
  planet={planet}
  onDateChange={onDateChange}
  selectedDate={selectedDate}
  isComparisonMode={isComparisonMode}
  onComparisonModeChange={setIsComparisonMode}
  comparisonDate={comparisonDate}
  onComparisonDateChange={setComparisonDate}
/>
```

### Critical CSS Classes (STYLE ONLY, DON'T REMOVE)
- `.comparison-maps` - Side-by-side container
- `.comparison-map-container` - Individual map wrapper
- `.comparison-map-label` - Date labels on maps
- `.search-controls` - Coordinate search section
- `.map-controls` - Main controls panel

## UI/Styling Changes (SAFE TO MODIFY)
- ✅ Colors, spacing, fonts
- ✅ Layout positioning
- ✅ Visual effects and animations
- ✅ Add new UI elements (drawer, buttons)

## NEVER MODIFY
- Component prop interfaces
- State management logic
- API endpoints or service calls
- Core functionality logic
- Comparison mode implementation
- Search validation logic

## Recovery Instructions
If functionality breaks, restore these key elements:
1. Map component's conditional rendering for comparison mode
2. Controls component prop interface
3. State management in Map component
4. API service retry logic
5. CSS classes for comparison layout

## Last Working State: October 5, 2025
All features tested and working including coordinate search and Earth comparison mode.