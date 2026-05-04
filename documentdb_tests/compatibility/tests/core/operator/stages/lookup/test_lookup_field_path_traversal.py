"""Tests for $lookup field path traversal in localField and foreignField."""

from __future__ import annotations

import pytest
from bson import DBRef

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Path Traversal]: dot-notation in localField and
# foreignField traverses nested documents and arrays.
LOOKUP_FIELD_PATH_TRAVERSAL_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "dot_notation_traverses_nested_documents",
        docs=[
            {"_id": 1, "nested": {"val": "a"}},
            {"_id": 2, "nested": {"val": "b"}},
        ],
        foreign_docs=[
            {"_id": 10, "deep": {"val": "a"}},
            {"_id": 11, "deep": {"val": "b"}},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "nested.val",
                    "foreignField": "deep.val",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "nested": {"val": "a"},
                "joined": [{"_id": 10, "deep": {"val": "a"}}],
            },
            {
                "_id": 2,
                "nested": {"val": "b"},
                "joined": [{"_id": 11, "deep": {"val": "b"}}],
            },
        ],
        msg=(
            "$lookup should traverse nested documents via dot-notation"
            " in both localField and foreignField"
        ),
    ),
    LookupTestCase(
        "array_traversal_extracts_field_from_each_element",
        docs=[
            {"_id": 1, "arr": [{"val": "a"}, {"val": "b"}]},
        ],
        foreign_docs=[
            {"_id": 10, "ff": "a"},
            {"_id": 11, "ff": "b"},
            {"_id": 12, "ff": "c"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "arr.val",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "arr": [{"val": "a"}, {"val": "b"}],
                "joined": [
                    {"_id": 10, "ff": "a"},
                    {"_id": 11, "ff": "b"},
                ],
            },
        ],
        msg=(
            "$lookup should extract the specified field from each element"
            " of an intermediate array when traversing with dot-notation"
        ),
    ),
    LookupTestCase(
        "numeric_path_component_indexes_into_array",
        docs=[{"_id": 1, "arr": ["x", "y", "z"]}],
        foreign_docs=[
            {"_id": 10, "ff": "x"},
            {"_id": 11, "ff": "y"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "arr.0",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "arr": ["x", "y", "z"],
                "joined": [{"_id": 10, "ff": "x"}],
            },
        ],
        msg=(
            "$lookup should use numeric path components to index into"
            ' arrays (e.g., "arr.0" accesses the first element)'
        ),
    ),
    LookupTestCase(
        "out_of_bounds_numeric_index_local_resolves_to_missing",
        docs=[{"_id": 1, "arr": ["x", "y"]}],
        foreign_docs=[
            {"_id": 10, "ff": None},
            {"_id": 11},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "arr.99",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "arr": ["x", "y"],
                "joined": [
                    {"_id": 10, "ff": None},
                    {"_id": 11},
                ],
            },
        ],
        msg=(
            "$lookup should resolve out-of-bounds numeric index in"
            " localField to missing, matching null/missing foreign"
        ),
    ),
    LookupTestCase(
        "negative_numeric_index_local_resolves_to_missing",
        docs=[{"_id": 1, "arr": ["x", "y"]}],
        foreign_docs=[
            {"_id": 10, "ff": None},
            {"_id": 11},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "arr.-1",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "arr": ["x", "y"],
                "joined": [
                    {"_id": 10, "ff": None},
                    {"_id": 11},
                ],
            },
        ],
        msg=(
            "$lookup should resolve negative numeric index in localField"
            " to missing, matching null/missing foreign"
        ),
    ),
    LookupTestCase(
        "unicode_and_special_characters_in_field_paths",
        docs=[{"_id": 1, "données": {"café": "a"}}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "données.café",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "données": {"café": "a"},
                "joined": [{"_id": 10, "ff": "a"}],
            },
        ],
        msg="$lookup should accept Unicode characters in field paths",
    ),
    LookupTestCase(
        "space_in_field_path",
        docs=[{"_id": 1, "a b": "x"}],
        foreign_docs=[{"_id": 10, "ff": "x"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "a b",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "a b": "x",
                "joined": [{"_id": 10, "ff": "x"}],
            },
        ],
        msg="$lookup should accept spaces in field paths",
    ),
    LookupTestCase(
        "dollar_sign_in_middle_of_field_path",
        docs=[{"_id": 1, "a$b": "x"}],
        foreign_docs=[{"_id": 10, "ff": "x"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "a$b",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "a$b": "x",
                "joined": [{"_id": 10, "ff": "x"}],
            },
        ],
        msg="$lookup should accept dollar signs in middle positions of field paths",
    ),
    LookupTestCase(
        "dollar_sign_at_end_of_field_path",
        docs=[{"_id": 1, "ab$": "x"}],
        foreign_docs=[{"_id": 10, "ff": "x"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "ab$",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "ab$": "x",
                "joined": [{"_id": 10, "ff": "x"}],
            },
        ],
        msg="$lookup should accept dollar signs at end positions of field paths",
    ),
    LookupTestCase(
        "control_character_in_field_path",
        docs=[{"_id": 1, "a\x01b": "x"}],
        foreign_docs=[{"_id": 10, "ff": "x"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "a\x01b",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "a\x01b": "x",
                "joined": [{"_id": 10, "ff": "x"}],
            },
        ],
        msg="$lookup should accept control characters in field paths",
    ),
    LookupTestCase(
        "dbref_field_names_accepted",
        docs=[
            {"_id": 1, "ref": DBRef("mycoll", "abc", "mydb")},
        ],
        foreign_docs=[
            {"_id": 10, "ff": "mydb"},
            {"_id": 11, "ff": "other"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "ref.$db",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "ref": DBRef("mycoll", "abc", "mydb"),
                "joined": [{"_id": 10, "ff": "mydb"}],
            },
        ],
        msg=(
            "$lookup should accept DBRef field names ($db, $ref, $id)"
            " as $-prefixed path components"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_FIELD_PATH_TRAVERSAL_TESTS))
def test_lookup_field_path_traversal(collection, test_case: LookupTestCase):
    """Test $lookup field path traversal."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
