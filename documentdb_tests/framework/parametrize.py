"""Pytest parametrize helpers for building test parameter lists."""

from collections.abc import Sequence

import pytest

from documentdb_tests.framework.test_case import BaseTestCase


def pytest_params(tests: Sequence[BaseTestCase]):
    """Build pytest parameters from a sequence of test cases, using each case's id."""
    return [pytest.param(test_case, id=test_case.id) for test_case in tests]


def with_expected(samples, expected_list):
    """Pair shared input samples with per-operator expected outcomes.

    Args:
        samples: List of pytest.param inputs (e.g. BSON_TYPE_SAMPLES).
        expected_list: Dict mapping sample id → expected value.

    Returns:
        List of pytest.param(input_value, expected_value, id=sample_id).
    """
    return [
        pytest.param(*s.values, expected_list[s.id], id=s.id)
        for s in samples
    ]
