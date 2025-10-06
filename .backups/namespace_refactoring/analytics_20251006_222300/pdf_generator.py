"""
PDF Report Generator for Student Analytics
Generates comprehensive PDF reports for instructors with student analytics data
"""

import io
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncpg
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.lib.colors import HexColor
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from io import BytesIO
import structlog

logger = structlog.get_logger()

class StudentAnalyticsPDFGenerator:
    """Generate comprehensive PDF analytics reports for instructors"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=10,
            backColor=colors.lightgrey
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        ))

    async def generate_course_analytics_report(
        self, 
        course_id: str, 
        start_date: datetime = None, 
        end_date: datetime = None,
        instructor_id: str = None
    ) -> io.BytesIO:
        """Generate a comprehensive course analytics PDF report"""
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        logger.info(f"Generating PDF report for course {course_id} from {start_date} to {end_date}")
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build report content
        story = []
        
        # Get course information
        course_info = await self.get_course_info(course_id)
        
        # Title page
        story.extend(await self.create_title_page(course_info, start_date, end_date))
        
        # Executive summary
        story.extend(await self.create_executive_summary(course_id, start_date, end_date))
        
        # Student enrollment and engagement
        story.extend(await self.create_enrollment_section(course_id, start_date, end_date))
        
        # Lab usage analytics
        story.extend(await self.create_lab_analytics_section(course_id, start_date, end_date))
        
        # Quiz performance analytics
        story.extend(await self.create_quiz_analytics_section(course_id, start_date, end_date))
        
        # Individual student performance
        story.extend(await self.create_student_performance_section(course_id, start_date, end_date))
        
        # Recommendations and insights
        story.extend(await self.create_recommendations_section(course_id, start_date, end_date))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"PDF report generated successfully for course {course_id}")
        return buffer

    async def get_course_info(self, course_id: str) -> Dict:
        """Get course information from database"""
        async with self.db_pool.acquire() as conn:
            course = await conn.fetchrow("""
                SELECT id, title, description, created_at, instructor_id
                FROM courses 
                WHERE id = $1
            """, course_id)
            
            if not course:
                return {"id": course_id, "title": "Unknown Course", "description": "", "created_at": datetime.utcnow()}
            
            return dict(course)

    async def create_title_page(self, course_info: Dict, start_date: datetime, end_date: datetime) -> List:
        """Create the title page of the report"""
        story = []
        
        # Title
        title = f"Student Analytics Report<br/>{course_info['title']}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Report details
        report_info = f"""
        <b>Course ID:</b> {course_info['id']}<br/>
        <b>Report Period:</b> {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}<br/>
        <b>Generated:</b> {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}<br/>
        <b>Report Type:</b> Comprehensive Student Analytics
        """
        story.append(Paragraph(report_info, self.styles['Normal']))
        story.append(Spacer(1, 1*inch))
        
        # Course description
        if course_info.get('description'):
            story.append(Paragraph("<b>Course Description:</b>", self.styles['Heading3']))
            story.append(Paragraph(course_info['description'], self.styles['Normal']))
        
        story.append(PageBreak())
        return story

    async def create_executive_summary(self, course_id: str, start_date: datetime, end_date: datetime) -> List:
        """Create executive summary section"""
        story = []
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Get key metrics
        metrics = await self.get_key_metrics(course_id, start_date, end_date)
        
        # Summary table
        summary_data = [
            ['Metric', 'Value', 'Status'],
            ['Total Students Enrolled', str(metrics['total_students']), '✓'],
            ['Active Students (Last 7 Days)', str(metrics['active_students']), '✓'],
            ['Total Lab Sessions', str(metrics['total_lab_sessions']), '✓'],
            ['Average Lab Duration', f"{metrics['avg_lab_duration']:.1f} minutes", '✓'],
            ['Quiz Completion Rate', f"{metrics['quiz_completion_rate']:.1f}%", '✓'],
            ['Average Quiz Score', f"{metrics['avg_quiz_score']:.1f}%", '✓'],
            ['Student Engagement Score', f"{metrics['engagement_score']:.1f}/100", '✓']
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Key insights
        insights = await self.generate_key_insights(metrics)
        story.append(Paragraph("<b>Key Insights:</b>", self.styles['Heading3']))
        for insight in insights:
            story.append(Paragraph(f"• {insight}", self.styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        return story

    async def get_key_metrics(self, course_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate key metrics for the course"""
        async with self.db_pool.acquire() as conn:
            # Total students enrolled
            total_students = await conn.fetchval("""
                SELECT COUNT(DISTINCT student_id) 
                FROM enrollments 
                WHERE course_id = $1
            """, course_id) or 0
            
            # Active students (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            active_students = await conn.fetchval("""
                SELECT COUNT(DISTINCT student_id) 
                FROM student_activities 
                WHERE course_id = $1 AND timestamp >= $2
            """, course_id, week_ago) or 0
            
            # Lab usage metrics
            lab_metrics = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_sessions,
                    AVG(duration_minutes) as avg_duration
                FROM lab_usage_metrics 
                WHERE course_id = $1 AND session_start BETWEEN $2 AND $3
            """, course_id, start_date, end_date)
            
            # Quiz performance metrics
            quiz_metrics = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_attempts,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    AVG(score_percentage) as avg_score
                FROM quiz_performance 
                WHERE course_id = $1 AND start_time BETWEEN $2 AND $3
            """, course_id, start_date, end_date)
            
            # Calculate metrics
            quiz_completion_rate = 0
            if quiz_metrics and quiz_metrics['total_attempts'] > 0:
                quiz_completion_rate = (quiz_metrics['completed'] / quiz_metrics['total_attempts']) * 100
            
            # Engagement score (simplified calculation)
            engagement_score = min(100, (active_students / max(total_students, 1)) * 100)
            
            return {
                'total_students': total_students,
                'active_students': active_students,
                'total_lab_sessions': lab_metrics['total_sessions'] if lab_metrics else 0,
                'avg_lab_duration': lab_metrics['avg_duration'] if lab_metrics and lab_metrics['avg_duration'] else 0,
                'quiz_completion_rate': quiz_completion_rate,
                'avg_quiz_score': quiz_metrics['avg_score'] if quiz_metrics and quiz_metrics['avg_score'] else 0,
                'engagement_score': engagement_score
            }

    async def generate_key_insights(self, metrics: Dict) -> List[str]:
        """Generate key insights based on metrics"""
        insights = []
        
        if metrics['engagement_score'] >= 80:
            insights.append("High student engagement with excellent participation rates")
        elif metrics['engagement_score'] >= 60:
            insights.append("Good student engagement with room for improvement")
        else:
            insights.append("Low student engagement - consider intervention strategies")
            
        if metrics['avg_quiz_score'] >= 80:
            insights.append("Students are performing well on quizzes")
        elif metrics['avg_quiz_score'] >= 60:
            insights.append("Quiz performance is satisfactory but could be improved")
        else:
            insights.append("Quiz scores indicate students may need additional support")
            
        if metrics['avg_lab_duration'] >= 30:
            insights.append("Students are spending good time on lab exercises")
        else:
            insights.append("Students may need encouragement to spend more time on labs")
            
        return insights

    async def create_enrollment_section(self, course_id: str, start_date: datetime, end_date: datetime) -> List:
        """Create student enrollment and engagement section"""
        story = []
        story.append(Paragraph("Student Enrollment & Engagement", self.styles['SectionHeader']))
        
        # Get enrollment data
        async with self.db_pool.acquire() as conn:
            enrollments = await conn.fetch("""
                SELECT 
                    e.student_id,
                    u.email,
                    u.full_name,
                    e.enrollment_date,
                    COUNT(sa.activity_id) as activity_count,
                    MAX(sa.timestamp) as last_activity
                FROM enrollments e
                LEFT JOIN users u ON e.student_id = u.id
                LEFT JOIN student_activities sa ON e.student_id = sa.student_id 
                    AND sa.course_id = e.course_id 
                    AND sa.timestamp BETWEEN $2 AND $3
                WHERE e.course_id = $1
                GROUP BY e.student_id, u.email, u.full_name, e.enrollment_date
                ORDER BY e.enrollment_date DESC
            """, course_id, start_date, end_date)
        
        if enrollments:
            # Create enrollment table
            enrollment_data = [['Student', 'Email', 'Enrolled Date', 'Activities', 'Last Active']]
            
            for enrollment in enrollments:
                name = enrollment['full_name'] or enrollment['student_id'][:8]
                
                last_activity = "Never"
                if enrollment['last_activity']:
                    last_activity = enrollment['last_activity'].strftime('%m/%d/%Y')
                
                enrollment_data.append([
                    name,
                    enrollment['email'] or 'N/A',
                    enrollment['enrollment_date'].strftime('%m/%d/%Y'),
                    str(enrollment['activity_count']),
                    last_activity
                ])
            
            enrollment_table = Table(enrollment_data, colWidths=[1.2*inch, 1.8*inch, 1*inch, 0.8*inch, 1*inch])
            enrollment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(enrollment_table)
        else:
            story.append(Paragraph("No student enrollments found for this course.", self.styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        return story

    async def create_lab_analytics_section(self, course_id: str, start_date: datetime, end_date: datetime) -> List:
        """Create lab usage analytics section"""
        story = []
        story.append(Paragraph("Lab Usage Analytics", self.styles['SectionHeader']))
        
        async with self.db_pool.acquire() as conn:
            lab_data = await conn.fetch("""
                SELECT 
                    student_id,
                    lab_id,
                    duration_minutes,
                    actions_performed,
                    code_executions,
                    errors_encountered,
                    completion_status,
                    session_start
                FROM lab_usage_metrics 
                WHERE course_id = $1 AND session_start BETWEEN $2 AND $3
                ORDER BY session_start DESC
            """, course_id, start_date, end_date)
        
        if lab_data:
            # Summary statistics
            total_sessions = len(lab_data)
            avg_duration = sum(row['duration_minutes'] for row in lab_data if row['duration_minutes']) / total_sessions if total_sessions > 0 else 0
            completed = sum(1 for row in lab_data if row['completion_status'] == 'completed')
            completion_rate = (completed / total_sessions) * 100 if total_sessions > 0 else 0
            
            summary_text = f"""
            <b>Lab Usage Summary:</b><br/>
            • Total Lab Sessions: {total_sessions}<br/>
            • Average Session Duration: {avg_duration:.1f} minutes<br/>
            • Completion Rate: {completion_rate:.1f}%<br/>
            • Completed Sessions: {completed} out of {total_sessions}
            """
            story.append(Paragraph(summary_text, self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Recent lab sessions table (top 10)
            story.append(Paragraph("<b>Recent Lab Sessions:</b>", self.styles['Heading3']))
            
            lab_table_data = [['Student ID', 'Lab ID', 'Duration (min)', 'Actions', 'Status']]
            for lab in lab_data[:10]:
                lab_table_data.append([
                    lab['student_id'][:12] + '...' if len(lab['student_id']) > 12 else lab['student_id'],
                    lab['lab_id'][:15] + '...' if len(lab['lab_id']) > 15 else lab['lab_id'],
                    str(lab['duration_minutes'] or 0),
                    str(lab['actions_performed']),
                    lab['completion_status'].title()
                ])
            
            lab_table = Table(lab_table_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 0.8*inch, 1*inch])
            lab_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(lab_table)
        else:
            story.append(Paragraph("No lab usage data found for this period.", self.styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        return story

    async def create_quiz_analytics_section(self, course_id: str, start_date: datetime, end_date: datetime) -> List:
        """Create quiz performance analytics section"""
        story = []
        story.append(Paragraph("Quiz Performance Analytics", self.styles['SectionHeader']))
        
        async with self.db_pool.acquire() as conn:
            quiz_data = await conn.fetch("""
                SELECT 
                    student_id,
                    quiz_id,
                    attempt_number,
                    duration_minutes,
                    questions_total,
                    questions_correct,
                    score_percentage,
                    status,
                    start_time
                FROM quiz_performance 
                WHERE course_id = $1 AND start_time BETWEEN $2 AND $3
                ORDER BY start_time DESC
            """, course_id, start_date, end_date)
        
        if quiz_data:
            # Summary statistics
            total_attempts = len(quiz_data)
            completed = sum(1 for row in quiz_data if row['status'] == 'completed')
            avg_score = sum(row['score_percentage'] for row in quiz_data if row['score_percentage']) / total_attempts if total_attempts > 0 else 0
            
            summary_text = f"""
            <b>Quiz Performance Summary:</b><br/>
            • Total Quiz Attempts: {total_attempts}<br/>
            • Completed Attempts: {completed}<br/>
            • Average Score: {avg_score:.1f}%<br/>
            • Completion Rate: {(completed/total_attempts)*100:.1f}%
            """
            story.append(Paragraph(summary_text, self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Recent quiz attempts table
            story.append(Paragraph("<b>Recent Quiz Attempts:</b>", self.styles['Heading3']))
            
            quiz_table_data = [['Student ID', 'Quiz ID', 'Score', 'Duration (min)', 'Status']]
            for quiz in quiz_data[:15]:
                quiz_table_data.append([
                    quiz['student_id'][:12] + '...' if len(quiz['student_id']) > 12 else quiz['student_id'],
                    quiz['quiz_id'][:15] + '...' if len(quiz['quiz_id']) > 15 else quiz['quiz_id'],
                    f"{quiz['score_percentage']:.1f}%" if quiz['score_percentage'] else "N/A",
                    str(quiz['duration_minutes'] or 0),
                    quiz['status'].title()
                ])
            
            quiz_table = Table(quiz_table_data, colWidths=[1.5*inch, 1.5*inch, 0.8*inch, 1*inch, 1*inch])
            quiz_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(quiz_table)
        else:
            story.append(Paragraph("No quiz performance data found for this period.", self.styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        return story

    async def create_student_performance_section(self, course_id: str, start_date: datetime, end_date: datetime) -> List:
        """Create individual student performance section"""
        story = []
        story.append(Paragraph("Individual Student Performance", self.styles['SectionHeader']))
        
        async with self.db_pool.acquire() as conn:
            student_performance = await conn.fetch("""
                SELECT 
                    e.student_id,
                    u.full_name,
                    u.email,
                    COUNT(DISTINCT sa.activity_id) as total_activities,
                    COUNT(DISTINCT lum.metric_id) as lab_sessions,
                    AVG(lum.duration_minutes) as avg_lab_duration,
                    COUNT(DISTINCT qp.performance_id) as quiz_attempts,
                    AVG(qp.score_percentage) as avg_quiz_score,
                    MAX(sa.timestamp) as last_activity
                FROM enrollments e
                LEFT JOIN users u ON e.student_id = u.id
                LEFT JOIN student_activities sa ON e.student_id = sa.student_id 
                    AND sa.course_id = e.course_id
                    AND sa.timestamp BETWEEN $2 AND $3
                LEFT JOIN lab_usage_metrics lum ON e.student_id = lum.student_id 
                    AND lum.course_id = e.course_id
                    AND lum.session_start BETWEEN $2 AND $3
                LEFT JOIN quiz_performance qp ON e.student_id = qp.student_id 
                    AND qp.course_id = e.course_id
                    AND qp.start_time BETWEEN $2 AND $3
                WHERE e.course_id = $1
                GROUP BY e.student_id, u.full_name, u.email
                ORDER BY total_activities DESC, avg_quiz_score DESC
            """, course_id, start_date, end_date)
        
        if student_performance:
            performance_data = [['Student', 'Activities', 'Lab Sessions', 'Avg Lab Time', 'Quiz Attempts', 'Avg Quiz Score']]
            
            for student in student_performance:
                name = student['full_name'] or student['student_id'][:12]
                
                performance_data.append([
                    name,
                    str(student['total_activities'] or 0),
                    str(student['lab_sessions'] or 0),
                    f"{student['avg_lab_duration'] or 0:.1f}m",
                    str(student['quiz_attempts'] or 0),
                    f"{student['avg_quiz_score'] or 0:.1f}%"
                ])
            
            performance_table = Table(performance_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
            performance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(performance_table)
        else:
            story.append(Paragraph("No student performance data available for this period.", self.styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        return story

    async def create_recommendations_section(self, course_id: str, start_date: datetime, end_date: datetime) -> List:
        """Create recommendations and insights section"""
        story = []
        story.append(Paragraph("Recommendations & Insights", self.styles['SectionHeader']))
        
        # Get metrics to base recommendations on
        metrics = await self.get_key_metrics(course_id, start_date, end_date)
        
        recommendations = []
        
        # Analyze engagement
        if metrics['engagement_score'] < 50:
            recommendations.append("Consider implementing engagement strategies such as gamification or interactive content")
        
        # Analyze lab usage
        if metrics['avg_lab_duration'] < 20:
            recommendations.append("Students may benefit from more guidance on lab exercises - consider adding tutorial videos")
        
        # Analyze quiz performance
        if metrics['avg_quiz_score'] < 70:
            recommendations.append("Quiz scores suggest students need additional support - consider review sessions or additional resources")
        
        # Active vs total students
        if metrics['active_students'] / max(metrics['total_students'], 1) < 0.7:
            recommendations.append("Low student activity rate - consider sending engagement reminders or check-in communications")
        
        if not recommendations:
            recommendations.append("Course performance is good across all metrics - continue current teaching strategies")
            recommendations.append("Consider surveying students for additional feedback on course improvements")
        
        story.append(Paragraph("<b>Actionable Recommendations:</b>", self.styles['Heading3']))
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", self.styles['Normal']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Footer
        story.append(Paragraph(
            "<i>This report was generated automatically by the Course Creator Analytics System. "
            "For questions about this data, please contact your system administrator.</i>",
            self.styles['Normal']
        ))
        
        return story