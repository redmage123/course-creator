"""
Advice System - Function Wrapping (Before/After/Around)

BUSINESS CONTEXT:
Provides Emacs-style advice for wrapping existing functions.
Enables plugins to modify behavior of core platform functions.

DESIGN PHILOSOPHY:
Like Emacs defadvice, allows plugins to:
- Run code BEFORE a function (modify args)
- Run code AFTER a function (modify return value)
- Run code AROUND a function (full control)

EXAMPLE USAGE:
    # Before advice - runs before original function
    @before_advice('course_service.create_course')
    def validate_course_name(course_data):
        if len(course_data['name']) < 5:
            raise ValueError("Course name must be at least 5 characters")

    # After advice - runs after original, can modify return value
    @after_advice('course_service.create_course')
    def add_default_settings(result, course_data):
        result.settings = get_default_settings()
        return result

    # Around advice - wraps original function
    @around_advice('quiz_service.submit_quiz')
    def log_quiz_submission(original_func, *args, **kwargs):
        logger.info("Quiz submission starting")
        result = original_func(*args, **kwargs)
        logger.info(f"Quiz submitted: {result.id}")
        return result

@module advice
"""

import asyncio
import functools
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class AdviceType(Enum):
    """Types of advice that can be applied."""
    BEFORE = "before"
    AFTER = "after"
    AROUND = "around"


@dataclass
class AdviceRecord:
    """
    Record of advice applied to a function.

    Attributes:
        advice_type: Type of advice (before/after/around)
        func: The advice function
        priority: Execution order (lower = earlier)
        name: Optional name for debugging
        plugin_id: Plugin that registered this advice
        enabled: Whether this advice is active
    """
    advice_type: AdviceType
    func: Callable
    priority: int = 50
    name: Optional[str] = None
    plugin_id: Optional[str] = None
    enabled: bool = True

    def __post_init__(self):
        if self.name is None:
            self.name = getattr(self.func, '__name__', str(self.func))


