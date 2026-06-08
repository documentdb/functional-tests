"""
Tests error behavior for the $elemMatch projection operator.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import SON, Binary, Code, Int64, MaxKey, MinKey, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    ELEMMATCH_NESTED_FIELD_ERROR,
    ELEMMATCH_OBJECT_REQUIRED_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    NEAR_NOT_ALLOWED_ERROR,
    PROJECT_ELEMATCH_CONFLICT_ERROR,
    PROJECT_ELEMATCH_POSITIONAL_CONFLICT_ERROR,
    QUERY_FEATURE_NOT_ALLOWED,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    OID_EPOCH,
)

# Property [Condition Type Validation - Errors]: a non-object value as the
# $elemMatch condition produces an error for every non-object BSON type.
ELEMMATCH_CONDITION_TYPE_ERROR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        f"cond_type_error_{tid}",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"arr": {"$elemMatch": val}},
        error_code=ELEMMATCH_OBJECT_REQUIRED_ERROR,
        msg=f"$elemMatch should reject a {tid} condition",
    )
    for tid, val in [
        ("null", None),
        ("bool", True),
        ("int32", 5),
        ("double", 3.14),
        ("int64", Int64(7)),
        ("decimal128", DECIMAL128_HALF),
        ("string", "hello"),
        ("empty_array", []),
        ("nonempty_array", [1, 2]),
        ("objectid", OID_EPOCH),
        ("datetime", datetime(2020, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01")),
        ("regex", Regex("^a", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Field Path Errors]: an invalid projection field name for $elemMatch
# produces a field-path validation error.
ELEMMATCH_FIELD_PATH_ERROR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "field_path_error_dotted",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"a.b": {"$elemMatch": {"$gt": 0}}},
        error_code=ELEMMATCH_NESTED_FIELD_ERROR,
        msg="$elemMatch should reject a dotted projection field name",
    ),
    ProjectionTestCase(
        "field_path_error_empty",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"": {"$elemMatch": {"$gt": 0}}},
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$elemMatch should reject an empty projection field name",
    ),
    ProjectionTestCase(
        "field_path_error_dollar_prefix",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"$foo": {"$elemMatch": {"$gt": 0}}},
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$elemMatch should reject a dollar-prefixed projection field name",
    ),
    ProjectionTestCase(
        "field_path_error_trailing_dot",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"arr.": {"$elemMatch": {"$gt": 0}}},
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$elemMatch should reject a projection field name with a trailing dot",
    ),
    ProjectionTestCase(
        "field_path_error_leading_dot",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={".arr": {"$elemMatch": {"$gt": 0}}},
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$elemMatch should reject a projection field name with a leading dot",
    ),
    ProjectionTestCase(
        "field_path_error_double_dot",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"a..b": {"$elemMatch": {"$gt": 0}}},
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$elemMatch should reject a projection field name with a double dot",
    ),
]

# Property [Operator Interaction Errors]: combining $elemMatch with $slice on the
# same field, with the positional operator on any field, or with an extra sibling
# key in the same projection object produces an error.
ELEMMATCH_OPERATOR_INTERACTION_ERROR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "interaction_slice_same_field",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"arr": SON([("$elemMatch", {"$gte": 2}), ("$slice", 1)])},
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$elemMatch should reject $slice on the same field",
    ),
    ProjectionTestCase(
        "interaction_positional_before_elemmatch",
        doc=[{"_id": 1, "arr": [1, 2, 3], "other": [4, 5, 6]}],
        projection=SON([("other.$", 1), ("arr", {"$elemMatch": {"$gte": 2}})]),
        error_code=PROJECT_ELEMATCH_CONFLICT_ERROR,
        msg="$elemMatch should reject a positional operator on a different field",
    ),
    ProjectionTestCase(
        "interaction_positional_after_elemmatch",
        doc=[{"_id": 1, "arr": [1, 2, 3], "other": [4, 5, 6]}],
        projection=SON([("arr", {"$elemMatch": {"$gte": 2}}), ("other.$", 1)]),
        error_code=PROJECT_ELEMATCH_POSITIONAL_CONFLICT_ERROR,
        msg="$elemMatch should reject a positional operator declared after it",
    ),
    ProjectionTestCase(
        "interaction_extra_sibling_inclusion",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"arr": SON([("$elemMatch", {"$gte": 2}), ("extra", 1)])},
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$elemMatch should reject an extra inclusion sibling key in the same object",
    ),
    ProjectionTestCase(
        "interaction_extra_sibling_exclusion",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        projection={"arr": SON([("$elemMatch", {"$gte": 2}), ("extra", 0)])},
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$elemMatch should reject an extra exclusion sibling key in the same object",
    ),
]

# Property [Restricted Operators in Condition - Errors]: query operators that are
# not permitted inside a projection $elemMatch condition are rejected with the
# operator-specific error code.
ELEMMATCH_RESTRICTED_OPERATOR_ERROR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "restricted_text",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$text": {"$search": "x"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject $text in the condition",
    ),
    ProjectionTestCase(
        "restricted_where",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$where": "this.x == 1"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject $where in the condition",
    ),
    ProjectionTestCase(
        "restricted_expr",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$expr": {"$eq": ["$x", 1]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject $expr in the condition",
    ),
    ProjectionTestCase(
        "restricted_sample_rate",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$sampleRate": 0.5}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject $sampleRate in the condition",
    ),
    ProjectionTestCase(
        "restricted_rand",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$rand": {}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject $rand in the condition",
    ),
    ProjectionTestCase(
        "restricted_unknown",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$totallyFakeOp": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject an unknown operator in the condition",
    ),
    ProjectionTestCase(
        "restricted_near",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"loc": {"$near": [0, 0]}}}},
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$elemMatch should reject $near in the condition",
    ),
    ProjectionTestCase(
        "restricted_near_sphere",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"loc": {"$nearSphere": [0, 0]}}}},
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$elemMatch should reject $nearSphere in the condition",
    ),
    ProjectionTestCase(
        "restricted_json_schema",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$jsonSchema": {"required": ["x"]}}}},
        error_code=QUERY_FEATURE_NOT_ALLOWED,
        msg="$elemMatch should reject $jsonSchema in the condition",
    ),
]

# Property [Logical Operator Argument Errors]: a $and/$or/$nor argument in the
# condition must be a non-empty array of field-based expressions, so an empty
# array or a bare top-level operator within the array is rejected.
ELEMMATCH_LOGICAL_OPERATOR_ERROR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "logical_and_empty",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$and": []}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject an empty $and array in the condition",
    ),
    ProjectionTestCase(
        "logical_or_empty",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$or": []}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject an empty $or array in the condition",
    ),
    ProjectionTestCase(
        "logical_nor_empty",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$nor": []}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject an empty $nor array in the condition",
    ),
    ProjectionTestCase(
        "logical_and_bare_op",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$and": [{"$gt": 5}]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject a bare top-level operator in a $and array",
    ),
    ProjectionTestCase(
        "logical_or_bare_op",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$or": [{"$gt": 5}]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject a bare top-level operator in a $or array",
    ),
    ProjectionTestCase(
        "logical_nor_bare_op",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"$nor": [{"$gt": 5}]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$elemMatch should reject a bare top-level operator in a $nor array",
    ),
]

ERROR_TESTS = (
    ELEMMATCH_CONDITION_TYPE_ERROR_TESTS
    + ELEMMATCH_FIELD_PATH_ERROR_TESTS
    + ELEMMATCH_OPERATOR_INTERACTION_ERROR_TESTS
    + ELEMMATCH_RESTRICTED_OPERATOR_ERROR_TESTS
    + ELEMMATCH_LOGICAL_OPERATOR_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_elemmatch_errors(collection, test):
    """Test $elemMatch projection error cases."""
    collection.insert_many(test.doc)
    cmd = {
        "find": collection.name,
        "projection": test.projection,
    }
    if test.filter is not None:
        cmd["filter"] = test.filter
    result = execute_command(collection, cmd)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
