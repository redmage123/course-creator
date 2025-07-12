"""
File Processing Module
Handles text extraction and processing from various file formats
"""

import os
import json
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
import asyncio
import aiofiles

# Document processing imports
try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False


@dataclass
class ProcessedContent:
    """Structured content extracted from files"""
    text: str
    metadata: Dict[str, Any]
    structure: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None
    tables: Optional[List[Dict]] = None


class SyllabusProcessor:
    """Processes syllabus files and extracts structured content"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc', '.txt']
    
    async def extract_text(self, file_path: str) -> str:
        """Extract text content from syllabus file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.txt':
            return await self._extract_text_from_txt(file_path)
        elif file_ext == '.pdf':
            return await self._extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return await self._extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    async def analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze syllabus structure and extract key components"""
        
        # Simple structure analysis
        lines = content.split('\n')
        
        # Find course information
        course_info = self._extract_course_info(lines)
        
        # Find learning objectives
        objectives = self._extract_learning_objectives(lines)
        
        # Find topics/modules
        topics = self._extract_topics(lines)
        
        # Find assessment methods
        assessments = self._extract_assessments(lines)
        
        # Find schedule/timeline
        schedule = self._extract_schedule(lines)
        
        return {
            "course_info": course_info,
            "learning_objectives": objectives,
            "topics": topics,
            "assessments": assessments,
            "schedule": schedule,
            "total_lines": len(lines),
            "estimated_weeks": self._estimate_course_length(lines)
        }
    
    async def _extract_text_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT file"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            return await file.read()
    
    async def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            raise ImportError("pypdf not available. Install with: pip install pypdf")
        
        def extract_pdf_sync():
            reader = PdfReader(str(file_path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract_pdf_sync)
    
    async def _extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not available. Install with: pip install python-docx")
        
        def extract_docx_sync():
            doc = Document(str(file_path))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract_docx_sync)
    
    def _extract_course_info(self, lines: List[str]) -> Dict[str, str]:
        """Extract basic course information"""
        info = {}
        
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if not line:
                continue
                
            # Look for course title, code, instructor
            if any(keyword in line.lower() for keyword in ['course', 'title']):
                info['title'] = line
            elif any(keyword in line.lower() for keyword in ['instructor', 'professor', 'teacher']):
                info['instructor'] = line
            elif any(keyword in line.lower() for keyword in ['code', 'number']):
                info['code'] = line
        
        return info
    
    def _extract_learning_objectives(self, lines: List[str]) -> List[str]:
        """Extract learning objectives"""
        objectives = []
        in_objectives_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if we're entering objectives section
            if any(keyword in line.lower() for keyword in 
                   ['objective', 'goal', 'outcome', 'learning outcome', 'by the end']):
                in_objectives_section = True
                continue
            
            # Check if we're leaving objectives section
            if in_objectives_section and any(keyword in line.lower() for keyword in 
                                           ['schedule', 'assessment', 'grading', 'textbook']):
                break
            
            # Extract objectives
            if in_objectives_section:
                # Look for numbered or bulleted items
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•', '*')):
                    objectives.append(line)
        
        return objectives
    
    def _extract_topics(self, lines: List[str]) -> List[str]:
        """Extract course topics/modules"""
        topics = []
        in_topics_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if we're entering topics section
            if any(keyword in line.lower() for keyword in 
                   ['topic', 'module', 'week', 'chapter', 'unit', 'lesson']):
                in_topics_section = True
                continue
            
            # Check if we're leaving topics section
            if in_topics_section and any(keyword in line.lower() for keyword in 
                                       ['assessment', 'grading', 'textbook', 'bibliography']):
                break
            
            # Extract topics
            if in_topics_section:
                if line.startswith(('week', 'module', 'chapter', 'unit')) or \
                   line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•', '*')):
                    topics.append(line)
        
        return topics
    
    def _extract_assessments(self, lines: List[str]) -> List[str]:
        """Extract assessment methods"""
        assessments = []
        in_assessment_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if we're entering assessment section
            if any(keyword in line.lower() for keyword in 
                   ['assessment', 'grading', 'evaluation', 'exam', 'quiz', 'assignment']):
                in_assessment_section = True
                assessments.append(line)
                continue
            
            # Check if we're leaving assessment section
            if in_assessment_section and any(keyword in line.lower() for keyword in 
                                           ['textbook', 'bibliography', 'schedule']):
                break
            
            # Extract assessments
            if in_assessment_section and ('%' in line or 'points' in line.lower()):
                assessments.append(line)
        
        return assessments
    
    def _extract_schedule(self, lines: List[str]) -> List[str]:
        """Extract course schedule"""
        schedule = []
        in_schedule_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if we're entering schedule section
            if any(keyword in line.lower() for keyword in 
                   ['schedule', 'calendar', 'timeline', 'dates']):
                in_schedule_section = True
                continue
            
            # Extract schedule items
            if in_schedule_section:
                if any(keyword in line.lower() for keyword in 
                       ['week', 'date', 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                        'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                    schedule.append(line)
        
        return schedule
    
    def _estimate_course_length(self, lines: List[str]) -> int:
        """Estimate course length in weeks"""
        week_mentions = sum(1 for line in lines if 'week' in line.lower())
        return max(12, min(16, week_mentions)) if week_mentions > 0 else 14


class SlidesProcessor:
    """Processes slide files and extracts content"""
    
    def __init__(self):
        self.supported_formats = ['.pptx', '.ppt', '.pdf', '.json']
    
    async def extract_content(self, file_path: str) -> ProcessedContent:
        """Extract content from slide files"""
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.json':
            return await self._process_json_slides(file_path)
        elif file_ext in ['.pptx', '.ppt']:
            return await self._process_powerpoint(file_path)
        elif file_ext == '.pdf':
            return await self._process_pdf_slides(file_path)
        else:
            raise ValueError(f"Unsupported slide format: {file_ext}")
    
    async def _process_json_slides(self, file_path: Path) -> ProcessedContent:
        """Process JSON slide format"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
            data = json.loads(content)
        
        # Extract text from slides
        text_content = ""
        slides_structure = []
        
        if isinstance(data, dict) and 'slides' in data:
            for i, slide in enumerate(data['slides']):
                slide_text = ""
                if 'title' in slide:
                    slide_text += f"Title: {slide['title']}\n"
                if 'content' in slide:
                    slide_text += f"Content: {slide['content']}\n"
                
                text_content += f"Slide {i+1}:\n{slide_text}\n"
                slides_structure.append({
                    'slide_number': i+1,
                    'title': slide.get('title', ''),
                    'content': slide.get('content', ''),
                    'notes': slide.get('notes', '')
                })
        
        return ProcessedContent(
            text=text_content,
            metadata={'format': 'json', 'slide_count': len(slides_structure)},
            structure={'slides': slides_structure}
        )
    
    async def _process_powerpoint(self, file_path: Path) -> ProcessedContent:
        """Process PowerPoint files"""
        if not PPTX_AVAILABLE:
            raise ImportError("python-pptx not available. Install with: pip install python-pptx")
        
        def process_pptx_sync():
            prs = Presentation(str(file_path))
            text_content = ""
            slides_structure = []
            
            for i, slide in enumerate(prs.slides):
                slide_text = ""
                title = ""
                content = ""
                
                # Extract text from shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        if shape.text.strip():
                            if not title and len(shape.text) < 100:
                                title = shape.text.strip()
                            else:
                                content += shape.text.strip() + "\n"
                            slide_text += shape.text + "\n"
                
                text_content += f"Slide {i+1}:\n{slide_text}\n"
                slides_structure.append({
                    'slide_number': i+1,
                    'title': title,
                    'content': content.strip(),
                    'notes': ''
                })
            
            return text_content, slides_structure
        
        loop = asyncio.get_event_loop()
        text_content, slides_structure = await loop.run_in_executor(None, process_pptx_sync)
        
        return ProcessedContent(
            text=text_content,
            metadata={'format': 'powerpoint', 'slide_count': len(slides_structure)},
            structure={'slides': slides_structure}
        )
    
    async def _process_pdf_slides(self, file_path: Path) -> ProcessedContent:
        """Process PDF slide files"""
        if not PDF_AVAILABLE:
            raise ImportError("pypdf not available. Install with: pip install pypdf")
        
        def process_pdf_sync():
            reader = PdfReader(str(file_path))
            text_content = ""
            slides_structure = []
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text_content += f"Slide {i+1}:\n{page_text}\n"
                
                slides_structure.append({
                    'slide_number': i+1,
                    'title': '',  # PDF doesn't have clear title extraction
                    'content': page_text.strip(),
                    'notes': ''
                })
            
            return text_content, slides_structure
        
        loop = asyncio.get_event_loop()
        text_content, slides_structure = await loop.run_in_executor(None, process_pdf_sync)
        
        return ProcessedContent(
            text=text_content,
            metadata={'format': 'pdf', 'slide_count': len(slides_structure)},
            structure={'slides': slides_structure}
        )


