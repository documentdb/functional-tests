"""Opt-in compatibility override hook for the assertion API.

An external test harness may register a single override *provider* to substitute
an engine-specific expected result or error for a known, reviewed behavioral
divergence, keyed by the test currently running. This lets a compatibility suite
for another MongoDB-compatible engine run the SAME test corpus against an engine that
legitimately differs from MongoDB in a small, tracked set of cases, without
forking the tests.

It is INERT unless a provider is registered: when no provider is registered
``consult_override`` returns False immediately, so the assertion API behaves
exactly as upstream and MongoDB (and any other engine that does not opt in) is
completely unaffected.

Every public assertion helper in ``framework.assertions`` is a thin wrapper
around ``assertResult``, and ``assertResult`` alone is wrapped by
``assertions._overridable``, which calls ``consult_override`` once per public
call and, if the provider does not handle it, runs the comparison unchanged.

A provider implements one method:
    handle(fn, args, kwargs) -> bool
where ``fn`` is the undecorated ``assertResult`` and ``args``/``kwargs`` are the
arguments it was called with. It returns True iff it fully handled the assertion
(passing, or raising ``AssertionError``). A provider evaluates a candidate by
calling ``fn`` with substituted arguments. While ``handle`` runs, the
``_IN_OVERRIDE`` guard makes any decorated call it reaches run plain, so an
override can never recurse or be applied twice.

This module deliberately contains NO engine-specific logic -- it is the generic
extension point only. All override data and decision logic live in the harness
that registers the provider.
"""

from typing import Any, Callable

_OVERRIDE_PROVIDER: Any = None
_IN_OVERRIDE: bool = False


def register_override_provider(provider: Any) -> None:
    """Register the override provider, or clear it with ``None``.

    Idempotent and global. When cleared, the assertion API reverts to pure
    upstream behavior.
    """
    global _OVERRIDE_PROVIDER
    _OVERRIDE_PROVIDER = provider


def get_override_provider() -> Any:
    """Return the currently registered provider, or ``None``."""
    return _OVERRIDE_PROVIDER


def consult_override(fn: Callable, args: tuple, kwargs: dict) -> bool:
    """Return True if a registered provider fully handled this assertion call.

    Guarded against reentrancy: while a provider is handling, the provider is
    not consulted again.
    """
    global _IN_OVERRIDE
    if _OVERRIDE_PROVIDER is None or _IN_OVERRIDE:
        return False
    _IN_OVERRIDE = True
    try:
        return bool(_OVERRIDE_PROVIDER.handle(fn, args, kwargs))
    finally:
        _IN_OVERRIDE = False
