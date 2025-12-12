"""
Course Creator Platform - Python Plugin System

BUSINESS CONTEXT:
Emacs-style extensibility system using Python as the extension language.
Enables organizations to customize platform behavior without modifying core code.

DESIGN PHILOSOPHY (inspired by Emacs):
- Everything is extensible via Python
- Hooks for all significant events
- Advise functions to wrap existing functionality
- Configuration via Python code
- Safe sandboxed execution

KEY CONCEPTS:
1. Plugins: Python modules that extend platform functionality
2. Hooks: Named extension points that plugins can attach to
3. Advice: Wrappers around existing functions (before/after/around)
4. Events: Async notifications plugins can subscribe to
5. API: Safe interface for plugins to interact with the platform

@module plugin_system
"""

from plugin_system.core.plugin_loader import PluginLoader, PluginRegistry
from plugin_system.core.hook_manager import HookManager, hook, Hook
from plugin_system.core.event_bus import EventBus, Event
from plugin_system.core.advice import Advice, before_advice, after_advice, around_advice
from plugin_system.core.sandbox import SandboxedExecutor
from plugin_system.api.platform_api import PlatformAPI

__all__ = [
    # Core
    'PluginLoader',
    'PluginRegistry',
    'HookManager',
    'Hook',
    'hook',
    'EventBus',
    'Event',
    'Advice',
    'before_advice',
    'after_advice',
    'around_advice',
    'SandboxedExecutor',
    # API
    'PlatformAPI',
]

__version__ = '1.0.0'
