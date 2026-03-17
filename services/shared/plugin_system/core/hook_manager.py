"""
Hook Manager - Emacs-style Hook System

BUSINESS CONTEXT:
Provides named extension points (hooks) that plugins can attach functions to.
Similar to Emacs hooks, allowing multiple functions to run at specific points.

DESIGN PHILOSOPHY:
- Hooks are named extension points (like Emacs: before-save-hook, after-load-hook)
- Multiple functions can be attached to each hook
- Functions run in order of priority (lower = earlier)
- Hooks can be normal (run all) or abnormal (stop on first truthy return)
- Thread-safe for concurrent access

EXAMPLE USAGE:
    # Define a hook
    course_created_hook = Hook('course-created')

    # Add functions to hook
    @course_created_hook.add
    def notify_admin(course):
        send_notification(f"New course: {course.name}")

    @course_created_hook.add(priority=100)
    def log_creation(course):
        logger.info(f"Course created: {course.id}")

    # Run hook
    course_created_hook.run(course)

@module hook_manager
"""

import asyncio
import functools
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Union
from enum import Enum

logger = logging.getLogger(__name__)


class HookType(Enum):
    """
    Types of hooks available.

    NORMAL: All functions run, results collected
    ABNORMAL: Stop on first truthy return value
    FILTER: Each function transforms the value (like Emacs filter hooks)
    """
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    FILTER = "filter"


@dataclass
class HookFunction:
    """
    A function registered to a hook.

    Attributes:
        func: The callable function
        priority: Execution order (lower = earlier, default 50)
        name: Optional name for debugging
        plugin_id: Plugin that registered this function
        enabled: Whether this function is currently active
    """
    func: Callable
    priority: int = 50
    name: Optional[str] = None
    plugin_id: Optional[str] = None
    enabled: bool = True

    def __post_init__(self):
        if self.name is None:
            self.name = getattr(self.func, '__name__', str(self.func))


