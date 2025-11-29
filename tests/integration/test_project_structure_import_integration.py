"""
Integration Tests for Project Structure Import API

These tests verify the complete flow of uploading project structure files
through the API endpoints, from validation to import.

BUSINESS CONTEXT:
Organization administrators can upload configuration files (JSON, YAML, or
plain text) to create complete project hierarchies instead of manually
creating each component through the UI.

TEST SCENARIOS:
1. Validate project structure files via API
2. Import project structure files via API
3. Download template files via API
4. Error handling for invalid files

INTEGRATION POINTS:
- Course Management Service API (port 8004)
- FastAPI file upload endpoints
- ProjectStructureParser service
"""
import pytest
import requests
import json
import yaml
import os
import jwt
from uuid import uuid4
from datetime import datetime, timedelta

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "https://localhost:8004")
VERIFY_SSL = os.getenv("VERIFY_SSL", "false").lower() == "true"
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "ivft2h9bsaVy3yfTdQal-EcXr6-ZRChzlbdct7hlNu8")

# Skip tests if auth service not available
SKIP_AUTH_TESTS = os.getenv("SKIP_AUTH_INTEGRATION", "true").lower() == "true"

# Suppress SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def generate_auth_token(user_id: str = None, org_id: str = None, role: str = "org_admin"):
    """
    Generate a valid JWT authentication token for testing.

    BUSINESS CONTEXT:
    Integration tests require authenticated requests. This helper
    generates valid JWT tokens that mimic real user authentication.

    Args:
        user_id: User ID to encode in token (defaults to random UUID)
        org_id: Organization ID for the user context
        role: User role (org_admin, instructor, admin, student)

    Returns:
        JWT token string
    """
    if not user_id:
        user_id = str(uuid4())

    payload = {
        'sub': user_id,
        'user_id': user_id,
        'email': f'test-{user_id[:8]}@example.com',
        'role': role,
        'organization_id': org_id or str(uuid4()),
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }

    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def get_auth_headers(org_id: str = None, role: str = "org_admin"):
    """
    Get headers with authentication token for API requests.

    Args:
        org_id: Organization ID to include in context
        role: User role for the token

    Returns:
        Dict of headers including Authorization
    """
    token = generate_auth_token(org_id=org_id, role=role)
    headers = {
        'Authorization': f'Bearer {token}'
    }
    if org_id:
        headers['X-Organization-ID'] = org_id
    return headers


