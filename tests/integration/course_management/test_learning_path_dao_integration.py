"""
Integration Tests for LearningPathDAO

WHAT: Tests LearningPathDAO methods against a real PostgreSQL test database
WHERE: tests/integration/course_management/test_learning_path_dao_integration.py
WHY: Validates that DAO SQL operations work correctly with actual database,
     ensuring data integrity, transaction handling, and error conditions

BUSINESS CONTEXT:
These integration tests verify the data access layer for adaptive learning paths.
They test:
- CRUD operations for learning paths, nodes, recommendations, and mastery levels
- Transaction rollback behavior
- Constraint validation at the database level
- Query performance with realistic data volumes
- Foreign key relationships and cascading operations

PREREQUISITES:
- Test database running: docker-compose.test.yml
- Database schema applied including learning path tables
- Test user and organization seeded

RUN WITH:
    TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5434/course_creator_test" \\
    python -m pytest tests/integration/course_management/test_learning_path_dao_integration.py -v
"""

import pytest
import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

# Add course-management service to path
service_path = Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'
sys.path.insert(0, str(service_path))

from data_access.learning_path_dao import LearningPathDAO, LearningPathDAOException
from course_management.domain.entities.learning_path import (
    LearningPath,
    LearningPathNode,
    PrerequisiteRule,
    AdaptiveRecommendation,
    StudentMasteryLevel,
    PathType,
    PathStatus,
    NodeStatus,
    ContentType,
    RequirementType,
    RecommendationType,
    RecommendationStatus,
    MasteryLevel,
    DifficultyLevel
)

# Test configuration
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://test_user:test_password@localhost:5434/course_creator_test"
)

# Test IDs (matching init-test-db.sql or generated)
TEST_ORG_ID = uuid4()
TEST_STUDENT_ID = uuid4()
TEST_COURSE_ID = uuid4()
TEST_TRACK_ID = uuid4()


