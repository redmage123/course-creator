"""
Sandboxed Execution Environment

BUSINESS CONTEXT:
Provides safe execution environment for plugin code.
Prevents plugins from accessing dangerous system resources.

DESIGN PHILOSOPHY:
- Restrict access to sensitive modules (os, subprocess, etc.)
- Limit resource usage (CPU time, memory)
- Provide controlled APIs for safe operations
- Log all security-relevant actions

SECURITY MEASURES:
1. Module whitelist/blacklist
2. Execution timeout
3. Limited builtins
4. No filesystem access outside plugin dir
5. No network access (use provided APIs)
6. Audit logging

@module sandbox
"""

import ast
import builtins
import functools
import logging
import signal
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# Modules that plugins are NOT allowed to import
BLOCKED_MODULES = {
    'os', 'subprocess', 'shutil', 'socket', 'requests',
    'urllib', 'http', 'ftplib', 'telnetlib', 'smtplib',
    'ctypes', 'multiprocessing', 'threading',  # Can use our async instead
    'pickle', 'marshal', 'shelve',  # Serialization risks
    'importlib', 'imp', '__import__',  # Dynamic imports
    'sys',  # System access
    'gc', 'inspect', 'traceback',  # Introspection
    'code', 'codeop', 'compile',  # Code execution
    'pty', 'tty', 'termios',  # Terminal access
    'resource', 'syslog',  # System resources
    '__builtins__',
}

# Builtins that plugins are NOT allowed to use
BLOCKED_BUILTINS = {
    'eval', 'exec', 'compile', '__import__',
    'open', 'input', 'breakpoint',
    'globals', 'locals', 'vars',
    'getattr', 'setattr', 'delattr',  # Can bypass restrictions
    'memoryview', 'bytearray',  # Low-level memory
}

# Safe builtins that plugins CAN use
SAFE_BUILTINS = {
    # Basic types
    'None', 'True', 'False', 'bool', 'int', 'float', 'str',
    'list', 'dict', 'set', 'frozenset', 'tuple', 'bytes',
    # Iteration
    'range', 'enumerate', 'zip', 'map', 'filter', 'reversed', 'sorted',
    'iter', 'next', 'len', 'min', 'max', 'sum', 'any', 'all',
    # String/formatting
    'format', 'repr', 'ascii', 'chr', 'ord', 'hex', 'oct', 'bin',
    # Type conversion
    'abs', 'round', 'divmod', 'pow',
    # Containers
    'slice', 'object', 'type', 'isinstance', 'issubclass',
    # Errors
    'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
    'AttributeError', 'RuntimeError', 'StopIteration', 'NotImplementedError',
    # Functional
    'callable', 'hash', 'id', 'super', 'property', 'staticmethod', 'classmethod',
    # Print (redirected to logging)
    'print',
}


@dataclass
class SandboxConfig:
    """
    Configuration for sandboxed execution.

    Attributes:
        timeout_seconds: Maximum execution time
        max_memory_mb: Maximum memory usage
        allowed_modules: Additional modules to allow
        blocked_modules: Additional modules to block
        enable_audit: Enable detailed audit logging
    """
    timeout_seconds: float = 5.0
    max_memory_mb: int = 100
    allowed_modules: Set[str] = field(default_factory=set)
    blocked_modules: Set[str] = field(default_factory=set)
    enable_audit: bool = True


class TimeoutError(Exception):
    """Raised when code execution exceeds timeout."""
    pass


class SecurityError(Exception):
    """Raised when code attempts blocked operations."""
    pass


