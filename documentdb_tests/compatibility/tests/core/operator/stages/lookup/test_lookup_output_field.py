"""Tests for $lookup output field (as) behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Output Field (as) Behavior]: the as field overwrites any
# existing field of the same name and always produces an array.
LOOKUP_OUTPUT_FIELD_AS_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "as_overwrites_existing_field",
        docs=[{"_id": 1, "lf": "a", "joined": "old_value"}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [{"_id": 10, "ff": "a"}],
            },
        ],
        msg=(
            "$lookup should overwrite an existing field when as names"
            " a field that already exists in the input document"
        ),
    ),
    LookupTestCase(
        "as_id_overwrites_document_id",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "_id",
                }
            }
        ],
        expected=[
            {"_id": [{"_id": 10, "ff": "a"}], "lf": "a"},
        ],
        msg="$lookup should overwrite the document _id with the joined array when as='_id'",
    ),
    LookupTestCase(
        "dotted_as_path_creates_nested_structure",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "a.b",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "a": {"b": [{"_id": 10, "ff": "a"}]},
            },
        ],
        msg=(
            "$lookup should create a nested document structure when as"
            ' uses a dotted path (e.g., "a.b" creates {a: {b: [...]}}'
            ")"
        ),
    ),
    LookupTestCase(
        "dotted_as_path_preserves_sibling_keys",
        docs=[{"_id": 1, "lf": "a", "a": {"x": 1}}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "a.b",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "a": {"x": 1, "b": [{"_id": 10, "ff": "a"}]},
            },
        ],
        msg=(
            "$lookup should preserve existing sibling keys at the same"
            " nesting level when as creates a nested path"
        ),
    ),
    LookupTestCase(
        "long_as_field_name",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "x" * 10_000,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "x" * 10_000: [{"_id": 10, "ff": "a"}],
            },
        ],
        msg="$lookup should accept as field names with no practical string length limit",
    ),
    LookupTestCase(
        "numeric_dotted_as_components_are_string_keys",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "a.0.b",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "a": {"0": {"b": [{"_id": 10, "ff": "a"}]}},
            },
        ],
        msg=(
            "$lookup should treat numeric components in dotted as paths"
            " as string keys, not array indices"
        ),
    ),
    LookupTestCase(
        "dotted_as_replaces_scalar_parent",
        docs=[{"_id": 1, "lf": "a", "a": "scalar"}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "a.b",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "a": {"b": [{"_id": 10, "ff": "a"}]},
            },
        ],
        msg=(
            "$lookup should replace a scalar value at a parent level"
            " with a nested document when as creates a nested path"
        ),
    ),
    LookupTestCase(
        "dotted_as_replaces_array_parent",
        docs=[{"_id": 1, "lf": "a", "a": [1, 2, 3]}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "a.b",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "a": {"b": [{"_id": 10, "ff": "a"}]},
            },
        ],
        msg=(
            "$lookup should replace an array value at a parent level"
            " with a nested document when as creates a nested path"
        ),
    ),
    LookupTestCase(
        "as_same_as_local_field_uses_original_for_matching",
        docs=[{"_id": 1, "lf": "a"}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "lf",
                }
            }
        ],
        expected=[
            {"_id": 1, "lf": [{"_id": 10, "ff": "a"}]},
        ],
        msg=(
            "$lookup should use the original localField value for matching"
            " before overwriting it when as names the same field"
        ),
    ),
    LookupTestCase(
        "multiple_lookups_same_as_field_last_wins",
        docs=[{"_id": 1, "lf1": "a", "lf2": "b"}],
        foreign_docs=[
            {"_id": 10, "ff1": "a"},
            {"_id": 11, "ff2": "b"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf1",
                    "foreignField": "ff1",
                    "as": "joined",
                }
            },
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf2",
                    "foreignField": "ff2",
                    "as": "joined",
                }
            },
        ],
        expected=[
            {
                "_id": 1,
                "lf1": "a",
                "lf2": "b",
                "joined": [{"_id": 11, "ff2": "b"}],
            },
        ],
        msg=(
            "$lookup should overwrite the previous stage output when"
            " multiple $lookup stages use the same as field name"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_OUTPUT_FIELD_AS_TESTS))
def test_lookup_output_field(collection, test_case: LookupTestCase):
    """Test $lookup output field (as) behavior."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