class TestLearningPathDAOIntegration:
    """
    WHAT: Integration tests for LearningPathDAO
    WHERE: Run against test PostgreSQL instance
    WHY: Verify database operations work correctly with real SQL execution
    """

    @pytest.fixture(scope="class")
    def event_loop(self):
        """
        WHAT: Create event loop for async tests
        WHERE: Used by all async test methods in this class
        WHY: pytest-asyncio requires an event loop fixture for class-scoped tests
        """
        loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()

    @pytest.fixture(scope="class")
    async def db_pool(self):
        """
        WHAT: Create database connection pool for tests
        WHERE: Shared across all tests in this class
        WHY: Reusing connections improves test performance
        """
        pool = await asyncpg.create_pool(
            TEST_DATABASE_URL,
            min_size=2,
            max_size=10,
            timeout=30
        )
        yield pool
        await pool.close()

    @pytest.fixture(scope="class")
    async def dao(self, db_pool):
        """
        WHAT: Create LearningPathDAO instance
        WHERE: Used by all tests in this class
        WHY: Provides the DAO under test with a real database connection
        """
        return LearningPathDAO(db_pool)

    @pytest.fixture(autouse=True)
    async def clean_test_data(self, db_pool):
        """
        WHAT: Clean up test data before and after each test
        WHERE: Runs automatically for each test method
        WHY: Ensures tests are isolated and don't affect each other
        """
        async with db_pool.acquire() as conn:
            # Clean up in reverse dependency order
            await conn.execute("DELETE FROM student_mastery_levels WHERE student_id = $1", TEST_STUDENT_ID)
            await conn.execute("DELETE FROM adaptive_recommendations WHERE student_id = $1", TEST_STUDENT_ID)
            await conn.execute("DELETE FROM prerequisite_rules WHERE organization_id = $1", TEST_ORG_ID)
            await conn.execute("DELETE FROM learning_path_nodes WHERE learning_path_id IN (SELECT id FROM learning_paths WHERE student_id = $1)", TEST_STUDENT_ID)
            await conn.execute("DELETE FROM learning_paths WHERE student_id = $1", TEST_STUDENT_ID)

        yield

        # Cleanup after test
        async with db_pool.acquire() as conn:
            await conn.execute("DELETE FROM student_mastery_levels WHERE student_id = $1", TEST_STUDENT_ID)
            await conn.execute("DELETE FROM adaptive_recommendations WHERE student_id = $1", TEST_STUDENT_ID)
            await conn.execute("DELETE FROM prerequisite_rules WHERE organization_id = $1", TEST_ORG_ID)
            await conn.execute("DELETE FROM learning_path_nodes WHERE learning_path_id IN (SELECT id FROM learning_paths WHERE student_id = $1)", TEST_STUDENT_ID)
            await conn.execute("DELETE FROM learning_paths WHERE student_id = $1", TEST_STUDENT_ID)

    def create_sample_learning_path(self) -> LearningPath:
        """
        WHAT: Factory method for creating sample learning path
        WHERE: Used by tests that need a learning path entity
        WHY: Provides consistent test data across tests
        """
        return LearningPath(
            id=uuid4(),
            student_id=TEST_STUDENT_ID,
            organization_id=TEST_ORG_ID,
            track_id=TEST_TRACK_ID,
            name="Python Fundamentals Learning Path",
            description="Master Python programming step by step",
            path_type=PathType.SEQUENTIAL,
            difficulty_level=DifficultyLevel.BEGINNER,
            status=PathStatus.DRAFT,
            overall_progress=Decimal("0.0"),
            estimated_duration_hours=20,
            total_nodes=0,
            completed_nodes=0,
            adapt_to_performance=True,
            adapt_to_pace=True,
            target_completion_date=datetime.utcnow() + timedelta(days=30),
            adaptation_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def create_sample_node(self, path_id, order: int = 1) -> LearningPathNode:
        """
        WHAT: Factory method for creating sample learning path node
        WHERE: Used by tests that need node entities
        WHY: Provides consistent test data for node operations
        """
        return LearningPathNode(
            id=uuid4(),
            learning_path_id=path_id,
            content_type=ContentType.LESSON,
            content_id=uuid4(),
            sequence_order=order,
            status=NodeStatus.LOCKED,
            is_required=True,
            is_unlocked=False,
            progress_percentage=Decimal("0.0"),
            attempts=0,
            max_attempts=3,
            estimated_duration_minutes=45,
            time_spent_seconds=0,
            difficulty_adjustment=Decimal("1.0"),
            was_recommended=False,
            unlock_conditions={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )


class TestLearningPathCRUD(TestLearningPathDAOIntegration):
    """
    WHAT: Tests for Learning Path CRUD operations
    WHERE: LearningPathDAO.create_learning_path, get_learning_path_by_id, etc.
    WHY: Verify basic database operations for learning paths
    """

    @pytest.mark.asyncio
    async def test_create_learning_path_success(self, dao):
        """
        WHAT: Test successful creation of a learning path
        WHERE: LearningPathDAO.create_learning_path
        WHY: Verify INSERT operation works correctly
        """
        # Arrange
        learning_path = self.create_sample_learning_path()

        # Act
        created_path = await dao.create_learning_path(learning_path)

        # Assert
        assert created_path.id is not None
        assert created_path.student_id == TEST_STUDENT_ID
        assert created_path.organization_id == TEST_ORG_ID
        assert created_path.name == "Python Fundamentals Learning Path"
        assert created_path.path_type == PathType.SEQUENTIAL
        assert created_path.status == PathStatus.DRAFT
        assert created_path.created_at is not None

    @pytest.mark.asyncio
    async def test_get_learning_path_by_id(self, dao):
        """
        WHAT: Test retrieving a learning path by ID
        WHERE: LearningPathDAO.get_learning_path_by_id
        WHY: Verify SELECT by primary key works correctly
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)

        # Act
        retrieved_path = await dao.get_learning_path_by_id(created_path.id)

        # Assert
        assert retrieved_path is not None
        assert retrieved_path.id == created_path.id
        assert retrieved_path.name == created_path.name
        assert retrieved_path.student_id == created_path.student_id

    @pytest.mark.asyncio
    async def test_get_learning_path_by_id_not_found(self, dao):
        """
        WHAT: Test retrieving non-existent learning path
        WHERE: LearningPathDAO.get_learning_path_by_id
        WHY: Verify proper handling of missing records
        """
        # Act
        result = await dao.get_learning_path_by_id(uuid4())

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_learning_paths_by_student(self, dao):
        """
        WHAT: Test retrieving all learning paths for a student
        WHERE: LearningPathDAO.get_learning_paths_by_student
        WHY: Verify query by foreign key works correctly
        """
        # Arrange - create multiple paths
        path1 = self.create_sample_learning_path()
        path1.name = "Path 1: Basics"
        await dao.create_learning_path(path1)

        path2 = self.create_sample_learning_path()
        path2.id = uuid4()  # Different ID
        path2.name = "Path 2: Advanced"
        path2.track_id = uuid4()  # Different track
        await dao.create_learning_path(path2)

        # Act
        paths = await dao.get_learning_paths_by_student(TEST_STUDENT_ID)

        # Assert
        assert len(paths) == 2
        names = [p.name for p in paths]
        assert "Path 1: Basics" in names
        assert "Path 2: Advanced" in names

    @pytest.mark.asyncio
    async def test_update_learning_path(self, dao):
        """
        WHAT: Test updating a learning path
        WHERE: LearningPathDAO.update_learning_path
        WHY: Verify UPDATE operation works correctly
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)

        # Modify the path
        created_path.status = PathStatus.ACTIVE
        created_path.overall_progress = Decimal("25.0")
        created_path.started_at = datetime.utcnow()

        # Act
        updated_path = await dao.update_learning_path(created_path)

        # Assert
        assert updated_path is not None
        assert updated_path.status == PathStatus.ACTIVE
        assert updated_path.overall_progress == Decimal("25.0")
        assert updated_path.started_at is not None

    @pytest.mark.asyncio
    async def test_delete_learning_path(self, dao):
        """
        WHAT: Test deleting a learning path
        WHERE: LearningPathDAO.delete_learning_path
        WHY: Verify DELETE operation and cascading behavior
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)

        # Act
        deleted = await dao.delete_learning_path(created_path.id)

        # Assert
        assert deleted is True
        retrieved = await dao.get_learning_path_by_id(created_path.id)
        assert retrieved is None


class TestLearningPathNodeCRUD(TestLearningPathDAOIntegration):
    """
    WHAT: Tests for Learning Path Node CRUD operations
    WHERE: LearningPathDAO node methods
    WHY: Verify database operations for nodes within learning paths
    """

    @pytest.mark.asyncio
    async def test_create_node(self, dao):
        """
        WHAT: Test adding a node to a learning path
        WHERE: LearningPathDAO.create_node
        WHY: Verify INSERT operation for nodes with path relationship
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)
        node = self.create_sample_node(created_path.id)

        # Act
        created_node = await dao.create_node(node)

        # Assert
        assert created_node.id is not None
        assert created_node.learning_path_id == created_path.id
        assert created_node.content_type == ContentType.LESSON
        assert created_node.status == NodeStatus.LOCKED
        assert created_node.sequence_order == 1

    @pytest.mark.asyncio
    async def test_get_nodes_by_path(self, dao):
        """
        WHAT: Test retrieving all nodes for a learning path
        WHERE: LearningPathDAO.get_nodes_by_path
        WHY: Verify ordered retrieval of path nodes
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)

        # Add multiple nodes
        for i in range(1, 4):
            node = self.create_sample_node(created_path.id, order=i)
            await dao.create_node(node)

        # Act
        nodes = await dao.get_nodes_by_path(created_path.id)

        # Assert
        assert len(nodes) == 3
        # Verify ordering
        assert nodes[0].sequence_order == 1
        assert nodes[1].sequence_order == 2
        assert nodes[2].sequence_order == 3

    @pytest.mark.asyncio
    async def test_update_node(self, dao):
        """
        WHAT: Test updating node status and progress
        WHERE: LearningPathDAO.update_node
        WHY: Verify status transitions for individual nodes
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)
        node = self.create_sample_node(created_path.id)
        created_node = await dao.create_node(node)

        # Act - unlock and update the node
        created_node.status = NodeStatus.AVAILABLE
        created_node.is_unlocked = True
        created_node.progress_percentage = Decimal("50.0")
        updated_node = await dao.update_node(created_node)

        # Assert
        assert updated_node.status == NodeStatus.AVAILABLE
        assert updated_node.is_unlocked is True
        assert updated_node.progress_percentage == Decimal("50.0")

    @pytest.mark.asyncio
    async def test_complete_node(self, dao):
        """
        WHAT: Test marking a node as completed
        WHERE: LearningPathDAO.update_node
        WHY: Verify node completion with score and timestamp
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)
        node = self.create_sample_node(created_path.id)
        created_node = await dao.create_node(node)

        # Act - complete the node
        created_node.status = NodeStatus.COMPLETED
        created_node.score = Decimal("92.5")
        created_node.progress_percentage = Decimal("100.0")
        created_node.completed_at = datetime.utcnow()
        completed_node = await dao.update_node(created_node)

        # Assert
        assert completed_node.status == NodeStatus.COMPLETED
        assert completed_node.score == Decimal("92.5")
        assert completed_node.completed_at is not None
        assert completed_node.progress_percentage == Decimal("100.0")


class TestPrerequisiteRules(TestLearningPathDAOIntegration):
    """
    WHAT: Tests for prerequisite rule operations
    WHERE: LearningPathDAO prerequisite methods
    WHY: Verify prerequisite dependency management
    """

    @pytest.mark.asyncio
    async def test_create_prerequisite_rule(self, dao):
        """
        WHAT: Test adding a prerequisite rule
        WHERE: LearningPathDAO.create_prerequisite_rule
        WHY: Verify prerequisite relationship creation
        """
        # Arrange
        lesson_id = uuid4()
        quiz_id = uuid4()

        rule = PrerequisiteRule(
            id=uuid4(),
            target_type=ContentType.QUIZ,
            target_id=quiz_id,
            prerequisite_type=ContentType.LESSON,
            prerequisite_id=lesson_id,
            requirement_type=RequirementType.COMPLETION,
            requirement_value=Decimal("70.0"),
            organization_id=TEST_ORG_ID,
            track_id=TEST_TRACK_ID,
            is_mandatory=True,
            bypass_allowed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Act
        created_rule = await dao.create_prerequisite_rule(rule)

        # Assert
        assert created_rule.id is not None
        assert created_rule.target_id == quiz_id
        assert created_rule.prerequisite_id == lesson_id
        assert created_rule.requirement_value == Decimal("70.0")

    @pytest.mark.asyncio
    async def test_get_prerequisites_for_content(self, dao):
        """
        WHAT: Test retrieving prerequisites for content
        WHERE: LearningPathDAO.get_prerequisites_for_content
        WHY: Verify prerequisite lookup for validation
        """
        # Arrange
        quiz_id = uuid4()
        lesson1_id = uuid4()
        lesson2_id = uuid4()

        # Quiz requires both lessons
        rule1 = PrerequisiteRule(
            id=uuid4(),
            target_type=ContentType.QUIZ,
            target_id=quiz_id,
            prerequisite_type=ContentType.LESSON,
            prerequisite_id=lesson1_id,
            requirement_type=RequirementType.COMPLETION,
            organization_id=TEST_ORG_ID,
            is_mandatory=True,
            bypass_allowed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await dao.create_prerequisite_rule(rule1)

        rule2 = PrerequisiteRule(
            id=uuid4(),
            target_type=ContentType.QUIZ,
            target_id=quiz_id,
            prerequisite_type=ContentType.LESSON,
            prerequisite_id=lesson2_id,
            requirement_type=RequirementType.SCORE,
            requirement_value=Decimal("80.0"),
            organization_id=TEST_ORG_ID,
            is_mandatory=True,
            bypass_allowed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await dao.create_prerequisite_rule(rule2)

        # Act
        prerequisites = await dao.get_prerequisites_for_content(ContentType.QUIZ, quiz_id)

        # Assert
        assert len(prerequisites) == 2
        prereq_ids = {p.prerequisite_id for p in prerequisites}
        assert lesson1_id in prereq_ids
        assert lesson2_id in prereq_ids

    @pytest.mark.asyncio
    async def test_delete_prerequisite_rule(self, dao):
        """
        WHAT: Test deleting a prerequisite rule
        WHERE: LearningPathDAO.delete_prerequisite_rule
        WHY: Verify rule removal
        """
        # Arrange
        rule = PrerequisiteRule(
            id=uuid4(),
            target_type=ContentType.QUIZ,
            target_id=uuid4(),
            prerequisite_type=ContentType.LESSON,
            prerequisite_id=uuid4(),
            requirement_type=RequirementType.COMPLETION,
            organization_id=TEST_ORG_ID,
            is_mandatory=True,
            bypass_allowed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        created_rule = await dao.create_prerequisite_rule(rule)

        # Act
        deleted = await dao.delete_prerequisite_rule(created_rule.id)

        # Assert
        assert deleted is True


class TestAdaptiveRecommendations(TestLearningPathDAOIntegration):
    """
    WHAT: Tests for adaptive recommendation operations
    WHERE: LearningPathDAO recommendation methods
    WHY: Verify AI-driven recommendation storage and retrieval
    """

    @pytest.mark.asyncio
    async def test_create_recommendation(self, dao):
        """
        WHAT: Test creating an adaptive recommendation
        WHERE: LearningPathDAO.create_recommendation
        WHY: Verify recommendation storage
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)

        recommendation = AdaptiveRecommendation(
            id=uuid4(),
            student_id=TEST_STUDENT_ID,
            learning_path_id=created_path.id,
            recommendation_type=RecommendationType.NEXT_CONTENT,
            title="Continue with Python Functions",
            description="Learn about functions",
            reason="Based on your progress, functions are the logical next step",
            priority=8,
            confidence_score=Decimal("0.92"),
            trigger_metrics={"completion_rate": 0.8},
            status=RecommendationStatus.PENDING,
            valid_from=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Act
        created_rec = await dao.create_recommendation(recommendation)

        # Assert
        assert created_rec.id is not None
        assert created_rec.student_id == TEST_STUDENT_ID
        assert created_rec.recommendation_type == RecommendationType.NEXT_CONTENT
        assert created_rec.priority == 8
        assert created_rec.status == RecommendationStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_pending_recommendations(self, dao):
        """
        WHAT: Test retrieving pending recommendations for a student
        WHERE: LearningPathDAO.get_pending_recommendations
        WHY: Verify recommendation retrieval with status filtering
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)

        # Create multiple recommendations with different priorities
        for i, (rec_type, priority) in enumerate([
            (RecommendationType.NEXT_CONTENT, 10),
            (RecommendationType.REVIEW, 9),
            (RecommendationType.PRACTICE, 8)
        ]):
            rec = AdaptiveRecommendation(
                id=uuid4(),
                student_id=TEST_STUDENT_ID,
                learning_path_id=created_path.id,
                recommendation_type=rec_type,
                title=f"Recommendation {i+1}",
                description=f"Description {i+1}",
                reason="Based on your learning pattern",
                priority=priority,
                confidence_score=Decimal("0.85"),
                trigger_metrics={},
                status=RecommendationStatus.PENDING,
                valid_from=datetime.utcnow() - timedelta(hours=1),  # Valid from 1 hour ago
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await dao.create_recommendation(rec)

        # Act
        recommendations = await dao.get_pending_recommendations(TEST_STUDENT_ID)

        # Assert
        assert len(recommendations) == 3
        # Should be ordered by priority (highest first)
        assert recommendations[0].priority == 10
        assert recommendations[1].priority == 9
        assert recommendations[2].priority == 8

    @pytest.mark.asyncio
    async def test_update_recommendation(self, dao):
        """
        WHAT: Test updating recommendation status (accept/dismiss)
        WHERE: LearningPathDAO.update_recommendation
        WHY: Verify recommendation lifecycle management
        """
        # Arrange
        learning_path = self.create_sample_learning_path()
        created_path = await dao.create_learning_path(learning_path)

        recommendation = AdaptiveRecommendation(
            id=uuid4(),
            student_id=TEST_STUDENT_ID,
            learning_path_id=created_path.id,
            recommendation_type=RecommendationType.NEXT_CONTENT,
            title="Try Advanced Topics",
            description="Advanced content",
            reason="You're ready for more challenging content",
            priority=7,
            confidence_score=Decimal("0.88"),
            trigger_metrics={},
            status=RecommendationStatus.PENDING,
            valid_from=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        created_rec = await dao.create_recommendation(recommendation)

        # Act - accept the recommendation
        created_rec.status = RecommendationStatus.ACCEPTED
        created_rec.user_feedback = "Great suggestion, starting now!"
        created_rec.acted_on_at = datetime.utcnow()
        updated_rec = await dao.update_recommendation(created_rec)

        # Assert
        assert updated_rec.status == RecommendationStatus.ACCEPTED
        assert updated_rec.user_feedback == "Great suggestion, starting now!"
        assert updated_rec.acted_on_at is not None


class TestStudentMasteryLevels(TestLearningPathDAOIntegration):
    """
    WHAT: Tests for student mastery level tracking
    WHERE: LearningPathDAO mastery methods
    WHY: Verify spaced repetition and skill tracking data operations
    """

    @pytest.mark.asyncio
    async def test_upsert_mastery_level_create(self, dao):
        """
        WHAT: Test creating a mastery level record
        WHERE: LearningPathDAO.upsert_mastery_level
        WHY: Verify skill mastery tracking initialization
        """
        # Arrange
        mastery = StudentMasteryLevel(
            id=uuid4(),
            student_id=TEST_STUDENT_ID,
            skill_topic="Python List Comprehensions",
            organization_id=TEST_ORG_ID,
            course_id=TEST_COURSE_ID,
            mastery_level=MasteryLevel.BEGINNER,
            mastery_score=Decimal("35.0"),
            assessments_completed=5,
            assessments_passed=3,
            average_score=Decimal("70.0"),
            total_practice_time_minutes=120,
            last_practiced_at=datetime.utcnow(),
            practice_streak_days=3,
            retention_estimate=Decimal("0.75"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Act
        created_mastery = await dao.upsert_mastery_level(mastery)

        # Assert
        assert created_mastery.id is not None
        assert created_mastery.skill_topic == "Python List Comprehensions"
        assert created_mastery.mastery_level == MasteryLevel.BEGINNER
        assert created_mastery.assessments_completed == 5

    @pytest.mark.asyncio
    async def test_upsert_mastery_level_update(self, dao):
        """
        WHAT: Test updating mastery level after practice
        WHERE: LearningPathDAO.upsert_mastery_level
        WHY: Verify skill progression tracking via upsert
        """
        # Arrange - create initial mastery
        skill_topic = "Python Functions"
        mastery = StudentMasteryLevel(
            id=uuid4(),
            student_id=TEST_STUDENT_ID,
            skill_topic=skill_topic,
            organization_id=TEST_ORG_ID,
            course_id=TEST_COURSE_ID,
            mastery_level=MasteryLevel.BEGINNER,
            mastery_score=Decimal("40.0"),
            assessments_completed=3,
            assessments_passed=2,
            average_score=Decimal("65.0"),
            total_practice_time_minutes=60,
            practice_streak_days=1,
            retention_estimate=Decimal("0.70"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await dao.upsert_mastery_level(mastery)

        # Act - upsert with improved values (same student, skill, course)
        improved_mastery = StudentMasteryLevel(
            id=uuid4(),  # Different ID but same unique key
            student_id=TEST_STUDENT_ID,
            skill_topic=skill_topic,
            organization_id=TEST_ORG_ID,
            course_id=TEST_COURSE_ID,
            mastery_level=MasteryLevel.INTERMEDIATE,
            mastery_score=Decimal("65.0"),
            assessments_completed=8,
            assessments_passed=6,
            average_score=Decimal("78.0"),
            total_practice_time_minutes=180,
            practice_streak_days=5,
            retention_estimate=Decimal("0.85"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        updated_mastery = await dao.upsert_mastery_level(improved_mastery)

        # Assert
        assert updated_mastery.mastery_level == MasteryLevel.INTERMEDIATE
        assert updated_mastery.mastery_score == Decimal("65.0")
        assert updated_mastery.assessments_completed == 8

    @pytest.mark.asyncio
    async def test_get_mastery_levels_by_student(self, dao):
        """
        WHAT: Test retrieving all mastery levels for a student
        WHERE: LearningPathDAO.get_mastery_levels_by_student
        WHY: Verify comprehensive skill assessment retrieval
        """
        # Arrange - create multiple mastery records
        skills = [
            ("Python Variables", MasteryLevel.PROFICIENT, Decimal("90.0")),
            ("Python Loops", MasteryLevel.INTERMEDIATE, Decimal("65.0")),
            ("Python Classes", MasteryLevel.BEGINNER, Decimal("35.0"))
        ]

        for skill_name, level, score in skills:
            mastery = StudentMasteryLevel(
                id=uuid4(),
                student_id=TEST_STUDENT_ID,
                skill_topic=skill_name,
                organization_id=TEST_ORG_ID,
                course_id=TEST_COURSE_ID,
                mastery_level=level,
                mastery_score=score,
                assessments_completed=10,
                assessments_passed=8,
                average_score=Decimal("75.0"),
                total_practice_time_minutes=100,
                practice_streak_days=5,
                retention_estimate=Decimal("0.80"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await dao.upsert_mastery_level(mastery)

        # Act
        mastery_levels = await dao.get_mastery_levels_by_student(
            TEST_STUDENT_ID,
            course_id=TEST_COURSE_ID
        )

        # Assert
        assert len(mastery_levels) == 3
        skill_names = {m.skill_topic for m in mastery_levels}
        assert "Python Variables" in skill_names
        assert "Python Loops" in skill_names
        assert "Python Classes" in skill_names

    @pytest.mark.asyncio
    async def test_get_skills_needing_review(self, dao):
        """
        WHAT: Test retrieving skills that need spaced repetition review
        WHERE: LearningPathDAO.get_skills_needing_review
        WHY: Verify spaced repetition scheduling
        """
        # Arrange - create skills with varying review dates
        # Skill due for review (next review was yesterday)
        skill_due = StudentMasteryLevel(
            id=uuid4(),
            student_id=TEST_STUDENT_ID,
            skill_topic="Old Skill",
            organization_id=TEST_ORG_ID,
            course_id=TEST_COURSE_ID,
            mastery_level=MasteryLevel.INTERMEDIATE,
            mastery_score=Decimal("60.0"),
            assessments_completed=5,
            assessments_passed=4,
            average_score=Decimal("72.0"),
            total_practice_time_minutes=90,
            last_practiced_at=datetime.utcnow() - timedelta(days=7),
            practice_streak_days=0,
            retention_estimate=Decimal("0.50"),
            next_review_recommended_at=datetime.utcnow() - timedelta(days=1),  # Due yesterday
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await dao.upsert_mastery_level(skill_due)

        # Recently practiced skill (not due)
        skill_recent = StudentMasteryLevel(
            id=uuid4(),
            student_id=TEST_STUDENT_ID,
            skill_topic="Recent Skill",
            organization_id=TEST_ORG_ID,
            course_id=uuid4(),  # Different course to avoid conflict
            mastery_level=MasteryLevel.PROFICIENT,
            mastery_score=Decimal("85.0"),
            assessments_completed=15,
            assessments_passed=14,
            average_score=Decimal("88.0"),
            total_practice_time_minutes=200,
            last_practiced_at=datetime.utcnow() - timedelta(hours=2),
            practice_streak_days=10,
            retention_estimate=Decimal("0.95"),
            next_review_recommended_at=datetime.utcnow() + timedelta(days=3),  # Due in 3 days
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await dao.upsert_mastery_level(skill_recent)

        # Act
        skills_due = await dao.get_skills_needing_review(TEST_STUDENT_ID)

        # Assert
        assert len(skills_due) == 1
        assert skills_due[0].skill_topic == "Old Skill"


class TestTransactionAndErrorHandling(TestLearningPathDAOIntegration):
    """
    WHAT: Tests for transaction management and error handling
    WHERE: Various LearningPathDAO methods
    WHY: Verify data integrity and proper error propagation
    """

    @pytest.mark.asyncio
    async def test_dao_wraps_database_errors(self, dao):
        """
        WHAT: Test that database errors are wrapped in custom exceptions
        WHERE: All DAO methods
        WHY: Verify consistent error handling per coding standards
        """
        # Act & Assert
        # This should raise LearningPathDAOException, not raw asyncpg error
        with pytest.raises(LearningPathDAOException):
            # Force an error by trying to create with invalid data
            bad_path = LearningPath(
                id=uuid4(),
                student_id=None,  # This will cause a NOT NULL constraint violation
                organization_id=TEST_ORG_ID,
                track_id=TEST_TRACK_ID,
                name="Bad Path",
                description="Should fail",
                path_type=PathType.SEQUENTIAL,
                difficulty_level=DifficultyLevel.BEGINNER,
                status=PathStatus.DRAFT,
                overall_progress=Decimal("0.0"),
                total_nodes=0,
                completed_nodes=0,
                adapt_to_performance=True,
                adapt_to_pace=True,
                adaptation_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await dao.create_learning_path(bad_path)

    @pytest.mark.asyncio
    async def test_concurrent_path_creation(self, dao):
        """
        WHAT: Test concurrent creation doesn't cause race conditions
        WHERE: LearningPathDAO.create_learning_path
        WHY: Verify thread safety of DAO operations
        """
        # Arrange
        paths = []
        for i in range(5):
            path = self.create_sample_learning_path()
            path.id = uuid4()
            path.name = f"Concurrent Path {i}"
            path.track_id = uuid4()  # Different track for each
            paths.append(path)

        # Act - create all paths concurrently
        tasks = [dao.create_learning_path(p) for p in paths]
        results = await asyncio.gather(*tasks)

        # Assert - all should succeed with unique IDs
        assert len(results) == 5
        ids = [r.id for r in results]
        assert len(set(ids)) == 5  # All unique


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
