"""
Tests for $meta invalid arguments and error cases in aggregation $project.
"""

import datetime
import re
from datetime import timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    META_NON_STRING_ERROR,
    QUERY_METADATA_NOT_AVAILABLE_ERROR,
    UNSUPPORTED_META_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


@pytest.fixture
def text_collection(collection):
    collection.create_index([("content", "text")])
    collection.insert_many([{"_id": 1, "content": "apple banana"}])
    return collection


INVALID_ARGUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "unknown_keyword",
        expression="unknownKeyword",
        error_code=UNSUPPORTED_META_FIELD_ERROR,
        msg="Unknown keyword string should fail",
    ),
    ExpressionTestCase(
        "empty_string",
        expression="",
        error_code=UNSUPPORTED_META_FIELD_ERROR,
        msg="Empty string should fail",
    ),
    ExpressionTestCase(
        "field_path",
        expression="$fieldName",
        error_code=UNSUPPORTED_META_FIELD_ERROR,
        msg="Field path as keyword should fail",
    ),
    ExpressionTestCase(
        "system_variable",
        expression="$$ROOT",
        error_code=UNSUPPORTED_META_FIELD_ERROR,
        msg="System variable as keyword should fail",
    ),
    ExpressionTestCase(
        "null", expression=None, error_code=META_NON_STRING_ERROR, msg="Null should fail"
    ),
    ExpressionTestCase(
        "int", expression=123, error_code=META_NON_STRING_ERROR, msg="Int should fail"
    ),
    ExpressionTestCase(
        "long", expression=Int64(123), error_code=META_NON_STRING_ERROR, msg="Long should fail"
    ),
    ExpressionTestCase(
        "double", expression=1.5, error_code=META_NON_STRING_ERROR, msg="Double should fail"
    ),
    ExpressionTestCase(
        "decimal128",
        expression=Decimal128("1.5"),
        error_code=META_NON_STRING_ERROR,
        msg="Decimal128 should fail",
    ),
    ExpressionTestCase(
        "boolean", expression=True, error_code=META_NON_STRING_ERROR, msg="Boolean should fail"
    ),
    ExpressionTestCase(
        "date",
        expression=datetime.datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=META_NON_STRING_ERROR,
        msg="Date should fail",
    ),
    ExpressionTestCase(
        "binary",
        expression=Binary(b"data"),
        error_code=META_NON_STRING_ERROR,
        msg="Binary should fail",
    ),
    ExpressionTestCase(
        "array", expression=["textScore"], error_code=META_NON_STRING_ERROR, msg="Array should fail"
    ),
    ExpressionTestCase(
        "object", expression={"a": 1}, error_code=META_NON_STRING_ERROR, msg="Object should fail"
    ),
    ExpressionTestCase(
        "expression",
        expression={"$concat": ["text", "Score"]},
        error_code=META_NON_STRING_ERROR,
        msg="Expression object should fail",
    ),
    ExpressionTestCase(
        "objectid",
        expression=ObjectId("507f1f77bcf86cd799439011"),
        error_code=META_NON_STRING_ERROR,
        msg="ObjectId should fail",
    ),
    ExpressionTestCase(
        "regex",
        expression=re.compile("textScore"),
        error_code=META_NON_STRING_ERROR,
        msg="Regex should fail",
    ),
    ExpressionTestCase(
        "timestamp",
        expression=Timestamp(0, 0),
        error_code=META_NON_STRING_ERROR,
        msg="Timestamp should fail",
    ),
    ExpressionTestCase(
        "minkey", expression=MinKey(), error_code=META_NON_STRING_ERROR, msg="MinKey should fail"
    ),
    ExpressionTestCase(
        "maxkey", expression=MaxKey(), error_code=META_NON_STRING_ERROR, msg="MaxKey should fail"
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_ARGUMENT_TESTS))
def test_meta_invalid_project(text_collection, test):
    """Test $meta with invalid argument in $project fails with expected error code."""
    result = execute_command(
        text_collection,
        {
            "aggregate": text_collection.name,
            "pipeline": [
                {"$match": {"$text": {"$search": "apple"}}},
                {"$project": {"s": {"$meta": test.expression}}},
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, test.error_code)


def test_meta_textscore_without_text(text_collection):
    """Test $meta textScore in $project without $text query fails with error 40218."""
    result = execute_command(
        text_collection,
        {
            "aggregate": text_collection.name,
            "pipeline": [{"$project": {"s": {"$meta": "textScore"}}}],
            "cursor": {},
        },
    )
    assertFailureCode(result, QUERY_METADATA_NOT_AVAILABLE_ERROR)
