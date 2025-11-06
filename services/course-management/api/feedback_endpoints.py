"""
Feedback Management API Endpoints

BUSINESS CONTEXT:
This module contains all bi-directional feedback REST API endpoints following the Single
Responsibility Principle. It handles both student→course feedback and instructor→student
feedback flows with comprehensive analytics integration.

SOLID PRINCIPLES APPLIED:
- Single Responsibility: Only feedback management endpoints
- Open/Closed: Extensible through dependency injection
- Liskov Substitution: Uses interface abstractions
- Interface Segregation: Depends only on IFeedbackService
- Dependency Inversion: Depends on abstractions

FEEDBACK WORKFLOWS:
1. Student Course Feedback: Students evaluate course quality, content, and instructor
2. Instructor Student Feedback: Instructors assess student performance and provide guidance

BI-DIRECTIONAL FEEDBACK SYSTEM:
- Student→Course: Overall ratings, content quality, instructor effectiveness
- Instructor→Student: Performance assessments, strengths, improvement areas

@module api/feedback_endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

# Domain entities and services
from course_management.domain.entities.feedback import CourseFeedback, StudentFeedback, FeedbackResponse
from course_management.domain.interfaces.feedback_service import IFeedbackService

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# API Models (DTOs - following Single Responsibility)
class CourseFeedbackRequest(BaseModel):
    """
    Data Transfer Object for student course feedback submissions.

    This DTO captures comprehensive student feedback on course quality, instructor
    effectiveness, and overall learning experience. It supports both quantitative
    ratings and qualitative comments to provide actionable insights for course improvement.

    FEEDBACK CATEGORIES:
    1. Overall Experience: Holistic course satisfaction rating
    2. Content Quality: Assessment of educational materials and curriculum design
    3. Instructor Effectiveness: Teaching methodology and communication evaluation
    4. Difficulty Appropriateness: Course challenge level relative to stated prerequisites
    5. Lab Quality: Hands-on learning environment assessment (for technical courses)

    EDUCATIONAL VALUE:
    - Quantitative ratings enable statistical analysis and trend tracking
    - Qualitative feedback provides specific, actionable improvement suggestions
    - Anonymous option encourages honest feedback without fear of retaliation
    - Recommendation flag indicates overall student satisfaction and course viability

    ANALYTICS INTEGRATION:
    - Ratings feed into course performance dashboards
    - Comments are analyzed for sentiment and common themes
    - Trends help identify course improvement opportunities
    - Aggregate scores influence course recommendations and instructor evaluations

    PRIVACY CONSIDERATIONS:
    - Anonymous feedback protects student identity while preserving feedback value
    - Comments are stored securely and access-controlled to authorized personnel
    - Feedback history enables longitudinal analysis of course improvements
    """
    course_id: str
    overall_rating: int = Field(..., ge=1, le=5)
    content_quality: Optional[int] = Field(None, ge=1, le=5)
    instructor_effectiveness: Optional[int] = Field(None, ge=1, le=5)
    difficulty_appropriateness: Optional[int] = Field(None, ge=1, le=5)
    lab_quality: Optional[int] = Field(None, ge=1, le=5)
    positive_aspects: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    additional_comments: Optional[str] = None
    would_recommend: Optional[bool] = None
    is_anonymous: bool = False

class StudentFeedbackRequest(BaseModel):
    """
    Data Transfer Object for instructor student feedback submissions.

    This DTO captures comprehensive instructor assessments of student performance,
    development progress, and personalized learning recommendations. It supports
    multi-dimensional performance evaluation and qualitative development guidance.

    ASSESSMENT DIMENSIONS:
    1. Overall Performance: Holistic academic achievement and learning progress
    2. Participation: Class engagement, discussion contributions, and collaboration
    3. Lab Performance: Hands-on technical skills and practical application ability
    4. Quiz Performance: Knowledge retention and conceptual understanding
    5. Improvement Trend: Progress trajectory and learning velocity assessment

    DEVELOPMENT GUIDANCE:
    - Strengths Identification: Recognizing and reinforcing positive learning behaviors
    - Improvement Areas: Specific, actionable guidance for skill development
    - Recommendations: Personalized learning paths and resource suggestions
    - Achievements: Notable accomplishments and milestone recognition
    - Concerns: Early intervention opportunities for academic support

    FEEDBACK SHARING:
    - Instructors control whether feedback is shared with students
    - Private feedback supports confidential developmental conversations
    - Shared feedback promotes transparent communication and growth
    """
    student_id: str
    course_id: str
    overall_performance: Optional[int] = Field(None, ge=1, le=5)
    participation: Optional[int] = Field(None, ge=1, le=5)
    lab_performance: Optional[int] = Field(None, ge=1, le=5)
    quiz_performance: Optional[int] = Field(None, ge=1, le=5)
    improvement_trend: Optional[str] = None
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    specific_recommendations: Optional[str] = None
    notable_achievements: Optional[str] = None
    concerns: Optional[str] = None
    progress_assessment: Optional[str] = None
    expected_outcome: Optional[str] = None
    feedback_type: str = "regular"
    is_shared_with_student: bool = False

# Create router with feedback prefix and tag
router = APIRouter(tags=["feedback"])

# Dependency injection helpers
def get_feedback_service() -> IFeedbackService:
    """Dependency injection for feedback service"""
    from main import container
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_feedback_service()

def get_current_user_id() -> str:
    """
    Extract user ID from JWT token
    For now, return a mock user ID - in production, this would validate JWT
    """
    # Use a real UUID from the database for testing
    # orgadmin@e2etest.com = b14efecc-de51-4056-8034-30d05bf6fe80
    return "b14efecc-de51-4056-8034-30d05bf6fe80"  # Mock implementation with valid UUID

# ============================================================================
# FEEDBACK ENDPOINTS
# ============================================================================

@router.post("/feedback/course")
async def submit_course_feedback(
    request: CourseFeedbackRequest,
    current_user_id: str = Depends(get_current_user_id),
    feedback_service: IFeedbackService = Depends(get_feedback_service)
):
    """
    Submit comprehensive course feedback from a student.

    This endpoint implements the student→course feedback flow of the bi-directional
    feedback system, capturing detailed student assessments of course quality,
    instructor effectiveness, and overall learning experience.

    FEEDBACK WORKFLOW:
    1. Validate student enrollment in the course being evaluated
    2. Process quantitative ratings across multiple quality dimensions
    3. Capture qualitative feedback for specific improvement insights
    4. Store feedback with appropriate privacy controls (anonymous option)
    5. Trigger analytics processing for course performance metrics
    6. Send notification to instructor about new feedback (if configured)

    QUALITY DIMENSIONS:
    - Overall Rating: Holistic course satisfaction and learning outcome assessment
    - Content Quality: Educational material relevance, accuracy, and effectiveness
    - Instructor Effectiveness: Teaching methodology, communication, and support quality
    - Difficulty Appropriateness: Course challenge level relative to prerequisites
    - Lab Quality: Hands-on learning environment and practical exercise effectiveness

    ANALYTICS INTEGRATION:
    - Quantitative ratings feed into instructor performance dashboards
    - Qualitative comments are processed for sentiment analysis and theme extraction
    - Trend analysis identifies course improvement opportunities over time
    - Aggregate feedback scores influence course recommendation algorithms

    PRIVACY AND ETHICS:
    - Anonymous feedback option protects student identity while preserving value
    - Feedback attribution enables follow-up communication when appropriate
    - Data retention policies ensure compliance with educational privacy regulations
    - Instructor access controls prevent misuse of student feedback information

    BUSINESS VALUE:
    - Continuous improvement cycle for course quality enhancement
    - Instructor development insights for teaching methodology optimization
    - Student satisfaction metrics for course catalog optimization
    - Platform quality assurance through systematic feedback collection

    REQUEST BODY:
    - course_id: ID of course being evaluated
    - overall_rating: Overall satisfaction (1-5 scale, required)
    - content_quality: Educational content rating (1-5 scale, optional)
    - instructor_effectiveness: Teaching quality rating (1-5 scale, optional)
    - difficulty_appropriateness: Challenge level rating (1-5 scale, optional)
    - lab_quality: Hands-on environment rating (1-5 scale, optional)
    - positive_aspects: What worked well (text, optional)
    - areas_for_improvement: Improvement suggestions (text, optional)
    - additional_comments: Additional feedback (text, optional)
    - would_recommend: Recommendation flag (boolean, optional)
    - is_anonymous: Anonymous submission (boolean, default: false)

    RESPONSE:
    - message: Success confirmation message
    - feedback_id: Unique identifier for the feedback record

    ERROR HANDLING:
    - 400: Invalid rating values or course not found
    - 403: Student not enrolled in course
    - 422: Business rule violation
    - 500: Database or internal server error

    EXAMPLE USAGE:
        curl -X POST "https://localhost:8001/feedback/course" \\
             -H "Authorization: Bearer $TOKEN" \\
             -H "Content-Type: application/json" \\
             -d '{
                   "course_id": "course-123",
                   "overall_rating": 5,
                   "content_quality": 4,
                   "instructor_effectiveness": 5,
                   "positive_aspects": "Great hands-on labs!",
                   "would_recommend": true
                 }'
    """
    try:
        feedback = CourseFeedback(
            student_id=current_user_id,
            course_id=request.course_id,
            overall_rating=request.overall_rating,
            content_quality=request.content_quality,
            instructor_effectiveness=request.instructor_effectiveness,
            difficulty_appropriateness=request.difficulty_appropriateness,
            lab_quality=request.lab_quality,
            positive_aspects=request.positive_aspects,
            areas_for_improvement=request.areas_for_improvement,
            additional_comments=request.additional_comments,
            would_recommend=request.would_recommend,
            is_anonymous=request.is_anonymous
        )

        feedback_id = await feedback_service.submit_course_feedback(feedback)
        return {"message": "Course feedback submitted successfully", "feedback_id": feedback_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Error submitting course feedback: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/feedback/course/{course_id}")
async def get_course_feedback(
    course_id: str,
    current_user_id: str = Depends(get_current_user_id),
    feedback_service: IFeedbackService = Depends(get_feedback_service)
):
    """
    Get feedback for a course (instructors only).

    This endpoint retrieves all student feedback for a specific course, enabling
    instructors to review student evaluations, identify improvement opportunities,
    and track course quality trends over time.

    AUTHORIZATION:
    - Only course instructors can access feedback for their courses
    - Site admins can access any course feedback for platform quality monitoring
    - Students cannot access feedback aggregates to protect individual privacy

    RESPONSE INCLUDES:
    - Individual feedback submissions (with anonymous submissions marked)
    - Aggregate statistics (average ratings, recommendation percentage)
    - Qualitative feedback themes and sentiment analysis
    - Time-series data for tracking improvement trends

    BUSINESS VALUE:
    - Actionable insights for course improvement
    - Teaching effectiveness assessment
    - Student satisfaction monitoring
    - Continuous quality enhancement

    PATH PARAMETERS:
    - course_id: ID of course to retrieve feedback for

    RESPONSE:
    - feedback: List of feedback submissions for the course

    ERROR HANDLING:
    - 400: Invalid course ID
    - 403: User not authorized to view feedback
    - 404: Course not found
    - 500: Database or internal server error

    EXAMPLE USAGE:
        curl -X GET "https://localhost:8001/feedback/course/course-123" \\
             -H "Authorization: Bearer $TOKEN"
    """
    try:
        feedback_list = await feedback_service.get_course_feedback(course_id, current_user_id)
        return {"feedback": feedback_list}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Error retrieving course feedback: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/feedback/student")
async def submit_student_feedback(
    request: StudentFeedbackRequest,
    current_user_id: str = Depends(get_current_user_id),
    feedback_service: IFeedbackService = Depends(get_feedback_service)
):
    """
    Submit comprehensive student assessment feedback from an instructor.

    This endpoint implements the instructor→student feedback flow of the bi-directional
    feedback system, enabling instructors to provide detailed performance assessments,
    development guidance, and personalized recommendations for student growth.

    ASSESSMENT WORKFLOW:
    1. Validate instructor authorization for the specific student and course
    2. Process multi-dimensional performance assessments across academic areas
    3. Capture qualitative development insights and improvement recommendations
    4. Store feedback with configurable sharing controls for student visibility
    5. Trigger analytics processing for student progress tracking
    6. Send optional notification to student about new feedback (if enabled)

    ASSESSMENT DIMENSIONS:
    - Overall Performance: Holistic academic achievement and learning progress
    - Participation: Class engagement, discussion contributions, and collaboration
    - Lab Performance: Hands-on technical skills and practical application ability
    - Quiz Performance: Knowledge retention and conceptual understanding
    - Improvement Trend: Progress trajectory and learning velocity assessment

    DEVELOPMENT GUIDANCE:
    - Strengths Identification: Recognizing and reinforcing positive learning behaviors
    - Improvement Areas: Specific, actionable guidance for skill development
    - Recommendations: Personalized learning paths and resource suggestions
    - Achievements: Notable accomplishments and milestone recognition
    - Concerns: Early intervention opportunities for academic support

    ANALYTICS INTEGRATION:
    - Performance metrics feed into student progress tracking systems
    - Instructor feedback patterns inform teaching effectiveness analysis
    - Student development trends guide personalized learning recommendations
    - Early warning systems for students requiring additional support

    PRIVACY AND ETHICS:
    - Instructor control over feedback sharing preserves appropriate boundaries
    - Student access to feedback promotes transparent communication
    - Confidential assessment options for sensitive developmental feedback
    - Audit trails maintain accountability for instructor assessments

    EDUCATIONAL IMPACT:
    - Personalized feedback improves student engagement and learning outcomes
    - Regular assessment supports timely intervention and course correction
    - Instructor reflection on student progress enhances teaching methodology
    - Longitudinal tracking enables comprehensive student development analysis

    REQUEST BODY:
    - student_id: ID of student being assessed
    - course_id: ID of course context for assessment
    - overall_performance: Overall performance rating (1-5 scale, optional)
    - participation: Class participation rating (1-5 scale, optional)
    - lab_performance: Hands-on skills rating (1-5 scale, optional)
    - quiz_performance: Knowledge assessment rating (1-5 scale, optional)
    - improvement_trend: Progress trajectory description (text, optional)
    - strengths: Student strengths identification (text, optional)
    - areas_for_improvement: Development areas (text, optional)
    - specific_recommendations: Personalized guidance (text, optional)
    - notable_achievements: Accomplishments recognition (text, optional)
    - concerns: Support needs identification (text, optional)
    - progress_assessment: Overall progress description (text, optional)
    - expected_outcome: Predicted outcome (text, optional)
    - feedback_type: Type of feedback (default: "regular")
    - is_shared_with_student: Sharing control (boolean, default: false)

    RESPONSE:
    - message: Success confirmation message
    - feedback_id: Unique identifier for the feedback record

    ERROR HANDLING:
    - 400: Invalid student/course ID or rating values
    - 403: Instructor not authorized for this student/course
    - 422: Business rule violation
    - 500: Database or internal server error

    EXAMPLE USAGE:
        curl -X POST "https://localhost:8001/feedback/student" \\
             -H "Authorization: Bearer $TOKEN" \\
             -H "Content-Type: application/json" \\
             -d '{
                   "student_id": "student-456",
                   "course_id": "course-123",
                   "overall_performance": 4,
                   "participation": 5,
                   "strengths": "Excellent problem-solving skills",
                   "is_shared_with_student": true
                 }'
    """
    try:
        feedback = StudentFeedback(
            instructor_id=current_user_id,
            student_id=request.student_id,
            course_id=request.course_id,
            overall_performance=request.overall_performance,
            participation=request.participation,
            lab_performance=request.lab_performance,
            quiz_performance=request.quiz_performance,
            improvement_trend=request.improvement_trend,
            strengths=request.strengths,
            areas_for_improvement=request.areas_for_improvement,
            specific_recommendations=request.specific_recommendations,
            notable_achievements=request.notable_achievements,
            concerns=request.concerns,
            progress_assessment=request.progress_assessment,
            expected_outcome=request.expected_outcome,
            feedback_type=request.feedback_type,
            is_shared_with_student=request.is_shared_with_student
        )

        feedback_id = await feedback_service.submit_student_feedback(feedback)
        return {"message": "Student feedback submitted successfully", "feedback_id": feedback_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Error submitting student feedback: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/feedback/student/{student_id}")
async def get_student_feedback(
    student_id: str,
    current_user_id: str = Depends(get_current_user_id),
    feedback_service: IFeedbackService = Depends(get_feedback_service)
):
    """
    Get feedback for a student.

    This endpoint retrieves instructor feedback for a specific student, supporting
    both student self-reflection and instructor assessment review workflows.

    AUTHORIZATION:
    - Students can view feedback shared with them (is_shared_with_student=true)
    - Instructors can view all feedback they created for their students
    - Site admins can view any student feedback for platform monitoring

    PRIVACY CONTROLS:
    - Confidential feedback (is_shared_with_student=false) is only visible to instructor
    - Shared feedback promotes transparent communication and development
    - Access controls enforce appropriate boundaries

    BUSINESS VALUE:
    - Student self-awareness and reflection
    - Instructor assessment review and tracking
    - Development progress monitoring
    - Personalized learning support

    PATH PARAMETERS:
    - student_id: ID of student to retrieve feedback for

    RESPONSE:
    - feedback: List of feedback submissions for the student

    ERROR HANDLING:
    - 400: Invalid student ID
    - 403: User not authorized to view feedback
    - 404: Student not found
    - 500: Database or internal server error

    EXAMPLE USAGE:
        curl -X GET "https://localhost:8001/feedback/student/student-456" \\
             -H "Authorization: Bearer $TOKEN"
    """
    try:
        feedback_list = await feedback_service.get_student_feedback(student_id, current_user_id)
        return {"feedback": feedback_list}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Error retrieving student feedback: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e