class Hook:
    """
    A named extension point that functions can attach to.

    BUSINESS VALUE:
    - Enables plugins to extend platform behavior
    - Provides clear, named extension points
    - Supports both sync and async functions
    - Thread-safe for concurrent access

    EMACS PARALLEL:
    Similar to Emacs hooks like `before-save-hook`, `after-load-hook`, etc.
    Functions are added to hooks and run when the hook is triggered.

    Example:
        # Create a hook for course creation
        on_course_created = Hook('on-course-created', hook_type=HookType.NORMAL)

        # Add a function
        @on_course_created.add(priority=10)
        def validate_course(course):
            if not course.name:
                raise ValueError("Course must have a name")

        # Run the hook
        on_course_created.run(new_course)
    """

    def __init__(
        self,
        name: str,
        hook_type: HookType = HookType.NORMAL,
        docstring: Optional[str] = None
    ):
        """
        Initialize a hook.

        Args:
            name: Unique identifier for this hook (e.g., 'before-course-save')
            hook_type: Type of hook behavior
            docstring: Description of when this hook runs and what it's for
        """
        self.name = name
        self.hook_type = hook_type
        self.docstring = docstring or f"Hook: {name}"
        self._functions: List[HookFunction] = []
        self._lock = threading.RLock()

    def add(
        self,
        func: Optional[Callable] = None,
        *,
        priority: int = 50,
        name: Optional[str] = None,
        plugin_id: Optional[str] = None
    ) -> Union[Callable, Callable[[Callable], Callable]]:
        """
        Add a function to this hook.

        Can be used as a decorator or called directly.

        Args:
            func: Function to add (optional, for decorator use)
            priority: Execution order (lower = earlier)
            name: Optional name for debugging
            plugin_id: Plugin that registered this

        Returns:
            The function (for decorator chaining)

        Example:
            # As decorator
            @my_hook.add(priority=10)
            def my_handler(data):
                pass

            # Direct call
            my_hook.add(my_handler, priority=10)
        """
        def decorator(fn: Callable) -> Callable:
            hook_func = HookFunction(
                func=fn,
                priority=priority,
                name=name,
                plugin_id=plugin_id,
                enabled=True
            )

            with self._lock:
                self._functions.append(hook_func)
                # Sort by priority (stable sort preserves order for same priority)
                self._functions.sort(key=lambda x: x.priority)

            logger.debug(f"Added {hook_func.name} to hook {self.name} (priority={priority})")
            return fn

        if func is not None:
            return decorator(func)
        return decorator

    def remove(self, func: Callable) -> bool:
        """
        Remove a function from this hook.

        Args:
            func: Function to remove

        Returns:
            True if function was found and removed
        """
        with self._lock:
            original_len = len(self._functions)
            self._functions = [hf for hf in self._functions if hf.func != func]
            removed = len(self._functions) < original_len

        if removed:
            logger.debug(f"Removed function from hook {self.name}")
        return removed

    def remove_by_plugin(self, plugin_id: str) -> int:
        """
        Remove all functions registered by a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Number of functions removed
        """
        with self._lock:
            original_len = len(self._functions)
            self._functions = [
                hf for hf in self._functions
                if hf.plugin_id != plugin_id
            ]
            removed = original_len - len(self._functions)

        if removed > 0:
            logger.debug(f"Removed {removed} functions from hook {self.name} for plugin {plugin_id}")
        return removed

    def clear(self) -> int:
        """
        Remove all functions from this hook.

        Returns:
            Number of functions removed
        """
        with self._lock:
            count = len(self._functions)
            self._functions = []
        return count

    def run(self, *args, **kwargs) -> Any:
        """
        Run all functions in this hook (synchronously).

        Args:
            *args: Arguments to pass to each function
            **kwargs: Keyword arguments to pass to each function

        Returns:
            - NORMAL: List of all return values
            - ABNORMAL: First truthy return value, or None
            - FILTER: Final transformed value (first arg transformed through each function)
        """
        with self._lock:
            functions = [hf for hf in self._functions if hf.enabled]

        if self.hook_type == HookType.FILTER:
            # Filter hooks transform the first argument
            value = args[0] if args else kwargs.get('value')
            for hook_func in functions:
                try:
                    value = hook_func.func(value, *args[1:], **kwargs)
                except Exception as e:
                    logger.error(f"Error in hook {self.name} function {hook_func.name}: {e}")
            return value

        results = []
        for hook_func in functions:
            try:
                result = hook_func.func(*args, **kwargs)
                results.append(result)

                # For abnormal hooks, stop on first truthy result
                if self.hook_type == HookType.ABNORMAL and result:
                    return result

            except Exception as e:
                logger.error(f"Error in hook {self.name} function {hook_func.name}: {e}")

        return results if self.hook_type == HookType.NORMAL else None

    async def run_async(self, *args, **kwargs) -> Any:
        """
        Run all functions in this hook (asynchronously).

        Async functions are awaited, sync functions run directly.

        Args:
            *args: Arguments to pass to each function
            **kwargs: Keyword arguments to pass to each function

        Returns:
            Same as run(), but async
        """
        with self._lock:
            functions = [hf for hf in self._functions if hf.enabled]

        if self.hook_type == HookType.FILTER:
            value = args[0] if args else kwargs.get('value')
            for hook_func in functions:
                try:
                    if asyncio.iscoroutinefunction(hook_func.func):
                        value = await hook_func.func(value, *args[1:], **kwargs)
                    else:
                        value = hook_func.func(value, *args[1:], **kwargs)
                except Exception as e:
                    logger.error(f"Error in hook {self.name} function {hook_func.name}: {e}")
            return value

        results = []
        for hook_func in functions:
            try:
                if asyncio.iscoroutinefunction(hook_func.func):
                    result = await hook_func.func(*args, **kwargs)
                else:
                    result = hook_func.func(*args, **kwargs)

                results.append(result)

                if self.hook_type == HookType.ABNORMAL and result:
                    return result

            except Exception as e:
                logger.error(f"Error in hook {self.name} function {hook_func.name}: {e}")

        return results if self.hook_type == HookType.NORMAL else None

    def __len__(self) -> int:
        """Return number of functions in this hook."""
        with self._lock:
            return len(self._functions)

    def __repr__(self) -> str:
        return f"Hook('{self.name}', type={self.hook_type.value}, functions={len(self)})"


