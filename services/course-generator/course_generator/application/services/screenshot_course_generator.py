"""
Screenshot Course Generator Service

BUSINESS PURPOSE:
Takes analyzed screenshot content and generates complete course structures
including modules, lessons, quizzes, and exercises. Integrates with the
course management service to create actual courses in the system.

TECHNICAL IMPLEMENTATION:
- Uses analysis results from ScreenshotAnalysisService
- Generates additional content using LLM text generation
- Creates course structure via course management API
- Supports customization and enhancement options

WHY:
This service completes the screenshot-to-course pipeline by transforming
extracted content into fully-fledged courses with all necessary components
for effective learning.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from course_generator.domain.entities.screenshot_analysis import (
    AnalysisResult,
    CourseModule,
    CourseStructure,
    DifficultyLevel,
    ScreenshotUpload,
    UploadStatus
)
from course_generator.infrastructure.llm_providers import (
    get_provider_for_organization,
    LLMResponse
)
from shared.exceptions import (
    CourseGenerationException,
    LLMProviderException
)


logger = logging.getLogger(__name__)


@dataclass
class LessonContent:
    """
    Generated content for a lesson

    BUSINESS CONTEXT:
    Represents the complete content for a single lesson
    within a module.
    """
    title: str
    description: str
    order: int
    content_html: str = ""
    learning_objectives: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    estimated_duration_minutes: int = 15
    has_quiz: bool = False
    has_exercise: bool = False


@dataclass
class ModuleContent:
    """
    Generated content for a module

    BUSINESS CONTEXT:
    Represents a complete module with all its lessons.
    """
    title: str
    description: str
    order: int
    lessons: List[LessonContent] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    estimated_duration_minutes: int = 0


@dataclass
class GeneratedCourse:
    """
    Complete generated course structure

    BUSINESS CONTEXT:
    The final output of the course generation process,
    ready to be created in the course management system.
    """
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    modules: List[ModuleContent] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    target_audience: str = ""
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    estimated_duration_hours: int = 0
    language: str = "en"
    source_screenshot_id: Optional[UUID] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API"""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "modules": [
                {
                    "title": m.title,
                    "description": m.description,
                    "order": m.order,
                    "estimated_duration_minutes": m.estimated_duration_minutes,
                    "learning_objectives": m.learning_objectives,
                    "lessons": [
                        {
                            "title": l.title,
                            "description": l.description,
                            "order": l.order,
                            "content_html": l.content_html,
                            "estimated_duration_minutes": l.estimated_duration_minutes,
                            "has_quiz": l.has_quiz,
                            "has_exercise": l.has_exercise
                        }
                        for l in m.lessons
                    ]
                }
                for m in self.modules
            ],
            "topics": self.topics,
            "learning_objectives": self.learning_objectives,
            "prerequisites": self.prerequisites,
            "target_audience": self.target_audience,
            "difficulty": self.difficulty.value,
            "estimated_duration_hours": self.estimated_duration_hours,
            "language": self.language,
            "source_screenshot_id": str(self.source_screenshot_id) if self.source_screenshot_id else None,
            "generated_at": self.generated_at.isoformat()
        }


@dataclass
class GenerationOptions:
    """
    Options for course generation

    BUSINESS CONTEXT:
    Allows customization of the generation process.
    """
    generate_lesson_content: bool = True
    generate_quizzes: bool = True
    generate_exercises: bool = True
    expand_modules: bool = True
    min_lessons_per_module: int = 3
    max_lessons_per_module: int = 10
    target_lesson_duration_minutes: int = 15
    include_code_examples: bool = True
    include_practical_exercises: bool = True
    quiz_questions_per_lesson: int = 5


