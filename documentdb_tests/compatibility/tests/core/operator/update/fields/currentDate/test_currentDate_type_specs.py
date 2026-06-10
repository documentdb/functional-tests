"""
Type specification tests for $currentDate update field operator.

Tests valid typeSpecification values, invalid values that should error,
and result type validation.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import (
    assertProperties,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import IsType

# ---------------------------------------------------------------------------
# Property [Valid Type Specs]: $currentDate accepts true, {$type:"date"}, {$type:"timestamp"}
# ---------------------------------------------------------------------------

VALID_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "boolean_true_sets_date",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$currentDate": {"field": True}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate with true should update field",
    ),
    UpdateTestCase(
        "boolean_false_sets_date",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$currentDate": {"field": False}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate with false should still update field to Date",
    ),
    UpdateTestCase(
        "type_date_sets_date",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "date"}}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate with {$type:'date'} should update field",
    ),
    UpdateTestCase(
        "type_timestamp_sets_timestamp",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "timestamp"}}},
        expected={"n": 1, "nModified": 1},
        msg="$currentDate with {$type:'timestamp'} should update field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_TESTS))
def test_currentDate_valid_type_specs(collection, test: UpdateTestCase):
    """Test $currentDate with valid typeSpecification values succeeds."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Result Type]: $currentDate produces correct BSON type in the field
# ---------------------------------------------------------------------------


def test_currentDate_boolean_true_produces_date_type(collection):
    """Test $currentDate with true produces a Date type field."""
    collection.insert_one({"_id": 1, "field": "old"})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"field": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(result, {"field": IsType("date")}, msg="true should produce Date type")


def test_currentDate_type_date_produces_date_type(collection):
    """Test $currentDate with {$type:'date'} produces a Date type field."""
    collection.insert_one({"_id": 1, "field": "old"})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"field": {"$type": "date"}}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result, {"field": IsType("date")}, msg="{$type:'date'} should produce Date type"
    )


def test_currentDate_type_timestamp_produces_timestamp_type(collection):
    """Test $currentDate with {$type:'timestamp'} produces a Timestamp type field."""
    collection.insert_one({"_id": 1, "field": "old"})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"field": {"$type": "timestamp"}}}}
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"field": IsType("timestamp")},
        msg="{$type:'timestamp'} should produce Timestamp type",
    )


# ---------------------------------------------------------------------------
# Property [Invalid Type Specs - BadValue]: invalid $type values produce error code 2
# ---------------------------------------------------------------------------

INVALID_TYPE_VALUE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "type_Date_uppercase",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "Date"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'Date' (uppercase) should be rejected",
    ),
    UpdateTestCase(
        "type_Timestamp_uppercase",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "Timestamp"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'Timestamp' (uppercase) should be rejected",
    ),
    UpdateTestCase(
        "type_DATE_all_caps",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "DATE"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'DATE' should be rejected",
    ),
    UpdateTestCase(
        "type_TIMESTAMP_all_caps",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "TIMESTAMP"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'TIMESTAMP' should be rejected",
    ),
    UpdateTestCase(
        "type_dAte_mixed_case",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "dAte"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'dAte' (mixed case) should be rejected",
    ),
    UpdateTestCase(
        "type_timeStamp_mixed_case",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "timeStamp"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'timeStamp' (mixed case) should be rejected",
    ),
    UpdateTestCase(
        "type_empty_string",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": ""}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type empty string should be rejected",
    ),
    UpdateTestCase(
        "type_string_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "string"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'string' should be rejected",
    ),
    UpdateTestCase(
        "type_int_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "int"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'int' should be rejected",
    ),
    UpdateTestCase(
        "type_double_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "double"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'double' should be rejected",
    ),
    UpdateTestCase(
        "type_bool_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "bool"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'bool' should be rejected",
    ),
    UpdateTestCase(
        "type_null_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type null should be rejected",
    ),
    UpdateTestCase(
        "type_numeric_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type numeric (1) should be rejected",
    ),
    UpdateTestCase(
        "type_boolean_true_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": True}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type boolean true should be rejected",
    ),
    UpdateTestCase(
        "type_dates_misspelling",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "dates"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'dates' (misspelling) should be rejected",
    ),
    UpdateTestCase(
        "type_timestam_misspelling",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "timestam"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$type 'timestam' (misspelling) should be rejected",
    ),
    UpdateTestCase(
        "unknown_key_in_spec_object",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"wrongKey": "date"}}},
        error_code=BAD_VALUE_ERROR,
        msg="Unknown key in spec object should be rejected",
    ),
    UpdateTestCase(
        "extra_keys_in_spec_object",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "date", "extra": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="Extra keys alongside $type should be rejected",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_TYPE_VALUE_TESTS))
def test_currentDate_invalid_type_values(collection, test: UpdateTestCase):
    """Test $currentDate with invalid $type values produces BadValue error."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Invalid Type Specs - BadValue]: non-boolean/non-object values produce code 2
# ---------------------------------------------------------------------------

INVALID_FORMAT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "integer_zero",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": 0}},
        error_code=BAD_VALUE_ERROR,
        msg="Integer 0 as typeSpecification should be rejected",
    ),
    UpdateTestCase(
        "integer_one",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="Integer 1 as typeSpecification should be rejected",
    ),
    UpdateTestCase(
        "empty_string",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty string as typeSpecification should be rejected",
    ),
    UpdateTestCase(
        "string_date",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": "date"}},
        error_code=BAD_VALUE_ERROR,
        msg="String 'date' as typeSpecification should be rejected",
    ),
    UpdateTestCase(
        "string_timestamp",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": "timestamp"}},
        error_code=BAD_VALUE_ERROR,
        msg="String 'timestamp' as typeSpecification should be rejected",
    ),
    UpdateTestCase(
        "null_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": None}},
        error_code=BAD_VALUE_ERROR,
        msg="Null as typeSpecification should be rejected",
    ),
    UpdateTestCase(
        "array_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": []}},
        error_code=BAD_VALUE_ERROR,
        msg="Array as typeSpecification should be rejected",
    ),
    UpdateTestCase(
        "int64_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": Int64(1)}},
        error_code=BAD_VALUE_ERROR,
        msg="Int64 as typeSpecification should be rejected",
    ),
    UpdateTestCase(
        "decimal128_value",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$currentDate": {"field": Decimal128("1")}},
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 as typeSpecification should be rejected",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_FORMAT_TESTS))
def test_currentDate_invalid_format(collection, test: UpdateTestCase):
    """Test $currentDate with non-boolean/non-object typeSpecification produces BadValue."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)
