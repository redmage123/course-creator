#!/usr/bin/env python3
"""
Security Implementation Validation Script

VALIDATION STRATEGY:
Comprehensive validation of the multi-tenant security implementation
to ensure all security measures are properly deployed and effective
against cross-organization data access and privilege escalation.

VALIDATION CATEGORIES:
1. Database Security - Row-level security and organization isolation
2. Middleware Security - Authorization middleware effectiveness
3. Cache Security - Redis cache organization isolation
4. API Security - Endpoint-level organization validation
5. Service Integration - Cross-service security coordination
6. Performance Impact - Security overhead measurement

VALIDATION COVERAGE:
- Organization boundary enforcement
- Cross-tenant access prevention
- Authentication and authorization flows
- Cache and database isolation
- Security logging and monitoring
- Performance under security constraints
"""

import asyncio
import sys
import os
import time
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'shared'))

# Import security components
try:
    from auth.organization_middleware import OrganizationAuthorizationMiddleware
    from cache.organization_redis_cache import OrganizationRedisCache, OrganizationCacheManager
except ImportError as e:
    print(f"❌ Failed to import security components: {e}")
    sys.exit(1)

# Import test fixtures
from tests.fixtures.security_fixtures import (
    create_test_organizations, create_test_users, generate_valid_jwt_token,
    SecurityTestClient, validate_organization_isolation, SecurityPerformanceTracker
)


