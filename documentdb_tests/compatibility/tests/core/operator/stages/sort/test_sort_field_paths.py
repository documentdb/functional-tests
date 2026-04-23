from __future__ import annotations

from functools import reduce
from typing import Any, cast

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Nested Field Paths]: dot notation traverses into embedded
# documents and arrays of objects for sort key extraction.
SORT_NESTED_FIELD_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nested_dot_notation_asc",
        docs=[
            {"_id": 1, "a": {"b": 30}},
            {"_id": 2, "a": {"b": 10}},
        ],
        pipeline=[{"$sort": {"a.b": 1}}],
        expected=[
            {"_id": 2, "a": {"b": 10}},
            {"_id": 1, "a": {"b": 30}},
        ],
        msg="$sort should traverse embedded documents via dot notation ascending",
    ),
    StageTestCase(
        "nested_dot_notation_desc",
        docs=[
            {"_id": 1, "a": {"b": 30}},
            {"_id": 2, "a": {"b": 10}},
        ],
        pipeline=[{"$sort": {"a.b": -1}}],
        expected=[
            {"_id": 1, "a": {"b": 30}},
            {"_id": 2, "a": {"b": 10}},
        ],
        msg="$sort should traverse embedded documents via dot notation descending",
    ),
    StageTestCase(
        "nested_array_of_objects_asc",
        docs=[
            {"_id": 3, "a": [{"b": 20}, {"b": 15}]},
            {"_id": 2, "a": [{"b": 25}, {"b": 5}]},
            {"_id": 1, "a": [{"b": 30}, {"b": 10}]},
        ],
        pipeline=[{"$sort": {"a.b": 1, "_id": 1}}],
        expected=[
            {"_id": 2, "a": [{"b": 25}, {"b": 5}]},
            {"_id": 1, "a": [{"b": 30}, {"b": 10}]},
            {"_id": 3, "a": [{"b": 20}, {"b": 15}]},
        ],
        msg=(
            "$sort ascending should use min of nested field values"
            " extracted from array of objects"
        ),
    ),
    StageTestCase(
        "nested_array_of_objects_desc",
        docs=[
            {"_id": 3, "a": [{"b": 20}, {"b": 15}]},
            {"_id": 2, "a": [{"b": 25}, {"b": 5}]},
            {"_id": 1, "a": [{"b": 30}, {"b": 10}]},
        ],
        pipeline=[{"$sort": {"a.b": -1, "_id": 1}}],
        expected=[
            {"_id": 1, "a": [{"b": 30}, {"b": 10}]},
            {"_id": 2, "a": [{"b": 25}, {"b": 5}]},
            {"_id": 3, "a": [{"b": 20}, {"b": 15}]},
        ],
        msg=(
            "$sort descending should use max of nested field values"
            " extracted from array of objects"
        ),
    ),
    StageTestCase(
        "nested_non_traversable_intermediate_treated_as_missing_asc",
        docs=[
            {"_id": 1, "a": 42},
            {"_id": 2, "a": None},
            {"_id": 3, "a": {"b": 10}},
            {"_id": 4},
            {"_id": 5, "a": {"b": 5}},
        ],
        pipeline=[{"$sort": {"a.b": 1, "_id": 1}}],
        expected=[
            {"_id": 1, "a": 42},
            {"_id": 2, "a": None},
            {"_id": 4},
            {"_id": 5, "a": {"b": 5}},
            {"_id": 3, "a": {"b": 10}},
        ],
        msg="$sort ascending should treat scalar and null at an intermediate path level as missing",
    ),
    StageTestCase(
        "nested_non_traversable_intermediate_treated_as_missing_desc",
        docs=[
            {"_id": 1, "a": 42},
            {"_id": 2, "a": None},
            {"_id": 3, "a": {"b": 10}},
            {"_id": 4},
            {"_id": 5, "a": {"b": 5}},
        ],
        pipeline=[{"$sort": {"a.b": -1, "_id": 1}}],
        expected=[
            {"_id": 3, "a": {"b": 10}},
            {"_id": 5, "a": {"b": 5}},
            {"_id": 1, "a": 42},
            {"_id": 2, "a": None},
            {"_id": 4},
        ],
        msg=(
            "$sort descending should treat scalar and null"
            " at an intermediate path level as missing"
        ),
    ),
    # The server limits document nesting to 180 levels, so the sort path
    # can only be verified up to that depth. The 200-component path test
    # below only proves acceptance (all values are missing).
    StageTestCase(
        "nested_max_depth_sort",
        docs=[
            {"_id": 1, **reduce(lambda v, k: {k: v}, reversed(["a"] * 180), cast(Any, 20))},
            {"_id": 2, **reduce(lambda v, k: {k: v}, reversed(["a"] * 180), cast(Any, 10))},
        ],
        pipeline=[{"$sort": {".".join(["a"] * 180): 1}}],
        expected=[
            {"_id": 2, **reduce(lambda v, k: {k: v}, reversed(["a"] * 180), cast(Any, 10))},
            {"_id": 1, **reduce(lambda v, k: {k: v}, reversed(["a"] * 180), cast(Any, 20))},
        ],
        msg="$sort should sort by a field path at the maximum document nesting depth of 180",
    ),
    StageTestCase(
        "nested_200_component_path_accepted",
        docs=[
            {"_id": 3, "v": 30},
            {"_id": 1, "v": 10},
            {"_id": 2, "v": 20},
        ],
        pipeline=[
            {"$sort": {".".join(["a"] * 200): 1, "_id": 1}},
        ],
        expected=[
            {"_id": 1, "v": 10},
            {"_id": 2, "v": 20},
            {"_id": 3, "v": 30},
        ],
        msg="$sort should accept a 200-component field path without error",
    ),
]

