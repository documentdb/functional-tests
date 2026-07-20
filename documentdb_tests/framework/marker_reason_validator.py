"""
Marker reason validator.

Enforces that markers which suppress or reclassify a test's outcome always carry
an explanation, so a run's skipped/xfailed tests are never unexplained. Checked
statically at collection time alongside the other framework invariants.

Covers two forms:

- **Markers** — ``@pytest.mark.skip`` / ``skipif`` / ``xfail`` and this repo's
  ``engine_xfail`` / ``engine_xcrash`` variants, via their ``reason=``.
- **Runtime calls** — ``pytest.skip(...)`` / ``fail(...)`` / ``xfail(...)``, via
  their positional message or ``reason=`` / ``msg=``.
"""

from __future__ import annotations

import ast

# Markers that must justify why they suppress or reclassify an outcome.
MARKERS_REQUIRING_REASON = frozenset({"skip", "skipif", "xfail", "engine_xfail", "engine_xcrash"})

# Bare (uncalled) decorator form is only meaningful for these two.
BARE_DECORATOR_MARKERS = frozenset({"skip", "xfail"})

# Runtime functions that suppress/reclassify an outcome and take a message.
RUNTIME_SKIP_FUNCTIONS = frozenset({"skip", "fail", "xfail"})


def _marker_name(node: ast.expr) -> str | None:
    """
    Return the marker name if ``node`` refers to a ``*.mark.<name>`` attribute.

    Matches ``pytest.mark.xfail`` and friends regardless of the module prefix, so
    it works for decorators, ``marks=`` entries, and module-level constants alike.
    """
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
    ):
        return node.attr
    return None


def _is_valid_explanation(value: ast.expr) -> bool:
    """
    An explanation is valid when present and, if a string literal, non-empty.

    A non-literal (Name / f-string / concatenation) is accepted because its value
    can't be resolved statically.
    """
    if isinstance(value, ast.Constant):
        return isinstance(value.value, str) and value.value.strip() != ""
    return True


def _marker_has_valid_reason(call: ast.Call) -> bool:
    """A marker's ``reason=`` keyword must be present and a valid explanation."""
    for keyword in call.keywords:
        if keyword.arg == "reason":
            return _is_valid_explanation(keyword.value)
    return False


def _runtime_skip_function(node: ast.Call) -> str | None:
    """
    Return the function name for a ``pytest.skip``/``fail``/``xfail`` call.

    Matches both ``pytest.skip(...)`` (attribute) and a bare ``skip(...)``
    imported via ``from pytest import skip``.
    """
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in RUNTIME_SKIP_FUNCTIONS:
        # Exclude marker attributes (``pytest.mark.skip``); those are handled
        # separately and would otherwise be double-flagged.
        if isinstance(func.value, ast.Attribute) and func.value.attr == "mark":
            return None
        return func.attr
    if isinstance(func, ast.Name) and func.id in RUNTIME_SKIP_FUNCTIONS:
        return func.id
    return None


def _runtime_call_has_message(call: ast.Call) -> bool:
    """A runtime skip/fail/xfail call needs a present, non-empty-if-literal message."""
    if call.args:
        return _is_valid_explanation(call.args[0])
    for keyword in call.keywords:
        if keyword.arg in ("reason", "msg"):
            return _is_valid_explanation(keyword.value)
    return False


def validate_marker_reasons(file_path: str) -> list[str]:
    """
    Validate that outcome-suppressing markers carry a reason.

    Returns:
        List of error messages for violations (empty if the file is clean or
        cannot be parsed).
    """
    errors: list[str] = []

    try:
        with open(file_path) as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception:
        return errors  # Skip files that can't be parsed

    # Called form: @pytest.mark.xfail(...), marks=pytest.mark.engine_xfail(...),
    # or module-level constants like X = pytest.mark.engine_xfail(...).
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _marker_name(node.func)
        if name in MARKERS_REQUIRING_REASON and not _marker_has_valid_reason(node):
            errors.append(
                f"  Line {node.lineno}: @pytest.mark.{name}(...) must pass a non-empty reason=."
            )
        # Runtime call form: pytest.skip(...) / fail(...) / xfail(...).
        runtime_name = _runtime_skip_function(node)
        if runtime_name is not None and not _runtime_call_has_message(node):
            errors.append(
                f"  Line {node.lineno}: pytest.{runtime_name}() must be called with "
                f"a non-empty message explaining why."
            )

    # Bare decorator form: @pytest.mark.skip / @pytest.mark.xfail (no reason at all).
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for decorator in node.decorator_list:
            name = _marker_name(decorator)
            if name in BARE_DECORATOR_MARKERS:
                errors.append(
                    f"  Line {decorator.lineno}: @pytest.mark.{name} used without a "
                    f"reason= (add @pytest.mark.{name}(reason=...))."
                )

    return errors
