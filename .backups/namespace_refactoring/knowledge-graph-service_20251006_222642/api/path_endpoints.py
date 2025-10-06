"""
Path Finding API Endpoints

BUSINESS REQUIREMENT:
Expose learning path generation and prerequisite checking
through REST API endpoints.

BUSINESS VALUE:
- Enables students to discover optimal learning paths
- Provides prerequisite validation before enrollment
- Suggests next courses to take
- Powers skill-based learning recommendations

TECHNICAL IMPLEMENTATION:
- FastAPI REST endpoints
- Integration with path finding algorithms
- Pydantic models for validation
- Clear error handling

WHY:
Frontend components need HTTP API to request learning paths
and check prerequisites in real-time.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from application.services.path_finding_service import (
    PathFindingService,
    PathNotFoundError,
    InvalidOptimizationError
)
from application.services.prerequisite_service import PrerequisiteService
from infrastructure.database import get_database_pool
from data_access.graph_dao import GraphDAO


router = APIRouter(prefix="/paths", tags=["Learning Paths"])


# ========================================
# REQUEST/RESPONSE MODELS
# ========================================

class LearningPathResponse(BaseModel):
    """Response model for learning path"""
    path: List[str] = Field(..., description="List of course UUIDs in order")
    course_details: List[Dict[str, Any]] = Field(..., description="Detailed course information")
    total_courses: int
    total_duration: int = Field(..., description="Total duration in hours")
    difficulty_progression: List[str]
    start_difficulty: Optional[str]
    end_difficulty: Optional[str]
    has_difficulty_jump: bool
    optimization_type: str


class PrerequisiteCheckResponse(BaseModel):
    """Response model for prerequisite check"""
    ready: bool = Field(..., description="Can student enroll?")
    course_id: str
    course_name: str
    prerequisites: List[Dict[str, Any]]
    missing_prerequisites: List[Dict[str, Any]]
    recommended_courses: List[Dict[str, Any]]
    total_prerequisites: int
    completed_prerequisites: int


class RecommendedCourseResponse(BaseModel):
    """Response model for recommended courses"""
    course_id: str
    course_name: str
    reason: str
    relationship: str
    weight: float
    priority: int


class SkillProgressionResponse(BaseModel):
    """Response model for skill progression path"""
    path: List[Dict[str, Any]]
    skills_covered: List[str]
    target_skills: List[str]
    coverage: float = Field(..., ge=0.0, le=1.0, description="Skill coverage ratio")


class CourseSequenceValidationResponse(BaseModel):
    """Response model for sequence validation"""
    valid: bool
    issues: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    total_courses: int


# ========================================
# DEPENDENCY INJECTION
# ========================================

async def get_path_finding_service() -> PathFindingService:
    """Dependency injection for PathFindingService"""
    pool = await get_database_pool()
    dao = GraphDAO(pool)
    return PathFindingService(dao)


async def get_prerequisite_service() -> PrerequisiteService:
    """Dependency injection for PrerequisiteService"""
    pool = await get_database_pool()
    dao = GraphDAO(pool)
    return PrerequisiteService(dao)


# ========================================
# LEARNING PATH ENDPOINTS
# ========================================

@router.get("/learning-path", response_model=LearningPathResponse)
async def find_learning_path(
    start: str = Query(..., description="Starting course UUID"),
    end: str = Query(..., description="Target course UUID"),
    optimization: str = Query("shortest", regex="^(shortest|easiest|fastest)$"),
    student: Optional[str] = Query(None, description="Student UUID for personalization"),
    max_depth: int = Query(10, ge=1, le=20, description="Maximum path length"),
    service: PathFindingService = Depends(get_path_finding_service)
):
    """
    Find optimal learning path between two courses

    BUSINESS USE CASE:
    Student wants to learn Advanced Python but is currently at Beginner level.
    Find the optimal sequence of courses to get there.

    OPTIMIZATION TYPES:
    - shortest: Fewest courses (Dijkstra)
    - easiest: Minimal difficulty jumps (A* with difficulty heuristic)
    - fastest: Minimal total duration (duration-weighted Dijkstra)
    """
    try:
        path_result = await service.find_learning_path(
            start_course_id=UUID(start),
            end_course_id=UUID(end),
            optimization=optimization,
            student_id=UUID(student) if student else None,
            max_depth=max_depth
        )

        return LearningPathResponse(
            path=path_result['path'],
            course_details=path_result['course_details'],
            total_courses=path_result['total_courses'],
            total_duration=path_result['total_duration'],
            difficulty_progression=path_result['difficulty_progression'],
            start_difficulty=path_result.get('start_difficulty'),
            end_difficulty=path_result.get('end_difficulty'),
            has_difficulty_jump=path_result.get('has_difficulty_jump', False),
            optimization_type=optimization
        )

    except PathNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidOptimizationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/alternative-paths", response_model=List[List[str]])
async def find_alternative_paths(
    start: str = Query(..., description="Starting course UUID"),
    end: str = Query(..., description="Target course UUID"),
    max_paths: int = Query(3, ge=1, le=10, description="Maximum number of paths"),
    max_depth: int = Query(5, ge=1, le=15, description="Maximum path length"),
    service: PathFindingService = Depends(get_path_finding_service)
):
    """
    Find multiple alternative learning paths

    BUSINESS USE CASE:
    Show students different routes to the same learning destination
    """
    try:
        paths = await service.find_alternative_paths(
            start_course_id=UUID(start),
            end_course_id=UUID(end),
            max_paths=max_paths,
            max_depth=max_depth
        )

        # Convert UUIDs to strings
        return [
            [str(course_id) for course_id in path]
            for path in paths
        ]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/next-courses", response_model=List[RecommendedCourseResponse])
async def get_recommended_next_courses(
    course_id: str = Query(..., description="Current course UUID"),
    student: Optional[str] = Query(None, description="Student UUID"),
    limit: int = Query(5, ge=1, le=20, description="Maximum recommendations"),
    service: PathFindingService = Depends(get_path_finding_service)
):
    """
    Get recommended next courses after completing current course

    BUSINESS USE CASE:
    Student completes "Introduction to Python", what should they take next?
    """
    recommendations = await service.get_recommended_next_courses(
        current_course_id=UUID(course_id),
        student_id=UUID(student) if student else None,
        limit=limit
    )

    return [
        RecommendedCourseResponse(
            course_id=rec['course_id'],
            course_name=rec['course_name'],
            reason=rec['reason'],
            relationship=rec['relationship'],
            weight=rec['weight'],
            priority=rec['priority']
        )
        for rec in recommendations
    ]


@router.get("/skill-progression", response_model=SkillProgressionResponse)
async def get_skill_progression_path(
    skills: List[str] = Query(..., description="Target skill names"),
    student: Optional[str] = Query(None, description="Student UUID"),
    max_courses: int = Query(10, ge=1, le=30, description="Maximum courses in path"),
    service: PathFindingService = Depends(get_path_finding_service)
):
    """
    Generate learning path to acquire specific skills

    BUSINESS USE CASE:
    Student wants to learn "Machine Learning" and "Data Visualization".
    Find the optimal course sequence to acquire these skills.
    """
    result = await service.get_skill_progression_path(
        target_skills=skills,
        student_id=UUID(student) if student else None,
        max_courses=max_courses
    )

    return SkillProgressionResponse(
        path=result['path'],
        skills_covered=result['skills_covered'],
        target_skills=result['target_skills'],
        coverage=result['coverage']
    )


# ========================================
# PREREQUISITE ENDPOINTS
# ========================================

@router.get("/prerequisites/{course_id}", response_model=PrerequisiteCheckResponse)
async def check_prerequisites(
    course_id: str,
    student: str = Query(..., description="Student UUID"),
    service: PrerequisiteService = Depends(get_prerequisite_service)
):
    """
    Check if student meets all prerequisites for a course

    BUSINESS USE CASE:
    Before allowing enrollment, verify student has completed
    all required prerequisite courses.
    """
    result = await service.check_prerequisites(
        course_id=UUID(course_id),
        student_id=UUID(student)
    )

    return PrerequisiteCheckResponse(**result)


@router.get("/prerequisites/{course_id}/chain", response_model=List[Dict[str, Any]])
async def get_prerequisite_chain(
    course_id: str,
    max_depth: int = Query(10, ge=1, le=20),
    service: PrerequisiteService = Depends(get_prerequisite_service)
):
    """
    Get complete prerequisite chain for a course

    BUSINESS USE CASE:
    Show students the full dependency tree for a course
    """
    chain = await service.get_prerequisite_chain(
        course_id=UUID(course_id),
        max_depth=max_depth
    )

    return chain


@router.post("/validate-sequence", response_model=CourseSequenceValidationResponse)
async def validate_course_sequence(
    sequence: List[str] = Query(..., description="Course UUIDs in planned order"),
    student: Optional[str] = Query(None, description="Student UUID"),
    service: PrerequisiteService = Depends(get_prerequisite_service)
):
    """
    Validate if a course sequence respects prerequisites

    BUSINESS USE CASE:
    Student plans to take courses A, B, C in that order.
    Verify this sequence is valid.
    """
    result = await service.validate_course_sequence(
        course_sequence=[UUID(cid) for cid in sequence],
        student_id=UUID(student) if student else None
    )

    return CourseSequenceValidationResponse(**result)


@router.get("/readiness", response_model=Dict[str, Any])
async def get_enrollment_readiness(
    student: str = Query(..., description="Student UUID"),
    courses: List[str] = Query(..., description="Course UUIDs to check"),
    service: PrerequisiteService = Depends(get_prerequisite_service)
):
    """
    Check student's readiness for multiple courses

    BUSINESS USE CASE:
    Student browsing course catalog. Show which courses
    they're ready for and which need prerequisites.
    """
    readiness = await service.get_enrollment_readiness(
        student_id=UUID(student),
        course_ids=[UUID(cid) for cid in courses]
    )

    return readiness


@router.get("/prerequisites/{course_id}/statistics", response_model=Dict[str, Any])
async def get_prerequisite_statistics(
    course_id: str,
    service: PrerequisiteService = Depends(get_prerequisite_service)
):
    """
    Get statistics about course prerequisites

    BUSINESS USE CASE:
    For instructors/admins to understand prerequisite complexity
    """
    stats = await service.get_prerequisite_statistics(
        course_id=UUID(course_id)
    )

    return stats


# ========================================
# VISUALIZATION ENDPOINTS
# ========================================

@router.get("/visualization/graph")
async def get_graph_visualization(
    center_course: Optional[str] = Query(None, description="Center the graph on this course"),
    depth: int = Query(2, ge=1, le=5, description="Levels of relationships to include"),
    node_types: Optional[List[str]] = Query(None, description="Filter by node types"),
    edge_types: Optional[List[str]] = Query(None, description="Filter by edge types"),
    service: PathFindingService = Depends(get_path_finding_service)
):
    """
    Get graph data for visualization (D3.js format)

    BUSINESS USE CASE:
    Render interactive knowledge graph in frontend

    RETURNS:
    {
        "nodes": [{"id": "...", "label": "...", "type": "...", ...}],
        "edges": [{"source": "...", "target": "...", "type": "...", "weight": ...}]
    }
    """
    # TODO: Implement graph visualization data generation
    # This would return nodes and edges in D3.js-compatible format

    return {
        "nodes": [],
        "edges": [],
        "message": "Visualization endpoint not yet implemented"
    }


@router.get("/visualization/concept-map/{topic_id}")
async def get_concept_map(
    topic_id: str,
    depth: int = Query(3, ge=1, le=5),
    service: PathFindingService = Depends(get_path_finding_service)
):
    """
    Get hierarchical concept map for a topic

    BUSINESS USE CASE:
    Show concept relationships in a tree/hierarchy format
    """
    # TODO: Implement concept map generation
    # This would return hierarchical concept structure

    return {
        "topic_id": topic_id,
        "concepts": [],
        "message": "Concept map endpoint not yet implemented"
    }
