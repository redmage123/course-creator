"""
TDD Tests for Materialized View Analytics

RED PHASE: These tests will fail until we implement the DAO methods
and run the migration to create materialized views.

Test Coverage:
- File upload analytics queries
- File download analytics queries
- Combined summary queries
- Refresh functionality
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from data_access.metadata_dao import MetadataDAO


@pytest.mark.asyncio
class TestFileUploadAnalytics:
    """Test materialized view queries for file upload analytics"""

    async def test_get_upload_analytics_by_course(self, metadata_dao: MetadataDAO):
        """
        Test retrieving upload analytics for a specific course

        EXPECTED: Returns aggregated upload metrics grouped by file type
        """
        course_id = 1

        result = await metadata_dao.get_upload_analytics_by_course(course_id)

        assert result is not None
        assert isinstance(result, list)
        # Should have upload stats grouped by file type
        if len(result) > 0:
            assert 'file_type' in result[0]
            assert 'total_uploads' in result[0]
            assert 'total_bytes' in result[0]
            assert 'avg_file_size_bytes' in result[0]

    async def test_get_upload_analytics_by_file_type(self, metadata_dao: MetadataDAO):
        """
        Test retrieving upload analytics filtered by file type

        EXPECTED: Returns stats for specific file type (e.g., 'syllabus')
        """
        file_type = 'syllabus'

        result = await metadata_dao.get_upload_analytics_by_file_type(file_type)

        assert result is not None
        assert isinstance(result, list)
        for row in result:
            assert row['file_type'] == file_type

    async def test_get_upload_analytics_recent_activity(self, metadata_dao: MetadataDAO):
        """
        Test retrieving recent upload activity (last 7 days)

        EXPECTED: Returns uploads from the last 7 days
        """
        days = 7

        result = await metadata_dao.get_recent_upload_activity(days=days)

        assert result is not None
        assert isinstance(result, list)
        # Should have last_7_days metrics
        if len(result) > 0:
            assert 'uploads_last_7_days' in result[0]


@pytest.mark.asyncio
class TestFileDownloadAnalytics:
    """Test materialized view queries for file download analytics"""

    async def test_get_download_analytics_by_course(self, metadata_dao: MetadataDAO):
        """
        Test retrieving download analytics for a specific course

        EXPECTED: Returns aggregated download metrics
        """
        course_id = 1

        result = await metadata_dao.get_download_analytics_by_course(course_id)

        assert result is not None
        assert isinstance(result, list)
        if len(result) > 0:
            assert 'file_type' in result[0]
            assert 'total_downloads' in result[0]
            assert 'unique_students' in result[0]

    async def test_get_most_downloaded_files(self, metadata_dao: MetadataDAO):
        """
        Test retrieving most downloaded files

        EXPECTED: Returns files ordered by download count
        """
        limit = 10

        result = await metadata_dao.get_most_downloaded_files(limit=limit)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) <= limit
        # Should be ordered by download count descending
        if len(result) > 1:
            assert result[0]['total_downloads'] >= result[1]['total_downloads']


@pytest.mark.asyncio
class TestCourseMaterialSummary:
    """Test combined upload/download summary queries"""

    async def test_get_course_material_summary(self, metadata_dao: MetadataDAO):
        """
        Test retrieving combined upload/download summary

        EXPECTED: Returns both upload and download metrics
        """
        course_id = 1

        result = await metadata_dao.get_course_material_summary(course_id)

        assert result is not None
        assert isinstance(result, dict) or isinstance(result, list)
        # Should have both upload and download metrics
        if isinstance(result, list) and len(result) > 0:
            assert 'total_uploads' in result[0]
            assert 'total_downloads' in result[0]
            assert 'downloads_per_upload' in result[0]

    async def test_get_engagement_metrics(self, metadata_dao: MetadataDAO):
        """
        Test retrieving engagement metrics (downloads per upload ratio)

        EXPECTED: Returns courses ordered by engagement
        """
        result = await metadata_dao.get_engagement_metrics(limit=20)

        assert result is not None
        assert isinstance(result, list)
        # Should have engagement ratio
        if len(result) > 0:
            assert 'downloads_per_upload' in result[0]


@pytest.mark.asyncio
class TestMaterializedViewRefresh:
    """Test materialized view refresh functionality"""

    async def test_refresh_analytics_views(self, metadata_dao: MetadataDAO):
        """
        Test refreshing all analytics materialized views

        EXPECTED: Successfully refreshes without errors
        """
        # This should call the PostgreSQL function to refresh views
        await metadata_dao.refresh_analytics_views()

        # If no exception raised, refresh succeeded
        assert True

    async def test_analytics_reflect_new_data(self, metadata_dao: MetadataDAO, sample_upload_metadata):
        """
        Test that analytics views reflect new data after refresh

        EXPECTED: New uploads appear in analytics after refresh
        """
        # Create new upload metadata
        await metadata_dao.create(sample_upload_metadata)

        # Refresh views
        await metadata_dao.refresh_analytics_views()

        # Query analytics - should include new data
        course_id = int(sample_upload_metadata.metadata.get('course_id'))
        result = await metadata_dao.get_upload_analytics_by_course(course_id)

        assert len(result) > 0


# Fixtures

@pytest_asyncio.fixture
async def metadata_dao(postgresql_pool):
    """Create MetadataDAO instance with test database pool"""
    return MetadataDAO(postgresql_pool)


@pytest.fixture
def sample_upload_metadata():
    """Create sample upload metadata for testing"""
    from metadata_service.domain.entities.metadata import Metadata

    return Metadata(
        entity_id=uuid4(),
        entity_type='course_material_upload',
        title='Test Syllabus Upload',
        description='Instructor uploaded course syllabus',
        tags=['syllabus', 'instructor_upload'],
        metadata={
            'course_id': 1,
            'file_type': 'syllabus',
            'filename': 'CS101-syllabus.pdf',
            'file_size_bytes': 524288,
            'instructor_id': str(uuid4()),
            'upload_timestamp': datetime.utcnow().isoformat()
        }
    )