class ExportProcessor:
    """Handles content export to various formats"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "course_exports"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def export_slides(self, course_data: Dict[str, Any], format_type: str) -> Path:
        """Export slides to specified format"""
        if format_type == "powerpoint":
            return await self._export_to_powerpoint(course_data)
        elif format_type == "json":
            return await self._export_to_json(course_data, "slides")
        elif format_type == "pdf":
            return await self._export_to_pdf(course_data, "slides")
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def export_exercises(self, course_data: Dict[str, Any], format_type: str) -> Path:
        """Export exercises to specified format"""
        if format_type == "pdf":
            return await self._export_to_pdf(course_data, "exercises")
        elif format_type == "json":
            return await self._export_to_json(course_data, "exercises")
        elif format_type == "excel":
            return await self._export_to_excel(course_data, "exercises")
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def export_quizzes(self, course_data: Dict[str, Any], format_type: str) -> Path:
        """Export quizzes to specified format"""
        if format_type == "pdf":
            return await self._export_to_pdf(course_data, "quizzes")
        elif format_type == "json":
            return await self._export_to_json(course_data, "quizzes")
        elif format_type == "excel":
            return await self._export_to_excel(course_data, "quizzes")
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def export_complete_course(self, course_data: Dict[str, Any], format_type: str) -> Path:
        """Export complete course package"""
        if format_type == "zip":
            return await self._export_complete_zip(course_data)
        elif format_type == "scorm":
            return await self._export_scorm_package(course_data)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def _export_to_powerpoint(self, course_data: Dict[str, Any]) -> Path:
        """Export to PowerPoint format"""
        if not PPTX_AVAILABLE:
            raise ImportError("python-pptx not available. Install with: pip install python-pptx")
        
        def create_pptx_sync():
            from pptx import Presentation
            from pptx.util import Inches
            
            prs = Presentation()
            
            # Title slide
            title_slide = prs.slides.add_slide(prs.slide_layouts[0])
            title_slide.shapes.title.text = course_data.get('title', 'Course Slides')
            
            # Add content slides
            slides = course_data.get('slides', [])
            for slide_data in slides:
                slide = prs.slides.add_slide(prs.slide_layouts[1])
                slide.shapes.title.text = slide_data.get('title', 'Slide Title')
                
                if 'content' in slide_data:
                    content_shape = slide.shapes.placeholders[1]
                    content_shape.text = slide_data['content']
            
            # Save file
            output_path = self.temp_dir / f"slides_{course_data.get('id', 'course')}.pptx"
            prs.save(str(output_path))
            return output_path
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, create_pptx_sync)
    
    async def _export_to_json(self, course_data: Dict[str, Any], content_type: str) -> Path:
        """Export to JSON format"""
        output_path = self.temp_dir / f"{content_type}_{course_data.get('id', 'course')}.json"
        
        export_data = {
            'course_id': course_data.get('id'),
            'course_title': course_data.get('title'),
            'content_type': content_type,
            'data': course_data.get(content_type, []),
            'exported_at': str(asyncio.get_event_loop().time())
        }
        
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(export_data, indent=2))
        
        return output_path
    
    async def _export_to_pdf(self, course_data: Dict[str, Any], content_type: str) -> Path:
        """Export to PDF format (placeholder - would need reportlab)"""
        # This is a placeholder implementation
        # In a real implementation, you'd use reportlab or similar
        output_path = self.temp_dir / f"{content_type}_{course_data.get('id', 'course')}.pdf"
        
        # For now, create a simple text file
        content = f"{course_data.get('title', 'Course Content')}\n\n"
        
        items = course_data.get(content_type, [])
        for i, item in enumerate(items):
            content += f"{i+1}. {item.get('title', 'Item')}\n"
            content += f"{item.get('content', '')}\n\n"
        
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as file:
            await file.write(content)
        
        return output_path
    
    async def _export_to_excel(self, course_data: Dict[str, Any], content_type: str) -> Path:
        """Export to Excel format (placeholder)"""
        # This is a placeholder implementation
        # In a real implementation, you'd use openpyxl or pandas
        output_path = self.temp_dir / f"{content_type}_{course_data.get('id', 'course')}.xlsx"
        
        # For now, create a CSV file
        import csv
        
        def create_csv_sync():
            with open(output_path.with_suffix('.csv'), 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Item', 'Title', 'Content'])
                
                items = course_data.get(content_type, [])
                for i, item in enumerate(items):
                    writer.writerow([
                        i+1,
                        item.get('title', ''),
                        item.get('content', '')
                    ])
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, create_csv_sync)
        
        return output_path.with_suffix('.csv')
    
    async def _export_complete_zip(self, course_data: Dict[str, Any]) -> Path:
        """Export complete course as ZIP"""
        output_path = self.temp_dir / f"complete_course_{course_data.get('id', 'course')}.zip"
        
        def create_zip_sync():
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add course info
                course_info = json.dumps(course_data, indent=2)
                zipf.writestr('course_info.json', course_info)
                
                # Add slides
                if 'slides' in course_data:
                    slides_json = json.dumps(course_data['slides'], indent=2)
                    zipf.writestr('slides.json', slides_json)
                
                # Add exercises
                if 'exercises' in course_data:
                    exercises_json = json.dumps(course_data['exercises'], indent=2)
                    zipf.writestr('exercises.json', exercises_json)
                
                # Add quizzes
                if 'quizzes' in course_data:
                    quizzes_json = json.dumps(course_data['quizzes'], indent=2)
                    zipf.writestr('quizzes.json', quizzes_json)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, create_zip_sync)
        
        return output_path
    
    async def _export_scorm_package(self, course_data: Dict[str, Any]) -> Path:
        """Export as SCORM package (placeholder)"""
        # This would be a complex implementation for SCORM compliance
        # For now, create a basic ZIP with SCORM structure
        output_path = self.temp_dir / f"scorm_course_{course_data.get('id', 'course')}.zip"
        
        def create_scorm_sync():
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # SCORM manifest
                manifest = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="course_manifest" version="1.2">
    <metadata>
        <schema>ADL SCORM</schema>
        <schemaversion>1.2</schemaversion>
    </metadata>
    <organizations default="course_org">
        <organization identifier="course_org">
            <title>''' + course_data.get('title', 'Course') + '''</title>
        </organization>
    </organizations>
    <resources>
    </resources>
</manifest>'''
                zipf.writestr('imsmanifest.xml', manifest)
                
                # Course content
                course_json = json.dumps(course_data, indent=2)
                zipf.writestr('course_content.json', course_json)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, create_scorm_sync)
        
        return output_path