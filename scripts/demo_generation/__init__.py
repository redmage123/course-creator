"""
Demo Generation Module

Generates demo screencasts using Playwright MCP + OBS Studio.
"""

from .demo_recorder import DemoRecorder, DemoSlide, DemoAction, DEMO_SLIDES

__all__ = ['DemoRecorder', 'DemoSlide', 'DemoAction', 'DEMO_SLIDES']
