"""
Integration tests for Metadata API

TESTING STRATEGY:
End-to-end tests with real database and FastAPI test client
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4

# Add service directory to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from main import app


@pytest.mark.asyncio
class TestMetadataAPIIntegration:
    """Integration tests for Metadata API endpoints"""

    async def test_health_endpoint(self):
        """Test: Health endpoint should return 200"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/metadata/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "metadata-service"

    async def test_root_endpoint(self):
        """Test: Root endpoint should return service info"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "metadata-service"
        assert "version" in data
        assert "api" in data

    async def test_create_and_get_metadata(self):
        """Test: Should create and retrieve metadata"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create metadata
            entity_id = str(uuid4())
            create_data = {
                "entity_id": entity_id,
                "entity_type": "test",
                "title": "Integration Test Metadata",
                "description": "Test description",
                "tags": ["test", "integration"],
                "keywords": ["api", "fastapi"],
                "metadata": {"test": "value"}
            }

            create_response = await client.post("/api/v1/metadata/", json=create_data)

            assert create_response.status_code == 201
            created = create_response.json()
            assert created["title"] == "Integration Test Metadata"
            assert created["entity_id"] == entity_id

            # Get metadata by ID
            metadata_id = created["id"]
            get_response = await client.get(f"/api/v1/metadata/{metadata_id}")

            assert get_response.status_code == 200
            retrieved = get_response.json()
            assert retrieved["id"] == metadata_id
            assert retrieved["title"] == "Integration Test Metadata"

    async def test_search_metadata(self):
        """Test: Should search metadata"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create test metadata
            entity_id = str(uuid4())
            create_data = {
                "entity_id": entity_id,
                "entity_type": "test",
                "title": "Python Programming Course",
                "tags": ["python"],
                "metadata": {}
            }

            await client.post("/api/v1/metadata/", json=create_data)

            # Search
            search_data = {
                "query": "Python",
                "entity_types": ["test"],
                "limit": 10
            }

            search_response = await client.post("/api/v1/metadata/search", json=search_data)

            assert search_response.status_code == 200
            results = search_response.json()
            assert len(results) > 0
            assert any("Python" in r["title"] for r in results)

    async def test_update_metadata(self):
        """Test: Should update metadata"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create metadata
            entity_id = str(uuid4())
            create_data = {
                "entity_id": entity_id,
                "entity_type": "test",
                "title": "Original Title",
                "metadata": {}
            }

            create_response = await client.post("/api/v1/metadata/", json=create_data)
            metadata_id = create_response.json()["id"]

            # Update
            update_data = {
                "title": "Updated Title",
                "description": "New description"
            }

            update_response = await client.put(
                f"/api/v1/metadata/{metadata_id}",
                json=update_data
            )

            assert update_response.status_code == 200
            updated = update_response.json()
            assert updated["title"] == "Updated Title"
            assert updated["description"] == "New description"

    async def test_delete_metadata(self):
        """Test: Should delete metadata"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create metadata
            entity_id = str(uuid4())
            create_data = {
                "entity_id": entity_id,
                "entity_type": "test",
                "title": "To Delete",
                "metadata": {}
            }

            create_response = await client.post("/api/v1/metadata/", json=create_data)
            metadata_id = create_response.json()["id"]

            # Delete
            delete_response = await client.delete(f"/api/v1/metadata/{metadata_id}")
            assert delete_response.status_code == 204

            # Verify deleted
            get_response = await client.get(f"/api/v1/metadata/{metadata_id}")
            assert get_response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
