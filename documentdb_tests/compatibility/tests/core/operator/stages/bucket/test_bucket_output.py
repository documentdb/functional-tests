"""Tests for $bucket aggregation stage — output specification behavior."""

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

# Property [Implicit Count Field]: when output is omitted, each bucket
# includes a count field; when output is specified, only _id and the
# specified fields appear; an empty output document returns only _id.
BUCKET_IMPLICIT_COUNT_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 15}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10, 20],
                }
            }
        ],
        expected=[{"_id": 0, "count": 2}, {"_id": 10, "count": 1}],
        msg="$bucket without output should include implicit count field",
        id="output_omitted_includes_count",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 1, "v": 10}, {"_id": 2, "x": 5, "v": 20}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"total": {"$sum": "$v"}},
                }
            }
        ],
        expected=[{"_id": 0, "total": 30}],
        msg="$bucket with output specified should not include implicit count field",
        id="output_specified_no_implicit_count",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {},
                }
            }
        ],
        expected=[{"_id": 0}],
        msg="$bucket with empty output should return only _id",
        id="empty_output_returns_only_id",
    ),
]

# Property [Multiple Accumulators]: multiple accumulator operators can be
# used simultaneously in the output specification.
BUCKET_MULTIPLE_ACCUMULATORS_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[
            {"_id": 1, "x": 1, "v": 10},
            {"_id": 2, "x": 1, "v": 20},
            {"_id": 3, "x": 1, "v": 30},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {
                        "total": {"$sum": "$v"},
                        "avg": {"$avg": "$v"},
                        "items": {"$push": "$v"},
                    },
                }
            }
        ],
        expected=[{"_id": 0, "total": 60, "avg": 20.0, "items": [10, 20, 30]}],
        msg="$bucket output should accept multiple accumulators simultaneously",
        id="multiple_accumulators_in_output",
    ),
]

# Property [Large Accumulator Count]: large numbers of accumulators
# (100+) are accepted in the output specification.
BUCKET_LARGE_ACCUMULATOR_COUNT_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {f"f{i}": {"$sum": 1} for i in range(100)},
                }
            }
        ],
        expected=[{"_id": 0, **{f"f{i}": 2 for i in range(100)}}],
        msg="$bucket should accept 100+ accumulators in output",
        id="large_accumulator_count",
    ),
]

# Property [Accumulator Input Field References]: accumulators reference
# input document fields, not sibling accumulator output fields.
BUCKET_ACCUMULATOR_INPUT_REF_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 1, "v": 10}, {"_id": 2, "x": 1, "v": 20}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {
                        "total": {"$sum": "$v"},
                        "ref_sibling": {"$sum": "$total"},
                    },
                }
            }
        ],
        expected=[{"_id": 0, "total": 30, "ref_sibling": 0}],
        msg=(
            "$bucket accumulators should reference input document"
            " fields, not sibling output fields"
        ),
        id="accumulator_references_input_not_sibling",
    ),
]

# Property [Nested Expressions in Accumulators]: nested expressions work
# within accumulator arguments.
BUCKET_NESTED_EXPR_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 1, "v": 10}, {"_id": 2, "x": 1, "v": 20}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {
                        "result": {"$sum": {"$add": ["$v", 1]}},
                    },
                }
            }
        ],
        expected=[{"_id": 0, "result": 32}],
        msg="$bucket should support nested expressions within accumulators",
        id="nested_expression_in_accumulator",
    ),
]

# Property [Push System Variables]: $push with $$ROOT or $$CURRENT returns
# full input documents; $push with $$REMOVE produces empty arrays.
BUCKET_PUSH_SYSTEM_VAR_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 1, "v": 10}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"docs": {"$push": "$$ROOT"}},
                }
            }
        ],
        expected=[{"_id": 0, "docs": [{"_id": 1, "x": 1, "v": 10}]}],
        msg="$bucket $push with $$ROOT should return full input documents",
        id="push_root_returns_full_docs",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 1, "v": 10}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"docs": {"$push": "$$CURRENT"}},
                }
            }
        ],
        expected=[{"_id": 0, "docs": [{"_id": 1, "x": 1, "v": 10}]}],
        msg="$bucket $push with $$CURRENT should return full input documents",
        id="push_current_returns_full_docs",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"docs": {"$push": "$$REMOVE"}},
                }
            }
        ],
        expected=[{"_id": 0, "docs": []}],
        msg="$bucket $push with $$REMOVE should produce empty arrays",
        id="push_remove_produces_empty_array",
    ),
]

# Property [Output Field Name Acceptance]: empty string, Unicode, emoji,
# spaces, and long field names (1000+ characters) are accepted as output
# field names.
BUCKET_OUTPUT_FIELD_NAME_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {
                        "": {"$sum": 1},
                        "\u00e9": {"$sum": 1},
                        "\U0001f389": {"$sum": 1},
                        "  ": {"$sum": 1},
                        "a" * 1_000: {"$sum": 1},
                    },
                }
            }
        ],
        expected=[
            {
                "_id": 0,
                "": 1,
                "\u00e9": 1,
                "\U0001f389": 1,
                "  ": 1,
                "a" * 1_000: 1,
            }
        ],
        msg=(
            "$bucket should accept empty string, Unicode, emoji,"
            " spaces, and long field names as output field names"
        ),
        id="special_output_field_names",
    ),
]

# Property [Duplicate Output Field Names]: duplicate output field names
# resolve to the last definition.
BUCKET_DUPLICATE_FIELD_NAME_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 1, "v": 10}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": SON(
                        [
                            ("total", {"$sum": "$v"}),
                            ("total", {"$sum": 1}),
                        ]
                    ),
                }
            }
        ],
        expected=[{"_id": 0, "total": 1}],
        msg="$bucket duplicate output field names should resolve to the last definition",
        id="duplicate_output_field_last_wins",
    ),
]

BUCKET_OUTPUT_TESTS = (
    BUCKET_IMPLICIT_COUNT_TESTS
    + BUCKET_MULTIPLE_ACCUMULATORS_TESTS
    + BUCKET_LARGE_ACCUMULATOR_COUNT_TESTS
    + BUCKET_ACCUMULATOR_INPUT_REF_TESTS
    + BUCKET_NESTED_EXPR_TESTS
    + BUCKET_PUSH_SYSTEM_VAR_TESTS
    + BUCKET_OUTPUT_FIELD_NAME_TESTS
    + BUCKET_DUPLICATE_FIELD_NAME_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_OUTPUT_TESTS))
def test_bucket_output(collection, test_case: StageTestCase):
    """Test $bucket output specification behavior."""
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