# Property [Field Name Acceptance]: field names with non-leading dollar signs,
# spaces, numeric names, and Unicode characters are accepted.
SORT_FIELD_NAME_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_name_non_leading_dollar",
        docs=[{"_id": 1, "a$bc": 20}, {"_id": 2, "a$bc": 10}],
        pipeline=[{"$sort": {"a$bc": 1}}],
        expected=[{"_id": 2, "a$bc": 10}, {"_id": 1, "a$bc": 20}],
        msg="$sort should accept non-leading $ in field names",
    ),
    StageTestCase(
        "field_name_space",
        docs=[{"_id": 1, "field name": 20}, {"_id": 2, "field name": 10}],
        pipeline=[{"$sort": {"field name": 1}}],
        expected=[{"_id": 2, "field name": 10}, {"_id": 1, "field name": 20}],
        msg="$sort should accept spaces in field names",
    ),
    StageTestCase(
        "field_name_numeric",
        docs=[{"_id": 1, "123": 20}, {"_id": 2, "123": 10}],
        pipeline=[{"$sort": {"123": 1}}],
        expected=[{"_id": 2, "123": 10}, {"_id": 1, "123": 20}],
        msg="$sort should accept numeric field names",
    ),
    StageTestCase(
        "field_name_unicode",
        docs=[{"_id": 1, "caf\u00e9": 20}, {"_id": 2, "caf\u00e9": 10}],
        pipeline=[{"$sort": {"caf\u00e9": 1}}],
        expected=[{"_id": 2, "caf\u00e9": 10}, {"_id": 1, "caf\u00e9": 20}],
        msg="$sort should accept Unicode characters in field names",
    ),
]

SORT_FIELD_PATH_TESTS = SORT_NESTED_FIELD_TESTS + SORT_FIELD_NAME_ACCEPTANCE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SORT_FIELD_PATH_TESTS))
def test_sort_field_paths(collection, test_case: StageTestCase):
    """Test $sort field path traversal and name acceptance."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
