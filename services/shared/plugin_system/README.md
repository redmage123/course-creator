# Course Creator Plugin System

A comprehensive Python plugin system for the Course Creator platform, inspired by Emacs Lisp's extensibility model.

## Overview

The plugin system allows developers to extend and customize the platform without modifying core code. Similar to how Emacs uses Lisp to enable endless customization, this system provides:

- **Hooks**: Named extension points for modifying behavior
- **Events**: Async pub/sub for reacting to platform activities
- **Advice**: Function wrapping (before/after/around) for core functions
- **Sandboxed Execution**: Safe environment for plugin code
- **Platform API**: Safe, controlled access to platform features

## Quick Start

### 1. Create a Plugin Directory

```
plugins/
└── my-plugin/
    ├── __init__.py       # Plugin entry point
    └── plugin.yaml       # Plugin metadata
```

### 2. Define Plugin Metadata (plugin.yaml)

```yaml
name: my-plugin
version: 1.0.0
description: My awesome plugin
author: Your Name

# Hooks your plugin uses
hooks:
  - before-course-save
  - after-quiz-submit

# Events your plugin subscribes to
events:
  - course.*
  - quiz.submitted

# Plugin settings
settings_schema:
  my_setting:
    type: string
    default: "value"
    description: My setting description
```

### 3. Implement Plugin Entry Point (__init__.py)

```python
"""My Plugin - Does something awesome."""

def activate(api):
    """Called when plugin is activated."""
    api.log.info("My plugin activated!")

    # Register a hook
    @api.hooks['before-course-save'].add
    def validate_course(course):
        if not course.get('title'):
            raise ValueError("Course must have a title")
        return course

    # Subscribe to events
    @api.events.subscribe('course.created')
    async def on_course_created(event):
        api.log.info(f"Course created: {event.data['name']}")

def deactivate(api):
    """Called when plugin is deactivated."""
    api.log.info("My plugin deactivated")
```

## Core Concepts

### Hooks

Hooks are named extension points where plugins can register functions to be called at specific times.

```python
from plugin_system.core.hook_manager import HookManager, hook

# Get the hook manager
hooks = HookManager.get_instance()

# Add a function to a hook
@hook('before-course-save')
def my_validation(course):
    # Validate course
    return course

# Or manually
hooks['before-course-save'].add(my_validation, priority=10)

# Run all hook functions
result = hooks.run_sync('before-course-save', course_data)
```

**Hook Types:**
- `NORMAL`: Functions are called in order, all return values collected
- `ABNORMAL`: Stop on first non-None return
- `FILTER`: Each function receives previous output as input (pipeline)

### Events

Events enable async pub/sub communication between components.

```python
from plugin_system.core.event_bus import EventBus, Event

bus = EventBus.get_instance()

# Subscribe to events
@bus.subscribe('course.created')
async def on_course_created(event):
    print(f"Course created: {event.data['name']}")

# Subscribe with wildcard patterns
@bus.subscribe('course.*')  # All course events
@bus.subscribe('*.created')  # All creation events
async def on_any_creation(event):
    pass

# Publish events
await bus.publish(Event(
    name='course.created',
    data={'name': 'My Course', 'id': '123'},
    source='course-service'
))
```

### Advice (Function Wrapping)

Advice allows plugins to wrap existing functions without modifying them.

```python
from plugin_system.core.advice import (
    Advice, before_advice, after_advice, around_advice
)

# Before advice - runs before the function
@before_advice('course_service.create_course')
def validate_input(course_data):
    if len(course_data['name']) < 5:
        raise ValueError("Name too short")

# After advice - runs after, can modify return value
@after_advice('course_service.create_course')
def add_metadata(result, course_data):
    result.created_by = 'plugin'
    return result

# Around advice - wraps the function completely
@around_advice('quiz_service.submit_quiz')
def with_timing(original_func, *args, **kwargs):
    start = time.time()
    result = original_func(*args, **kwargs)
    print(f"Took {time.time() - start}s")
    return result
```

### Platform API

The Platform API provides safe access to platform features.

```python
def activate(api):
    # Logging
    api.log.info("Message")
    api.log.error("Error")

    # Configuration
    value = api.config.get('my_setting', default='fallback')
    api.config.set('my_setting', 'new_value')

    # Storage
    await api.storage.set('my_key', {'data': 'value'})
    data = await api.storage.get('my_key')

    # Users
    user = await api.users.get_current()
    has_permission = await api.users.has_permission(user_id, 'create_course')

    # Courses
    course = await api.courses.get(course_id)
    courses = await api.courses.list_by_organization(org_id)

    # Notifications
    await api.notify.send_to_user(user_id, "Title", "Message")
    await api.notify.send_email(email, "Subject", "Body")

    # Analytics
    await api.analytics.track_event('custom_event', {'key': 'value'})

    # Emit custom events
    api.emit('my-plugin.custom-event', {'data': 'value'})

    # Schedule tasks
    schedule_id = api.schedule(my_function, delay_seconds=60, repeat=True)
```

