"""Shared helpers for $convert expression forms.

$convert is the general form behind $toString, $toInt, $toDouble, etc.
Each to* operator's tests are parametrized over both the native operator
and the equivalent $convert expression using the helpers below.
"""

import pytest


def convert_expr(to: str):
    """Return a pytest.param that builds a $convert expression for the given target type."""
    return pytest.param(lambda tc: {"$convert": {"input": tc.value, "to": to}}, id="convert")


def convert_field_expr(to: str):
    """Return a pytest.param that builds a $convert expression for a field path."""
    return pytest.param(lambda field: {"$convert": {"input": field, "to": to}}, id="convert")
