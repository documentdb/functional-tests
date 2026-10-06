"""Unit tests for the opt-in assertion override hook (no database needed)."""

import pytest

from documentdb_tests.framework import assertions, override_hook
from documentdb_tests.framework.property_checks import Eq


class _Recorder:
    """Provider that records every call and handles it or not, as configured."""

    def __init__(self, handles=True, raises=False):
        self.handles = handles
        self.raises = raises
        self.calls = []

    def handle(self, fn, args, kwargs):
        self.calls.append((fn, args, kwargs))
        if self.raises:
            raise AssertionError("provider rejected the result")
        return self.handles


@pytest.fixture
def provider():
    """Register a provider for one test and always clear it afterwards."""
    registered = []

    def _register(p):
        override_hook.register_override_provider(p)
        registered.append(p)
        return p

    yield _register
    override_hook.register_override_provider(None)


# One call per public helper: (helper, args, kwargs). Each one, run plain, FAILS
# against the given result, so a pass proves the provider handled it.
_PUBLIC_CALLS = [
    (assertions.assertResult, ({"ok": 1.0}, {"ok": 2.0}), {"raw_res": True}),
    (assertions.assertSuccess, ({"ok": 1.0}, {"ok": 2.0}), {"raw_res": True}),
    (assertions.assertSuccessPartial, ({"ok": 1.0, "n": 1}, {"n": 2}), {}),
    (assertions.assertSuccessNaN, ({"cursor": {"firstBatch": [{"a": 1}]}}, [{"a": 2}]), {}),
    (assertions.assertFailure, ({"ok": 1.0}, {"code": 2}), {}),
    (assertions.assertFailureCode, ({"ok": 1.0}, 2), {}),
    (assertions.assertExceptionType, ({"ok": 1.0}, ValueError), {}),
    (assertions.assertNotError, (ValueError("boom"),), {}),
    (assertions.assertProperties, ({"ok": 1.0}, {"ok": Eq(2.0)}), {"raw_res": True}),
]


@pytest.mark.unit
class TestOverrideHook:
    def test_inert_without_a_provider(self):
        assert override_hook.get_override_provider() is None
        assertions.assertSuccess({"ok": 1.0}, {"ok": 1.0}, raw_res=True)
        with pytest.raises(AssertionError):
            assertions.assertSuccess({"ok": 1.0}, {"ok": 2.0}, raw_res=True)

    @pytest.mark.parametrize(
        "helper,args,kwargs", _PUBLIC_CALLS, ids=[c[0].__name__ for c in _PUBLIC_CALLS]
    )
    def test_every_public_helper_fails_plain(self, helper, args, kwargs):
        with pytest.raises(AssertionError):
            helper(*args, **kwargs)

    @pytest.mark.parametrize(
        "helper,args,kwargs", _PUBLIC_CALLS, ids=[c[0].__name__ for c in _PUBLIC_CALLS]
    )
    def test_every_public_helper_consults_the_provider_once(self, provider, helper, args, kwargs):
        p = provider(_Recorder(handles=True))
        helper(*args, **kwargs)  # would fail plain; the provider handled it
        assert len(p.calls) == 1
        fn, call_args, _ = p.calls[0]
        assert fn is assertions.assertResult.__wrapped__  # always the undecorated assertResult
        assert call_args[0] is args[0]  # with the test's own result

    def test_provider_declining_runs_the_normal_comparison(self, provider):
        p = provider(_Recorder(handles=False))
        assertions.assertSuccess({"ok": 1.0}, {"ok": 1.0}, raw_res=True)
        with pytest.raises(AssertionError):
            assertions.assertSuccess({"ok": 1.0}, {"ok": 2.0}, raw_res=True)
        assert len(p.calls) == 2

    def test_provider_assertion_error_propagates(self, provider):
        provider(_Recorder(raises=True))
        with pytest.raises(AssertionError, match="provider rejected"):
            assertions.assertSuccess({"ok": 1.0}, {"ok": 1.0}, raw_res=True)

    def test_calls_made_while_handling_run_plain(self, provider):
        class Nested(_Recorder):
            def handle(self, fn, args, kwargs):
                self.calls.append(fn)
                assertions.assertSuccess({"ok": 1.0}, {"ok": 1.0}, raw_res=True)  # passes plain
                with pytest.raises(AssertionError):
                    assertions.assertSuccess({"ok": 1.0}, {"ok": 2.0}, raw_res=True)  # fails plain
                return True

        p = provider(Nested())
        assertions.assertSuccess({"ok": 1.0}, {"ok": 2.0}, raw_res=True)
        assert len(p.calls) == 1  # never re-entered

    def test_guard_is_released_after_the_provider_raises(self, provider):
        provider(_Recorder(raises=True))
        with pytest.raises(AssertionError):
            assertions.assertSuccess({"ok": 1.0}, {"ok": 1.0}, raw_res=True)
        p = provider(_Recorder(handles=True))
        assertions.assertSuccess({"ok": 1.0}, {"ok": 2.0}, raw_res=True)
        assert len(p.calls) == 1

    def test_registering_again_replaces_and_none_clears(self, provider):
        first, second = provider(_Recorder()), provider(_Recorder())
        assertions.assertSuccess({"ok": 1.0}, {"ok": 2.0}, raw_res=True)
        assert (len(first.calls), len(second.calls)) == (0, 1)
        override_hook.register_override_provider(None)
        with pytest.raises(AssertionError):
            assertions.assertSuccess({"ok": 1.0}, {"ok": 2.0}, raw_res=True)
