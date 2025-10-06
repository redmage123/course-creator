"""
Course Generator Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for course generation operations,
centralizing all SQL queries and database interactions for AI-powered educational content creation.

Business Context:
The Course Generator service is the AI-powered content creation engine of the Course Creator Platform.
It generates comprehensive educational materials including syllabi, quizzes, slides, exercises, and
lab environments using advanced AI models. By centralizing all SQL operations in this DAO, we achieve:
- Single source of truth for all course generation database queries
- Enhanced data consistency for AI-generated educational content
- Improved performance through optimized query patterns for content creation workflows
- Better maintainability and testing capabilities for content generation operations
- Clear separation between AI generation logic and data persistence concerns

Technical Rationale:
- Follows the Single Responsibility Principle by isolating course generation data access
- Enables comprehensive transaction support for complex content creation operations
- Provides consistent error handling using shared platform exceptions
- Supports connection pooling for optimal database resource utilization
- Facilitates content schema evolution without affecting AI generation logic
- Enables easier unit testing and content validation
"""

import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import sys
sys.path.append('/app/shared')
from exceptions import (
    CourseCreatorBaseException,
    DatabaseException,
    ValidationException,
    ContentException,
    ContentNotFoundException
)


class CourseGeneratorDAO:
    """
    Data Access Object for Course Generation Operations
    
    This class centralizes all SQL queries and database operations for the course generator
    service, following the DAO pattern for clean architecture.
    
    Business Context:
    Provides comprehensive data access methods for AI-powered course generation including:
    - Syllabus creation, storage, and retrieval for course structure definition
    - Quiz generation with question banks and assessment criteria
    - Slide content creation and presentation management
    - Exercise development and hands-on learning activity creation
    - Lab environment configuration and setup automation
    - Content versioning and iterative improvement tracking
    
    Technical Implementation:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides transaction support for complex content creation operations
    - Includes comprehensive error handling and content validation
    - Supports prepared statements for performance optimization
    - Implements efficient content generation and storage patterns
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the Course Generator DAO with database connection pool.
        
        Business Context:
        The DAO requires a connection pool to efficiently manage database connections
        across the course generation service's AI-powered content creation operations.
        
        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
    
    # ================================================================
    # SYLLABUS GENERATION AND MANAGEMENT QUERIES
    # ================================================================
    
    async def create_syllabus(self, syllabus_data: Dict[str, Any]) -> str:
        """
        Create a new AI-generated syllabus with comprehensive course structure.
        
        Business Context:
        Syllabus creation is the foundation of course generation, defining the overall
        course structure, learning objectives, topics, and assessment methods that
        guide all subsequent AI content generation activities.
        
        Technical Implementation:
        - Stores comprehensive syllabus metadata and structure
        - Maintains version history for iterative improvements
        - Integrates with AI generation tracking for optimization
        - Supports rich content structure with JSON storage
        
        Args:
            syllabus_data: Dictionary containing syllabus information
                - id: Unique syllabus identifier
                - course_id: Associated course identifier
                - title: Syllabus title and course name
                - description: Course description and overview
                - objectives: Learning objectives and outcomes
                - topics: Course topics and module structure
                - structure: Detailed course structure and timeline
                - ai_metadata: AI generation metadata and parameters
                - created_by: User who initiated generation
                
        Returns:
            Created syllabus ID for tracking and reference
        """
        try:
            async with self.db_pool.acquire() as conn:
                syllabus_id = await conn.fetchval(
                    """INSERT INTO course_creator.course_outlines (
                        id, course_id, title, description, objectives, topics,
                        structure, ai_metadata, created_by, version,
                        status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) 
                    RETURNING id""",
                    syllabus_data['id'],
                    syllabus_data['course_id'],
                    syllabus_data['title'],
                    syllabus_data['description'],
                    json.dumps(syllabus_data.get('objectives', [])),
                    json.dumps(syllabus_data.get('topics', [])),
                    json.dumps(syllabus_data['structure']),
                    json.dumps(syllabus_data.get('ai_metadata', {})),
                    syllabus_data['created_by'],
                    syllabus_data.get('version', 1),
                    syllabus_data.get('status', 'generated'),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(syllabus_id)
        except Exception as e:
            raise ContentException(
                message="Failed to create AI-generated syllabus",
                error_code="SYLLABUS_CREATION_ERROR",
                details={
                    "course_id": syllabus_data.get('course_id'),
                    "title": syllabus_data.get('title')
                },
                original_exception=e
            )
    
    async def get_syllabus_by_course_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest syllabus for a specific course.
        
        Business Context:
        Syllabus retrieval enables course structure access for content generation,
        student viewing, and instructional planning activities.
        
        Args:
            course_id: Course to get syllabus for
            
        Returns:
            Complete syllabus record or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                syllabus = await conn.fetchrow(
                    """SELECT id, course_id, title, description, objectives, topics,
                              structure, ai_metadata, created_by, version, status,
                              created_at, updated_at
                       FROM course_creator.course_outlines 
                       WHERE course_id = $1 
                       ORDER BY version DESC, created_at DESC 
                       LIMIT 1""",
                    course_id
                )
                return dict(syllabus) if syllabus else None
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve course syllabus",
                error_code="SYLLABUS_RETRIEVAL_ERROR",
                details={"course_id": course_id},
                original_exception=e
            )
    
    # ================================================================
    # QUIZ GENERATION AND MANAGEMENT QUERIES
    # ================================================================
    
    async def create_quiz(self, quiz_data: Dict[str, Any]) -> str:
        """
        Create a new AI-generated quiz with questions and assessment criteria.
        
        Business Context:
        Quiz creation enables automated assessment generation, providing consistent
        evaluation methods and reducing instructor workload while maintaining
        educational quality and learning objective alignment.
        
        Args:
            quiz_data: Dictionary containing quiz information
                - id: Unique quiz identifier
                - course_id: Associated course identifier
                - title: Quiz title and topic focus
                - description: Quiz description and instructions
                - questions: List of generated questions with answers
                - difficulty_level: Quiz difficulty (beginner, intermediate, advanced)
                - time_limit: Recommended time limit in minutes
                - ai_metadata: AI generation parameters and model information
                - created_by: User who initiated generation
                
        Returns:
            Created quiz ID for tracking and reference
        """
        try:
            async with self.db_pool.acquire() as conn:
                quiz_id = await conn.fetchval(
                    """INSERT INTO course_creator.quizzes (
                        id, course_id, title, description, questions, difficulty_level,
                        time_limit, points_total, ai_metadata, created_by,
                        status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) 
                    RETURNING id""",
                    quiz_data['id'],
                    quiz_data['course_id'],
                    quiz_data['title'],
                    quiz_data.get('description'),
                    json.dumps(quiz_data['questions']),
                    quiz_data.get('difficulty_level', 'intermediate'),
                    quiz_data.get('time_limit', 30),
                    quiz_data.get('points_total', 100),
                    json.dumps(quiz_data.get('ai_metadata', {})),
                    quiz_data['created_by'],
                    quiz_data.get('status', 'generated'),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(quiz_id)
        except Exception as e:
            raise ContentException(
                message="Failed to create AI-generated quiz",
                error_code="QUIZ_CREATION_ERROR",
                details={
                    "course_id": quiz_data.get('course_id'),
                    "title": quiz_data.get('title')
                },
                original_exception=e
            )
    
    async def get_course_quizzes(self, course_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve all quizzes for a specific course with metadata.
        
        Business Context:
        Course quiz listing supports instructional planning, assessment management,
        and student progress tracking within educational content delivery.
        
        Args:
            course_id: Course to get quizzes for
            limit: Maximum number of quizzes to return
            
        Returns:
            List of quiz records with generation metadata
        """
        try:
            async with self.db_pool.acquire() as conn:
                quizzes = await conn.fetch(
                    """SELECT id, course_id, title, description, difficulty_level,
                              time_limit, points_total, status, created_at, updated_at
                       FROM course_creator.quizzes 
                       WHERE course_id = $1 
                       ORDER BY created_at DESC 
                       LIMIT $2""",
                    course_id, limit
                )
                return [dict(quiz) for quiz in quizzes]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve course quizzes",
                error_code="QUIZ_RETRIEVAL_ERROR",
                details={"course_id": course_id},
                original_exception=e
            )
    
    async def get_quiz_by_id(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete quiz details including questions and answers.
        
        Business Context:
        Detailed quiz retrieval enables quiz administration, grading, and
        content review for educational quality assurance.
        
        Args:
            quiz_id: Quiz identifier to retrieve
            
        Returns:
            Complete quiz record with questions or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                quiz = await conn.fetchrow(
                    """SELECT id, course_id, title, description, questions,
                              difficulty_level, time_limit, points_total,
                              ai_metadata, created_by, status, created_at, updated_at
                       FROM course_creator.quizzes WHERE id = $1""",
                    quiz_id
                )
                return dict(quiz) if quiz else None
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve quiz details",
                error_code="QUIZ_DETAIL_ERROR",
                details={"quiz_id": quiz_id},
                original_exception=e
            )
    
    # ================================================================
    # SLIDE GENERATION AND MANAGEMENT QUERIES
    # ================================================================
    
    async def create_slide_set(self, slide_data: Dict[str, Any]) -> str:
        """
        Create a new AI-generated slide set for course presentations.
        
        Business Context:
        Slide generation automates presentation creation, providing consistent
        visual learning materials and reducing instructor preparation time
        while maintaining pedagogical quality and engagement.
        
        Args:
            slide_data: Dictionary containing slide set information
                - id: Unique slide set identifier
                - course_id: Associated course identifier
                - title: Slide set title and topic
                - description: Slide set description and learning focus
                - slides: List of generated slide content
                - template: Visual template and styling information
                - ai_metadata: AI generation parameters and content sources
                - created_by: User who initiated generation
                
        Returns:
            Created slide set ID for tracking and reference
        """
        try:
            async with self.db_pool.acquire() as conn:
                slide_id = await conn.fetchval(
                    """INSERT INTO course_creator.slides (
                        id, course_id, title, description, content, template,
                        slide_count, ai_metadata, created_by,
                        status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) 
                    RETURNING id""",
                    slide_data['id'],
                    slide_data['course_id'],
                    slide_data['title'],
                    slide_data.get('description'),
                    json.dumps(slide_data['slides']),
                    slide_data.get('template', 'default'),
                    len(slide_data.get('slides', [])),
                    json.dumps(slide_data.get('ai_metadata', {})),
                    slide_data['created_by'],
                    slide_data.get('status', 'generated'),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(slide_id)
        except Exception as e:
            raise ContentException(
                message="Failed to create AI-generated slide set",
                error_code="SLIDE_CREATION_ERROR",
                details={
                    "course_id": slide_data.get('course_id'),
                    "title": slide_data.get('title')
                },
                original_exception=e
            )
    
    async def get_course_slide_sets(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all slide sets for a specific course.
        
        Business Context:
        Slide set listing supports instructional content organization,
        presentation planning, and educational material management.
        
        Args:
            course_id: Course to get slide sets for
            
        Returns:
            List of slide set records with metadata
        """
        try:
            async with self.db_pool.acquire() as conn:
                slide_sets = await conn.fetch(
                    """SELECT id, course_id, title, description, template,
                              slide_count, status, created_at, updated_at
                       FROM course_creator.slides 
                       WHERE course_id = $1 
                       ORDER BY created_at DESC""",
                    course_id
                )
                return [dict(slide_set) for slide_set in slide_sets]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve course slide sets",
                error_code="SLIDE_RETRIEVAL_ERROR",
                details={"course_id": course_id},
                original_exception=e
            )
    
    # ================================================================
    # EXERCISE GENERATION AND MANAGEMENT QUERIES
    # ================================================================
    
    async def create_exercise(self, exercise_data: Dict[str, Any]) -> str:
        """
        Create a new AI-generated exercise with instructions and solutions.
        
        Business Context:
        Exercise generation creates hands-on learning activities that reinforce
        theoretical concepts through practical application, enhancing student
        engagement and skill development in educational programs.
        
        Args:
            exercise_data: Dictionary containing exercise information
                - id: Unique exercise identifier
                - course_id: Associated course identifier
                - title: Exercise title and learning focus
                - description: Exercise description and objectives
                - instructions: Step-by-step exercise instructions
                - solution: Complete solution and explanation
                - difficulty_level: Exercise difficulty level
                - estimated_time: Estimated completion time in minutes
                - resources: Required resources and tools
                - ai_metadata: AI generation parameters and sources
                
        Returns:
            Created exercise ID for tracking and reference
        """
        try:
            async with self.db_pool.acquire() as conn:
                exercise_id = await conn.fetchval(
                    """INSERT INTO course_creator.quizzes (
                        id, course_id, title, description, instructions, solution,
                        difficulty_level, estimated_time, resources, ai_metadata,
                        created_by, status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14) 
                    RETURNING id""",
                    exercise_data['id'],
                    exercise_data['course_id'],
                    exercise_data['title'],
                    exercise_data['description'],
                    exercise_data['instructions'],
                    exercise_data.get('solution'),
                    exercise_data.get('difficulty_level', 'intermediate'),
                    exercise_data.get('estimated_time', 60),
                    json.dumps(exercise_data.get('resources', [])),
                    json.dumps(exercise_data.get('ai_metadata', {})),
                    exercise_data['created_by'],
                    exercise_data.get('status', 'generated'),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(exercise_id)
        except Exception as e:
            raise ContentException(
                message="Failed to create AI-generated exercise",
                error_code="EXERCISE_CREATION_ERROR",
                details={
                    "course_id": exercise_data.get('course_id'),
                    "title": exercise_data.get('title')
                },
                original_exception=e
            )
    
    async def get_course_exercises(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all exercises for a specific course.
        
        Business Context:
        Exercise listing supports course content organization, learning
        activity planning, and hands-on skill development tracking.
        
        Args:
            course_id: Course to get exercises for
            
        Returns:
            List of exercise records with metadata
        """
        try:
            async with self.db_pool.acquire() as conn:
                exercises = await conn.fetch(
                    """SELECT id, course_id, title, description, difficulty_level,
                              time_limit as estimated_time, status, created_at, updated_at
                       FROM course_creator.quizzes 
                       WHERE course_id = $1 AND quiz_type = 'exercise'
                       ORDER BY created_at DESC""",
                    course_id
                )
                return [dict(exercise) for exercise in exercises]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve course exercises",
                error_code="EXERCISE_RETRIEVAL_ERROR",
                details={"course_id": course_id},
                original_exception=e
            )
    
    # ================================================================
    # LAB ENVIRONMENT GENERATION QUERIES
    # ================================================================
    
    async def create_lab_environment(self, lab_data: Dict[str, Any]) -> str:
        """
        Create a new AI-generated lab environment configuration.
        
        Business Context:
        Lab environment generation automates the creation of hands-on learning
        environments, providing consistent development setups and reducing
        technical barriers for students in practical learning activities.
        
        Args:
            lab_data: Dictionary containing lab environment information
                - id: Unique lab environment identifier
                - course_id: Associated course identifier
                - name: Lab environment name and purpose
                - description: Lab description and learning objectives
                - configuration: Technical environment configuration
                - docker_config: Docker container configuration
                - tools: Pre-installed tools and software
                - startup_script: Environment initialization script
                - ai_metadata: AI generation parameters and optimization data
                
        Returns:
            Created lab environment ID for tracking and deployment
        """
        try:
            async with self.db_pool.acquire() as conn:
                lab_id = await conn.fetchval(
                    """INSERT INTO course_creator.lab_sessions (
                        id, course_id, container_name, container_id, environment_config,
                        port_mapping, environment_config, user_id, status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $10, $11, $12, $13) 
                    RETURNING id""",
                    lab_data['id'],
                    lab_data['course_id'],
                    lab_data['name'],
                    lab_data.get('description', lab_data['name']),
                    json.dumps(lab_data['configuration']),
                    json.dumps(lab_data.get('docker_config', {})),
                    json.dumps(lab_data.get('tools', [])),
                    lab_data['created_by'],
                    lab_data.get('status', 'generated'),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(lab_id)
        except Exception as e:
            raise ContentException(
                message="Failed to create AI-generated lab environment",
                error_code="LAB_CREATION_ERROR",
                details={
                    "course_id": lab_data.get('course_id'),
                    "name": lab_data.get('name')
                },
                original_exception=e
            )
    
    async def get_course_lab_environments(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all lab environments for a specific course.
        
        Business Context:
        Lab environment listing supports hands-on learning setup, technical
        resource planning, and practical skill development activities.
        
        Args:
            course_id: Course to get lab environments for
            
        Returns:
            List of lab environment records with configuration metadata
        """
        try:
            async with self.db_pool.acquire() as conn:
                lab_envs = await conn.fetch(
                    """SELECT id, course_id, container_name as name, container_id as description, status,
                              created_at, updated_at
                       FROM course_creator.lab_sessions 
                       WHERE course_id = $1 
                       ORDER BY created_at DESC""",
                    course_id
                )
                return [dict(lab_env) for lab_env in lab_envs]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve course lab environments",
                error_code="LAB_RETRIEVAL_ERROR",
                details={"course_id": course_id},
                original_exception=e
            )
    
    # ================================================================
    # CONTENT GENERATION ANALYTICS AND OPTIMIZATION
    # ================================================================
    
    async def track_generation_job(self, job_data: Dict[str, Any]) -> str:
        """
        Track AI content generation job progress and performance metrics.
        
        Business Context:
        Generation job tracking enables performance monitoring, optimization
        analysis, and quality assurance for AI-powered content creation processes.
        
        Args:
            job_data: Dictionary containing generation job information
                - id: Unique job identifier
                - job_type: Type of content being generated
                - course_id: Associated course identifier
                - parameters: Generation parameters and settings
                - status: Current job status
                - progress: Generation progress percentage
                - ai_model: AI model used for generation
                - started_by: User who initiated generation
                
        Returns:
            Created job tracking ID for monitoring
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Map generation job to course_outline tracking
                job_id = await conn.fetchval(
                    """INSERT INTO course_creator.course_outlines (
                        id, course_id, title, description, structure, status, version,
                        ai_metadata, created_by, created_at, updated_at
                    ) VALUES ($1, $3, $2, 'Generation Job', $4, $5, $6, $7, $8, $9, $10) 
                    RETURNING id""",
                    job_data['id'],
                    job_data['course_id'],
                    job_data['job_type'],
                    f"Generation Job: {job_data['job_type']}",
                    json.dumps(job_data.get('parameters', {})),
                    job_data.get('status', 'started'),
                    job_data.get('progress', 0),
                    json.dumps({"ai_model": job_data.get('ai_model', 'gpt-4')}),
                    job_data['started_by'],
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(job_id)
        except Exception as e:
            raise DatabaseException(
                message="Failed to track content generation job",
                error_code="JOB_TRACKING_ERROR",
                details=job_data,
                original_exception=e
            )
    
    async def update_generation_job_progress(self, job_id: str, progress: int, 
                                           status: Optional[str] = None) -> bool:
        """
        Update generation job progress and status.
        
        Business Context:
        Progress tracking enables real-time monitoring of AI content generation,
        providing users with feedback and enabling system optimization.
        
        Args:
            job_id: Job to update progress for
            progress: Current progress percentage (0-100)
            status: Optional status update
            
        Returns:
            True if progress was updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                if status:
                    result = await conn.execute(
                        """UPDATE course_creator.course_outlines 
                           SET version = $1, status = $2, updated_at = $3 
                           WHERE id = $4""",
                        progress, status, datetime.utcnow(), job_id
                    )
                else:
                    result = await conn.execute(
                        """UPDATE course_creator.course_outlines 
                           SET version = $1, updated_at = $2 
                           WHERE id = $3""",
                        progress, datetime.utcnow(), job_id
                    )
                return result.split()[-1] == '1'
        except Exception as e:
            raise DatabaseException(
                message="Failed to update generation job progress",
                error_code="JOB_UPDATE_ERROR",
                details={"job_id": job_id, "progress": progress, "status": status},
                original_exception=e
            )
    
    async def get_generation_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate comprehensive AI content generation statistics.
        
        Business Context:
        Generation statistics support platform optimization, usage analysis,
        and AI model performance evaluation for continuous improvement.
        
        Args:
            days: Number of days to analyze (default 30)
            
        Returns:
            Dictionary containing comprehensive generation statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            async with self.db_pool.acquire() as conn:
                # Get generation job statistics
                job_stats = await conn.fetchrow(
                    """SELECT 
                        COUNT(*) as total_jobs,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
                        AVG(CASE WHEN status = 'completed' THEN version END) as avg_completion_rate
                       FROM course_creator.course_outlines 
                       WHERE created_at >= $1""",
                    start_date
                )
                
                # Get content type distribution
                content_stats = await conn.fetch(
                    """SELECT 'course_outline' as job_type, COUNT(*) as count, 
                              COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
                       FROM course_creator.course_outlines 
                       WHERE created_at >= $1
                       GROUP BY 'course_outline' 
                       ORDER BY count DESC""",
                    start_date
                )
                
                return {
                    "total_jobs": job_stats['total_jobs'] or 0,
                    "completed_jobs": job_stats['completed_jobs'] or 0,
                    "failed_jobs": job_stats['failed_jobs'] or 0,
                    "success_rate": (
                        (job_stats['completed_jobs'] or 0) / max(job_stats['total_jobs'] or 1, 1) * 100
                    ),
                    "average_completion": float(job_stats['avg_completion_rate'] or 0),
                    "content_breakdown": [
                        {
                            "type": row['job_type'],
                            "total": row['count'],
                            "completed": row['completed'],
                            "success_rate": (row['completed'] / max(row['count'], 1) * 100)
                        }
                        for row in content_stats
                    ]
                }
        except Exception as e:
            raise DatabaseException(
                message="Failed to calculate generation statistics",
                error_code="STATS_CALCULATION_ERROR",
                details={"days": days},
                original_exception=e
            )