### Sandboxed Execution

The sandbox provides safe execution of plugin code.

```python
from plugin_system.core.sandbox import SandboxedExecutor, SandboxConfig

config = SandboxConfig(
    timeout_seconds=5.0,
    max_memory_mb=100,
    enable_audit=True
)

executor = SandboxedExecutor(config)

# Execute code safely
result = executor.exec_code('''
def process(data):
    return data.upper()
result = process("hello")
''')

# Wrap functions with timeout
@executor.safe_call(timeout=2.0)
def my_function(data):
    return transform(data)
```

**Blocked Operations:**
- File system access (os, shutil)
- Network access (socket, requests, urllib)
- Subprocess/shell execution
- Dynamic imports
- eval/exec/compile
- System introspection

## Plugin Lifecycle

1. **Discovery**: Plugins are discovered in configured directories
2. **Loading**: Plugin module is loaded and dependencies checked
3. **Activation**: `activate(api)` is called
4. **Running**: Plugin responds to hooks and events
5. **Deactivation**: `deactivate(api)` is called
6. **Unloading**: Plugin is removed from memory

```python
from plugin_system.core.plugin_loader import PluginLoader

loader = PluginLoader(['/path/to/plugins'])

# Discover all plugins
loader.discover_all()

# Load and activate all
loader.load_all()
loader.activate_all()

# Reload a specific plugin
loader.reload('my-plugin@1.0.0')

# Deactivate all on shutdown
loader.deactivate_all()
```

## Standard Events

The platform emits these standard events:

### User Events
- `user.created` - New user registered
- `user.login` - User logged in
- `user.logout` - User logged out
- `user.enrolled` - User enrolled in course
- `user.completed_course` - User completed course

### Course Events
- `course.created` - Course created
- `course.updated` - Course modified
- `course.deleted` - Course deleted
- `course.published` - Course made public
- `course.viewed` - Course page viewed

### Content Events
- `content.created` - Content created
- `content.generated` - AI content generated
- `content.accessed` - Content accessed by user
- `video.watched` - Video watched

### Quiz Events
- `quiz.created` - Quiz created
- `quiz.started` - User started quiz
- `quiz.submitted` - Quiz submitted
- `quiz.graded` - Quiz automatically graded

### Lab Events
- `lab.session_started` - Lab session started
- `lab.session_ended` - Lab session ended
- `lab.code_executed` - Code executed in lab

## Standard Hooks

### Course Hooks
- `before-course-save` - Before course is saved
- `after-course-save` - After course is saved
- `before-course-delete` - Before course deletion

### Quiz Hooks
- `before-quiz-save` - Before quiz is saved
- `after-quiz-submit` - After quiz submission
- `quiz-grade` - Custom grading logic

### Content Hooks
- `before-content-publish` - Before publishing
- `after-content-generate` - After AI generation
- `content-transform` - Transform content

## Security

The plugin system implements multiple security layers:

1. **Module Blocking**: Dangerous modules (os, subprocess) are blocked
2. **Builtin Restrictions**: eval, exec, open are removed
3. **Timeout Protection**: Code execution has time limits
4. **AST Analysis**: Code is analyzed before execution
5. **Audit Logging**: All security events are logged

## Example Plugins

See the `/plugins` directory for example plugins:

- **course-validator**: Validates courses before saving
- **notification-enhancer**: Smart notification routing
- **analytics-tracker**: Detailed user analytics

## Best Practices

1. **Keep plugins focused**: One plugin, one responsibility
2. **Use hooks sparingly**: Only hook into what you need
3. **Handle errors gracefully**: Don't crash the platform
4. **Log appropriately**: Use api.log for debugging
5. **Test thoroughly**: Test hooks and events in isolation
6. **Document settings**: Describe all configuration options
7. **Version appropriately**: Follow semver for updates

## API Reference

See the source code documentation for complete API details:

- `plugin_system/core/hook_manager.py` - Hook system
- `plugin_system/core/event_bus.py` - Event system
- `plugin_system/core/advice.py` - Advice system
- `plugin_system/core/sandbox.py` - Sandboxed execution
- `plugin_system/core/plugin_loader.py` - Plugin loading
- `plugin_system/api/platform_api.py` - Platform API
