"""Tests for the $replaceRoot aggregation stage."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_DOT_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    MISSING_FIELD_ERROR,
    REPLACE_ROOT_SPEC_NOT_OBJECT_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Object-Literal Field-Name Errors]: a constructed newRoot object
# literal with an invalid key is rejected at parse time, each invalid-key kind
# hitting a distinct code, with no reclassification when nested in a sub-object.
REPLACEROOT_FIELD_NAME_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "fieldname_empty_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"": 1}}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$replaceRoot should reject a constructed literal with an empty key",
    ),
    StageTestCase(
        "fieldname_sole_dollar_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"$x": 1}}}],
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="$replaceRoot should reject a sole dollar-prefixed key as an unknown operator",
    ),
    StageTestCase(
        "fieldname_dollar_key_with_sibling",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"good": 1, "$bad": 2}}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$replaceRoot should reject a dollar-prefixed key alongside a plain sibling field",
    ),
    StageTestCase(
        "fieldname_multiple_dollar_keys",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"$a": 1, "$b": 2}}}],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$replaceRoot should reject multiple dollar-prefixed operator keys in one object",
    ),
    StageTestCase(
        "fieldname_dotted_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"a.b": 1}}}],
        error_code=FIELD_PATH_DOT_ERROR,
        msg="$replaceRoot should reject a dotted key without expanding it into a path",
    ),
    StageTestCase(
        "fieldname_nested_sole_dollar_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"a": {"$bad": 1}}}}],
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="$replaceRoot should reject a sole dollar-prefixed key in a sub-object identically",
    ),
    StageTestCase(
        "fieldname_nested_dollar_key_with_sibling",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"a": {"good": 1, "$bad": 2}}}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$replaceRoot should reject a dollar-prefixed key with a sibling in a sub-object",
    ),
    StageTestCase(
        "fieldname_nested_dotted_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": {"a": {"b.c": 1}}}}],
        error_code=FIELD_PATH_DOT_ERROR,
        msg="$replaceRoot should reject a dotted key in a sub-object identically",
    ),
]

# Property [Stage Specification Errors]: a $replaceRoot specification that is not
# an object, that omits the newRoot field, or that carries an extra or wrong
# field is rejected at the specification-wrapper level.
REPLACEROOT_SPEC_ERROR_TESTS: list[StageTestCase] = [
    *(
        StageTestCase(
            f"spec_not_object_{tid}",
            docs=[{"_id": 1}],
            pipeline=[{"$replaceRoot": val}],
            error_code=REPLACE_ROOT_SPEC_NOT_OBJECT_ERROR,
            msg=f"$replaceRoot should reject a {tid} specification that is not an object",
        )
        for tid, val in [
            ("string", "foo"),
            ("int32", 5),
            ("int64", Int64(9_999_999_999)),
            ("double", 3.5),
            ("decimal128", Decimal128("123.456")),
            ("bool_true", True),
            ("bool_false", False),
            ("array", [1, 2]),
            ("null", None),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1_700_000_000, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex("^abc", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ),
    StageTestCase(
        "spec_missing_newroot",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$replaceRoot should reject a specification with no newRoot field",
    ),
    StageTestCase(
        "spec_extra_field",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"newRoot": "$$ROOT", "extra": 1}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$replaceRoot should reject a specification with an extra unknown field",
    ),
    StageTestCase(
        "spec_wrong_key",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceRoot": {"foo": "$$ROOT"}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$replaceRoot should reject a specification with a wrong key instead of newRoot",
    ),
]

REPLACEROOT_PARSE_ERROR_TESTS = REPLACEROOT_FIELD_NAME_ERROR_TESTS + REPLACEROOT_SPEC_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REPLACEROOT_PARSE_ERROR_TESTS))
def test_replaceRoot_parse_error_cases(collection, test_case: StageTestCase):
    """Test $replaceRoot parse error cases."""
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
        ignore_doc_order=True,
    )