class HookManager:
    """
    Central registry and manager for all hooks.

    BUSINESS VALUE:
    - Single point of access for all platform hooks
    - Automatic hook discovery and registration
    - Plugin lifecycle management (cleanup on unload)
    - Debugging and introspection tools

    EMACS PARALLEL:
    Similar to Emacs' hook variable system, where hooks are global
    variables that can be modified by any package.

    Example:
        # Get the global hook manager
        hooks = HookManager.get_instance()

        # Define a new hook
        hooks.define('before-quiz-submit', docstring="Runs before quiz is submitted")

        # Add a function
        @hooks['before-quiz-submit'].add
        def validate_quiz(quiz):
            if not quiz.answers:
                raise ValueError("Quiz has no answers")

        # Run the hook
        hooks.run('before-quiz-submit', quiz)
    """

    _instance: Optional['HookManager'] = None
    _lock = threading.Lock()

    def __init__(self):
        self._hooks: Dict[str, Hook] = {}
        self._hook_lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> 'HookManager':
        """
        Get the singleton HookManager instance.

        Returns:
            The global HookManager
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def define(
        self,
        name: str,
        hook_type: HookType = HookType.NORMAL,
        docstring: Optional[str] = None
    ) -> Hook:
        """
        Define a new hook or return existing one.

        Args:
            name: Hook identifier (e.g., 'before-course-save')
            hook_type: Type of hook
            docstring: Description of the hook

        Returns:
            The Hook instance
        """
        with self._hook_lock:
            if name not in self._hooks:
                self._hooks[name] = Hook(name, hook_type, docstring)
                logger.debug(f"Defined hook: {name}")
            return self._hooks[name]

    def get(self, name: str) -> Optional[Hook]:
        """
        Get a hook by name.

        Args:
            name: Hook identifier

        Returns:
            Hook instance or None if not found
        """
        with self._hook_lock:
            return self._hooks.get(name)

    def __getitem__(self, name: str) -> Hook:
        """
        Get a hook by name, creating if needed.

        Args:
            name: Hook identifier

        Returns:
            Hook instance (creates new if not exists)
        """
        return self.define(name)

    def run(self, name: str, *args, **kwargs) -> Any:
        """
        Run a hook by name.

        Args:
            name: Hook identifier
            *args: Arguments to pass
            **kwargs: Keyword arguments to pass

        Returns:
            Hook results
        """
        hook = self.get(name)
        if hook:
            return hook.run(*args, **kwargs)
        return None

    async def run_async(self, name: str, *args, **kwargs) -> Any:
        """
        Run a hook asynchronously.

        Args:
            name: Hook identifier
            *args: Arguments to pass
            **kwargs: Keyword arguments to pass

        Returns:
            Hook results
        """
        hook = self.get(name)
        if hook:
            return await hook.run_async(*args, **kwargs)
        return None

    def remove_plugin(self, plugin_id: str) -> Dict[str, int]:
        """
        Remove all functions registered by a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Dict of hook_name -> functions_removed
        """
        removed = {}
        with self._hook_lock:
            for name, hook in self._hooks.items():
                count = hook.remove_by_plugin(plugin_id)
                if count > 0:
                    removed[name] = count
        return removed

    def list_hooks(self) -> List[str]:
        """
        List all defined hooks.

        Returns:
            List of hook names
        """
        with self._hook_lock:
            return list(self._hooks.keys())

    def describe_hook(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a hook.

        Args:
            name: Hook identifier

        Returns:
            Dict with hook details or None
        """
        hook = self.get(name)
        if not hook:
            return None

        with hook._lock:
            return {
                'name': hook.name,
                'type': hook.hook_type.value,
                'docstring': hook.docstring,
                'function_count': len(hook._functions),
                'functions': [
                    {
                        'name': hf.name,
                        'priority': hf.priority,
                        'plugin_id': hf.plugin_id,
                        'enabled': hf.enabled
                    }
                    for hf in hook._functions
                ]
            }


# Decorator for easily adding functions to hooks
def hook(name: str, priority: int = 50, plugin_id: Optional[str] = None):
    """
    Decorator to add a function to a named hook.

    Example:
        @hook('before-course-save', priority=10)
        def validate_course_name(course):
            if len(course.name) < 3:
                raise ValueError("Course name too short")

    Args:
        name: Hook name to attach to
        priority: Execution order (lower = earlier)
        plugin_id: Plugin identifier

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        hooks = HookManager.get_instance()
        hooks[name].add(func, priority=priority, plugin_id=plugin_id)
        return func
    return decorator
