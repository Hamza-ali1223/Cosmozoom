// src/utils/diagnostics.js
import api from '../services/api';

/**
 * Comprehensive diagnostic utility for testing API endpoints
 */
export class APIDiagnostics {
  
  /**
   * Test all planets' health endpoints
   */
  static async testAllPlanetsHealth() {
    const planets = ['moon', 'mercury', 'earth', 'mars'];
    const results = {};
    
    console.log('🔍 Testing all planet health endpoints...');
    
    for (const planet of planets) {
      try {
        const start = Date.now();
        const health = await api.getHealth(planet);
        const duration = Date.now() - start;
        
        results[planet] = {
          success: health.success,
          status: health.status,
          duration: `${duration}ms`,
          timestamp: new Date().toISOString()
        };
        
        console.log(`${planet}: ${health.success ? '✅' : '❌'} (${duration}ms)`);
      } catch (error) {
        results[planet] = {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        };
        console.log(`${planet}: ❌ ${error.message}`);
      }
    }
    
    return results;
  }
  
  /**
   * Test tile endpoints for all planets
   */
  static async testAllPlanetsTiles() {
    const planets = ['moon', 'mercury', 'earth', 'mars'];
    const results = {};
    
    console.log('🗺️ Testing all planet tile endpoints...');
    
    for (const planet of planets) {
      try {
        const start = Date.now();
        const tileTest = await api.testTileEndpoint(planet);
        const duration = Date.now() - start;
        
        results[planet] = {
          ...tileTest,
          duration: `${duration}ms`,
          timestamp: new Date().toISOString()
        };
        
        console.log(`${planet} tiles: ${tileTest.success ? '✅' : '❌'} (${duration}ms)`);
      } catch (error) {
        results[planet] = {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        };
        console.log(`${planet} tiles: ❌ ${error.message}`);
      }
    }
    
    return results;
  }
  
  /**
   * Run comprehensive diagnostics
   */
  static async runFullDiagnostics() {
    console.log('🚀 Running full API diagnostics...');
    
    const healthResults = await this.testAllPlanetsHealth();
    const tileResults = await this.testAllPlanetsTiles();
    
    const summary = {
      timestamp: new Date().toISOString(),
      health: healthResults,
      tiles: tileResults,
      summary: {
        healthyPlanets: Object.values(healthResults).filter(r => r.success).length,
        totalPlanets: Object.keys(healthResults).length,
        workingTiles: Object.values(tileResults).filter(r => r.success).length,
        totalTileEndpoints: Object.keys(tileResults).length
      }
    };
    
    console.log('📊 Diagnostics Summary:', summary);
    return summary;
  }
  
  /**
   * Monitor API for a specified duration
   */
  static async monitorAPI(durationMinutes = 5) {
    const startTime = Date.now();
    const endTime = startTime + (durationMinutes * 60 * 1000);
    const results = [];
    
    console.log(`📡 Monitoring API for ${durationMinutes} minutes...`);
    
    while (Date.now() < endTime) {
      const result = await this.runFullDiagnostics();
      results.push(result);
      
      // Wait 30 seconds before next check
      await new Promise(resolve => setTimeout(resolve, 30000));
    }
    
    console.log(`📈 Monitoring complete. Collected ${results.length} data points.`);
    return results;
  }
}

// Make it available globally for console debugging
if (typeof window !== 'undefined') {
  window.APIDiagnostics = APIDiagnostics;
}

export default APIDiagnostics;