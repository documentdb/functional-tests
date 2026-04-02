"""
Reusable testing framework for DocumentDB functional tests.

This framework provides:
- Assertion helpers for common test scenarios
- Fixture utilities for test isolation and database management
"""

from documentdb_tests.framework.assertions import assertFailure, assertSuccess
from documentdb_tests.framework.executor import execute_command

__all__ = ["execute_command", "assertSuccess", "assertFailure"]
