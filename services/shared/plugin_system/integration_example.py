"""
Plugin System Integration Example

BUSINESS CONTEXT:
Shows how the Course Creator Platform services can integrate
with the plugin system to enable extensibility.

This example demonstrates:
1. Initializing the plugin system on platform startup
2. Emitting events from services
3. Using hooks to allow plugins to modify behavior
4. Applying advice to service methods

@module integration_example
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from plugin_system import (
    PluginLoader,
    HookManager,
    EventBus,
    Event,
    Advice,
    PlatformAPI
)


@dataclass
class Course:
    """Example course entity."""
    id: UUID
    title: str
    description: str
    organization_id: UUID
    instructor_id: UUID
    learning_objectives: List[str]


class CourseService:
    """
    Example Course Service with plugin integration.

    BUSINESS VALUE:
    - Core course CRUD operations
    - Extensible via hooks and events
    - Plugin-modifiable behavior
    """

    def __init__(self):
        self.hooks = HookManager.get_instance()
        self.events = EventBus.get_instance()
        self.advice = Advice.get_instance()
        self._courses: Dict[UUID, Course] = {}

    async def create_course(self, data: Dict[str, Any]) -> Course:
        """
        Create a new course.

        Plugins can:
        - Hook into 'before-course-save' to validate/modify
        - Subscribe to 'course.created' event
        - Add advice around this method

        Args:
            data: Course data

        Returns:
            Created course
        """
        # Run before hooks - plugins can validate/modify
        modified_data = self.hooks.run_sync('before-course-save', data)
        if isinstance(modified_data, dict):
            data = modified_data

        # Create the course
        course = Course(
            id=uuid4(),
            title=data['title'],
            description=data.get('description', ''),
            organization_id=UUID(data['organization_id']),
            instructor_id=UUID(data['instructor_id']),
            learning_objectives=data.get('learning_objectives', [])
        )

        self._courses[course.id] = course

        # Run after hooks
        self.hooks.run_sync('after-course-save', course)

        # Emit event for subscribers
        await self.events.publish(Event(
            name='course.created',
            data={
                'course_id': str(course.id),
                'title': course.title,
                'organization_id': str(course.organization_id),
                'instructor_id': str(course.instructor_id)
            },
            source='course-service'
        ))

        return course

    async def get_course(self, course_id: UUID) -> Optional[Course]:
        """Get a course by ID."""
        return self._courses.get(course_id)

    async def update_course(
        self,
        course_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[Course]:
        """Update a course."""
        course = self._courses.get(course_id)
        if not course:
            return None

        # Run before hooks
        modified_data = self.hooks.run_sync('before-course-save', data)
        if isinstance(modified_data, dict):
            data = modified_data

        # Update fields
        if 'title' in data:
            course.title = data['title']
        if 'description' in data:
            course.description = data['description']
        if 'learning_objectives' in data:
            course.learning_objectives = data['learning_objectives']

        # Emit event
        await self.events.publish(Event(
            name='course.updated',
            data={
                'course_id': str(course_id),
                'title': course.title
            },
            source='course-service'
        ))

        return course

    async def delete_course(self, course_id: UUID) -> bool:
        """Delete a course."""
        if course_id not in self._courses:
            return False

        # Run before hooks - can abort deletion
        result = self.hooks.run_sync('before-course-delete', course_id)
        # If any hook returns False, abort
        if result is False:
            return False

        course = self._courses.pop(course_id)

        await self.events.publish(Event(
            name='course.deleted',
            data={'course_id': str(course_id)},
            source='course-service'
        ))

        return True


class QuizService:
    """
    Example Quiz Service with plugin integration.

    BUSINESS VALUE:
    - Quiz submission and grading
    - Custom grading via hooks
    - Event-based notifications
    """

    def __init__(self):
        self.hooks = HookManager.get_instance()
        self.events = EventBus.get_instance()

    async def submit_quiz(
        self,
        quiz_id: UUID,
        user_id: UUID,
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit a quiz attempt.

        Plugins can:
        - Hook into 'before-quiz-submit' to validate
        - Use 'quiz-grade' hook for custom grading
        - Subscribe to 'quiz.submitted' event

        Args:
            quiz_id: Quiz ID
            user_id: User submitting
            answers: User's answers

        Returns:
            Submission result with score
        """
        # Run before hooks
        self.hooks.run_sync('before-quiz-submit', {
            'quiz_id': quiz_id,
            'user_id': user_id,
            'answers': answers
        })

        # Calculate score (simplified)
        score = self._calculate_score(answers)

        # Allow custom grading hooks
        custom_score = self.hooks.run_sync('quiz-grade', {
            'quiz_id': quiz_id,
            'answers': answers,
            'calculated_score': score
        })

        if isinstance(custom_score, (int, float)):
            score = custom_score

        result = {
            'quiz_id': str(quiz_id),
            'user_id': str(user_id),
            'score': score,
            'passed': score >= 70
        }

        # Emit submission event
        await self.events.publish(Event(
            name='quiz.submitted',
            data=result,
            source='quiz-service'
        ))

        return result

    def _calculate_score(self, answers: Dict[str, Any]) -> float:
        """Calculate quiz score (simplified)."""
        # Real implementation would compare to correct answers
        return 85.0


