"""
Integration Tests for Track System
Tests integration between service layer, repository, and database
"""
import pytest
import asyncio
import asyncpg
from uuid import uuid4
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/organization-management'))

from organization_management.domain.entities.track import Track, TrackStatus, TrackType
from organization_management.infrastructure.repositories.postgresql_track_repository import PostgreSQLTrackRepository
from organization_management.application.services.track_service import TrackService


class TestTrackSystemIntegration:
    """Integration tests for track system components"""
    
    @pytest.fixture
    async def db_connection(self):
        """Create test database connection"""
        # Use test database connection parameters
        connection = await asyncpg.connect(
            host='localhost',
            port=5433,
            user='postgres',
            password='postgres_password',
            database='course_creator'
        )
        
        # Setup test schema
        await self._setup_test_schema(connection)
        
        yield connection
        
        # Cleanup
        await self._cleanup_test_data(connection)
        await connection.close()
    
    @pytest.fixture
    async def db_pool(self, db_connection):
        """Create test database pool"""
        pool = await asyncpg.create_pool(
            host='localhost',
            port=5433,
            user='postgres',
            password='postgres_password',
            database='course_creator',
            min_size=1,
            max_size=5
        )
        yield pool
        await pool.close()
    
    @pytest.fixture
    def repository(self, db_pool):
        """Create repository with real database pool"""
        return PostgreSQLTrackRepository(db_pool)
    
    @pytest.fixture
    def service(self, repository):
        """Create service with real repository"""
        return TrackService(repository)
    
    @pytest.fixture
    async def test_project_id(self, db_connection):
        """Create test project and return its ID"""
        # First create test organization
        org_id = uuid4()
        await db_connection.execute("""
            INSERT INTO organizations (id, name, slug) 
            VALUES ($1, 'Test Organization', 'test-org')
            ON CONFLICT (slug) DO NOTHING
        """, org_id)
        
        # Create test project
        project_id = uuid4()
        await db_connection.execute("""
            INSERT INTO projects (id, organization_id, name, slug) 
            VALUES ($1, $2, 'Test Project', 'test-project')
            ON CONFLICT (organization_id, slug) DO NOTHING
        """, project_id, org_id)
        
        return project_id
    
    async def _setup_test_schema(self, connection):
        """Setup test database schema"""
        # Ensure required enums exist
        await connection.execute("""
            DO $$ BEGIN
                CREATE TYPE track_type AS ENUM ('sequential', 'flexible', 'milestone_based');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        await connection.execute("""
            DO $$ BEGIN
                CREATE TYPE track_status AS ENUM ('draft', 'active', 'completed', 'archived');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # Ensure tracks table exists
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(100) NOT NULL,
                description TEXT,
                track_type track_type DEFAULT 'sequential',
                target_audience TEXT[],
                prerequisites TEXT[],
                duration_weeks INTEGER,
                max_enrolled INTEGER,
                learning_objectives TEXT[],
                skills_taught TEXT[],
                difficulty_level VARCHAR(20) DEFAULT 'beginner',
                sequence_order INTEGER DEFAULT 0,
                auto_enroll_enabled BOOLEAN DEFAULT true,
                status track_status DEFAULT 'draft',
                settings JSONB DEFAULT '{}',
                created_by UUID,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, slug)
            )
        """)
    
    async def _cleanup_test_data(self, connection):
        """Clean up test data"""
        await connection.execute("DELETE FROM tracks WHERE name LIKE 'Test%' OR name LIKE '%Test%'")
        await connection.execute("DELETE FROM projects WHERE name LIKE 'Test%'")
        await connection.execute("DELETE FROM organizations WHERE name LIKE 'Test%'")
    
    @pytest.mark.asyncio
    async def test_track_crud_operations(self, repository, test_project_id):
        """Test complete CRUD operations for tracks"""
        # Create track
        track = Track(
            project_id=test_project_id,
            name="Integration Test Track",
            slug="integration-test-track",
            description="Track for integration testing",
            track_type=TrackType.SEQUENTIAL,
            target_audience=["Developer", "Tester"],
            prerequisites=["Basic Programming"],
            duration_weeks=8,
            max_enrolled=30,
            learning_objectives=["Learn Testing", "Master Integration"],
            skills_taught=["Python", "Pytest"],
            difficulty_level="intermediate",
            auto_enroll_enabled=True,
            settings={"test_mode": True}
        )
        
        # Test create
        created_track = await repository.create(track)
        assert created_track.id is not None
        assert created_track.name == "Integration Test Track"
        assert created_track.slug == "integration-test-track"
        assert created_track.project_id == test_project_id
        
        # Test get by ID
        retrieved_track = await repository.get_by_id(created_track.id)
        assert retrieved_track is not None
        assert retrieved_track.name == created_track.name
        assert retrieved_track.target_audience == ["Developer", "Tester"]
        assert retrieved_track.settings == {"test_mode": True}
        
        # Test update
        retrieved_track.name = "Updated Integration Test Track"
        retrieved_track.duration_weeks = 12
        updated_track = await repository.update(retrieved_track)
        assert updated_track.name == "Updated Integration Test Track"
        assert updated_track.duration_weeks == 12
        
        # Test get by project and slug
        slug_track = await repository.get_by_project_and_slug(test_project_id, "integration-test-track")
        assert slug_track is not None
        assert slug_track.id == created_track.id
        
        # Test existence check
        exists = await repository.exists_by_project_and_slug(test_project_id, "integration-test-track")
        assert exists is True
        
        non_exists = await repository.exists_by_project_and_slug(test_project_id, "non-existent-slug")
        assert non_exists is False
        
        # Test delete
        deleted = await repository.delete(created_track.id)
        assert deleted is True
        
        # Verify deletion
        deleted_track = await repository.get_by_id(created_track.id)
        assert deleted_track is None
    
    @pytest.mark.asyncio
    async def test_track_queries(self, repository, test_project_id):
        """Test various track query operations"""
        # Create multiple test tracks
        tracks_data = [
            {
                "name": "Beginner Python Track",
                "slug": "beginner-python",
                "difficulty_level": "beginner",
                "target_audience": ["New Developer"],
                "status": TrackStatus.ACTIVE,
                "skills_taught": ["Python Basics"]
            },
            {
                "name": "Advanced React Track",
                "slug": "advanced-react",
                "difficulty_level": "advanced",
                "target_audience": ["Frontend Developer"],
                "status": TrackStatus.ACTIVE,
                "skills_taught": ["React", "Redux"]
            },
            {
                "name": "Draft DevOps Track",
                "slug": "draft-devops",
                "difficulty_level": "intermediate",
                "target_audience": ["DevOps Engineer"],
                "status": TrackStatus.DRAFT,
                "skills_taught": ["Docker", "Kubernetes"]
            }
        ]
        
        created_tracks = []
        for track_data in tracks_data:
            track = Track(
                project_id=test_project_id,
                name=track_data["name"],
                slug=track_data["slug"],
                difficulty_level=track_data["difficulty_level"],
                target_audience=track_data["target_audience"],
                status=track_data["status"],
                skills_taught=track_data["skills_taught"]
            )
            created_track = await repository.create(track)
            created_tracks.append(created_track)
        
        try:
            # Test get by project
            project_tracks = await repository.get_by_project(test_project_id)
            assert len(project_tracks) >= 3
            
            # Test get by status
            active_tracks = await repository.get_by_status(TrackStatus.ACTIVE)
            active_track_names = [t.name for t in active_tracks]
            assert "Beginner Python Track" in active_track_names
            assert "Advanced React Track" in active_track_names
            
            # Test get by project and status
            project_active_tracks = await repository.get_by_project_and_status(test_project_id, TrackStatus.ACTIVE)
            assert len(project_active_tracks) == 2
            
            # Test get by target audience
            dev_tracks = await repository.get_by_target_audience("Frontend Developer", test_project_id)
            assert len(dev_tracks) == 1
            assert dev_tracks[0].name == "Advanced React Track"
            
            # Test get by difficulty level
            beginner_tracks = await repository.get_by_difficulty_level("beginner", test_project_id)
            assert len(beginner_tracks) == 1
            assert beginner_tracks[0].name == "Beginner Python Track"
            
            # Test search
            search_results = await repository.search_by_project(test_project_id, "React")
            assert len(search_results) >= 1
            assert any("React" in track.name for track in search_results)
            
            # Test count operations
            total_count = await repository.count_by_project(test_project_id)
            assert total_count >= 3
            
            active_count = await repository.count_by_status(TrackStatus.ACTIVE)
            assert active_count >= 2
            
        finally:
            # Cleanup created tracks
            for track in created_tracks:
                await repository.delete(track.id)
    
    @pytest.mark.asyncio
    async def test_service_integration(self, service, test_project_id):
        """Test service layer integration"""
        created_by = uuid4()
        
        # Test track creation through service
        track = await service.create_track(
            project_id=test_project_id,
            name="Service Integration Track",
            slug="service-integration-track",
            description="Testing service integration",
            target_audience=["Integration Tester"],
            skills_taught=["Integration Testing"],
            duration_weeks=6,
            difficulty_level="intermediate",
            created_by=created_by
        )
        
        assert track.id is not None
        assert track.name == "Service Integration Track"
        assert track.sequence_order == 1  # First track in project
        
        try:
            # Test service validation
            with pytest.raises(ValueError, match="Track with slug .* already exists"):
                await service.create_track(
                    project_id=test_project_id,
                    name="Duplicate Track",
                    slug="service-integration-track"  # Same slug
                )
            
            # Test track retrieval
            retrieved = await service.get_track(track.id)
            assert retrieved.name == track.name
            
            # Test track update
            updated = await service.update_track(
                track_id=track.id,
                name="Updated Service Integration Track",
                duration_weeks=10
            )
            assert updated.name == "Updated Service Integration Track"
            assert updated.duration_weeks == 10
            
            # Test track activation
            activated = await service.activate_track(track.id)
            assert activated.status == TrackStatus.ACTIVE
            assert activated.is_active() is True
            
            # Test track statistics
            stats = await service.get_track_statistics(track.id)
            assert stats["name"] == "Updated Service Integration Track"
            assert stats["status"] == TrackStatus.ACTIVE.value
            assert "estimated_completion" in stats
            
            # Test prerequisites validation
            validation = await service.validate_track_prerequisites(
                track.id,
                ["Integration Testing", "Python"]
            )
            assert validation["meets_requirements"] is True
            
        finally:
            # Cleanup
            await service.delete_track(track.id)
    
    @pytest.mark.asyncio
    async def test_auto_enrollment_tracks(self, repository, test_project_id):
        """Test auto-enrollment track queries"""
        # Create tracks with different auto-enrollment settings
        auto_track = Track(
            project_id=test_project_id,
            name="Auto Enrollment Track",
            slug="auto-enrollment-track",
            status=TrackStatus.ACTIVE,
            auto_enroll_enabled=True
        )
        
        manual_track = Track(
            project_id=test_project_id,
            name="Manual Enrollment Track",
            slug="manual-enrollment-track",
            status=TrackStatus.ACTIVE,
            auto_enroll_enabled=False
        )
        
        auto_created = await repository.create(auto_track)
        manual_created = await repository.create(manual_track)
        
        try:
            # Test get active tracks with auto-enrollment
            auto_tracks = await repository.get_active_tracks_with_auto_enroll(test_project_id)
            
            auto_track_names = [t.name for t in auto_tracks]
            assert "Auto Enrollment Track" in auto_track_names
            assert "Manual Enrollment Track" not in auto_track_names
            
        finally:
            await repository.delete(auto_created.id)
            await repository.delete(manual_created.id)
    
    @pytest.mark.asyncio
    async def test_track_ordering(self, repository, test_project_id):
        """Test track sequence ordering"""
        # Create tracks with specific orders
        tracks_data = [
            {"name": "Third Track", "slug": "third-track", "sequence_order": 3},
            {"name": "First Track", "slug": "first-track", "sequence_order": 1},
            {"name": "Second Track", "slug": "second-track", "sequence_order": 2}
        ]
        
        created_tracks = []
        for track_data in tracks_data:
            track = Track(
                project_id=test_project_id,
                name=track_data["name"],
                slug=track_data["slug"],
                sequence_order=track_data["sequence_order"]
            )
            created_track = await repository.create(track)
            created_tracks.append(created_track)
        
        try:
            # Test ordered retrieval
            ordered_tracks = await repository.get_ordered_tracks_by_project(test_project_id)
            
            # Should be ordered by sequence_order
            track_names = [t.name for t in ordered_tracks]
            assert track_names.index("First Track") < track_names.index("Second Track")
            assert track_names.index("Second Track") < track_names.index("Third Track")
            
        finally:
            for track in created_tracks:
                await repository.delete(track.id)
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository, test_project_id):
        """Test concurrent track operations"""
        async def create_track(name_suffix):
            track = Track(
                project_id=test_project_id,
                name=f"Concurrent Track {name_suffix}",
                slug=f"concurrent-track-{name_suffix}",
                target_audience=["Concurrent Tester"]
            )
            return await repository.create(track)
        
        # Create tracks concurrently
        tasks = [create_track(i) for i in range(5)]
        created_tracks = await asyncio.gather(*tasks)
        
        try:
            # Verify all tracks were created
            assert len(created_tracks) == 5
            assert all(track.id is not None for track in created_tracks)
            
            # Verify concurrent retrieval
            tasks = [repository.get_by_id(track.id) for track in created_tracks]
            retrieved_tracks = await asyncio.gather(*tasks)
            
            assert len(retrieved_tracks) == 5
            assert all(track is not None for track in retrieved_tracks)
            
        finally:
            # Cleanup concurrently
            cleanup_tasks = [repository.delete(track.id) for track in created_tracks]
            await asyncio.gather(*cleanup_tasks)


if __name__ == "__main__":
    pytest.main([__file__])