"""
NASA Trek Mercury WMTS Service - Comprehensive Test Suite
Tests all endpoints, edge cases, error handling, and performance
Generates detailed test reports with results storage
"""

import httpx
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sys


# ============================================
# CONFIGURATION
# ============================================

BASE_URL = "http://localhost:8000"
MERCURY_ENDPOINT = f"{BASE_URL}/mercury"
RESULTS_DIR = Path("test_results/mercury")
TIMEOUT = 30.0  # seconds

# Create results directory
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class TestResult:
    """Store individual test result"""
    test_name: str
    category: str
    status: str  # PASS, FAIL, ERROR
    duration_ms: float
    expected_status: int
    actual_status: int
    expected_content_type: Optional[str] = None
    actual_content_type: Optional[str] = None
    response_size: Optional[int] = None
    error_message: Optional[str] = None
    request_params: Optional[Dict] = None
    response_headers: Optional[Dict] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


@dataclass
class TestSummary:
    """Overall test execution summary"""
    total_tests: int
    passed: int
    failed: int
    errors: int
    total_duration_sec: float
    pass_rate: float
    timestamp: str
    categories: Dict[str, Dict[str, int]]
    
    def to_dict(self):
        return asdict(self)


# ============================================
# TEST RUNNER
# ============================================

class MercuryTestRunner:
    """Comprehensive test runner for Mercury service"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.client: Optional[httpx.AsyncClient] = None
        self.start_time: float = 0
        
    async def setup(self):
        """Initialize test environment"""
        print("=" * 80)
        print("Mercury Test Suite Initializing...")
        print(f"Target: {MERCURY_ENDPOINT}")
        print(f"Results directory: {RESULTS_DIR}")
        print("-" * 80)
        
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.start_time = time.time()
        
    async def teardown(self):
        """Cleanup test environment"""
        if self.client:
            await self.client.aclose()
            
    async def run_test(
        self,
        test_name: str,
        category: str,
        endpoint: str,
        params: Optional[Dict] = None,
        expected_status: int = 200,
        expected_content_type: Optional[str] = None,
        validate_json: bool = False,
        validate_image: bool = False,
        save_response: bool = False
    ) -> TestResult:
        """
        Execute a single test case
        
        Args:
            test_name: Descriptive name for the test
            category: Test category (validation, edge_cases, etc.)
            endpoint: API endpoint to test
            params: Query parameters
            expected_status: Expected HTTP status code
            expected_content_type: Expected Content-Type header
            validate_json: Whether to validate JSON response
            validate_image: Whether to validate image response
            save_response: Whether to save response to file
        """
        test_start = time.time()
        
        try:
            # Make request
            response = await self.client.get(endpoint, params=params)
            duration_ms = (time.time() - test_start) * 1000
            
            # Determine test status
            status_match = response.status_code == expected_status
            content_type_match = True
            
            actual_content_type = response.headers.get("content-type", "")
            
            if expected_content_type:
                content_type_match = expected_content_type in actual_content_type
            
            # Validate JSON response
            json_valid = True
            if validate_json and status_match:
                try:
                    json_data = response.json()
                    json_valid = isinstance(json_data, dict)
                except Exception as e:
                    json_valid = False
            
            # Validate image response
            image_valid = True
            if validate_image and status_match:
                image_valid = len(response.content) > 0 and \
                             response.content[:2] in [b'\xff\xd8', b'\x89\x50']  # JPEG or PNG
            
            # Determine overall status
            if status_match and content_type_match and json_valid and image_valid:
                status = "PASS"
            else:
                status = "FAIL"
            
            # Save response if requested
            if save_response and status == "PASS":
                await self._save_response(test_name, response, params)
            
            # Create result
            result = TestResult(
                test_name=test_name,
                category=category,
                status=status,
                duration_ms=duration_ms,
                expected_status=expected_status,
                actual_status=response.status_code,
                expected_content_type=expected_content_type,
                actual_content_type=actual_content_type,
                response_size=len(response.content),
                request_params=params,
                response_headers=dict(response.headers)
            )
            
            # Print result
            status_emoji = "[PASS]" if status == "PASS" else "[FAIL]"
            print(f"{status_emoji} {test_name:60} {duration_ms:6.1f}ms [{response.status_code}]")
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - test_start) * 1000
            
            result = TestResult(
                test_name=test_name,
                category=category,
                status="ERROR",
                duration_ms=duration_ms,
                expected_status=expected_status,
                actual_status=0,
                error_message=str(e),
                request_params=params
            )
            
            print(f"[ERROR] {test_name:60} {duration_ms:6.1f}ms [{str(e)[:50]}]")
            
            return result
    
    async def _save_response(self, test_name: str, response: httpx.Response, params: Optional[Dict]):
        """Save response content to file"""
        # Create sanitized filename
        filename = test_name.replace(" ", "_").replace("/", "_").lower()
        
        # Determine file extension
        content_type = response.headers.get("content-type", "")
        if "image/jpeg" in content_type:
            ext = ".jpg"
        elif "image/png" in content_type:
            ext = ".png"
        elif "image/tiff" in content_type:
            ext = ".tif"
        elif "application/json" in content_type:
            ext = ".json"
        else:
            ext = ".bin"
        
        # Save file
        filepath = RESULTS_DIR / f"{filename}{ext}"
        filepath.write_bytes(response.content)
        
        # Save metadata
        metadata = {
            "test_name": test_name,
            "params": params,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        metadata_path = RESULTS_DIR / f"{filename}_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    
    async def run_all_tests(self):
        """Execute all test categories"""
        await self.setup()
        
        try:
            # Run test categories
            await self.test_service_info()
            await self.test_valid_tiles()
            await self.test_zoom_levels()
            await self.test_coordinate_bounds()
            await self.test_format_variations()
            await self.test_parameter_combinations()
            await self.test_edge_cases()
            await self.test_error_handling()
            await self.test_performance()
            await self.test_caching_headers()
            await self.test_capabilities_endpoint()
            await self.test_custom_headers()
            await self.test_concurrent_requests()
            
        except Exception as e:
            print(f"\n[ERROR] Test execution failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.teardown()
            self.generate_report()
    
    # ============================================
    # TEST CATEGORIES
    # ============================================
    
    async def test_service_info(self):
        """Test service information endpoint"""
        print("\n" + "=" * 80)
        print("Testing Service Information Endpoints")
        print("=" * 80)
        
        result = await self.run_test(
            test_name="Get Mercury service info",
            category="service_info",
            endpoint=MERCURY_ENDPOINT,
            expected_status=200,
            expected_content_type="application/json",
            validate_json=True
        )
        self.results.append(result)
        
        # Validate response structure
        if result.status == "PASS":
            response = await self.client.get(MERCURY_ENDPOINT)
            data = response.json()
            
            # Check required fields
            required_fields = ["service", "celestial_body", "status", "defaults", "example"]
            for field in required_fields:
                field_result = await self.run_test(
                    test_name=f"Service info has '{field}' field",
                    category="service_info",
                    endpoint=MERCURY_ENDPOINT,
                    expected_status=200,
                    validate_json=True
                )
                field_result.status = "PASS" if field in data else "FAIL"
                self.results.append(field_result)
    
    async def test_valid_tiles(self):
        """Test valid tile requests across different zoom levels"""
        print("\n" + "=" * 80)
        print("Testing Valid Tile Requests")
        print("=" * 80)
        
        test_cases = [
            # (z, y, x)  - FIXED: Removed description from tuple
            (0, 0, 0),
            (0, 0, 1),
            (1, 0, 0),
            (1, 1, 3),
            (2, 2, 4),
            (3, 4, 8),
            (4, 8, 16),
            (5, 16, 32),
            (6, 32, 64),
            (7, 64, 128),
        ]
        
        for z, y, x in test_cases:
            result = await self.run_test(
                test_name=f"Get tile z={z}, y={y}, x={x}",
                category="valid_tiles",
                endpoint=f"{MERCURY_ENDPOINT}/tile",
                params={"z": z, "y": y, "x": x},
                expected_status=200,
                expected_content_type="image/jpeg",
                validate_image=True,
                save_response=True
            )
            self.results.append(result)
    
    async def test_zoom_levels(self):
        """Test all zoom levels (0-7)"""
        print("\n" + "=" * 80)
        print("Testing All Zoom Levels")
        print("=" * 80)
        
        for z in range(8):  # 0-7
            # Calculate valid middle coordinates for this zoom
            max_y = 2 ** z
            max_x = 2 ** (z + 1)
            y = max_y // 2
            x = max_x // 2
            
            result = await self.run_test(
                test_name=f"Zoom level {z} (matrix: {max_x}x{max_y})",
                category="zoom_levels",
                endpoint=f"{MERCURY_ENDPOINT}/tile",
                params={"z": z, "y": y, "x": x},
                expected_status=200,
                expected_content_type="image/jpeg",
                validate_image=True
            )
            self.results.append(result)
    
    async def test_coordinate_bounds(self):
        """Test coordinate boundary validation"""
        print("\n" + "=" * 80)
        print("Testing Coordinate Bounds Validation")
        print("=" * 80)
        
        # Test minimum bounds (should pass)
        result = await self.run_test(
            test_name="Minimum coordinates (0,0,0)",
            category="coordinate_bounds",
            endpoint=f"{MERCURY_ENDPOINT}/tile",
            params={"z": 0, "y": 0, "x": 0},
            expected_status=200
        )
        self.results.append(result)
        
        # Test maximum bounds for each zoom level
        for z in range(8):
            max_y = 2 ** z - 1
            max_x = 2 ** (z + 1) - 1
            
            result = await self.run_test(
                test_name=f"Maximum coordinates for z={z} ({max_x},{max_y})",
                category="coordinate_bounds",
                endpoint=f"{MERCURY_ENDPOINT}/tile",
                params={"z": z, "y": max_y, "x": max_x},
                expected_status=200
            )
            self.results.append(result)
        
        # Test out-of-bounds coordinates (should fail with 400)
        invalid_cases = [
            (3, 8, 15, "Y coordinate too high"),
            (3, 4, 16, "X coordinate too high"),
            (5, 32, 63, "Y coordinate at limit boundary"),
            (5, 16, 64, "X coordinate at limit boundary"),
            (7, 128, 255, "Y coordinate beyond maximum"),
            (7, 64, 256, "X coordinate beyond maximum"),
        ]
        
        for z, y, x, desc in invalid_cases:
            result = await self.run_test(
                test_name=f"Invalid: {desc} (z={z}, y={y}, x={x})",
                category="coordinate_bounds",
                endpoint=f"{MERCURY_ENDPOINT}/tile",
                params={"z": z, "y": y, "x": x},
                expected_status=400,
                expected_content_type="application/json"
            )
            self.results.append(result)
    
    async def test_format_variations(self):
        """Test different image format options"""
        print("\n" + "=" * 80)
        print("Testing Image Format Variations")
        print("=" * 80)
        
        formats = [
            ("jpg", "image/jpeg", True),
            ("png", "image/png", False),
            ("tif", "image/tiff", False),
        ]
        
        for fmt, expected_ct, strict in formats:
            result = await self.run_test(
                test_name=f"Format: {fmt.upper()}",
                category="format_variations",
                endpoint=f"{MERCURY_ENDPOINT}/tile",
                params={"z": 3, "y": 4, "x": 8, "format": fmt},
                expected_status=200 if strict else None,
                expected_content_type=expected_ct if strict else None,
                validate_image=strict
            )
            self.results.append(result)
        
        # Test invalid format
        result = await self.run_test(
            test_name="Invalid format: 'invalid'",
            category="format_variations",
            endpoint=f"{MERCURY_ENDPOINT}/tile",
            params={"z": 3, "y": 4, "x": 8, "format": "invalid"},
            expected_status=422,
            expected_content_type="application/json"
        )
        self.results.append(result)
    
    async def test_parameter_combinations(self):
        """Test various parameter combinations"""
        print("\n" + "=" * 80)
        print("Testing Parameter Combinations")
        print("=" * 80)
        
        # Test with all default parameters
        result = await self.run_test(
            test_name="All default parameters",
            category="parameter_combinations",
            endpoint=f"{MERCURY_ENDPOINT}/tile",
            params={"z": 2, "y": 1, "x": 3},
            expected_status=200,
            expected_content_type="image/jpeg"
        )
        self.results.append(result)
        
        # Test with custom layer
        result = await self.run_test(
            test_name="Custom layer parameter",
            category="parameter_combinations",
            endpoint=f"{MERCURY_ENDPOINT}/tile",
            params={
                "z": 2, "y": 1, "x": 3,
                "layer": "Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m"
            },
            expected_status=200
        )
        self.results.append(result)
        
        # Test with all parameters
        result = await self.run_test(
            test_name="All parameters specified",
            category="parameter_combinations",
            endpoint=f"{MERCURY_ENDPOINT}/tile",
            params={
                "z": 3, "y": 4, "x": 8,
                "layer": "Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m",
                "version": "1.0.0",
                "style": "default",
                "TileMatrixSet": "default028mm",
                "format": "jpg"
            },
            expected_status=200,
            expected_content_type="image/jpeg",
            save_response=True
        )
        self.results.append(result)
    
    async def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n" + "=" * 80)
        print("Testing Edge Cases")
        print("=" * 80)
        
        # Negative coordinates
        result = await self.run_test(
            test_name="Negative Z coordinate",
            category="edge_cases",
            endpoint=f"{MERCURY_ENDPOINT}/tile",
            params={"z": -1, "y": 0, "x": 0},
            expected_status=422,
            expected_content_type="application/json"
        )
        self.results.append(result)
        
        # Zoom level beyond maximum
        result = await self.run_test(
            test_name="Zoom level beyond maximum (z=8)",
            category="edge_cases",
            endpoint=f"{MERCURY_ENDPOINT}/tile",
            params={"z": 8, "y": 0, "x": 0},
            expected_status=400,
            expected_content_type="application/json"
        )
        self.results.append(result)
        
        # Missing required parameters
        result = await self.run_test(
            test_name="Missing Z parameter",
            category="edge_cases",
            endpoint=f"{MERCURY_ENDPOINT}/tile",
            params={"y": 4, "x": 8},
            expected_status=422
        )
        self.results.append(result)
    
    async def test_error_handling(self):
        """Test error handling and response format"""
        print("\n" + "=" * 80)
        print("Testing Error Handling")
        print("=" * 80)
        
        result = await self.run_test(
            test_name="400 error has proper JSON format",
            category="error_handling",
            endpoint=f"{MERCURY_ENDPOINT}/tile",
            params={"z": 10, "y": 0, "x": 0},
            expected_status=400,
            expected_content_type="application/json",
            validate_json=True
        )
        self.results.append(result)
    
    async def test_performance(self):
        """Test performance and response times"""
        print("\n" + "=" * 80)
        print("Testing Performance")
        print("=" * 80)
        
        times = []
        for i in range(10):
            result = await self.run_test(
                test_name=f"Performance test {i+1}/10",
                category="performance",
                endpoint=f"{MERCURY_ENDPOINT}/tile",
                params={"z": 3, "y": 4, "x": 8},
                expected_status=200
            )
            self.results.append(result)
            times.append(result.duration_ms)
        
        avg_time = sum(times) / len(times)
        print(f"\nPerformance Statistics:")
        print(f"  Average: {avg_time:.1f}ms")
        print(f"  Minimum: {min(times):.1f}ms")
        print(f"  Maximum: {max(times):.1f}ms")
    
    async def test_caching_headers(self):
        """Test caching headers are properly set"""
        print("\n" + "=" * 80)
        print("Testing Caching Headers")
        print("=" * 80)
        
        response = await self.client.get(
            f"{MERCURY_ENDPOINT}/tile",
            params={"z": 3, "y": 4, "x": 8}
        )
        
        has_cache_control = "cache-control" in response.headers
        result = TestResult(
            test_name="Response has Cache-Control header",
            category="caching_headers",
            status="PASS" if has_cache_control else "FAIL",
            duration_ms=0,
            expected_status=200,
            actual_status=response.status_code,
            response_headers=dict(response.headers)
        )
        self.results.append(result)
        print(f"[{'PASS' if has_cache_control else 'FAIL'}] Response has Cache-Control header")
    
    async def test_capabilities_endpoint(self):
        """Test capabilities/metadata endpoint"""
        print("\n" + "=" * 80)
        print("Testing Capabilities Endpoint")
        print("=" * 80)
        
        result = await self.run_test(
            test_name="Get capabilities endpoint",
            category="capabilities",
            endpoint=f"{MERCURY_ENDPOINT}/capabilities",
            expected_status=200,
            expected_content_type="application/json",
            validate_json=True
        )
        self.results.append(result)
    
    async def test_custom_headers(self):
        """Test custom response headers"""
        print("\n" + "=" * 80)
        print("Testing Custom Response Headers")
        print("=" * 80)
        
        response = await self.client.get(
            f"{MERCURY_ENDPOINT}/tile",
            params={"z": 3, "y": 4, "x": 8}
        )
        
        expected_headers = {
            "x-tile-source": "NASA Trek Mercury WMTS",
            "x-dataset": "MESSENGER MDIS Enhanced Color Mosaic",
        }
        
        for header_name, expected_value in expected_headers.items():
            actual_value = response.headers.get(header_name, "")
            matches = expected_value.lower() in actual_value.lower()
            
            result = TestResult(
                test_name=f"Header '{header_name}' present",
                category="custom_headers",
                status="PASS" if matches else "FAIL",
                duration_ms=0,
                expected_status=200,
                actual_status=200
            )
            self.results.append(result)
            print(f"[{'PASS' if matches else 'FAIL'}] Header '{header_name}' present")
    
    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        print("\n" + "=" * 80)
        print("Testing Concurrent Requests")
        print("=" * 80)
        
        tasks = []
        for i in range(20):
            z = (i % 8)
            y = i % (2 ** z) if 2 ** z > 0 else 0
            x = i % (2 ** (z + 1)) if 2 ** (z + 1) > 0 else 0
            
            task = self.run_test(
                test_name=f"Concurrent request {i+1}/20",
                category="concurrent_requests",
                endpoint=f"{MERCURY_ENDPOINT}/tile",
                params={"z": z, "y": y, "x": x},
                expected_status=200
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        self.results.extend(results)
    
    # ============================================
    # REPORT GENERATION
    # ============================================
    
    def generate_report(self):
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        
        # Calculate statistics
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        # Group by category
        categories = {}
        for result in self.results:
            cat = result.category
            if cat not in categories:
                categories[cat] = {"PASS": 0, "FAIL": 0, "ERROR": 0}
            categories[cat][result.status] += 1
        
        # Create summary
        summary = TestSummary(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            errors=errors,
            total_duration_sec=total_duration,
            pass_rate=pass_rate,
            timestamp=datetime.utcnow().isoformat() + "Z",
            categories=categories
        )
        
        # Print console report
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests:     {total_tests}")
        print(f"[PASS] Passed:   {passed} ({pass_rate:.1f}%)")
        print(f"[FAIL] Failed:   {failed}")
        print(f"[ERROR] Errors:  {errors}")
        print(f"Duration:        {total_duration:.2f}s")
        print("\nResults by Category:")
        print("-" * 80)
        
        for cat, stats in sorted(categories.items()):
            total_cat = sum(stats.values())
            cat_pass_rate = (stats["PASS"] / total_cat * 100) if total_cat > 0 else 0
            print(f"{cat:30} {stats['PASS']:3}[PASS] {stats['FAIL']:3}[FAIL] {stats['ERROR']:3}[ERROR] ({cat_pass_rate:.0f}%)")
        
        # Save detailed results
        self._save_json_report(summary)
        self._save_html_report(summary)
        self._save_failed_tests()
        
        print(f"\nReports saved to: {RESULTS_DIR}")
        print(f"  - summary.json")
        print(f"  - report.html")
        print(f"  - all_results.json")
        if failed > 0 or errors > 0:
            print(f"  - failed_tests.json")
    
    def _save_json_report(self, summary: TestSummary):
        """Save JSON report"""
        summary_path = RESULTS_DIR / "summary.json"
        summary_path.write_text(json.dumps(summary.to_dict(), indent=2), encoding='utf-8')
        
        all_results_path = RESULTS_DIR / "all_results.json"
        all_results_data = [asdict(r) for r in self.results]
        all_results_path.write_text(json.dumps(all_results_data, indent=2), encoding='utf-8')
    
    def _save_failed_tests(self):
        """Save failed tests for debugging"""
        failed = [r for r in self.results if r.status in ["FAIL", "ERROR"]]
        
        if failed:
            failed_path = RESULTS_DIR / "failed_tests.json"
            failed_data = [asdict(r) for r in failed]
            failed_path.write_text(json.dumps(failed_data, indent=2), encoding='utf-8')
    
    def _save_html_report(self, summary: TestSummary):
        """Generate HTML report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mercury Service Test Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .pass {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .fail {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .error {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .rate {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .status-pass {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-fail {{
            color: #dc3545;
            font-weight: bold;
        }}
        .status-error {{
            color: #ffc107;
            font-weight: bold;
        }}
        .category {{
            background: #e9ecef;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }}
        .category h2 {{
            margin-top: 0;
            color: #495057;
        }}
        .progress-bar {{
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            height: 30px;
            margin: 10px 0;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Mercury Service Test Report</h1>
        <p><strong>Timestamp:</strong> {summary.timestamp}</p>
        <p><strong>Duration:</strong> {summary.total_duration_sec:.2f} seconds</p>
        
        <div class="summary">
            <div class="stat-card">
                <h3>Total Tests</h3>
                <div class="value">{summary.total_tests}</div>
            </div>
            <div class="stat-card pass">
                <h3>Passed</h3>
                <div class="value">{summary.passed}</div>
            </div>
            <div class="stat-card fail">
                <h3>Failed</h3>
                <div class="value">{summary.failed}</div>
            </div>
            <div class="stat-card error">
                <h3>Errors</h3>
                <div class="value">{summary.errors}</div>
            </div>
            <div class="stat-card rate">
                <h3>Pass Rate</h3>
                <div class="value">{summary.pass_rate:.1f}%</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {summary.pass_rate}%">
                {summary.pass_rate:.1f}%
            </div>
        </div>
        
        <h2>Results by Category</h2>
        """
        
        # Add category results
        for cat, stats in sorted(summary.categories.items()):
            total_cat = sum(stats.values())
            cat_pass_rate = (stats["PASS"] / total_cat * 100) if total_cat > 0 else 0
            
            html += f"""
        <div class="category">
            <h2>{cat.replace('_', ' ').title()}</h2>
            <p>
                Passed: {stats["PASS"]} | 
                Failed: {stats["FAIL"]} | 
                Errors: {stats["ERROR"]} | 
                Pass Rate: {cat_pass_rate:.1f}%
            </p>
        </div>
            """
        
        # Add detailed results table
        html += """
        <h2>Detailed Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Duration (ms)</th>
                    <th>Status Code</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for result in self.results:
            status_class = f"status-{result.status.lower()}"
            html += f"""
                <tr>
                    <td>{result.test_name}</td>
                    <td>{result.category}</td>
                    <td class="{status_class}">{result.status}</td>
                    <td>{result.duration_ms:.1f}</td>
                    <td>{result.actual_status}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
        """
        
        report_path = RESULTS_DIR / "report.html"
        # FIXED: Added encoding='utf-8' to handle Unicode characters
        report_path.write_text(html, encoding='utf-8')


# ============================================
# MAIN EXECUTION
# ============================================

async def main():
    """Main test execution"""
    print("=" * 80)
    print("NASA MERCURY SERVICE - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"Started: {datetime.utcnow().isoformat()}Z")
    print()
    
    runner = MercuryTestRunner()
    
    try:
        await runner.run_all_tests()
        
        # Exit with error code if tests failed
        failed_count = sum(1 for r in runner.results if r.status in ["FAIL", "ERROR"])
        sys.exit(0 if failed_count == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())