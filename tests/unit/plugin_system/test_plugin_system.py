"""
Plugin System Unit Tests

Tests the core plugin system components:
- Hook Manager
- Event Bus
- Advice System
- Sandboxed Execution
- Plugin Loader

@module test_plugin_system

NOTE: This test file has been refactored to use real implementations
instead of mocks, as the plugin system is self-contained and doesn't
require external dependencies.
"""

import asyncio
import pytest
import sys
import os
from pathlib import Path

# Add the shared services to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'shared'))

from plugin_system.core.hook_manager import HookManager, Hook, HookType, hook
from plugin_system.core.event_bus import EventBus, Event, PlatformEvents
from plugin_system.core.advice import Advice, AdviceType, before_advice, after_advice, around_advice
from plugin_system.core.sandbox import SandboxedExecutor, SandboxConfig, SecurityError


class TestHookManager:
    """Tests for the Hook Manager - using real HookManager instance."""

    def setup_method(self):
        """Reset singleton for each test."""
        HookManager._instance = None

    def test_singleton_pattern(self):
        """Test that HookManager follows singleton pattern."""
        manager1 = HookManager.get_instance()
        manager2 = HookManager.get_instance()
        assert manager1 is manager2

    def test_get_or_create_hook(self):
        """Test hook creation."""
        manager = HookManager.get_instance()
        hook = manager.get_or_create('test-hook')
        assert hook is not None
        assert hook.name == 'test-hook'

    def test_hook_registration(self):
        """Test adding functions to hooks."""
        manager = HookManager.get_instance()

        @hook('my-test-hook')
        def my_func():
            return "called"

        assert 'my-test-hook' in manager._hooks
        assert len(manager._hooks['my-test-hook']._functions) == 1

    def test_hook_execution_sync(self):
        """Test synchronous hook execution."""
        manager = HookManager.get_instance()
        results = []

        @manager['test-run'].add
        def func1(x):
            results.append(f"func1:{x}")
            return x * 2

        @manager['test-run'].add
        def func2(x):
            results.append(f"func2:{x}")
            return x * 3

        output = manager.run_sync('test-run', 5)
        assert 'func1:5' in results
        assert 'func2:5' in results

    def test_hook_priority(self):
        """Test hook execution order by priority."""
        manager = HookManager.get_instance()
        order = []

        manager['priority-test'].add(lambda: order.append('low'), priority=100)
        manager['priority-test'].add(lambda: order.append('high'), priority=10)
        manager['priority-test'].add(lambda: order.append('mid'), priority=50)

        manager.run_sync('priority-test')
        assert order == ['high', 'mid', 'low']

    def test_filter_hook(self):
        """Test filter hook type (pipeline)."""
        manager = HookManager.get_instance()
        hook = manager.get_or_create('filter-test', hook_type=HookType.FILTER)

        hook.add(lambda x: x + ' modified')
        hook.add(lambda x: x.upper())

        result = manager.run_sync('filter-test', 'input')
        assert result == 'INPUT MODIFIED'

    def test_plugin_removal(self):
        """Test removing all hooks for a plugin."""
        manager = HookManager.get_instance()

        manager['cleanup-test'].add(lambda: None, plugin_id='test-plugin')
        manager['cleanup-test'].add(lambda: None, plugin_id='other-plugin')

        assert len(manager._hooks['cleanup-test']._functions) == 2

        manager.remove_plugin('test-plugin')
        assert len(manager._hooks['cleanup-test']._functions) == 1


