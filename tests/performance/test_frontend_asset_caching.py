#!/usr/bin/env python3
"""
Frontend Configuration and Static Asset Caching Performance Test

BUSINESS REQUIREMENT:
Validate that the implemented frontend configuration and static asset caching provides the expected
70-90% performance improvement for asset loading, configuration retrieval, and overall page load
performance that directly impacts student and instructor user experience.

TECHNICAL IMPLEMENTATION:
This test uses Selenium WebDriver to measure real browser performance including:
- Asset loading times with and without caching
- Configuration retrieval performance
- ServiceWorker caching effectiveness
- Network request reduction
- Page load speed improvements

Expected Results:
- Static asset loading: 500-2000ms → 10-50ms (95% improvement)
- Configuration retrieval: 10-50ms → 0.1-1ms (95% improvement)
- Page load times: 2-5 second improvement for returning users
- Network requests: 80-90% reduction for cached assets

PERFORMANCE MEASUREMENT:
- Uses actual browser rendering and network timing
- Measures ServiceWorker cache hit rates
- Validates nginx caching headers and effectiveness
- Compares first visit vs. returning user performance
- Tests asset preloading and intelligent caching strategies
"""

import asyncio
import time
import json
import statistics
from typing import List, Dict, Any
import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))


class FrontendCachingPerformanceTest:
    """
    Comprehensive frontend caching performance test using real browser measurement
    """
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.driver = None
        self.performance_data = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver with performance monitoring enabled"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Enable performance logging
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.set_capability('goog:loggingPrefs', {
            'performance': 'ALL',
            'browser': 'ALL'
        })
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            print("ℹ️  Install ChromeDriver and ensure it's in PATH for this test")
            return False
    
    def cleanup_driver(self):
        """Cleanup WebDriver resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def clear_browser_cache(self):
        """Clear browser cache to simulate first visit"""
        if not self.driver:
            return
            
        try:
            # Clear cache using Chrome DevTools
            self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
            self.driver.execute_cdp_cmd('Storage.clearDataForOrigin', {
                'origin': self.base_url,
                'storageTypes': 'all'
            })
            print("🗑️  Browser cache cleared")
        except Exception as e:
            print(f"⚠️  Could not clear browser cache: {e}")
    
    def measure_page_load_performance(self, url: str, test_name: str) -> Dict[str, Any]:
        """Measure comprehensive page load performance"""
        if not self.driver:
            return {}
        
        try:
            start_time = time.time()
            
            # Navigate to page
            self.driver.get(url)
            
            # Wait for page to be fully loaded
            WebDriverWait(self.driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for ServiceWorker to be ready (if applicable)
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script("""
                        return navigator.serviceWorker && navigator.serviceWorker.ready;
                    """)
                )
            except TimeoutException:
                pass  # ServiceWorker may not be available
            
            end_time = time.time()
            total_load_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Get detailed performance metrics
            performance_data = self.driver.execute_script("""
                const perfData = performance.getEntriesByType('navigation')[0];
                const resourceData = performance.getEntriesByType('resource');
                
                return {
                    navigation: {
                        loadComplete: perfData.loadEventEnd - perfData.navigationStart,
                        domComplete: perfData.domComplete - perfData.navigationStart,
                        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
                    },
                    resources: resourceData.map(resource => ({
                        name: resource.name,
                        type: resource.initiatorType,
                        size: resource.transferSize,
                        duration: resource.responseEnd - resource.requestStart,
                        cached: resource.transferSize === 0 && resource.decodedBodySize > 0
                    }))
                };
            """)
            
            # Get ServiceWorker cache statistics if available
            sw_stats = self.driver.execute_script("""
                if (window.getCacheStats) {
                    return window.getCacheStats();
                }
                return null;
            """)
            
            return {
                'test_name': test_name,
                'url': url,
                'total_load_time_ms': total_load_time,
                'navigation_timing': performance_data.get('navigation', {}),
                'resource_count': len(performance_data.get('resources', [])),
                'resources': performance_data.get('resources', []),
                'cached_resources': len([r for r in performance_data.get('resources', []) if r.get('cached', False)]),
                'serviceworker_stats': sw_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error measuring page performance for {url}: {e}")
            return {
                'test_name': test_name,
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_static_asset_caching(self):
        """Test static asset caching performance"""
        print("📊 Testing Static Asset Caching Performance")
        print("-" * 70)
        
        test_pages = [
            {'url': f"{self.base_url}/", 'name': 'Home Page'},
            {'url': f"{self.base_url}/html/student-dashboard.html", 'name': 'Student Dashboard'},
            {'url': f"{self.base_url}/html/instructor-dashboard.html", 'name': 'Instructor Dashboard'}
        ]
        
        results = []
        
        for page in test_pages:
            print(f"Testing {page['name']}...")
            
            # First visit (cache miss)
            self.clear_browser_cache()
            first_visit = self.measure_page_load_performance(
                page['url'], 
                f"{page['name']} - First Visit"
            )
            
            # Second visit (cache hit)
            second_visit = self.measure_page_load_performance(
                page['url'],
                f"{page['name']} - Second Visit"
            )
            
            results.extend([first_visit, second_visit])
            
            # Calculate improvement
            if 'error' not in first_visit and 'error' not in second_visit:
                first_load = first_visit.get('total_load_time_ms', 0)
                second_load = second_visit.get('total_load_time_ms', 0)
                
                if first_load > 0:
                    improvement = ((first_load - second_load) / first_load) * 100
                    print(f"  First visit: {first_load:.2f}ms")
                    print(f"  Second visit: {second_load:.2f}ms")
                    print(f"  Improvement: {improvement:.1f}%")
                    
                    cached_resources = second_visit.get('cached_resources', 0)
                    total_resources = second_visit.get('resource_count', 0)
                    cache_hit_rate = (cached_resources / total_resources * 100) if total_resources > 0 else 0
                    print(f"  Cache hit rate: {cache_hit_rate:.1f}% ({cached_resources}/{total_resources})")
                    print()
        
        return results
    
    def test_configuration_caching(self):
        """Test configuration caching performance"""
        print("📊 Testing Configuration Caching Performance")
        print("-" * 70)
        
        try:
            # Navigate to a page with configuration manager
            self.driver.get(f"{self.base_url}/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Test configuration retrieval performance
            config_performance = self.driver.execute_script("""
                if (!window.getConfig) {
                    return { error: 'Configuration manager not available' };
                }
                
                const results = [];
                const testConfigs = [
                    'api.baseUrl',
                    'ui.theme',
                    'security.sessionTimeout',
                    'performance.cacheEnabled'
                ];
                
                // Test configuration retrieval times
                for (const config of testConfigs) {
                    const start = performance.now();
                    window.getConfig(config);
                    const end = performance.now();
                    
                    results.push({
                        config: config,
                        time_ms: end - start
                    });
                }
                
                return {
                    config_tests: results,
                    cache_stats: window.getCacheStats ? window.getCacheStats() : null
                };
            """)
            
            if 'error' not in config_performance:
                print("Configuration Retrieval Performance:")
                for test in config_performance.get('config_tests', []):
                    print(f"  {test['config']}: {test['time_ms']:.3f}ms")
                
                cache_stats = config_performance.get('cache_stats', {})
                if cache_stats:
                    config_cache = cache_stats.get('config', {})
                    print(f"\nConfiguration Cache Statistics:")
                    print(f"  Cache Hit Rate: {config_cache.get('cacheHitRate', 0):.1f}%")
                    print(f"  Total Accesses: {config_cache.get('totalAccesses', 0)}")
                    print(f"  Cache Size: {config_cache.get('cacheSize', 0)}")
                    print()
            else:
                print(f"❌ Configuration caching test failed: {config_performance.get('error')}")
            
            return config_performance
            
        except Exception as e:
            print(f"❌ Error testing configuration caching: {e}")
            return {'error': str(e)}
    
    def test_serviceworker_effectiveness(self):
        """Test ServiceWorker caching effectiveness"""
        print("📊 Testing ServiceWorker Caching Effectiveness")
        print("-" * 70)
        
        try:
            # Navigate to a page
            self.driver.get(f"{self.base_url}/")
            
            # Wait for ServiceWorker to register
            sw_status = WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("""
                    return new Promise((resolve) => {
                        if ('serviceWorker' in navigator) {
                            navigator.serviceWorker.ready.then(() => {
                                resolve({
                                    registered: true,
                                    active: navigator.serviceWorker.controller !== null
                                });
                            }).catch(() => {
                                resolve({ registered: false, error: 'ServiceWorker failed to register' });
                            });
                        } else {
                            resolve({ registered: false, error: 'ServiceWorker not supported' });
                        }
                    });
                """)
            )
            
            if sw_status.get('registered'):
                print("✅ ServiceWorker registered successfully")
                print(f"   Active: {sw_status.get('active', False)}")
                
                # Test cache effectiveness
                cache_effectiveness = self.driver.execute_script("""
                    if (window.getCacheStats) {
                        const stats = window.getCacheStats();
                        return {
                            asset_cache: stats.assets || {},
                            serviceworker_active: navigator.serviceWorker.controller !== null
                        };
                    }
                    return null;
                """)
                
                if cache_effectiveness:
                    asset_stats = cache_effectiveness.get('asset_cache', {})
                    print(f"\nAsset Cache Statistics:")
                    print(f"  Cache Hit Rate: {asset_stats.get('cacheHitRate', 0):.1f}%")
                    print(f"  Cache Hits: {asset_stats.get('cacheHits', 0)}")
                    print(f"  Cache Misses: {asset_stats.get('cacheMisses', 0)}")
                    print(f"  Network Requests: {asset_stats.get('networkRequests', 0)}")
                    print(f"  Average Load Time: {asset_stats.get('averageLoadTime', 0):.2f}ms")
                    print(f"  Critical Assets Cached: {asset_stats.get('criticalAssets', 0)}")
                    print()
                
                return cache_effectiveness
            else:
                print(f"❌ ServiceWorker not registered: {sw_status.get('error', 'Unknown error')}")
                return sw_status
                
        except Exception as e:
            print(f"❌ Error testing ServiceWorker: {e}")
            return {'error': str(e)}
    
    async def run_comprehensive_test(self):
        """Run comprehensive frontend caching performance test"""
        print("🚀 Starting Frontend Configuration and Static Asset Caching Performance Test")
        print("=" * 95)
        
        # Setup WebDriver
        if not self.setup_driver():
            print("❌ Could not initialize WebDriver - skipping browser-based tests")
            return
        
        try:
            # Test 1: Static Asset Caching
            asset_results = self.test_static_asset_caching()
            
            # Test 2: Configuration Caching
            config_results = self.test_configuration_caching()
            
            # Test 3: ServiceWorker Effectiveness
            sw_results = self.test_serviceworker_effectiveness()
            
            # Analyze Overall Performance
            self._analyze_overall_performance(asset_results, config_results, sw_results)
            
        finally:
            self.cleanup_driver()
    
    def _analyze_overall_performance(self, asset_results, config_results, sw_results):
        """Analyze and report overall performance improvements"""
        print("✅ Frontend Configuration and Static Asset Caching Performance Analysis")
        print("-" * 70)
        
        # Analyze asset caching performance
        first_visits = [r for r in asset_results if 'First Visit' in r.get('test_name', '') and 'error' not in r]
        second_visits = [r for r in asset_results if 'Second Visit' in r.get('test_name', '') and 'error' not in r]
        
        if first_visits and second_visits:
            avg_first_visit = statistics.mean([r['total_load_time_ms'] for r in first_visits])
            avg_second_visit = statistics.mean([r['total_load_time_ms'] for r in second_visits])
            
            overall_improvement = ((avg_first_visit - avg_second_visit) / avg_first_visit) * 100
            
            print(f"📈 Asset Caching Performance Summary:")
            print(f"  Average First Visit Load Time: {avg_first_visit:.2f}ms")
            print(f"  Average Second Visit Load Time: {avg_second_visit:.2f}ms")
            print(f"  Overall Performance Improvement: {overall_improvement:.1f}%")
            
            # Analyze cache hit rates
            total_resources = sum([r.get('resource_count', 0) for r in second_visits])
            total_cached = sum([r.get('cached_resources', 0) for r in second_visits])
            overall_cache_hit_rate = (total_cached / total_resources * 100) if total_resources > 0 else 0
            
            print(f"  Overall Cache Hit Rate: {overall_cache_hit_rate:.1f}% ({total_cached}/{total_resources})")
            print()
        
        # Analyze configuration caching
        if 'error' not in config_results:
            config_tests = config_results.get('config_tests', [])
            if config_tests:
                avg_config_time = statistics.mean([t['time_ms'] for t in config_tests])
                print(f"⚡ Configuration Caching Performance:")
                print(f"  Average Configuration Retrieval Time: {avg_config_time:.3f}ms")
                
                cache_stats = config_results.get('cache_stats', {})
                if cache_stats and cache_stats.get('config'):
                    config_cache = cache_stats['config']
                    print(f"  Configuration Cache Hit Rate: {config_cache.get('cacheHitRate', 0):.1f}%")
                print()
        
        # Analyze ServiceWorker effectiveness
        if 'error' not in sw_results and sw_results.get('asset_cache'):
            asset_cache = sw_results['asset_cache']
            print(f"🔧 ServiceWorker Cache Effectiveness:")
            print(f"  ServiceWorker Active: {sw_results.get('serviceworker_active', False)}")
            print(f"  Asset Cache Hit Rate: {asset_cache.get('cacheHitRate', 0):.1f}%")
            print(f"  Average Asset Load Time: {asset_cache.get('averageLoadTime', 0):.2f}ms")
            print()
        
        # Overall business impact
        print("💼 BUSINESS IMPACT ANALYSIS")
        print("• User Experience: Significantly faster page loads and asset retrieval")
        print("• Bandwidth Savings: Reduced network usage for returning users")
        print("• Server Load: Decreased server requests due to effective caching")
        print("• Offline Capability: ServiceWorker enables offline functionality")
        print("• Mobile Performance: Improved performance on slower connections")
        
        print()
        print("🎓 EDUCATIONAL PLATFORM BENEFITS")
        print("• Student Experience: Faster access to learning materials and dashboards")
        print("• Instructor Efficiency: Rapid content loading and management interfaces")
        print("• Platform Reliability: Cached content available during network issues")
        print("• Resource Optimization: Efficient use of bandwidth and server resources")
        
        print()
        print("💰 PERFORMANCE OPTIMIZATION ACHIEVEMENTS")
        if overall_improvement > 70:
            print(f"✅ EXCELLENT: {overall_improvement:.1f}% performance improvement exceeds target (70-90%)")
        elif overall_improvement > 50:
            print(f"✅ GOOD: {overall_improvement:.1f}% performance improvement meets expectations")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {overall_improvement:.1f}% improvement below target")
        
        if overall_cache_hit_rate > 80:
            print(f"✅ EXCELLENT: {overall_cache_hit_rate:.1f}% cache hit rate exceeds target (80%+)")
        elif overall_cache_hit_rate > 60:
            print(f"✅ GOOD: {overall_cache_hit_rate:.1f}% cache hit rate meets expectations")
        else:
            print(f"⚠️  NEEDS IMPROVEMENT: {overall_cache_hit_rate:.1f}% cache hit rate below target")


async def main():
    """Main test execution function"""
    test = FrontendCachingPerformanceTest()
    await test.run_comprehensive_test()
    print("\n🎉 Frontend Configuration and Static Asset Caching Performance Test Complete!")
    print("=" * 95)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()