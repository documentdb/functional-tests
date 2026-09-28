"""Aggregation $group stage tests - error cases."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    CLUSTER_TIME_NOT_AVAILABLE_ERROR,
    FAILED_TO_PARSE_ERROR,
    FIELD_PATH_DOT_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    GROUP_INCLUSION_STYLE_ERROR,
    GROUP_MISSING_ID_ERROR,
    GROUP_NON_OBJECT_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Structural Errors on Empty and Non-Existent Collections]: structural
# validation errors fire even when the collection is empty or does not exist.
GROUP_EMPTY_INPUT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="empty_collection_non_object_error",
        docs=[],
        pipeline=[{"$group": "not_an_object"}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="Non-object $group argument should error even on empty collection",
    ),
    StageTestCase(
        id="nonexistent_collection_non_object_error",
        docs=None,
        pipeline=[{"$group": "not_an_object"}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="Non-object $group argument should error even on non-existent collection",
    ),
    StageTestCase(
        id="empty_collection_missing_id_error",
        docs=[],
        pipeline=[{"$group": {}}],
        error_code=GROUP_MISSING_ID_ERROR,
        msg="Missing _id should error even on empty collection",
    ),
    StageTestCase(
        id="nonexistent_collection_missing_id_error",
        docs=None,
        pipeline=[{"$group": {}}],
        error_code=GROUP_MISSING_ID_ERROR,
        msg="Missing _id should error even on non-existent collection",
    ),
]

# Property [Stage Argument Type Rejection]: all non-object BSON types as the
# $group stage argument produce an error.
GROUP_STAGE_ARGUMENT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="stage_arg_string",
        docs=[{"_id": 1}],
        pipeline=[{"$group": "not_an_object"}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="String as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$group": 1}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="int32 as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$group": Int64(1)}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="Int64 as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_double",
        docs=[{"_id": 1}],
        pipeline=[{"$group": 1.5}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="double as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$group": Decimal128("1")}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="Decimal128 as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$group": True}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="bool as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_null",
        docs=[{"_id": 1}],
        pipeline=[{"$group": None}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="null as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_array",
        docs=[{"_id": 1}],
        pipeline=[{"$group": [1, 2]}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="array as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$group": ObjectId("507f1f77bcf86cd799439011")}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="ObjectId as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$group": datetime(2024, 1, 1)}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="datetime as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$group": Timestamp(1, 1)}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="Timestamp as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$group": Binary(b"data")}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="Binary as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$group": Regex("abc", "i")}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="Regex as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_code",
        docs=[{"_id": 1}],
        pipeline=[{"$group": Code("function(){}")}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="Code as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$group": MinKey()}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="MinKey as $group argument should produce an error",
    ),
    StageTestCase(
        id="stage_arg_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$group": MaxKey()}],
        error_code=GROUP_NON_OBJECT_ERROR,
        msg="MaxKey as $group argument should produce an error",
    ),
]

# Property [Missing _id Error]: omitting _id from the $group document produces
# an error, even on empty or non-existent collections.
GROUP_MISSING_ID_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="missing_id_with_accumulator",
        docs=[{"_id": 1, "v": 10}],
        pipeline=[{"$group": {"total": {"$sum": "$v"}}}],
        error_code=GROUP_MISSING_ID_ERROR,
        msg="Omitting _id from $group should produce an error",
    ),
]

# Property [Compound _id Field Name Errors]: dots, empty strings, and
# $-prefixed names in compound _id field names produce errors.
GROUP_COMPOUND_ID_FIELD_NAME_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="compound_id_dot_in_field_name",
        docs=[{"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": {"a.b": "$v"}}}],
        error_code=FIELD_PATH_DOT_ERROR,
        msg="Dot in compound _id field name should produce an error",
    ),
    StageTestCase(
        id="compound_id_empty_string_field_name",
        docs=[{"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": {"": "$v"}}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="Empty string as compound _id field name should produce an error",
    ),
    StageTestCase(
        id="compound_id_dollar_prefix_field_name",
        docs=[{"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": {"$bad": "$v"}}}],
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="$-prefixed compound _id field name should produce an error",
    ),
]

# Property [Inclusion-Style Detection Errors (Compound _id)]: any top-level
# field in a compound _id with a numeric (int32, Int64, double, Decimal128) or
# boolean value triggers an error; only top-level fields are checked, and
# $literal wrapping bypasses the check.
GROUP_INCLUSION_STYLE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="inclusion_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": {"a": 1}}}],
        error_code=GROUP_INCLUSION_STYLE_ERROR,
        msg="int32 value in compound _id should trigger inclusion-style error",
    ),
    StageTestCase(
        id="inclusion_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": {"a": Int64(1)}}}],
        error_code=GROUP_INCLUSION_STYLE_ERROR,
        msg="Int64 value in compound _id should trigger inclusion-style error",
    ),
    StageTestCase(
        id="inclusion_double",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": {"a": 1.5}}}],
        error_code=GROUP_INCLUSION_STYLE_ERROR,
        msg="double value in compound _id should trigger inclusion-style error",
    ),
    StageTestCase(
        id="inclusion_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": {"a": Decimal128("1")}}}],
        error_code=GROUP_INCLUSION_STYLE_ERROR,
        msg="Decimal128 value in compound _id should trigger inclusion-style error",
    ),
    StageTestCase(
        id="inclusion_bool_true",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": {"a": True}}}],
        error_code=GROUP_INCLUSION_STYLE_ERROR,
        msg="boolean true in compound _id should trigger inclusion-style error",
    ),
    StageTestCase(
        id="inclusion_bool_false",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": {"a": False}}}],
        error_code=GROUP_INCLUSION_STYLE_ERROR,
        msg="boolean false in compound _id should trigger inclusion-style error",
    ),
]

# Property [String _id Reference Errors]: bare "$" in _id produces an
# invalid field path error, bare "$$" produces a failed-to-parse error, and
# $$CLUSTER_TIME in _id produces a standalone-mode error.
GROUP_STRING_ID_REFERENCE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="bare_dollar_in_id",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": "$"}}],
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="Bare '$' in _id should produce an invalid field path error",
    ),
    StageTestCase(
        id="bare_double_dollar_in_id",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": "$$"}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Bare '$$' in _id should produce a failed-to-parse error",
    ),
    StageTestCase(
        marks=(pytest.mark.requires(cluster_time=False),),
        id="cluster_time_in_id_standalone",
        docs=[{"_id": 1}],
        pipeline=[{"$group": {"_id": "$$CLUSTER_TIME"}}],
        error_code=CLUSTER_TIME_NOT_AVAILABLE_ERROR,
        msg="$$CLUSTER_TIME in _id should produce an error in standalone mode",
    ),
]


GROUP_ERROR_TESTS = (
    GROUP_EMPTY_INPUT_ERROR_TESTS
    + GROUP_STAGE_ARGUMENT_ERROR_TESTS
    + GROUP_MISSING_ID_ERROR_TESTS
    + GROUP_COMPOUND_ID_FIELD_NAME_ERROR_TESTS
    + GROUP_INCLUSION_STYLE_ERROR_TESTS
    + GROUP_STRING_ID_REFERENCE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_ERROR_TESTS))
def test_group_stage_error(collection, test_case: StageTestCase):
    """Test $group stage error cases."""
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
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
