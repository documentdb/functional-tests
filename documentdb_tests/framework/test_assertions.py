"""Unit tests for the public ``assertResult`` entry point (no database needed)."""

import pytest

from documentdb_tests.framework import assertions

# Pairs of expectation selectors that must not be combined. Each dict is passed
# as keyword arguments alongside a dummy result; every pair names two different
# branches of assertResult's if/elif chain.
_CONFLICTING_SELECTORS = [
    ({"expected": {"ok": 1.0}, "error_code": 2}, "expected+error_code"),
    ({"error_code": 2, "exception_type": ValueError}, "error_code+exception_type"),
    ({"error": {"code": 2, "msg": "x"}, "error_code": 2}, "error+error_code"),
    ({"not_error": True, "error_code": 2}, "not_error+error_code"),
    ({"expected": {"ok": 1.0}, "error": {"code": 2, "msg": "x"}}, "expected+error"),
]


@pytest.mark.unit
class TestAssertResultSelectorGuard:
    """assertResult accepts exactly one expectation selector per call."""

    @pytest.mark.parametrize(
        "kwargs", [c[0] for c in _CONFLICTING_SELECTORS], ids=[c[1] for c in _CONFLICTING_SELECTORS]
    )
    def test_multiple_selectors_raise_setup_error(self, kwargs):
        """Passing two expectation selectors is a setup error, not silent precedence."""
        with pytest.raises(assertions.TestSetupError, match="mutually-exclusive"):
            assertions.assertResult({"ok": 1.0}, raw_res=True, **kwargs)

    def test_single_selector_does_not_trip_the_guard(self):
        """A lone expectation selector is accepted and compared normally."""
        assertions.assertResult({"ok": 1.0}, {"ok": 1.0}, raw_res=True)