class TestEventBus:
    """Tests for the Event Bus - using real EventBus instance."""

    def setup_method(self):
        """Reset singleton for each test."""
        EventBus._instance = None

    def test_singleton_pattern(self):
        """Test that EventBus follows singleton pattern."""
        bus1 = EventBus.get_instance()
        bus2 = EventBus.get_instance()
        assert bus1 is bus2

    @pytest.mark.asyncio
    async def test_event_subscription(self):
        """Test subscribing to events."""
        bus = EventBus.get_instance()
        received = []

        @bus.subscribe('test.event')
        async def handler(event):
            received.append(event)

        await bus.publish(Event(
            name='test.event',
            data={'key': 'value'},
            source='test'
        ))

        await asyncio.sleep(0.1)  # Allow async processing
        assert len(received) == 1
        assert received[0].data['key'] == 'value'

    @pytest.mark.asyncio
    async def test_wildcard_subscription(self):
        """Test wildcard pattern matching."""
        bus = EventBus.get_instance()
        received = []

        @bus.subscribe('course.*')
        async def handler(event):
            received.append(event.name)

        await bus.publish(Event(name='course.created', data={}, source='test'))
        await bus.publish(Event(name='course.updated', data={}, source='test'))
        await bus.publish(Event(name='user.created', data={}, source='test'))

        await asyncio.sleep(0.1)
        assert 'course.created' in received
        assert 'course.updated' in received
        assert 'user.created' not in received

    def test_sync_publish(self):
        """Test synchronous event publishing."""
        bus = EventBus.get_instance()
        received = []

        def sync_handler(event):
            received.append(event)

        bus.subscribe_sync('sync.test', sync_handler)
        bus.publish_sync(Event(name='sync.test', data={}, source='test'))

        assert len(received) == 1

    def test_plugin_unsubscribe(self):
        """Test unsubscribing all plugin handlers."""
        bus = EventBus.get_instance()

        bus.subscribe_sync('unsub.test', lambda e: None, plugin_id='plugin-a')
        bus.subscribe_sync('unsub.test', lambda e: None, plugin_id='plugin-b')

        assert len(bus._subscribers.get('unsub.test', [])) == 2

        bus.unsubscribe_plugin('plugin-a')
        assert len(bus._subscribers.get('unsub.test', [])) == 1


class TestAdvice:
    """Tests for the Advice system - using real Advice instance."""

    def setup_method(self):
        """Reset singleton for each test."""
        Advice._instance = None

    def test_singleton_pattern(self):
        """Test that Advice follows singleton pattern."""
        adv1 = Advice.get_instance()
        adv2 = Advice.get_instance()
        assert adv1 is adv2

    def test_before_advice(self):
        """Test before advice execution."""
        advice = Advice.get_instance()
        before_calls = []

        def original(x):
            return x * 2

        advice.add_before(
            'test.before',
            lambda x: before_calls.append(x)
        )

        wrapped = advice.apply('test.before', original)
        result = wrapped(5)

        assert 5 in before_calls
        assert result == 10

    def test_after_advice(self):
        """Test after advice execution."""
        advice = Advice.get_instance()

        def original(x):
            return x * 2

        advice.add_after(
            'test.after',
            lambda result, x: result + 1  # Add 1 to result
        )

        wrapped = advice.apply('test.after', original)
        result = wrapped(5)

        assert result == 11  # (5 * 2) + 1

    def test_around_advice(self):
        """Test around advice execution."""
        advice = Advice.get_instance()
        wrap_calls = []

        def original(x):
            return x * 2

        def wrapper(orig, x):
            wrap_calls.append('before')
            result = orig(x)
            wrap_calls.append('after')
            return result + 100

        advice.add_around('test.around', wrapper)

        wrapped = advice.apply('test.around', original)
        result = wrapped(5)

        assert wrap_calls == ['before', 'after']
        assert result == 110  # (5 * 2) + 100

    def test_advice_priority(self):
        """Test advice execution order by priority."""
        advice = Advice.get_instance()
        order = []

        def original():
            return 'original'

        advice.add_before('test.priority', lambda: order.append('low'), priority=100)
        advice.add_before('test.priority', lambda: order.append('high'), priority=10)

        wrapped = advice.apply('test.priority', original)
        wrapped()

        assert order == ['high', 'low']

    def test_advice_removal(self):
        """Test removing advice."""
        advice = Advice.get_instance()

        def my_advice():
            pass

        advice.add_before('test.remove', my_advice)
        assert len(advice.get_advice('test.remove')) == 1

        advice.remove_advice('test.remove', my_advice)
        assert len(advice.get_advice('test.remove')) == 0