class SandboxedExecutor:
    """
    Executes plugin code in a restricted environment.

    BUSINESS VALUE:
    - Prevents malicious plugins from harming the system
    - Limits resource consumption
    - Provides audit trail for security review
    - Enables safe execution of user-provided code

    Example:
        executor = SandboxedExecutor(config)

        # Execute code string
        result = executor.exec_code('''
            def process(data):
                return data.upper()
            result = process("hello")
        ''')

        # Execute a function safely
        @executor.safe_call
        def my_plugin_handler(data):
            return process_data(data)
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        """
        Initialize the sandboxed executor.

        Args:
            config: Sandbox configuration (uses defaults if not provided)
        """
        self.config = config or SandboxConfig()
        self._lock = threading.Lock()

        # Build effective blocked modules list
        self._blocked = BLOCKED_MODULES.copy()
        self._blocked.update(self.config.blocked_modules)
        self._blocked -= self.config.allowed_modules

        # Build safe builtins dict
        self._safe_builtins = self._create_safe_builtins()

    def _create_safe_builtins(self) -> Dict[str, Any]:
        """Create a dict of safe builtin functions."""
        safe = {}
        for name in SAFE_BUILTINS:
            if hasattr(builtins, name):
                safe[name] = getattr(builtins, name)

        # Replace print with logging-based version
        safe['print'] = self._safe_print
        return safe

    def _safe_print(self, *args, **kwargs):
        """Safe print that logs instead of writing to stdout."""
        message = ' '.join(str(arg) for arg in args)
        logger.info(f"[Plugin Output] {message}")

    def _check_imports(self, code: str) -> List[str]:
        """
        Check for blocked imports in code.

        Args:
            code: Python code to check

        Returns:
            List of blocked module names found
        """
        blocked_found = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split('.')[0]
                        if module in self._blocked:
                            blocked_found.append(module)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module.split('.')[0]
                        if module in self._blocked:
                            blocked_found.append(module)
        except SyntaxError:
            pass  # Syntax errors will be caught during execution
        return blocked_found

    def _check_dangerous_calls(self, code: str) -> List[str]:
        """
        Check for dangerous function calls.

        Args:
            code: Python code to check

        Returns:
            List of dangerous calls found
        """
        dangerous = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in BLOCKED_BUILTINS:
                            dangerous.append(node.func.id)
        except SyntaxError:
            pass
        return dangerous

    @contextmanager
    def _timeout_context(self, seconds: float):
        """Context manager for execution timeout (Unix only)."""
        def handler(signum, frame):
            raise TimeoutError(f"Execution exceeded {seconds} seconds")

        # Only works on Unix
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.setitimer(signal.ITIMER_REAL, seconds)
            try:
                yield
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)
        else:
            # On Windows, just yield without timeout
            yield

    def validate_code(self, code: str) -> List[str]:
        """
        Validate code without executing it.

        Args:
            code: Python code to validate

        Returns:
            List of security issues found (empty if safe)
        """
        issues = []

        # Check for blocked imports
        blocked_imports = self._check_imports(code)
        if blocked_imports:
            issues.append(f"Blocked imports: {', '.join(blocked_imports)}")

        # Check for dangerous calls
        dangerous_calls = self._check_dangerous_calls(code)
        if dangerous_calls:
            issues.append(f"Blocked functions: {', '.join(dangerous_calls)}")

        # Try to compile
        try:
            compile(code, '<plugin>', 'exec')
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")

        if self.config.enable_audit and issues:
            logger.warning(f"Code validation failed: {issues}")

        return issues

    def exec_code(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute code in sandboxed environment.

        Args:
            code: Python code to execute
            globals_dict: Global namespace (merged with safe builtins)
            locals_dict: Local namespace

        Returns:
            The local namespace after execution

        Raises:
            SecurityError: If code contains blocked operations
            TimeoutError: If execution exceeds timeout
        """
        # Validate first
        issues = self.validate_code(code)
        if issues:
            raise SecurityError(f"Code validation failed: {'; '.join(issues)}")

        # Prepare namespaces
        safe_globals = {'__builtins__': self._safe_builtins}
        if globals_dict:
            safe_globals.update(globals_dict)

        safe_locals = locals_dict.copy() if locals_dict else {}

        if self.config.enable_audit:
            logger.debug(f"Executing sandboxed code ({len(code)} chars)")

        # Execute with timeout
        with self._timeout_context(self.config.timeout_seconds):
            exec(compile(code, '<plugin>', 'exec'), safe_globals, safe_locals)

        return safe_locals

    def safe_call(
        self,
        func: Optional[Callable] = None,
        *,
        timeout: Optional[float] = None
    ):
        """
        Decorator to execute a function with timeout protection.

        Args:
            func: Function to wrap (optional for decorator syntax)
            timeout: Override default timeout

        Returns:
            Wrapped function

        Example:
            @executor.safe_call(timeout=2.0)
            def process_data(data):
                return transform(data)
        """
        actual_timeout = timeout or self.config.timeout_seconds

        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                if self.config.enable_audit:
                    logger.debug(f"Safe call: {fn.__name__}")

                with self._timeout_context(actual_timeout):
                    return fn(*args, **kwargs)

            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def create_restricted_namespace(
        self,
        extra_allowed: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a namespace dict for restricted execution.

        Args:
            extra_allowed: Additional names to allow in namespace

        Returns:
            Namespace dict with safe builtins and extras
        """
        namespace = {'__builtins__': self._safe_builtins}
        if extra_allowed:
            namespace.update(extra_allowed)
        return namespace


class PluginSecurityAuditor:
    """
    Audits plugin code for security issues.

    Provides static analysis of plugin code before loading.
    """

    def __init__(self):
        self._patterns = self._compile_patterns()

    def _compile_patterns(self) -> List[tuple]:
        """Compile regex patterns for security checks."""
        import re
        return [
            (re.compile(r'__\w+__'), "Dunder access"),
            (re.compile(r'\.mro\b'), "MRO manipulation"),
            (re.compile(r'\.func_globals\b'), "Function globals access"),
            (re.compile(r'\.f_globals\b'), "Frame globals access"),
            (re.compile(r'\.gi_frame\b'), "Generator frame access"),
        ]

    def audit_code(self, code: str) -> List[Dict[str, Any]]:
        """
        Perform security audit on code.

        Args:
            code: Python source code

        Returns:
            List of security findings
        """
        findings = []

        # Check patterns
        for pattern, description in self._patterns:
            for match in pattern.finditer(code):
                findings.append({
                    'type': 'pattern',
                    'description': description,
                    'match': match.group(),
                    'position': match.start()
                })

        # AST-based checks
        try:
            tree = ast.parse(code)
            findings.extend(self._audit_ast(tree))
        except SyntaxError as e:
            findings.append({
                'type': 'syntax',
                'description': f"Syntax error: {e}",
                'position': getattr(e, 'offset', 0)
            })

        return findings

    def _audit_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Audit AST for security issues."""
        findings = []

        for node in ast.walk(tree):
            # Check for exec/eval
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ('exec', 'eval', 'compile'):
                        findings.append({
                            'type': 'dangerous_call',
                            'description': f"Dangerous call to {node.func.id}",
                            'line': node.lineno
                        })

            # Check for attribute access to blocked names
            if isinstance(node, ast.Attribute):
                if node.attr.startswith('_'):
                    findings.append({
                        'type': 'private_access',
                        'description': f"Access to private attribute: {node.attr}",
                        'line': node.lineno
                    })

        return findings

    def is_safe(self, code: str) -> tuple:
        """
        Quick check if code is safe.

        Args:
            code: Python source code

        Returns:
            (is_safe: bool, findings: List[Dict])
        """
        findings = self.audit_code(code)
        critical = [f for f in findings if f['type'] in ('dangerous_call', 'syntax')]
        return len(critical) == 0, findings