class PlatformInitializer:
    """
    Initializes the plugin system for the platform.

    Call this during platform startup.
    """

    def __init__(self, plugin_directories: List[str]):
        self.plugin_dirs = plugin_directories
        self.loader = PluginLoader(plugin_directories)

    def initialize(self) -> None:
        """
        Initialize the plugin system.

        1. Discover all plugins
        2. Load plugins (check dependencies)
        3. Activate plugins (call activate functions)
        4. Register standard hooks
        """
        # Register standard platform hooks
        self._register_standard_hooks()

        # Discover plugins
        plugins = self.loader.discover_all()
        print(f"Discovered {len(plugins)} plugins")

        # Load all plugins
        load_results = self.loader.load_all()
        loaded = sum(1 for v in load_results.values() if v)
        print(f"Loaded {loaded}/{len(load_results)} plugins")

        # Create Platform API for plugins
        # In real implementation, would pass proper API instance
        # self.loader.set_api(platform_api)

        # Activate plugins
        activate_results = self.loader.activate_all()
        activated = sum(1 for v in activate_results.values() if v)
        print(f"Activated {activated}/{len(activate_results)} plugins")

    def shutdown(self) -> None:
        """Shutdown the plugin system gracefully."""
        self.loader.deactivate_all()
        print("All plugins deactivated")

    def _register_standard_hooks(self) -> None:
        """Register platform's standard hooks."""
        hooks = HookManager.get_instance()

        # Course hooks
        hooks.get_or_create('before-course-save')
        hooks.get_or_create('after-course-save')
        hooks.get_or_create('before-course-delete')

        # Quiz hooks
        hooks.get_or_create('before-quiz-submit')
        hooks.get_or_create('after-quiz-submit')
        hooks.get_or_create('quiz-grade')

        # Content hooks
        hooks.get_or_create('before-content-publish')
        hooks.get_or_create('after-content-generate')
        hooks.get_or_create('content-transform')

        print("Standard hooks registered")


async def demo() -> None:
    """
    Demonstrate the plugin system integration.

    Shows how services use hooks and events.
    """
    print("=" * 60)
    print("Plugin System Integration Demo")
    print("=" * 60)

    # Initialize the plugin system
    initializer = PlatformInitializer(['/path/to/plugins'])

    # Register some example hooks/events manually for demo
    hooks = HookManager.get_instance()
    events = EventBus.get_instance()

    # Example plugin hook - validate course titles
    @hooks['before-course-save'].add
    def validate_title(data):
        if data.get('title') and len(data['title']) < 5:
            raise ValueError("Course title must be at least 5 characters")
        return data

    # Example plugin event handler
    @events.subscribe('course.created')
    async def log_course_creation(event):
        print(f"  [Event Handler] Course created: {event.data['title']}")

    # Create services
    course_service = CourseService()

    print("\n1. Creating a course...")
    try:
        course = await course_service.create_course({
            'title': 'Python Programming 101',
            'description': 'Learn Python from scratch',
            'organization_id': str(uuid4()),
            'instructor_id': str(uuid4()),
            'learning_objectives': ['Learn basics', 'Build projects']
        })
        print(f"   Created course: {course.title} (ID: {course.id})")
    except ValueError as e:
        print(f"   Validation error: {e}")

    print("\n2. Attempting to create course with short title...")
    try:
        course = await course_service.create_course({
            'title': 'Py',  # Too short - hook will reject
            'description': 'Short title test',
            'organization_id': str(uuid4()),
            'instructor_id': str(uuid4())
        })
    except ValueError as e:
        print(f"   Validation error (expected): {e}")

    print("\n3. Quiz submission with event...")
    quiz_service = QuizService()

    @events.subscribe('quiz.submitted')
    async def notify_instructor(event):
        print(f"  [Event Handler] Quiz submitted with score: {event.data['score']}%")

    result = await quiz_service.submit_quiz(
        quiz_id=uuid4(),
        user_id=uuid4(),
        answers={'q1': 'a', 'q2': 'b'}
    )
    print(f"   Quiz result: {result['score']}% - {'Passed' if result['passed'] else 'Failed'}")

    # Wait for async event processing
    await asyncio.sleep(0.2)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(demo())
