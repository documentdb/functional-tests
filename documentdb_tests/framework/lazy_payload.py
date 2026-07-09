"""Deferred construction of large test payloads.

Some tests operate on multi-megabyte strings and byte buffers. Building those
values directly in the parametrized test data keeps every copy in memory for the
whole session, on every xdist worker, which is a large and needless footprint.

Wrap the large value in ``Lazy`` so the test data holds only a small builder.
The framework calls ``materialize`` where it consumes the value (building the
command and comparing the expected result), so the large value is created only
while its own test runs and is freed afterward. Plain values pass through
``materialize`` untouched, so wrapping is needed only on the large fields.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar, cast

T = TypeVar("T")


class Lazy:
    """A value built on demand rather than when the test data is defined."""

    def __init__(self, build: Callable[[], Any]) -> None:
        self.build = build

    def resolve(self) -> Any:
        return materialize(self.build())

    def __repr__(self) -> str:
        return "Lazy(...)"


def lazy(build: Callable[[], T]) -> T:
    """Defer building a value until test time, keeping the field's normal type.

    Returns a ``Lazy`` at runtime but is typed as the value ``build`` produces, so
    a field annotated ``list[dict]`` can hold ``lazy(lambda: [...])`` without
    widening its type and ordinary consumers still see the built type.
    ``materialize`` replaces it with the built value where the framework uses it.
    """
    return cast(T, Lazy(build))


def materialize(value: Any) -> Any:
    """Return ``value`` with any ``Lazy`` in it replaced by its built result.

    Recurses through dicts, lists, and tuples so a ``Lazy`` nested inside a
    command or an expected document is resolved too. When a container holds no
    ``Lazy``, the original object is returned unchanged, so calling this on
    ordinary values on a hot path is cheap and allocation-free.
    """
    if isinstance(value, Lazy):
        return value.resolve()
    if isinstance(value, dict):
        built_dict = {key: materialize(item) for key, item in value.items()}
        if any(built_dict[key] is not value[key] for key in value):
            return built_dict
        return value
    if isinstance(value, list):
        built_list = [materialize(item) for item in value]
        if any(new is not old for new, old in zip(built_list, value)):
            return built_list
        return value
    if isinstance(value, tuple):
        built_tuple = tuple(materialize(item) for item in value)
        if any(new is not old for new, old in zip(built_tuple, value)):
            return built_tuple
        return value
    return value