@pytest.mark.skipif(SKIP_AUTH_TESTS, reason="Auth integration tests require full environment (set SKIP_AUTH_INTEGRATION=false)")
class TestProjectStructureValidationAPI:
    """
    Integration tests for project structure validation endpoint.

    ENDPOINT: POST /organizations/{org_id}/projects/import/validate

    BUSINESS FLOW:
    1. User uploads a project structure file
    2. API validates the file format and structure
    3. Returns validation result with counts and any errors
    4. User can then decide whether to proceed with import

    NOTE: These tests require the full auth infrastructure including user-management service.
    Set SKIP_AUTH_INTEGRATION=false to run these tests.
    """

    @pytest.fixture
    def organization_id(self):
        """Generate a test organization ID."""
        return str(uuid4())

    @pytest.fixture
    def valid_json_content(self, organization_id):
        """Create valid JSON project structure."""
        return json.dumps({
            "organization_id": organization_id,
            "project": {
                "name": "Integration Test Project",
                "slug": "integration-test-project",
                "description": "Project created via integration test",
                "tracks": [
                    {
                        "name": "Backend Track",
                        "description": "Backend development training",
                        "courses": [
                            {"title": "Python Basics", "description": "Intro to Python"},
                            {"title": "Django Framework", "description": "Web development with Django"}
                        ]
                    },
                    {
                        "name": "Frontend Track",
                        "courses": [
                            {"title": "React Fundamentals", "description": "React.js basics"}
                        ]
                    }
                ],
                "subprojects": [
                    {
                        "name": "Q1 2024 Cohort",
                        "location": "Main Campus",
                        "start_date": "2024-01-15",
                        "end_date": "2024-03-31",
                        "max_students": 30
                    }
                ],
                "instructors": [
                    {"email": "lead@example.com", "name": "Lead Instructor", "role": "lead"},
                    {"email": "assistant@example.com", "name": "Assistant Instructor"}
                ]
            }
        })

    @pytest.fixture
    def valid_yaml_content(self, organization_id):
        """Create valid YAML project structure."""
        return f"""
organization_id: {organization_id}
project:
  name: YAML Test Project
  slug: yaml-test-project
  description: Project created from YAML file
  tracks:
    - name: Data Science Track
      description: Data science and ML training
      courses:
        - title: Python for Data Science
          description: Python fundamentals for data analysis
          difficulty: beginner
        - title: Machine Learning Basics
          description: Introduction to ML algorithms
          difficulty: intermediate
  subprojects:
    - name: Summer 2024 Cohort
      location: Online
      start_date: 2024-06-01
      max_students: 50
  instructors:
    - email: data.lead@example.com
      name: Data Science Lead
      role: lead
"""

    @pytest.fixture
    def valid_text_content(self, organization_id):
        """Create valid plain text project structure."""
        return f"""
Organization: {organization_id}
Project: Text Format Test Project
Slug: text-format-test
Description: Project created from plain text file

Tracks:
  - Name: DevOps Track
    Description: DevOps and infrastructure training
    Courses:
      - Title: Docker Fundamentals
        Description: Container basics
      - Title: Kubernetes
        Description: Container orchestration

Subprojects:
  - Name: Fall 2024 Cohort
    Location: NYC Office
    Start: 2024-09-01
    End: 2024-12-15
    Max Students: 25

Instructors:
  - Email: devops.lead@example.com
    Name: DevOps Lead
    Role: lead
"""

    def test_validate_json_file_success(self, organization_id, valid_json_content):
        """
        Test that valid JSON file passes validation.

        EXPECTED:
        - HTTP 200 response
        - valid: true
        - Correct entity counts
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/validate"

        files = {
            'file': ('project.json', valid_json_content, 'application/json')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["project_name"] == "Integration Test Project"
        assert data["tracks_count"] == 2
        assert data["courses_count"] == 0  # Direct courses only
        assert data["subprojects_count"] == 1
        assert data["instructors_count"] == 2

    def test_validate_yaml_file_success(self, organization_id, valid_yaml_content):
        """
        Test that valid YAML file passes validation.

        EXPECTED:
        - HTTP 200 response
        - valid: true
        - Correct entity counts
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/validate"

        files = {
            'file': ('project.yaml', valid_yaml_content, 'text/yaml')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["project_name"] == "YAML Test Project"
        assert data["tracks_count"] == 1

    def test_validate_text_file_success(self, organization_id, valid_text_content):
        """
        Test that valid plain text file passes validation.

        EXPECTED:
        - HTTP 200 response
        - valid: true
        - Correct entity counts
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/validate"

        files = {
            'file': ('project.txt', valid_text_content, 'text/plain')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["project_name"] == "Text Format Test Project"

    def test_validate_empty_file_fails(self, organization_id):
        """
        Test that empty file fails validation.

        EXPECTED:
        - HTTP 200 response (validation response, not error)
        - valid: false
        - Error message about empty file
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/validate"

        files = {
            'file': ('empty.json', '', 'application/json')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert "empty" in data["errors"][0].lower()

    def test_validate_invalid_json_fails(self, organization_id):
        """
        Test that invalid JSON syntax fails validation.

        EXPECTED:
        - HTTP 200 response
        - valid: false
        - Error message about JSON syntax
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/validate"

        invalid_json = '{"project": invalid}'

        files = {
            'file': ('broken.json', invalid_json, 'application/json')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_validate_missing_required_field_fails(self, organization_id):
        """
        Test that file missing required fields fails validation.

        EXPECTED:
        - HTTP 200 response
        - valid: false
        - Error message about missing field
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/validate"

        # Missing organization_id
        incomplete = json.dumps({
            "project": {
                "name": "Test",
                "slug": "test",
                "description": "Test"
            }
        })

        files = {
            'file': ('incomplete.json', incomplete, 'application/json')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert any("organization" in err.lower() for err in data["errors"])

    def test_validate_org_id_mismatch_warning(self, organization_id):
        """
        Test that org ID mismatch in file produces warning.

        EXPECTED:
        - HTTP 200 response
        - valid: true (file is still valid)
        - Warning about org ID mismatch
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/validate"

        different_org = str(uuid4())
        content = json.dumps({
            "organization_id": different_org,  # Different from URL
            "project": {
                "name": "Test",
                "slug": "test",
                "description": "Test"
            }
        })

        files = {
            'file': ('project.json', content, 'application/json')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert len(data["warnings"]) > 0
        assert any("organization" in warning.lower() for warning in data["warnings"])


@pytest.mark.skipif(SKIP_AUTH_TESTS, reason="Auth integration tests require full environment (set SKIP_AUTH_INTEGRATION=false)")
class TestProjectStructureImportAPI:
    """
    Integration tests for project structure import endpoint.

    ENDPOINT: POST /organizations/{org_id}/projects/import

    BUSINESS FLOW:
    1. User uploads a validated project structure file
    2. API creates all entities in the database
    3. Returns import result with created entity counts

    NOTE: These tests require the full auth infrastructure including user-management service.
    Set SKIP_AUTH_INTEGRATION=false to run these tests.
    """

    @pytest.fixture
    def organization_id(self):
        """Generate a test organization ID."""
        return str(uuid4())

    @pytest.fixture
    def valid_json_content(self, organization_id):
        """Create valid JSON project structure for import."""
        return json.dumps({
            "organization_id": organization_id,
            "project": {
                "name": "Import Test Project",
                "slug": "import-test-project",
                "description": "Project created via import",
                "tracks": [
                    {
                        "name": "Test Track",
                        "courses": [
                            {"title": "Test Course", "description": "Test course description"}
                        ]
                    }
                ],
                "instructors": [
                    {"email": "test@example.com", "name": "Test Instructor"}
                ]
            }
        })

    def test_import_dry_run_does_not_create(self, organization_id, valid_json_content):
        """
        Test that dry_run=true validates without creating entities.

        EXPECTED:
        - HTTP 200 response
        - success: true
        - message indicates dry run
        - created counts are all 0
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import?dry_run=true"

        files = {
            'file': ('project.json', valid_json_content, 'application/json')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "dry run" in data["message"].lower()
        assert data["created"]["project"] == 0
        assert data["created"]["tracks"] == 0
        assert data["created"]["courses"] == 0

    def test_import_parses_successfully(self, organization_id, valid_json_content):
        """
        Test that import parses file and returns expected structure.

        NOTE: Full DAO integration is pending, so this test verifies
        the parsing and response structure.

        EXPECTED:
        - HTTP 200 response
        - success: true
        - Created counts reflect parsed structure
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import"

        files = {
            'file': ('project.json', valid_json_content, 'application/json')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["project_name"] == "Import Test Project"
        # Verify counts match the structure
        assert data["created"]["tracks"] == 1
        assert data["created"]["courses"] == 1
        assert data["created"]["instructors"] == 1

    def test_import_invalid_file_returns_400(self, organization_id):
        """
        Test that invalid file returns 400 error.

        EXPECTED:
        - HTTP 400 response
        - Error detail in response
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import"

        invalid_content = '{"invalid": "json"}'  # Missing required fields

        files = {
            'file': ('broken.json', invalid_content, 'application/json')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_import_empty_file_returns_400(self, organization_id):
        """
        Test that empty file returns 400 error.

        EXPECTED:
        - HTTP 400 response
        - Error about empty file
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import"

        files = {
            'file': ('empty.json', '', 'application/json')
        }
        headers = get_auth_headers(org_id=organization_id)

        response = requests.post(url, files=files, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 400


@pytest.mark.skipif(SKIP_AUTH_TESTS, reason="Auth integration tests require full environment (set SKIP_AUTH_INTEGRATION=false)")
class TestProjectTemplateDownloadAPI:
    """
    Integration tests for project template download endpoint.

    ENDPOINT: GET /organizations/{org_id}/projects/import/template

    BUSINESS FLOW:
    1. User requests a template file in desired format
    2. API generates template with organization ID populated
    3. User downloads and fills in the template
    4. User uploads completed template for import

    NOTE: These tests require the full auth infrastructure including user-management service.
    Set SKIP_AUTH_INTEGRATION=false to run these tests.
    """

    @pytest.fixture
    def organization_id(self):
        """Generate a test organization ID."""
        return str(uuid4())

    def test_download_json_template(self, organization_id):
        """
        Test downloading JSON format template.

        EXPECTED:
        - HTTP 200 response
        - Content-Type: application/json
        - Valid JSON with org ID populated
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/template?format=json"
        headers = get_auth_headers(org_id=organization_id)

        response = requests.get(url, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")

        # Verify it's valid JSON
        content = response.text
        data = json.loads(content)

        # Verify org ID is populated
        assert organization_id in content

    def test_download_yaml_template(self, organization_id):
        """
        Test downloading YAML format template.

        EXPECTED:
        - HTTP 200 response
        - Content-Type: text/yaml
        - Valid YAML with org ID populated
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/template?format=yaml"
        headers = get_auth_headers(org_id=organization_id)

        response = requests.get(url, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        assert "yaml" in response.headers.get("Content-Type", "").lower()

        # Verify it's valid YAML
        content = response.text
        data = yaml.safe_load(content)

        # Verify org ID is populated
        assert organization_id in content

    def test_download_text_template(self, organization_id):
        """
        Test downloading plain text format template.

        EXPECTED:
        - HTTP 200 response
        - Content-Type: text/plain
        - Template with org ID populated
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/template?format=text"
        headers = get_auth_headers(org_id=organization_id)

        response = requests.get(url, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        assert "text/plain" in response.headers.get("Content-Type", "")

        # Verify org ID is populated
        content = response.text
        assert organization_id in content

    def test_download_default_format_is_yaml(self, organization_id):
        """
        Test that default template format is YAML.

        EXPECTED:
        - HTTP 200 response
        - Content-Type: text/yaml
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/template"
        headers = get_auth_headers(org_id=organization_id)

        response = requests.get(url, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 200
        assert "yaml" in response.headers.get("Content-Type", "").lower()

    def test_download_invalid_format_returns_400(self, organization_id):
        """
        Test that invalid format parameter returns 400.

        EXPECTED:
        - HTTP 400 response
        - Error about invalid format
        """
        url = f"{BASE_URL}/organizations/{organization_id}/projects/import/template?format=invalid"
        headers = get_auth_headers(org_id=organization_id)

        response = requests.get(url, headers=headers, verify=VERIFY_SSL)

        assert response.status_code == 400
        data = response.json()
        assert "format" in data.get("detail", "").lower()

    def test_template_has_content_disposition_header(self, organization_id):
        """
        Test that response includes Content-Disposition for download.

        EXPECTED:
        - Content-Disposition header present
        - Filename includes format extension
        """
        headers = get_auth_headers(org_id=organization_id)
        for format_type in ["json", "yaml", "text"]:
            url = f"{BASE_URL}/organizations/{organization_id}/projects/import/template?format={format_type}"

            response = requests.get(url, headers=headers, verify=VERIFY_SSL)

            assert response.status_code == 200
            content_disposition = response.headers.get("Content-Disposition", "")
            assert "attachment" in content_disposition
            assert f"project-template.{format_type}" in content_disposition


@pytest.mark.skipif(SKIP_AUTH_TESTS, reason="Auth integration tests require full environment (set SKIP_AUTH_INTEGRATION=false)")
class TestRoundTripWorkflow:
    """
    Integration tests for complete round-trip workflow.

    BUSINESS FLOW:
    1. Download template
    2. Fill in template
    3. Validate filled template
    4. Import project structure
    5. Verify created entities

    NOTE: These tests require the full auth infrastructure including user-management service.
    Set SKIP_AUTH_INTEGRATION=false to run these tests.
    """

    @pytest.fixture
    def organization_id(self):
        """Generate a test organization ID."""
        return str(uuid4())

    def test_download_validate_import_cycle(self, organization_id):
        """
        Test complete workflow: download template, fill, validate, import.

        EXPECTED:
        - Can download template
        - Can modify template with actual data
        - Validation passes
        - Import succeeds
        """
        headers = get_auth_headers(org_id=organization_id)

        # Step 1: Download YAML template
        template_url = f"{BASE_URL}/organizations/{organization_id}/projects/import/template?format=yaml"
        template_response = requests.get(template_url, headers=headers, verify=VERIFY_SSL)

        assert template_response.status_code == 200

        # Step 2: Parse and modify template
        template_content = yaml.safe_load(template_response.text)
        template_content["organization_id"] = organization_id
        template_content["project"]["name"] = "Round Trip Test Project"
        template_content["project"]["slug"] = "round-trip-test"
        template_content["project"]["description"] = "Created via round-trip workflow test"

        modified_yaml = yaml.dump(template_content)

        # Step 3: Validate modified template
        validate_url = f"{BASE_URL}/organizations/{organization_id}/projects/import/validate"
        validate_response = requests.post(
            validate_url,
            files={'file': ('project.yaml', modified_yaml, 'text/yaml')},
            headers=headers,
            verify=VERIFY_SSL
        )

        assert validate_response.status_code == 200
        validation_data = validate_response.json()
        assert validation_data["valid"] is True

        # Step 4: Import the project (dry run to avoid side effects)
        import_url = f"{BASE_URL}/organizations/{organization_id}/projects/import?dry_run=true"
        import_response = requests.post(
            import_url,
            files={'file': ('project.yaml', modified_yaml, 'text/yaml')},
            headers=headers,
            verify=VERIFY_SSL
        )

        assert import_response.status_code == 200
        import_data = import_response.json()
        assert import_data["success"] is True


# Run tests with: pytest tests/integration/test_project_structure_import_integration.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
