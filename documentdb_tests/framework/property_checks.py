"""Property check primitives for ``assertProperties``.

Each check class evaluates a single field value against an expectation
and returns an error string on failure or ``None`` on success.
"""

from __future__ import annotations

from datetime import datetime as _datetime
from typing import Any

from bson import Binary, Decimal128, Int64

from documentdb_tests.framework.bson_compare import _NUMERIC_BSON_TYPES, strict_equal

_FIELD_ABSENT = object()
"""Sentinel used by check classes when a dotted path is absent."""


class Check:
    """Base class for property checks used with ``assertProperties``."""

    def check(self, value: Any, path: str) -> str | None:
        raise NotImplementedError


class Exists(Check):
    """Assert that the field is present."""

    def check(self, value: Any, path: str) -> str | None:
        if value is _FIELD_ABSENT:
            return f"expected '{path}' to exist"
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class NotExists(Check):
    """Assert that the field is absent."""

    def check(self, value: Any, path: str) -> str | None:
        if value is not _FIELD_ABSENT:
            return f"expected '{path}' to be absent, got {value!r}"
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class IsType(Check):
    """Assert the BSON type name of the field (as returned by ``$type``)."""

    _PY_TO_BSON: dict[type[Any], str] = {
        float: "double",
        str: "string",
        dict: "object",
        list: "array",
        Binary: "binData",
        bool: "bool",
        type(None): "null",
        int: "int",
        Int64: "long",
        Decimal128: "decimal",
        _datetime: "date",
    }

    _VALID_TYPES: set[str] = set(_PY_TO_BSON.values())

    def __init__(self, bson_type: str) -> None:
        if bson_type not in self._VALID_TYPES:
            raise ValueError(
                f"unknown BSON type {bson_type!r}, expected one of {sorted(self._VALID_TYPES)}"
            )
        self.bson_type = bson_type

    def check(self, value: Any, path: str) -> str | None:
        if value is _FIELD_ABSENT:
            return f"expected '{path}' to have type '{self.bson_type}', but field is missing"
        actual = self._PY_TO_BSON.get(type(value), type(value).__name__)
        if actual != self.bson_type:
            return f"expected '{path}' type '{self.bson_type}', got '{actual}'"
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.bson_type!r})"


class Eq(Check):
    """Assert that the field equals an expected value."""

    def __init__(self, expected: Any) -> None:
        self.expected = expected

    def check(self, value: Any, path: str) -> str | None:
        if value is _FIELD_ABSENT:
            return f"expected '{path}' == {self.expected!r}, but field is missing"
        if not strict_equal(value, self.expected):
            return f"expected '{path}' == {self.expected!r}, got {value!r}"
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.expected!r})"


class Len(Check):
    """Assert that the field is a list with the expected length."""

    def __init__(self, expected: int) -> None:
        self.expected = expected

    def check(self, value: Any, path: str) -> str | None:
        if value is _FIELD_ABSENT:
            return f"expected '{path}' to have length {self.expected}, but field is missing"
        if not isinstance(value, list):
            return f"expected '{path}' to be a list, got {type(value).__name__}"
        if len(value) != self.expected:
            return f"expected '{path}' length {self.expected}, got {len(value)}"
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.expected!r})"


class Contains(Check):
    """Assert that a list contains a dict where ``key`` equals ``value``."""

    def __init__(self, key: str, value: Any) -> None:
        self.key = key
        self.value = value

    def check(self, value: Any, path: str) -> str | None:
        if value is _FIELD_ABSENT:
            return f"expected '{path}' to exist"
        if not isinstance(value, list):
            return f"expected '{path}' to be a list, got {type(value).__name__}"
        for item in value:
            if isinstance(item, dict) and strict_equal(item.get(self.key), self.value):
                return None
        return f"expected '{path}' to contain {self.key}={self.value!r}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.key!r}, {self.value!r})"


class NotContains(Check):
    """Assert that no dict in a list has ``key`` equal to ``value``."""

    def __init__(self, key: str, value: Any) -> None:
        self.key = key
        self.value = value

    def check(self, value: Any, path: str) -> str | None:
        if value is _FIELD_ABSENT:
            return None
        if not isinstance(value, list):
            return f"expected '{path}' to be a list, got {type(value).__name__}"
        for item in value:
            if isinstance(item, dict) and strict_equal(item.get(self.key), self.value):
                return f"expected '{path}' not to contain {self.key}={self.value!r}"
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.key!r}, {self.value!r})"


class Ne(Check):
    """Assert that the field does not equal a value."""

    def __init__(self, rejected: Any) -> None:
        self.rejected = rejected

    def check(self, value: Any, path: str) -> str | None:
        if value is _FIELD_ABSENT:
            return None  # absent is not equal
        if strict_equal(value, self.rejected):
            return f"expected '{path}' != {self.rejected!r}, but got {value!r}"
        if (
            type(value) in _NUMERIC_BSON_TYPES
            and type(self.rejected) in _NUMERIC_BSON_TYPES
            and type(value) is not type(self.rejected)
        ):
            return (
                f"Ne() type mismatch on '{path}': actual is {type(value).__name__} "
                f"but rejected value is {type(self.rejected).__name__} — "
                f"cross-type numeric Ne is always true"
            )
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.rejected!r})"


class Gt(Check):
    """Assert that the field is strictly greater than a value."""

    def __init__(self, minimum: Any) -> None:
        self.minimum = minimum

    def check(self, value: Any, path: str) -> str | None:
        if value is _FIELD_ABSENT:
            return f"expected '{path}' > {self.minimum!r}, but field is missing"
        if value <= self.minimum:
            return f"expected '{path}' > {self.minimum!r}, got {value!r}"
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.minimum!r})"


class Gte(Check):
    """Assert that the field is greater than or equal to a value."""

    def __init__(self, minimum: Any) -> None:
        self.minimum = minimum

    def check(self, value: Any, path: str) -> str | None:
        if value is _FIELD_ABSENT:
            return f"expected '{path}' >= {self.minimum!r}, but field is missing"
        if value < self.minimum:
            return f"expected '{path}' >= {self.minimum!r}, got {value!r}"
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.minimum!r})"