class Advice:
    """
    Central manager for function advice.

    BUSINESS VALUE:
    - Allows plugins to modify core behavior without changing source
    - Provides clean separation between core and extensions
    - Enables reversible modifications (can remove advice)
    - Supports priority ordering for advice execution

    EMACS PARALLEL:
    Similar to Emacs defadvice system where you can wrap any
    function with before/after/around advice.

    Example:
        advice = Advice.get_instance()

        # Add before advice
        advice.add_before(
            'course_service.create_course',
            validate_course,
            priority=10,
            plugin_id='my-plugin'
        )

        # Apply advice to a function
        create_course = advice.apply('course_service.create_course', original_create_course)
    """

    _instance: Optional['Advice'] = None
    _lock = threading.Lock()

    def __init__(self):
        # Map of function_name -> list of advice records
        self._advice: Dict[str, List[AdviceRecord]] = {}
        self._advice_lock = threading.RLock()
        # Map of function_name -> original function (before advice)
        self._originals: Dict[str, Callable] = {}

    @classmethod
    def get_instance(cls) -> 'Advice':
        """Get the singleton Advice instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def add_before(
        self,
        function_name: str,
        advice_func: Callable,
        priority: int = 50,
        name: Optional[str] = None,
        plugin_id: Optional[str] = None
    ) -> AdviceRecord:
        """
        Add before advice to a function.

        Before advice runs BEFORE the original function.
        It receives the same arguments and can modify them.
        Raise an exception to prevent the original from running.

        Args:
            function_name: Dotted path to function (e.g., 'module.func')
            advice_func: Function to run before
            priority: Execution order (lower = earlier)
            name: Optional name for debugging
            plugin_id: Plugin identifier

        Returns:
            The advice record

        Example:
            def check_permissions(user, course_id):
                if not user.can_create_course():
                    raise PermissionError("Cannot create course")

            advice.add_before('course_service.create', check_permissions)
        """
        return self._add_advice(
            function_name, advice_func, AdviceType.BEFORE,
            priority, name, plugin_id
        )

    def add_after(
        self,
        function_name: str,
        advice_func: Callable,
        priority: int = 50,
        name: Optional[str] = None,
        plugin_id: Optional[str] = None
    ) -> AdviceRecord:
        """
        Add after advice to a function.

        After advice runs AFTER the original function.
        It receives the original return value as first argument,
        followed by the original arguments.
        It should return a value (modified or original).

        Args:
            function_name: Dotted path to function
            advice_func: Function to run after
            priority: Execution order (lower = earlier)
            name: Optional name for debugging
            plugin_id: Plugin identifier

        Returns:
            The advice record

        Example:
            def add_metadata(result, user, course_id):
                result.created_by = user.id
                return result

            advice.add_after('course_service.create', add_metadata)
        """
        return self._add_advice(
            function_name, advice_func, AdviceType.AFTER,
            priority, name, plugin_id
        )

    def add_around(
        self,
        function_name: str,
        advice_func: Callable,
        priority: int = 50,
        name: Optional[str] = None,
        plugin_id: Optional[str] = None
    ) -> AdviceRecord:
        """
        Add around advice to a function.

        Around advice wraps the original function.
        It receives the original function as first argument,
        followed by all original arguments.
        It is responsible for calling the original (or not).

        Args:
            function_name: Dotted path to function
            advice_func: Function to wrap around
            priority: Execution order (lower = earlier)
            name: Optional name for debugging
            plugin_id: Plugin identifier

        Returns:
            The advice record

        Example:
            def with_timing(original_func, *args, **kwargs):
                start = time.time()
                result = original_func(*args, **kwargs)
                elapsed = time.time() - start
                logger.info(f"Elapsed: {elapsed}s")
                return result

            advice.add_around('course_service.create', with_timing)
        """
        return self._add_advice(
            function_name, advice_func, AdviceType.AROUND,
            priority, name, plugin_id
        )

    def _add_advice(
        self,
        function_name: str,
        advice_func: Callable,
        advice_type: AdviceType,
        priority: int,
        name: Optional[str],
        plugin_id: Optional[str]
    ) -> AdviceRecord:
        """Internal method to add advice."""
        record = AdviceRecord(
            advice_type=advice_type,
            func=advice_func,
            priority=priority,
            name=name,
            plugin_id=plugin_id,
            enabled=True
        )

        with self._advice_lock:
            if function_name not in self._advice:
                self._advice[function_name] = []
            self._advice[function_name].append(record)
            # Sort by type (before, around, after) then priority
            self._advice[function_name].sort(
                key=lambda r: (r.advice_type.value, r.priority)
            )

        logger.debug(
            f"Added {advice_type.value} advice '{record.name}' to {function_name}"
        )
        return record

    def remove_advice(
        self,
        function_name: str,
        advice_func: Callable
    ) -> bool:
        """
        Remove specific advice from a function.

        Args:
            function_name: Function the advice was applied to
            advice_func: The advice function to remove

        Returns:
            True if found and removed
        """
        with self._advice_lock:
            if function_name not in self._advice:
                return False

            original_len = len(self._advice[function_name])
            self._advice[function_name] = [
                r for r in self._advice[function_name]
                if r.func != advice_func
            ]
            return len(self._advice[function_name]) < original_len

    def remove_plugin_advice(self, plugin_id: str) -> Dict[str, int]:
        """
        Remove all advice registered by a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Dict of function_name -> count removed
        """
        removed = {}
        with self._advice_lock:
            for function_name in list(self._advice.keys()):
                original_len = len(self._advice[function_name])
                self._advice[function_name] = [
                    r for r in self._advice[function_name]
                    if r.plugin_id != plugin_id
                ]
                count = original_len - len(self._advice[function_name])
                if count > 0:
                    removed[function_name] = count

        return removed

    def get_advice(
        self,
        function_name: str
    ) -> List[AdviceRecord]:
        """
        Get all advice for a function.

        Args:
            function_name: Function to query

        Returns:
            List of advice records
        """
        with self._advice_lock:
            return list(self._advice.get(function_name, []))

    def apply(
        self,
        function_name: str,
        original_func: Callable
    ) -> Callable:
        """
        Apply all advice to a function, returning wrapped version.

        Args:
            function_name: Identifier for the function
            original_func: The original function to wrap

        Returns:
            Wrapped function with all advice applied
        """
        # Store original
        self._originals[function_name] = original_func

        # Get advice records
        advice_records = self.get_advice(function_name)
        if not advice_records:
            return original_func

        # Separate by type
        before_advice = [r for r in advice_records if r.advice_type == AdviceType.BEFORE and r.enabled]
        after_advice = [r for r in advice_records if r.advice_type == AdviceType.AFTER and r.enabled]
        around_advice = [r for r in advice_records if r.advice_type == AdviceType.AROUND and r.enabled]

        is_async = asyncio.iscoroutinefunction(original_func)

        if is_async:
            @functools.wraps(original_func)
            async def async_wrapped(*args, **kwargs):
                # Run before advice
                for record in before_advice:
                    if asyncio.iscoroutinefunction(record.func):
                        await record.func(*args, **kwargs)
                    else:
                        record.func(*args, **kwargs)

                # Build the around chain
                async def call_original(*a, **kw):
                    return await original_func(*a, **kw)

                current = call_original
                for record in reversed(around_advice):
                    prev = current
                    if asyncio.iscoroutinefunction(record.func):
                        async def make_around(adv, p):
                            async def around_call(*a, **kw):
                                return await adv(p, *a, **kw)
                            return around_call
                        current = await make_around(record.func, prev)
                    else:
                        def make_around_sync(adv, p):
                            def around_call(*a, **kw):
                                return adv(p, *a, **kw)
                            return around_call
                        current = make_around_sync(record.func, prev)

                # Call the chain
                result = await current(*args, **kwargs)

                # Run after advice
                for record in after_advice:
                    if asyncio.iscoroutinefunction(record.func):
                        result = await record.func(result, *args, **kwargs)
                    else:
                        result = record.func(result, *args, **kwargs)

                return result

            return async_wrapped
        else:
            @functools.wraps(original_func)
            def sync_wrapped(*args, **kwargs):
                # Run before advice
                for record in before_advice:
                    record.func(*args, **kwargs)

                # Build the around chain
                current = original_func
                for record in reversed(around_advice):
                    prev = current
                    current = lambda *a, adv=record.func, p=prev, **kw: adv(p, *a, **kw)

                # Call the chain
                result = current(*args, **kwargs)

                # Run after advice
                for record in after_advice:
                    result = record.func(result, *args, **kwargs)

                return result

            return sync_wrapped

    def get_original(self, function_name: str) -> Optional[Callable]:
        """Get the original unwrapped function."""
        return self._originals.get(function_name)


# Convenience decorators
def before_advice(
    function_name: str,
    priority: int = 50,
    plugin_id: Optional[str] = None
):
    """
    Decorator to add before advice.

    Example:
        @before_advice('course_service.create')
        def validate(course_data):
            if not course_data.get('name'):
                raise ValueError("Name required")
    """
    def decorator(func: Callable) -> Callable:
        Advice.get_instance().add_before(
            function_name, func, priority=priority, plugin_id=plugin_id
        )
        return func
    return decorator


def after_advice(
    function_name: str,
    priority: int = 50,
    plugin_id: Optional[str] = None
):
    """
    Decorator to add after advice.

    Example:
        @after_advice('course_service.create')
        def add_timestamp(result, course_data):
            result.created_at = datetime.now()
            return result
    """
    def decorator(func: Callable) -> Callable:
        Advice.get_instance().add_after(
            function_name, func, priority=priority, plugin_id=plugin_id
        )
        return func
    return decorator


def around_advice(
    function_name: str,
    priority: int = 50,
    plugin_id: Optional[str] = None
):
    """
    Decorator to add around advice.

    Example:
        @around_advice('course_service.create')
        def with_transaction(original, course_data):
            with db.transaction():
                return original(course_data)
    """
    def decorator(func: Callable) -> Callable:
        Advice.get_instance().add_around(
            function_name, func, priority=priority, plugin_id=plugin_id
        )
        return func
    return decorator
