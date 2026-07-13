"""Tests for $bucketAuto aggregation stage — output specification behavior."""

from __future__ import annotations

import pytest
from bson.son import SON

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Implicit Count Field]: when output is omitted each bucket includes
# a count field; specifying output replaces the implicit count with the named
# fields; an empty output document still yields the implicit count.
BUCKET_AUTO_IMPLICIT_COUNT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_omitted_includes_count",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 1}}],
        expected=[{"_id": {"min": 1, "max": 5}, "count": 2}],
        msg="$bucketAuto without output should include implicit count field",
    ),
    StageTestCase(
        "output_specified_replaces_count",
        docs=[{"_id": 1, "x": 1, "v": 10}, {"_id": 2, "x": 5, "v": 20}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {"total": {"$sum": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 1, "max": 5}, "total": 30}],
        msg="$bucketAuto with output specified should not include implicit count field",
    ),
    StageTestCase(
        "output_explicit_count",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {"c": {"$sum": 1}},
                }
            }
        ],
        expected=[{"_id": {"min": 1, "max": 5}, "c": 2}],
        msg="$bucketAuto output can re-add count explicitly via {$sum: 1}",
    ),
    StageTestCase(
        "empty_output_yields_count",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 1, "output": {}}}],
        expected=[{"_id": {"min": 1, "max": 5}, "count": 2}],
        msg="$bucketAuto with an empty output document should still yield the implicit count",
    ),
]

# Property [Multiple Accumulators]: multiple accumulator operators can be used
# simultaneously in the output specification.
BUCKET_AUTO_MULTIPLE_ACCUMULATORS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multiple_accumulators_in_output",
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {
                        "total": {"$sum": "$v"},
                        "avg": {"$avg": "$v"},
                        "items": {"$push": "$v"},
                    },
                }
            }
        ],
        expected=[{"_id": {"min": 1, "max": 1}, "total": 60, "avg": 20.0, "items": [10, 20, 30]}],
        msg="$bucketAuto output should accept multiple accumulators simultaneously",
    ),
]

# Property [Accumulator Input Field References]: accumulators reference input
# document fields, not sibling accumulator output fields.
BUCKET_AUTO_ACCUMULATOR_INPUT_REF_TESTS: list[StageTestCase] = [
    StageTestCase(
        "accumulator_references_input_not_sibling",
        docs=[{"_id": 1, "x": 1, "v": 10}, {"_id": 2, "x": 1, "v": 20}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {
                        "total": {"$sum": "$v"},
                        "ref_sibling": {"$sum": "$total"},
                    },
                }
            }
        ],
        expected=[{"_id": {"min": 1, "max": 1}, "total": 30, "ref_sibling": 0}],
        msg=(
            "$bucketAuto accumulators should reference input document"
            " fields, not sibling output fields"
        ),
    ),
]

# Property [Nested Expressions in Accumulators]: nested expressions work within
# accumulator arguments.
BUCKET_AUTO_NESTED_EXPR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nested_expression_in_accumulator",
        docs=[{"_id": 1, "x": 1, "v": 10}, {"_id": 2, "x": 1, "v": 20}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {"result": {"$sum": {"$add": ["$v", 1]}}},
                }
            }
        ],
        expected=[{"_id": {"min": 1, "max": 1}, "result": 32}],
        msg="$bucketAuto should support nested expressions within accumulators",
    ),
]

# Property [Push System Variables]: $push with $$ROOT or $$CURRENT returns full
# input documents; $push with $$REMOVE produces empty arrays.
BUCKET_AUTO_PUSH_SYSTEM_VAR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "push_root_returns_full_docs",
        docs=[{"_id": 1, "x": 1, "v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {"docs": {"$push": "$$ROOT"}},
                }
            }
        ],
        expected=[{"_id": {"min": 1, "max": 1}, "docs": [{"_id": 1, "x": 1, "v": 10}]}],
        msg="$bucketAuto $push with $$ROOT should return full input documents",
    ),
    StageTestCase(
        "push_current_returns_full_docs",
        docs=[{"_id": 1, "x": 1, "v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {"docs": {"$push": "$$CURRENT"}},
                }
            }
        ],
        expected=[{"_id": {"min": 1, "max": 1}, "docs": [{"_id": 1, "x": 1, "v": 10}]}],
        msg="$bucketAuto $push with $$CURRENT should return full input documents",
    ),
    StageTestCase(
        "push_remove_produces_empty_array",
        docs=[{"_id": 1, "x": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {"docs": {"$push": "$$REMOVE"}},
                }
            }
        ],
        expected=[{"_id": {"min": 1, "max": 1}, "docs": []}],
        msg="$bucketAuto $push with $$REMOVE should produce empty arrays",
    ),
]

# Property [Output Field Name Acceptance]: empty string, Unicode, emoji,
# spaces, and long field names are accepted as output field names.
BUCKET_AUTO_OUTPUT_FIELD_NAME_TESTS: list[StageTestCase] = [
    StageTestCase(
        "special_output_field_names",
        docs=[{"_id": 1, "x": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {
                        "": {"$sum": 1},
                        "é": {"$sum": 1},
                        "\U0001f389": {"$sum": 1},
                        "  ": {"$sum": 1},
                        "a" * 1_000: {"$sum": 1},
                    },
                }
            }
        ],
        expected=[
            {
                "_id": {"min": 1, "max": 1},
                "": 1,
                "é": 1,
                "\U0001f389": 1,
                "  ": 1,
                "a" * 1_000: 1,
            }
        ],
        msg=(
            "$bucketAuto should accept empty string, Unicode, emoji,"
            " spaces, and long field names as output field names"
        ),
    ),
]

# Property [Duplicate Output Field Names]: duplicate output field names resolve
# to the last definition.
BUCKET_AUTO_DUPLICATE_FIELD_NAME_TESTS: list[StageTestCase] = [
    StageTestCase(
        "duplicate_output_field_last_wins",
        docs=[{"_id": 1, "x": 1, "v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": SON(
                        [
                            ("total", {"$sum": "$v"}),
                            ("total", {"$sum": 1}),
                        ]
                    ),
                }
            }
        ],
        expected=[{"_id": {"min": 1, "max": 1}, "total": 1}],
        msg="$bucketAuto duplicate output field names should resolve to the last definition",
    ),
]

BUCKET_AUTO_OUTPUT_TESTS = (
    BUCKET_AUTO_IMPLICIT_COUNT_TESTS
    + BUCKET_AUTO_MULTIPLE_ACCUMULATORS_TESTS
    + BUCKET_AUTO_ACCUMULATOR_INPUT_REF_TESTS
    + BUCKET_AUTO_NESTED_EXPR_TESTS
    + BUCKET_AUTO_PUSH_SYSTEM_VAR_TESTS
    + BUCKET_AUTO_OUTPUT_FIELD_NAME_TESTS
    + BUCKET_AUTO_DUPLICATE_FIELD_NAME_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_OUTPUT_TESTS))
def test_bucketAuto_output(collection, test_case: StageTestCase):
    """Test $bucketAuto output specification behavior."""
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