class ScreenshotCourseGenerator:
    """
    Service for generating courses from screenshot analysis

    BUSINESS PURPOSE:
    Transforms screenshot analysis results into complete courses:
    - Expands module structures with detailed lessons
    - Generates lesson content using LLM
    - Creates quizzes and exercises
    - Produces publication-ready course structures

    USAGE:
    ```python
    generator = ScreenshotCourseGenerator()

    # Generate course from analysis
    course = await generator.generate_course(
        analysis=analysis_result,
        organization_id=org_id,
        options=GenerationOptions(
            generate_quizzes=True,
            expand_modules=True
        )
    )

    # Generate from screenshot upload
    course = await generator.generate_from_upload(
        upload=screenshot_upload,
        options=options
    )
    ```
    """

    def __init__(self):
        """Initialize the course generator"""
        self._generation_cache: Dict[str, GeneratedCourse] = {}

    async def generate_course(
        self,
        analysis: AnalysisResult,
        organization_id: UUID,
        user_id: Optional[UUID] = None,
        options: Optional[GenerationOptions] = None
    ) -> GeneratedCourse:
        """
        Generate a complete course from analysis result

        BUSINESS FLOW:
        1. Extract base structure from analysis
        2. Expand modules with lessons (if enabled)
        3. Generate lesson content (if enabled)
        4. Add quizzes and exercises (if enabled)
        5. Return complete course structure

        Args:
            analysis: Screenshot analysis result
            organization_id: Organization ID
            user_id: User ID for tracking
            options: Generation options

        Returns:
            GeneratedCourse ready for creation

        Raises:
            CourseGenerationException: If generation fails
        """
        options = options or GenerationOptions()

        logger.info(
            f"Generating course from analysis {analysis.id} "
            f"for org {organization_id}"
        )

        try:
            # Start with base structure from analysis
            if not analysis.course_structure:
                raise CourseGenerationException(
                    "Analysis does not contain course structure"
                )

            base_structure = analysis.course_structure

            # Create initial course
            course = GeneratedCourse(
                title=base_structure.title,
                description=base_structure.description,
                topics=base_structure.topics,
                learning_objectives=base_structure.learning_objectives,
                prerequisites=base_structure.prerequisites,
                difficulty=base_structure.difficulty,
                estimated_duration_hours=base_structure.estimated_duration_hours,
                language=base_structure.language,
                source_screenshot_id=analysis.screenshot_id
            )

            # Get LLM provider for content generation
            provider = None
            if options.expand_modules or options.generate_lesson_content:
                provider = await get_provider_for_organization(
                    organization_id=organization_id,
                    require_vision=False
                )

            # Expand modules with lessons
            if options.expand_modules and base_structure.modules:
                course.modules = await self._expand_modules(
                    base_modules=base_structure.modules,
                    course_context=base_structure,
                    provider=provider,
                    options=options
                )
            else:
                # Use modules as-is
                course.modules = [
                    ModuleContent(
                        title=m.title,
                        description=m.description,
                        order=m.order,
                        learning_objectives=m.learning_objectives,
                        estimated_duration_minutes=m.estimated_duration_minutes
                    )
                    for m in base_structure.modules
                ]

            # Generate lesson content
            if options.generate_lesson_content and provider:
                await self._generate_lesson_content(
                    course=course,
                    provider=provider,
                    options=options
                )

            # Calculate total duration
            total_minutes = sum(
                sum(l.estimated_duration_minutes for l in m.lessons)
                for m in course.modules
            )
            course.estimated_duration_hours = max(1, total_minutes // 60)

            # Close provider
            if provider:
                await provider.close()

            logger.info(
                f"Generated course '{course.title}' with "
                f"{len(course.modules)} modules"
            )

            return course

        except LLMProviderException as e:
            raise CourseGenerationException(
                f"LLM provider error during generation: {e}"
            ) from e
        except Exception as e:
            logger.exception("Unexpected error during course generation")
            raise CourseGenerationException(
                f"Course generation failed: {e}"
            ) from e

    async def generate_from_upload(
        self,
        upload: ScreenshotUpload,
        options: Optional[GenerationOptions] = None
    ) -> GeneratedCourse:
        """
        Generate course directly from screenshot upload

        Args:
            upload: Screenshot upload with analysis
            options: Generation options

        Returns:
            GeneratedCourse

        Raises:
            CourseGenerationException: If upload not analyzed
        """
        if not upload.analysis_result:
            raise CourseGenerationException(
                "Screenshot upload has not been analyzed"
            )

        if upload.status != UploadStatus.ANALYZED:
            raise CourseGenerationException(
                f"Upload status is {upload.status.value}, expected ANALYZED"
            )

        upload.mark_generating()

        try:
            course = await self.generate_course(
                analysis=upload.analysis_result,
                organization_id=upload.organization_id,
                user_id=upload.user_id,
                options=options
            )

            # Update upload with generated course ID
            upload.mark_completed(course.id)

            return course

        except Exception as e:
            upload.mark_failed(str(e))
            raise

    async def _expand_modules(
        self,
        base_modules: List[CourseModule],
        course_context: CourseStructure,
        provider,
        options: GenerationOptions
    ) -> List[ModuleContent]:
        """
        Expand base modules with detailed lessons

        Args:
            base_modules: Modules from analysis
            course_context: Full course structure for context
            provider: LLM provider
            options: Generation options

        Returns:
            List of expanded ModuleContent
        """
        expanded_modules = []

        for module in base_modules:
            # Generate lessons for this module
            lessons = await self._generate_module_lessons(
                module=module,
                course_context=course_context,
                provider=provider,
                options=options
            )

            expanded_module = ModuleContent(
                title=module.title,
                description=module.description,
                order=module.order,
                lessons=lessons,
                learning_objectives=module.learning_objectives,
                estimated_duration_minutes=sum(
                    l.estimated_duration_minutes for l in lessons
                )
            )

            expanded_modules.append(expanded_module)

        return expanded_modules

    async def _generate_module_lessons(
        self,
        module: CourseModule,
        course_context: CourseStructure,
        provider,
        options: GenerationOptions
    ) -> List[LessonContent]:
        """
        Generate lessons for a module

        Args:
            module: Module to generate lessons for
            course_context: Course structure for context
            provider: LLM provider
            options: Generation options

        Returns:
            List of LessonContent
        """
        # If module already has lessons, use them
        if module.lessons:
            return [
                LessonContent(
                    title=lesson_title,
                    description=f"Lesson on {lesson_title}",
                    order=i + 1,
                    estimated_duration_minutes=options.target_lesson_duration_minutes
                )
                for i, lesson_title in enumerate(module.lessons)
            ]

        # Generate lessons using LLM
        prompt = self._get_lesson_generation_prompt(
            module=module,
            course_context=course_context,
            options=options
        )

        response: LLMResponse = await provider.generate_text(
            prompt=prompt,
            system_prompt=self._get_system_prompt(),
            json_mode=True,
            temperature=0.7
        )

        # Parse response
        import json
        try:
            data = json.loads(response.content)
            lessons_data = data.get("lessons", [])

            return [
                LessonContent(
                    title=l.get("title", f"Lesson {i+1}"),
                    description=l.get("description", ""),
                    order=i + 1,
                    learning_objectives=l.get("learning_objectives", []),
                    key_concepts=l.get("key_concepts", []),
                    estimated_duration_minutes=l.get(
                        "duration_minutes",
                        options.target_lesson_duration_minutes
                    ),
                    has_quiz=options.generate_quizzes,
                    has_exercise=options.generate_exercises
                )
                for i, l in enumerate(lessons_data)
            ]
        except json.JSONDecodeError:
            # Fallback to basic lessons
            return [
                LessonContent(
                    title=f"Introduction to {module.title}",
                    description=f"Learn the basics of {module.title}",
                    order=1,
                    estimated_duration_minutes=options.target_lesson_duration_minutes
                ),
                LessonContent(
                    title=f"{module.title} in Practice",
                    description=f"Apply {module.title} concepts",
                    order=2,
                    estimated_duration_minutes=options.target_lesson_duration_minutes
                ),
                LessonContent(
                    title=f"Advanced {module.title}",
                    description=f"Explore advanced topics in {module.title}",
                    order=3,
                    estimated_duration_minutes=options.target_lesson_duration_minutes
                )
            ]

    async def _generate_lesson_content(
        self,
        course: GeneratedCourse,
        provider,
        options: GenerationOptions
    ):
        """
        Generate actual content for all lessons

        Args:
            course: Course with modules and lessons
            provider: LLM provider
            options: Generation options
        """
        for module in course.modules:
            for lesson in module.lessons:
                if not lesson.content_html:
                    content = await self._generate_single_lesson_content(
                        lesson=lesson,
                        module=module,
                        course=course,
                        provider=provider,
                        options=options
                    )
                    lesson.content_html = content

    async def _generate_single_lesson_content(
        self,
        lesson: LessonContent,
        module: ModuleContent,
        course: GeneratedCourse,
        provider,
        options: GenerationOptions
    ) -> str:
        """
        Generate content for a single lesson

        Args:
            lesson: Lesson to generate content for
            module: Parent module
            course: Parent course
            provider: LLM provider
            options: Generation options

        Returns:
            HTML content for the lesson
        """
        prompt = f"""Generate educational content for this lesson:

Course: {course.title}
Module: {module.title}
Lesson: {lesson.title}
Description: {lesson.description}
Target Duration: {lesson.estimated_duration_minutes} minutes
Difficulty: {course.difficulty.value}

Learning Objectives for this lesson:
{chr(10).join(f'- {obj}' for obj in lesson.learning_objectives) if lesson.learning_objectives else '- Understand the key concepts'}

Generate well-structured educational content that:
1. Introduces the topic clearly
2. Explains concepts progressively
3. Includes relevant examples
{"4. Includes code examples where appropriate" if options.include_code_examples else ""}
{"5. Suggests practical exercises" if options.include_practical_exercises else ""}

Format the output as HTML with appropriate headings, paragraphs, lists, and code blocks."""

        response = await provider.generate_text(
            prompt=prompt,
            system_prompt="You are an expert educational content creator. Generate clear, engaging, and well-structured lesson content.",
            temperature=0.7
        )

        return response.content

    def _get_lesson_generation_prompt(
        self,
        module: CourseModule,
        course_context: CourseStructure,
        options: GenerationOptions
    ) -> str:
        """Get prompt for lesson generation"""
        return f"""Generate a list of lessons for this module:

Course Title: {course_context.title}
Course Description: {course_context.description}
Course Difficulty: {course_context.difficulty.value}

Module Title: {module.title}
Module Description: {module.description}
Module Learning Objectives:
{chr(10).join(f'- {obj}' for obj in module.learning_objectives) if module.learning_objectives else '- Cover the module topic thoroughly'}

Requirements:
- Generate {options.min_lessons_per_module} to {options.max_lessons_per_module} lessons
- Each lesson should be approximately {options.target_lesson_duration_minutes} minutes
- Progress from basic to advanced within the module
- Include practical application opportunities

Return a JSON object with this structure:
{{
    "lessons": [
        {{
            "title": "Lesson title",
            "description": "Brief description",
            "learning_objectives": ["Objective 1", "Objective 2"],
            "key_concepts": ["Concept 1", "Concept 2"],
            "duration_minutes": 15
        }}
    ]
}}"""

    def _get_system_prompt(self) -> str:
        """Get system prompt for course generation"""
        return """You are an expert instructional designer and curriculum developer.
Your task is to create well-structured educational content that:
- Follows pedagogical best practices
- Progresses logically from simple to complex
- Includes clear learning objectives
- Engages learners with practical examples
- Accommodates different learning styles

Always respond with valid JSON when requested."""

    async def enhance_course(
        self,
        course: GeneratedCourse,
        organization_id: UUID,
        enhancement_type: str = "all"
    ) -> GeneratedCourse:
        """
        Enhance an existing generated course

        Args:
            course: Course to enhance
            organization_id: Organization ID
            enhancement_type: Type of enhancement (quizzes, exercises, content, all)

        Returns:
            Enhanced GeneratedCourse
        """
        provider = await get_provider_for_organization(
            organization_id=organization_id,
            require_vision=False
        )

        try:
            if enhancement_type in ("content", "all"):
                await self._generate_lesson_content(
                    course=course,
                    provider=provider,
                    options=GenerationOptions()
                )

            # Additional enhancements would go here
            # - Quiz generation
            # - Exercise generation
            # - Resource suggestions

            return course

        finally:
            await provider.close()
