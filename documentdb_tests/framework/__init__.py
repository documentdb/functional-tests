"""
Reusable testing framework for DocumentDB functional tests.

This framework provides:
- Assertion helpers for common test scenarios
- Fixture utilities for test isolation and database management
"""

from . import assertions, fixtures

__all__ = ["assertions", "fixtures"]