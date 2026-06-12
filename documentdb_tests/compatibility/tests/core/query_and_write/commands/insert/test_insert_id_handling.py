"""
Insert _id field handling tests.

Tests auto-generated _id, custom _id types, numeric equivalence,
type distinction, and _id field ordering.
"""

from dataclasses import dataclass
from typing import Any, Dict, cast

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertProperties,
    assertResult,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import DUPLICATE_KEY_ERROR, INVALID_BSON_ID_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import IsType
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DECIMAL128_HALF,
    INT64_MAX,
    OID_EPOCH,
    TS_EPOCH,
)


@dataclass(frozen=True)
class IdTypeTest(BaseTestCase):
    """Test case for a single custom _id type: the inserted value and expected stored value."""

    id_value: Any = None
    expected_id: Any = None


@pytest.mark.insert
def test_insert_auto_generates_objectid(collection):
    """Test that insert without _id generates ObjectId _id."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"a": 1}]},
    )
    result = execute_command(collection, {"find": collection.name})
    assertProperties(
        result, {"_id": IsType("objectId")}, msg="insert should auto-generate ObjectId _id."
    )


# Property [Custom _id Types]: insert accepts all non-deprecated BSON types as _id.
CUSTOM_ID_TYPE_TESTS: list[IdTypeTest] = [
    IdTypeTest("double", id_value=3.14, expected_id=3.14, msg="insert should accept double _id."),
    IdTypeTest("string", id_value="abc", expected_id="abc", msg="insert should accept string _id."),
    IdTypeTest(
        "object",
        id_value={"a": 1, "b": 2},
        expected_id={"a": 1, "b": 2},
        msg="insert should accept object _id.",
    ),
    IdTypeTest(
        "objectId",
        id_value=OID_EPOCH,
        expected_id=OID_EPOCH,
        msg="insert should accept ObjectId _id.",
    ),
    IdTypeTest("bool", id_value=True, expected_id=True, msg="insert should accept bool _id."),
    IdTypeTest(
        "date",
        id_value=DATE_EPOCH,
        expected_id=DATE_EPOCH,
        msg="insert should accept date _id.",
    ),
    IdTypeTest("null", id_value=None, expected_id=None, msg="insert should accept null _id."),
    IdTypeTest("int32", id_value=42, expected_id=42, msg="insert should accept int32 _id."),
    IdTypeTest(
        "int64",
        id_value=INT64_MAX,
        expected_id=INT64_MAX,
        msg="insert should accept int64 _id.",
    ),
    IdTypeTest(
        "decimal128",
        id_value=DECIMAL128_HALF,
        expected_id=DECIMAL128_HALF,
        msg="insert should accept decimal128 _id.",
    ),
    IdTypeTest(
        "timestamp",
        id_value=TS_EPOCH,
        expected_id=TS_EPOCH,
        msg="insert should accept timestamp _id.",
    ),
    IdTypeTest(
        "minKey", id_value=MinKey(), expected_id=MinKey(), msg="insert should accept MinKey _id."
    ),
    IdTypeTest(
        "maxKey", id_value=MaxKey(), expected_id=MaxKey(), msg="insert should accept MaxKey _id."
    ),
    IdTypeTest(
        "binary",
        id_value=Binary(b"\x01\x02"),
        expected_id=b"\x01\x02",
        msg="insert should accept binary _id.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(CUSTOM_ID_TYPE_TESTS))
def test_insert_custom_id_type(collection, test: IdTypeTest):
    """Test that insert accepts various BSON types as _id."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": test.id_value, "x": 1}]},
    )
    result = execute_command(collection, {"find": collection.name})
    assertSuccess(result, [{"_id": test.expected_id, "x": 1}], msg=test.msg)


# Property [Numeric _id Equivalence]: numerically equal values of different
# numeric types collide on _id.
NUMERIC_EQUIVALENCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "int_long",
        docs=[{"_id": 1}],
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": Int64(1)}]},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="insert should treat int(1) and long(1) as same _id.",
    ),
    CommandTestCase(
        "int_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": 1.0}]},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="insert should treat int(1) and 1.0 as same _id.",
    ),
    CommandTestCase(
        "int_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": Decimal128("1")}]},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="insert should treat int(1) and Decimal128('1') as same _id.",
    ),
    CommandTestCase(
        "zero_int_double",
        docs=[{"_id": 0}],
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": 0.0}]},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="insert should treat int(0) and 0.0 as same _id.",
    ),
    CommandTestCase(
        "null_null",
        docs=[{"_id": None}],
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": None}]},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="insert should allow only one null _id.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(NUMERIC_EQUIVALENCE_TESTS))
def test_insert_id_equivalence(collection, test: CommandTestCase):
    """Test that numerically equivalent _id values produce duplicate key error."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    expected = cast(Dict[str, Any], test.build_expected(ctx))
    assertSuccessPartial(result, expected, msg=test.msg)


# Property [Cross-type _id Distinction]: values of different BSON type families
# are distinct for _id.
CROSS_TYPE_DISTINCTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "false_vs_zero",
        docs=[{"_id": False}],
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": 0}]},
        expected={"ok": 1.0, "n": 1},
        msg="insert should treat false and 0 as distinct _ids.",
    ),
    CommandTestCase(
        "string_vs_int",
        docs=[{"_id": "1"}],
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": 1}]},
        expected={"ok": 1.0, "n": 1},
        msg="insert should treat string '1' and int 1 as distinct _ids.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(CROSS_TYPE_DISTINCTION_TESTS))
def test_insert_id_distinction(collection, test: CommandTestCase):
    """Test that different BSON type families are distinct for _id."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    expected = cast(Dict[str, Any], test.build_expected(ctx))
    assertSuccessPartial(result, expected, msg=test.msg)


# Property [Rejected _id Types]: array and regex are not valid _id types and are rejected.
REJECTED_ID_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "array_as_id",
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": [1, 2, 3]}],
        },
        error_code=INVALID_BSON_ID_ERROR,
        msg="insert should reject array as _id.",
    ),
    CommandTestCase(
        "regex_as_id",
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": Regex(".*")}],
        },
        error_code=INVALID_BSON_ID_ERROR,
        msg="insert should reject regex as _id.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(REJECTED_ID_TYPE_TESTS))
def test_insert_rejected_id_type(collection, test: CommandTestCase):
    """Test that insert rejects array and regex as _id."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


@pytest.mark.insert
def test_insert_id_is_first_field(collection):
    """Test that _id is always the first field in stored documents."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"a": 1, "b": 2, "_id": 1}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result, [{"_id": 1, "a": 1, "b": 2}], msg="insert should reorder _id to first field."
    )


@pytest.mark.insert
def test_insert_id_compound_object(collection):
    """Test that compound object _id is accepted."""
    compound_id = {"a": 1, "b": "x"}
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": compound_id, "val": 1}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": compound_id}})
    assertSuccess(
        result, [{"_id": compound_id, "val": 1}], msg="insert should accept compound object _id."
    )