class TestSandboxedExecutor:
    """Tests for the Sandboxed Executor - using real SandboxedExecutor instance."""

    def test_safe_code_execution(self):
        """Test executing safe code."""
        executor = SandboxedExecutor()

        result = executor.exec_code('''
result = 2 + 2
        ''')

        assert result['result'] == 4

    def test_blocked_import(self):
        """Test that dangerous imports are blocked."""
        executor = SandboxedExecutor()

        with pytest.raises(SecurityError) as exc_info:
            executor.exec_code('import os')

        assert 'os' in str(exc_info.value)

    def test_blocked_builtin(self):
        """Test that dangerous builtins are blocked."""
        executor = SandboxedExecutor()

        with pytest.raises(SecurityError) as exc_info:
            executor.exec_code('eval("1+1")')

        assert 'eval' in str(exc_info.value)

    def test_code_validation(self):
        """Test code validation without execution."""
        executor = SandboxedExecutor()

        issues = executor.validate_code('import os\nimport subprocess')
        assert len(issues) > 0
        assert any('os' in issue for issue in issues)
        assert any('subprocess' in issue for issue in issues)

    def test_safe_builtins_available(self):
        """Test that safe builtins work."""
        executor = SandboxedExecutor()

        result = executor.exec_code('''
data = [1, 2, 3, 4, 5]
total = sum(data)
maximum = max(data)
length = len(data)
result = (total, maximum, length)
        ''')

        assert result['result'] == (15, 5, 5)

    def test_print_redirected(self):
        """Test that print is redirected to logging."""
        executor = SandboxedExecutor()

        # This should not raise an error
        result = executor.exec_code('''
print("Hello from sandbox")
result = "printed"
        ''')

        assert result['result'] == 'printed'

    def test_safe_call_decorator(self):
        """Test safe_call decorator."""
        executor = SandboxedExecutor()

        @executor.safe_call
        def my_func(x):
            return x * 2

        assert my_func(5) == 10


class TestPluginIntegration:
    """Integration tests for the plugin system - using real instances."""

    def test_hook_and_event_together(self):
        """Test hooks and events working together."""
        HookManager._instance = None
        EventBus._instance = None

        hooks = HookManager.get_instance()
        bus = EventBus.get_instance()

        results = []

        # Hook that emits an event
        @hooks['test-integration'].add
        def hook_func(data):
            bus.publish_sync(Event(
                name='hook.completed',
                data={'result': data * 2},
                source='hook'
            ))
            return data * 2

        # Event handler
        bus.subscribe_sync('hook.completed', lambda e: results.append(e.data['result']))

        # Run the hook
        hooks.run_sync('test-integration', 5)

        assert 10 in results

    def test_advice_with_hooks(self):
        """Test advice wrapping a function that uses hooks."""
        Advice._instance = None
        HookManager._instance = None

        advice = Advice.get_instance()
        hooks = HookManager.get_instance()
        calls = []

        def original_service(data):
            hooks.run_sync('service.called', data)
            return data + '_processed'

        # Add hook
        hooks['service.called'].add(lambda d: calls.append(f'hook:{d}'))

        # Add advice
        advice.add_before('my.service', lambda d: calls.append(f'before:{d}'))
        advice.add_after('my.service', lambda r, d: calls.append(f'after:{r}') or r)

        wrapped = advice.apply('my.service', original_service)
        result = wrapped('input')

        assert 'before:input' in calls
        assert 'hook:input' in calls
        assert 'after:input_processed' in calls
        assert result == 'input_processed'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
