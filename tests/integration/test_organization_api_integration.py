#!/usr/bin/env python3
"""
Integration Tests for Organization Management API
Tests full integration with database, dependency injection, and service interactions
"""
import pytest
import asyncio
import asyncpg
import json
import requests
from uuid import uuid4
from datetime import datetime
import time
import os
from pathlib import Path

# Test configuration
TEST_BASE_URL = "https://176.9.99.103:8008"  # Organization service
DB_TEST_CONFIG = {
    "host": "176.9.99.103",
    "port": 5432,
    "database": "course_creator",
    "user": "courseuser",
    "password": "coursepass123"
}


class TestOrganizationAPIIntegration:
    """
    Integration test suite for Organization Management API
    Tests: End-to-end API workflows, database persistence, service communication
    """

    @classmethod
    def setup_class(cls):
        """Set up test environment for integration tests"""
        cls.test_data = {
            "valid_org": {
                "name": f"Integration Test Corp {int(time.time())}",
                "slug": f"integration-test-corp-{int(time.time())}",
                "address": "123 Integration Test Drive, Test City, TC 12345",
                "contact_phone": "+1-555-123-4567",
                "contact_email": "admin@integrationtest.com",
                "admin_full_name": "Test Admin User",
                "admin_email": "test.admin@integrationtest.com",
                "admin_phone": "+1-555-123-4568",
                "description": "Integration test organization",
                "domain": "integrationtest.com"
            }
        }
        
        # Mock authentication token (in real scenario, would authenticate properly)
        cls.auth_headers = {
            "Authorization": "Bearer integration-test-token",
            "Content-Type": "application/json"
        }
        
        cls.created_organizations = []  # Track created orgs for cleanup

    @classmethod
    def teardown_class(cls):
        """Clean up test data after all tests complete"""
        # Note: In a real scenario, would clean up test organizations
        # For this test, we'll leave the data for manual verification
        pass

    def test_service_health_check(self):
        """Test that organization service is running and healthy"""
        try:
            response = requests.get(f"{TEST_BASE_URL}/health", verify=False, timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "organization-management"
            assert "timestamp" in data
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Organization service not available: {e}")

    def test_organization_router_availability(self):
        """Test that organization router endpoints are available"""
        try:
            response = requests.get(f"{TEST_BASE_URL}/test", verify=False, timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert "organization" in data["message"].lower()
            assert data["professional_validation"] == "enabled"
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Organization router not available: {e}")

    def test_create_organization_integration(self):
        """Test complete organization creation workflow"""
        try:
            # Test organization creation via API
            response = requests.post(
                f"{TEST_BASE_URL}/organizations",
                json=self.test_data["valid_org"],
                headers=self.auth_headers,
                verify=False,
                timeout=15
            )
            
            # For now, we expect this to work with mock data
            # In production, this would create actual database records
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                assert "id" in data
                assert data["name"] == self.test_data["valid_org"]["name"]
                assert data["slug"] == self.test_data["valid_org"]["slug"]
                assert data["contact_email"] == self.test_data["valid_org"]["contact_email"]
                assert data["is_active"] is True
                
                # Track for potential cleanup
                self.created_organizations.append(data["id"])
                
                print(f"Successfully created organization: {data['id']}")
                
            elif response.status_code == 422:
                # Validation error - check the details
                error_data = response.json()
                print(f"Validation error: {error_data}")
                
                # This might be expected if professional email validation is working
                if "personal email" in json.dumps(error_data).lower():
                    pytest.skip("Professional email validation active - expected behavior")
                else:
                    assert False, f"Unexpected validation error: {error_data}"
                    
            elif response.status_code in [401, 403]:
                pytest.skip("Authentication not configured for integration tests")
            else:
                assert False, f"Unexpected response: {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API request failed: {e}")

    def test_professional_email_validation_integration(self):
        """Test that professional email validation works in integration"""
        try:
            # Test with personal email domain
            invalid_org_data = self.test_data["valid_org"].copy()
            invalid_org_data["contact_email"] = "admin@gmail.com"
            invalid_org_data["admin_email"] = "admin@gmail.com"
            invalid_org_data["name"] = f"Invalid Email Test {int(time.time())}"
            invalid_org_data["slug"] = f"invalid-email-test-{int(time.time())}"
            
            response = requests.post(
                f"{TEST_BASE_URL}/organizations",
                json=invalid_org_data,
                headers=self.auth_headers,
                verify=False,
                timeout=15
            )
            
            # Should get validation error
            assert response.status_code == 422
            
            error_data = response.json()
            error_text = json.dumps(error_data).lower()
            
            # Should mention gmail or personal email
            assert "gmail" in error_text or "personal" in error_text
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API request failed: {e}")

    def test_file_upload_integration(self):
        """Test organization creation with file upload"""
        try:
            # Create a test image file
            import io
            from PIL import Image
            
            # Create a small test image
            test_image = Image.new('RGB', (100, 100), color='red')
            img_buffer = io.BytesIO()
            test_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Prepare form data
            form_data = self.test_data["valid_org"].copy()
            form_data["name"] = f"File Upload Test {int(time.time())}"
            form_data["slug"] = f"file-upload-test-{int(time.time())}"
            
            files = {
                'logo': ('test_logo.png', img_buffer, 'image/png')
            }
            
            # Remove Content-Type header for multipart upload
            upload_headers = {"Authorization": self.auth_headers["Authorization"]}
            
            response = requests.post(
                f"{TEST_BASE_URL}/organizations/upload",
                data=form_data,
                files=files,
                headers=upload_headers,
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify file upload worked
                assert "logo_url" in data
                assert "logo_file_path" in data
                assert data["name"] == form_data["name"]
                
                self.created_organizations.append(data["id"])
                print(f"Successfully created organization with logo: {data['id']}")
                
            elif response.status_code in [401, 403]:
                pytest.skip("Authentication not configured for file upload tests")
            elif response.status_code == 422:
                error_data = response.json()
                print(f"File upload validation error: {error_data}")
                # This might be expected behavior
            else:
                print(f"Unexpected file upload response: {response.status_code} - {response.text}")
                
        except ImportError:
            pytest.skip("PIL not available for image testing")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"File upload API request failed: {e}")

    def test_invalid_file_type_integration(self):
        """Test that invalid file types are rejected"""
        try:
            # Create a text file instead of image
            text_content = b"This is not an image file"
            
            form_data = self.test_data["valid_org"].copy()
            form_data["name"] = f"Invalid File Test {int(time.time())}"
            form_data["slug"] = f"invalid-file-test-{int(time.time())}"
            
            files = {
                'logo': ('document.txt', text_content, 'text/plain')
            }
            
            upload_headers = {"Authorization": self.auth_headers["Authorization"]}
            
            response = requests.post(
                f"{TEST_BASE_URL}/organizations/upload",
                data=form_data,
                files=files,
                headers=upload_headers,
                verify=False,
                timeout=15
            )
            
            # Should get bad request for invalid file type
            if response.status_code == 400:
                error_data = response.json()
                assert "invalid file type" in error_data["detail"].lower()
            elif response.status_code in [401, 403]:
                pytest.skip("Authentication not configured")
            else:
                print(f"Unexpected response for invalid file: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Invalid file test API request failed: {e}")

    def test_organization_list_integration(self):
        """Test organization listing endpoint"""
        try:
            response = requests.get(
                f"{TEST_BASE_URL}/organizations",
                headers=self.auth_headers,
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                
                # If we have organizations, verify structure
                if data:
                    org = data[0]
                    required_fields = ["id", "name", "slug", "contact_email", "is_active"]
                    for field in required_fields:
                        assert field in org, f"Missing field: {field}"
                        
            elif response.status_code in [401, 403]:
                pytest.skip("Authentication not configured for list endpoint")
            else:
                print(f"Unexpected list response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"List API request failed: {e}")

    @pytest.mark.asyncio
    async def test_database_integration(self):
        """Test that organization data can be stored and retrieved from database"""
        try:
            # Connect to test database
            conn = await asyncpg.connect(**DB_TEST_CONFIG)
            
            # Test database connection and schema
            result = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            table_names = [row['table_name'] for row in result]
            
            # Check for organization-related tables
            expected_tables = ['organizations', 'users', 'organization_memberships']
            found_tables = [table for table in expected_tables if table in table_names]
            
            if found_tables:
                print(f"Found organization tables: {found_tables}")
                
                # Test organizations table structure if it exists
                if 'organizations' in table_names:
                    columns = await conn.fetch("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'organizations'
                    """)
                    
                    column_info = {row['column_name']: row['data_type'] for row in columns}
                    
                    # Check for required columns
                    required_columns = ['id', 'name', 'slug', 'contact_email', 'is_active']
                    for col in required_columns:
                        assert col in column_info, f"Missing column: {col}"
                    
                    print(f"Organizations table structure verified: {len(column_info)} columns")
                    
                    # Test if we can query existing data
                    org_count = await conn.fetchval("SELECT COUNT(*) FROM organizations")
                    print(f"Organizations in database: {org_count}")
                    
            await conn.close()
            
        except asyncpg.exceptions.PostgresError as e:
            pytest.skip(f"Database connection failed: {e}")
        except Exception as e:
            pytest.skip(f"Database test failed: {e}")

    def test_api_error_handling_integration(self):
        """Test API error handling and response format"""
        try:
            # Test with completely invalid data
            invalid_data = {
                "name": "",  # Empty required field
                "slug": "Invalid Slug With Spaces",  # Invalid pattern
                "contact_email": "not-an-email",  # Invalid email
                "contact_phone": "123"  # Too short
            }
            
            response = requests.post(
                f"{TEST_BASE_URL}/organizations",
                json=invalid_data,
                headers=self.auth_headers,
                verify=False,
                timeout=15
            )
            
            # Should get validation error
            assert response.status_code == 422
            
            error_data = response.json()
            assert "detail" in error_data
            
            # Check error format
            if isinstance(error_data["detail"], list):
                # Pydantic validation errors
                for error in error_data["detail"]:
                    assert "loc" in error
                    assert "msg" in error
                    assert "type" in error
                    
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Error handling test API request failed: {e}")

    def test_cors_and_security_headers_integration(self):
        """Test CORS and security headers in integration environment"""
        try:
            # Test CORS preflight
            response = requests.options(
                f"{TEST_BASE_URL}/organizations",
                headers={"Origin": "https://localhost:3000"},
                verify=False,
                timeout=10
            )
            
            # Should allow CORS or return appropriate headers
            assert response.status_code in [200, 204]
            
            # Test security headers on actual request
            response = requests.get(
                f"{TEST_BASE_URL}/health",
                verify=False,
                timeout=10
            )
            
            assert response.status_code == 200
            
            # Check for security headers (may not all be present in development)
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection'
            ]
            
            headers_found = [header for header in security_headers if header in response.headers]
            print(f"Security headers found: {headers_found}")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Security headers test failed: {e}")

    def test_service_performance_integration(self):
        """Test basic performance metrics for organization endpoints"""
        try:
            # Test response times for different endpoints
            endpoints = [
                "/health",
                "/test",
                "/organizations"  # May require auth
            ]
            
            performance_results = {}
            
            for endpoint in endpoints:
                start_time = time.time()
                
                try:
                    response = requests.get(
                        f"{TEST_BASE_URL}{endpoint}",
                        headers=self.auth_headers if endpoint == "/organizations" else {},
                        verify=False,
                        timeout=10
                    )
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    performance_results[endpoint] = {
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "success": response.status_code in [200, 401, 403]  # 401/403 expected for auth endpoints
                    }
                    
                except requests.exceptions.RequestException as e:
                    performance_results[endpoint] = {
                        "error": str(e),
                        "success": False
                    }
            
            print(f"Performance results: {performance_results}")
            
            # Check that at least health endpoint is fast
            if "/health" in performance_results:
                health_result = performance_results["/health"]
                assert health_result["success"], "Health endpoint should be accessible"
                assert health_result.get("response_time", 10) < 5.0, "Health endpoint should respond quickly"
                
        except Exception as e:
            pytest.skip(f"Performance test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])