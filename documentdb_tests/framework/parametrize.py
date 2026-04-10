"""Pytest parametrize helpers for building test parameter lists."""

from collections.abc import Sequence

import pytest

from documentdb_tests.framework.test_case import BaseTestCase


def pytest_params(tests: Sequence[BaseTestCase]):
    """Build pytest parameters from a sequence of test cases, using each case's id.

    Passes through any pytest marks defined on individual test cases.
    """
    return [pytest.param(t, id=t.id, marks=t.marks) for t in tests]
