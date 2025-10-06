"""
PDF Report Endpoints for Analytics Service
Provides endpoints for generating and downloading PDF reports
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
import asyncio
import io

import structlog

# Initialize logger
logger = structlog.get_logger()

# Initialize PDF generator
pdf_generator = None

# This will be set by main.py when it imports this module
app = None
db_pool = None
get_current_user = None

def initialize_pdf_routes(fastapi_app, database_pool, auth_function):
    """Initialize PDF routes with dependencies from main module"""
    global app, db_pool, get_current_user, pdf_generator
    app = fastapi_app
    db_pool = database_pool
    get_current_user = auth_function
    
    from pdf_generator import StudentAnalyticsPDFGenerator
    
    # Create wrapped functions that use the correct dependency
    def create_course_pdf_endpoint():
        async def endpoint(
            course_id: str,
            start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
            end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
            current_user: dict = Depends(get_current_user)
        ):
            return await download_course_analytics_pdf(course_id, start_date, end_date, current_user)
        return endpoint
    
    def create_student_pdf_endpoint():
        async def endpoint(
            student_id: str,
            course_id: Optional[str] = Query(None, description="Course ID to filter by"),
            start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
            end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
            current_user: dict = Depends(get_current_user)
        ):
            return await download_student_analytics_pdf(student_id, course_id, start_date, end_date, current_user)
        return endpoint
        
    def create_preview_endpoint():
        async def endpoint(
            course_id: str,
            start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
            end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
            current_user: dict = Depends(get_current_user)
        ):
            return await preview_course_analytics_data(course_id, start_date, end_date, current_user)
        return endpoint
    
    # Register the routes
    app.add_api_route("/analytics/reports/course/{course_id}/pdf", create_course_pdf_endpoint(), methods=["GET"])
    app.add_api_route("/analytics/reports/student/{student_id}/pdf", create_student_pdf_endpoint(), methods=["GET"])
    app.add_api_route("/analytics/reports/preview/{course_id}", create_preview_endpoint(), methods=["GET"])
    
    logger.info("PDF endpoints registered successfully")

async def initialize_pdf_generator():
    """Initialize PDF generator on startup"""
    global pdf_generator
    await asyncio.sleep(1)  # Wait for db_pool to be initialized
    if db_pool:
        from pdf_generator import StudentAnalyticsPDFGenerator
        pdf_generator = StudentAnalyticsPDFGenerator(db_pool)
        logger.info("PDF generator initialized")

async def download_course_analytics_pdf(
    course_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = None
):
    """
    Generate and download a comprehensive PDF analytics report for a course
    
    This endpoint creates a detailed PDF report containing:
    - Executive summary with key metrics
    - Student enrollment and engagement data
    - Lab usage analytics
    - Quiz performance statistics
    - Individual student performance breakdown
    - Recommendations and insights
    """
    if not pdf_generator:
        raise HTTPException(
            status_code=503, 
            detail="PDF generation service not available"
        )
    
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Set default date range if not provided (last 30 days)
        if not end_dt:
            end_dt = datetime.utcnow()
        if not start_dt:
            start_dt = end_dt - timedelta(days=30)
        
        # Validate date range
        if start_dt > end_dt:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )
        
        logger.info(f"Generating PDF report for course {course_id} from {start_dt} to {end_dt}")
        
        # Generate PDF
        pdf_buffer = await pdf_generator.generate_course_analytics_report(
            course_id=course_id,
            start_date=start_dt,
            end_date=end_dt,
            instructor_id=current_user.get('id')
        )
        
        # Create filename
        filename = f"analytics_report_{course_id}_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.pdf"
        
        # Return PDF as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_buffer.read()),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF report: {str(e)}"
        )

async def download_student_analytics_pdf(
    student_id: str,
    course_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = None
):
    """
    Generate and download a PDF analytics report for a specific student
    
    This endpoint creates a detailed PDF report for an individual student containing:
    - Student profile and enrollment information
    - Activity timeline and engagement metrics
    - Lab usage detailed analysis
    - Quiz performance history
    - Progress tracking across course modules
    - Personalized recommendations
    """
    if not pdf_generator:
        raise HTTPException(
            status_code=503, 
            detail="PDF generation service not available"
        )
    
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Set default date range if not provided (last 60 days for individual student)
        if not end_dt:
            end_dt = datetime.utcnow()
        if not start_dt:
            start_dt = end_dt - timedelta(days=60)
        
        logger.info(f"Generating individual PDF report for student {student_id}")
        
        # For now, we'll use the course report but filtered to one student
        # In a full implementation, you'd create a separate student-specific report
        if not course_id:
            # Get the student's most recent course
            async with db_pool.acquire() as conn:
                course_record = await conn.fetchrow("""
                    SELECT course_id 
                    FROM enrollments 
                    WHERE student_id = $1 
                    ORDER BY enrolled_at DESC 
                    LIMIT 1
                """, student_id)
                
                if not course_record:
                    raise HTTPException(
                        status_code=404,
                        detail="No course enrollment found for this student"
                    )
                
                course_id = course_record['course_id']
        
        # Generate PDF (using course report for now)
        pdf_buffer = await pdf_generator.generate_course_analytics_report(
            course_id=course_id,
            start_date=start_dt,
            end_date=end_dt,
            instructor_id=current_user.get('id')
        )
        
        # Create filename
        filename = f"student_report_{student_id}_{course_id}_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_buffer.read()),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating student PDF report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate student PDF report: {str(e)}"
        )

async def preview_course_analytics_data(
    course_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = None
):
    """
    Preview the data that would be included in a course analytics PDF report
    Returns JSON data for frontend preview before generating PDF
    """
    if not pdf_generator:
        raise HTTPException(
            status_code=503, 
            detail="PDF generation service not available"
        )
    
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Set defaults
        if not end_dt:
            end_dt = datetime.utcnow()
        if not start_dt:
            start_dt = end_dt - timedelta(days=30)
        
        # Get preview data
        course_info = await pdf_generator.get_course_info(course_id)
        key_metrics = await pdf_generator.get_key_metrics(course_id, start_dt, end_dt)
        
        return {
            "course_info": course_info,
            "date_range": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat()
            },
            "key_metrics": key_metrics,
            "report_sections": [
                "Executive Summary",
                "Student Enrollment & Engagement", 
                "Lab Usage Analytics",
                "Quiz Performance Analytics",
                "Individual Student Performance",
                "Recommendations & Insights"
            ],
            "estimated_pages": 5 + (key_metrics['total_students'] // 10)  # Rough estimate
        }
        
    except Exception as e:
        logger.error(f"Error generating preview data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview data: {str(e)}"
        )