class SecurityValidationSuite:
    """Comprehensive security validation suite"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_total': 0,
            'security_score': 0.0,
            'validation_details': []
        }
        self.performance_tracker = SecurityPerformanceTracker()
    
    def log_test_result(self, test_name: str, passed: bool, details: str = "", duration: float = 0.0):
        """Log individual test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if details:
            print(f"    {details}")
        
        if duration > 0:
            print(f"    Duration: {duration:.3f}s")
            self.performance_tracker.record_operation(test_name, duration)
        
        self.results['tests_total'] += 1
        if passed:
            self.results['tests_passed'] += 1
        else:
            self.results['tests_failed'] += 1
        
        self.results['validation_details'].append({
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def validate_middleware_security(self) -> bool:
        """Validate organization authorization middleware"""
        print("\n🔒 Validating Organization Authorization Middleware...")

        start_time = time.time()

        try:
            # Test middleware configuration
            config = {
                'jwt': {
                    'secret_key': 'test-secret-key',
                    'algorithm': 'HS256'
                },
                'services': {
                    'user_management_url': 'http://test-user:8000',
                    'organization_management_url': 'http://test-org:8008'
                }
            }

            middleware = OrganizationAuthorizationMiddleware(None, config)

            # Create a simple request stub
            from collections import namedtuple
            URL = namedtuple('URL', ['path'])
            Request = namedtuple('Request', ['headers', 'url', 'query_params', 'method'])

            test_org_id = str(uuid.uuid4())
            request = Request(
                headers={'X-Organization-ID': test_org_id},
                url=URL(path='/api/v1/courses'),
                query_params={},
                method='GET'
            )

            org_id = await middleware._extract_organization_id(request)

            if org_id:
                self.log_test_result(
                    "Middleware Organization ID Extraction",
                    True,
                    f"Successfully extracted organization ID: {org_id}",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    "Middleware Organization ID Extraction",
                    False,
                    "Failed to extract organization ID from header"
                )
                return False

        except Exception as e:
            self.log_test_result(
                "Middleware Security Validation",
                False,
                f"Exception during middleware validation: {e}"
            )
            return False
    
    async def validate_cache_isolation(self) -> bool:
        """Validate Redis cache organization isolation"""
        print("\n💾 Validating Cache Organization Isolation...")
        
        try:
            # Use fake Redis for testing
            import fakeredis.aioredis
            redis_client = fakeredis.aioredis.FakeRedis()
            cache = OrganizationRedisCache(redis_client)
            
            # Test data
            org_a = str(uuid.uuid4())
            org_b = str(uuid.uuid4())
            test_data = {'sensitive': 'organization-specific-data', 'timestamp': datetime.utcnow().isoformat()}
            
            start_time = time.time()
            
            # Store data for organization A
            await cache.set(org_a, 'course', 'test123', test_data)
            
            # Try to access from organization B (should fail)
            result = await cache.get(org_b, 'course', 'test123')
            
            isolation_duration = time.time() - start_time
            
            if result is None:
                self.log_test_result(
                    "Cache Organization Isolation",
                    True,
                    "Organization B cannot access Organization A's cached data",
                    isolation_duration
                )
                
                # Test key enumeration prevention
                start_time = time.time()
                
                org_a_keys = await cache.get_keys_by_pattern(org_a, 'course', '*')
                org_b_keys = await cache.get_keys_by_pattern(org_b, 'course', '*')
                
                enumeration_duration = time.time() - start_time
                
                if len(org_a_keys) == 1 and len(org_b_keys) == 0:
                    self.log_test_result(
                        "Cache Key Enumeration Prevention",
                        True,
                        f"Org A: {len(org_a_keys)} keys, Org B: {len(org_b_keys)} keys",
                        enumeration_duration
                    )
                    return True
                else:
                    self.log_test_result(
                        "Cache Key Enumeration Prevention",
                        False,
                        f"Key enumeration failed - Org A: {len(org_a_keys)}, Org B: {len(org_b_keys)}"
                    )
                    return False
            else:
                self.log_test_result(
                    "Cache Organization Isolation",
                    False,
                    "Organization B can access Organization A's cached data - SECURITY BREACH"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Cache Isolation Validation",
                False,
                f"Exception during cache validation: {e}"
            )
            return False
    
    async def validate_database_security(self) -> bool:
        """Validate database organization security"""
        print("\n🗄️ Validating Database Organization Security...")
        
        try:
            # Check if migration was applied
            start_time = time.time()
            
            # Simulate database check (would connect to actual DB in real implementation)
            migration_file = project_root / 'data' / 'migrations' / '016_add_organization_security.sql'
            
            if migration_file.exists():
                with open(migration_file, 'r') as f:
                    migration_content = f.read()
                
                # Check for key security components
                security_checks = [
                    ('Organization ID columns', 'ADD COLUMN IF NOT EXISTS organization_id UUID'),
                    ('Foreign key constraints', 'REFERENCES organizations(id)'),
                    ('Row-level security', 'ENABLE ROW LEVEL SECURITY'),
                    ('Security policies', 'CREATE POLICY'),
                    ('Security functions', 'set_organization_context'),
                    ('Audit logging', 'security_audit_log')
                ]
                
                all_checks_passed = True
                
                for check_name, check_pattern in security_checks:
                    if check_pattern in migration_content:
                        self.log_test_result(
                            f"Database Security - {check_name}",
                            True,
                            f"Found {check_pattern} in migration"
                        )
                    else:
                        self.log_test_result(
                            f"Database Security - {check_name}",
                            False,
                            f"Missing {check_pattern} in migration"
                        )
                        all_checks_passed = False
                
                validation_duration = time.time() - start_time
                
                self.log_test_result(
                    "Database Security Migration",
                    all_checks_passed,
                    f"Migration file validation completed",
                    validation_duration
                )
                
                return all_checks_passed
            else:
                self.log_test_result(
                    "Database Security Migration",
                    False,
                    "Migration file 016_add_organization_security.sql not found"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Database Security Validation",
                False,
                f"Exception during database validation: {e}"
            )
            return False
    
    async def validate_api_security(self) -> bool:
        """Validate API endpoint security"""
        print("\n🌐 Validating API Security...")
        
        try:
            # Create test organizations and users
            organizations = create_test_organizations([
                {'name': 'Test Org A', 'slug': 'test-org-a'},
                {'name': 'Test Org B', 'slug': 'test-org-b'}
            ])
            
            users = create_test_users([
                {'email': 'user1@orga.com', 'role': 'instructor', 'organization_id': organizations[0].id},
                {'email': 'user2@orgb.com', 'role': 'instructor', 'organization_id': organizations[1].id}
            ])
            
            client = SecurityTestClient()
            
            # Test legitimate access
            start_time = time.time()
            
            user_a_token = generate_valid_jwt_token(users[0])
            
            async with client.authenticated_request(user_a_token, organizations[0].id) as test_client:
                response = await test_client.get('/api/v1/courses')
                legitimate_access_success = response.status_code == 200
            
            legitimate_duration = time.time() - start_time
            
            self.log_test_result(
                "API Legitimate Access",
                legitimate_access_success,
                f"Status code: {response.status_code}",
                legitimate_duration
            )
            
            # Test cross-organization access (should fail)
            start_time = time.time()
            
            async with client.authenticated_request(user_a_token, organizations[1].id) as test_client:
                response = await test_client.get('/api/v1/courses')
                cross_org_blocked = response.status_code == 403
            
            cross_org_duration = time.time() - start_time
            
            self.log_test_result(
                "API Cross-Organization Access Prevention",
                cross_org_blocked,
                f"Status code: {response.status_code}",
                cross_org_duration
            )
            
            return legitimate_access_success and cross_org_blocked
            
        except Exception as e:
            self.log_test_result(
                "API Security Validation",
                False,
                f"Exception during API validation: {e}"
            )
            return False
    
    async def validate_service_integration(self) -> bool:
        """Validate cross-service security integration"""
        print("\n🔗 Validating Service Integration Security...")
        
        try:
            # Check that services are properly configured
            services_to_check = [
                'services/course-management/main.py',
                'services/user-management/app/factory.py',  # User management uses factory pattern
                'services/content-management/main.py',
                'services/analytics/main.py'
            ]
            
            integration_checks = []
            
            for service_path in services_to_check:
                service_file = project_root / service_path
                
                if service_file.exists():
                    with open(service_file, 'r') as f:
                        service_content = f.read()
                    
                    # Check for organization middleware integration
                    has_middleware = 'OrganizationAuthorizationMiddleware' in service_content
                    has_org_context = 'get_organization_context' in service_content
                    
                    service_name = service_path.split('/')[1]
                    
                    self.log_test_result(
                        f"Service Integration - {service_name}",
                        has_middleware and has_org_context,
                        f"Middleware: {has_middleware}, Context: {has_org_context}"
                    )
                    
                    integration_checks.append(has_middleware and has_org_context)
                else:
                    self.log_test_result(
                        f"Service Integration - {service_path}",
                        False,
                        "Service file not found"
                    )
                    integration_checks.append(False)
            
            overall_integration = all(integration_checks)
            
            self.log_test_result(
                "Overall Service Integration",
                overall_integration,
                f"Integrated services: {sum(integration_checks)}/{len(integration_checks)}"
            )
            
            return overall_integration
            
        except Exception as e:
            self.log_test_result(
                "Service Integration Validation",
                False,
                f"Exception during service integration validation: {e}"
            )
            return False
    
    async def validate_performance_impact(self) -> bool:
        """Validate security performance impact"""
        print("\n⚡ Validating Security Performance Impact...")
        
        try:
            # Test cache performance with organization isolation
            import fakeredis.aioredis
            redis_client = fakeredis.aioredis.FakeRedis()
            cache = OrganizationRedisCache(redis_client)
            
            org_id = str(uuid.uuid4())
            test_data = {'data': 'performance test'}
            
            # Measure cache operations
            iterations = 100
            
            # Set operations
            start_time = time.time()
            for i in range(iterations):
                await cache.set(org_id, 'perf', f'key_{i}', test_data)
            set_duration = time.time() - start_time
            
            # Get operations
            start_time = time.time()
            for i in range(iterations):
                await cache.get(org_id, 'perf', f'key_{i}')
            get_duration = time.time() - start_time
            
            # Calculate performance metrics
            avg_set_time = (set_duration / iterations) * 1000  # ms
            avg_get_time = (get_duration / iterations) * 1000  # ms
            
            # Performance thresholds (adjustable based on requirements)
            set_threshold = 10.0  # 10ms per operation
            get_threshold = 5.0   # 5ms per operation
            
            set_performance_ok = avg_set_time < set_threshold
            get_performance_ok = avg_get_time < get_threshold
            
            self.log_test_result(
                "Cache Set Performance",
                set_performance_ok,
                f"Average: {avg_set_time:.2f}ms (threshold: {set_threshold}ms)",
                set_duration
            )
            
            self.log_test_result(
                "Cache Get Performance",
                get_performance_ok,
                f"Average: {avg_get_time:.2f}ms (threshold: {get_threshold}ms)",
                get_duration
            )
            
            return set_performance_ok and get_performance_ok
            
        except Exception as e:
            self.log_test_result(
                "Performance Impact Validation",
                False,
                f"Exception during performance validation: {e}"
            )
            return False
    
    def calculate_security_score(self) -> float:
        """Calculate overall security score"""
        if self.results['tests_total'] == 0:
            return 0.0
        
        base_score = (self.results['tests_passed'] / self.results['tests_total']) * 100
        
        # Apply weights for critical security components
        critical_tests = [
            'Cache Organization Isolation',
            'API Cross-Organization Access Prevention',
            'Database Security Migration'
        ]
        
        critical_passed = sum(
            1 for detail in self.results['validation_details']
            if detail['test_name'] in critical_tests and detail['passed']
        )
        critical_total = len(critical_tests)
        
        if critical_total > 0:
            critical_score = (critical_passed / critical_total) * 100
            # Weight critical tests more heavily
            final_score = (base_score * 0.6) + (critical_score * 0.4)
        else:
            final_score = base_score
        
        return round(final_score, 1)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        self.results['security_score'] = self.calculate_security_score()
        
        # Add performance metrics
        self.results['performance_metrics'] = self.performance_tracker.get_performance_report()
        
        # Security status
        if self.results['security_score'] >= 90:
            self.results['security_status'] = 'EXCELLENT'
        elif self.results['security_score'] >= 80:
            self.results['security_status'] = 'GOOD'
        elif self.results['security_score'] >= 70:
            self.results['security_status'] = 'ACCEPTABLE'
        else:
            self.results['security_status'] = 'NEEDS_IMPROVEMENT'
        
        return self.results
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete security validation suite"""
        print("🔐 Starting Comprehensive Security Validation...")
        print("=" * 60)
        
        # Run all validation tests
        validation_results = await asyncio.gather(
            self.validate_middleware_security(),
            self.validate_cache_isolation(),
            self.validate_database_security(),
            self.validate_api_security(),
            self.validate_service_integration(),
            self.validate_performance_impact(),
            return_exceptions=True
        )
        
        # Handle any exceptions
        for i, result in enumerate(validation_results):
            if isinstance(result, Exception):
                self.log_test_result(
                    f"Validation Test {i+1}",
                    False,
                    f"Validation failed with exception: {result}"
                )
        
        return self.generate_report()


async def main():
    """Main validation entry point"""
    print("🛡️  Course Creator Platform - Security Validation Suite")
    print("=" * 60)
    
    validator = SecurityValidationSuite()
    
    try:
        report = await validator.run_validation()
        
        print("\n" + "=" * 60)
        print("📊 SECURITY VALIDATION SUMMARY")
        print("=" * 60)
        
        print(f"Tests Run: {report['tests_total']}")
        print(f"Tests Passed: {report['tests_passed']}")
        print(f"Tests Failed: {report['tests_failed']}")
        print(f"Security Score: {report['security_score']}%")
        print(f"Security Status: {report['security_status']}")
        
        # Performance summary
        if report['performance_metrics']:
            print(f"\n⚡ Performance Metrics:")
            for operation, metrics in report['performance_metrics'].items():
                print(f"  {operation}: {metrics['average_time']:.3f}s avg ({metrics['count']} ops)")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for detail in report['validation_details']:
            status = "✅" if detail['passed'] else "❌"
            print(f"  {status} {detail['test_name']}")
            if detail['details']:
                print(f"      {detail['details']}")
        
        # Save report
        report_file = project_root / 'security_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_file}")
        
        # Exit with appropriate code
        if report['tests_failed'] == 0:
            print("\n🎉 All security validations passed!")
            return 0
        else:
            print(f"\n⚠️  {report['tests_failed']} security validation(s) failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Validation suite failed with exception: {e}")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)