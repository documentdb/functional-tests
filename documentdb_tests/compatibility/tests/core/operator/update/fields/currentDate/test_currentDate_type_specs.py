"""
Type specification tests for $currentDate update field operator.

Tests valid typeSpecification values, invalid values that should error,
and result type validation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertNotError,
    assertProperties,
    assertResult,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
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
        expected={"field": IsType("date")},
        msg="$currentDate with true should set field to Date",
    ),
    UpdateTestCase(
        "boolean_false_sets_date",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$currentDate": {"field": False}},
        expected={"field": IsType("date")},
        msg="$currentDate with false should still set field to Date",
    ),
    UpdateTestCase(
        "type_date_sets_date",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "date"}}},
        expected={"field": IsType("date")},
        msg="$currentDate with {$type:'date'} should set field to Date",
    ),
    UpdateTestCase(
        "type_timestamp_sets_timestamp",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$currentDate": {"field": {"$type": "timestamp"}}},
        expected={"field": IsType("timestamp")},
        msg="$currentDate with {$type:'timestamp'} should set field to Timestamp",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_TESTS))
def test_currentDate_valid_type_specs(collection, test: UpdateTestCase):
    """Test $currentDate with valid typeSpecification values produces the correct type."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertProperties(result, test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Value Type]: $currentDate typeSpecification must be a boolean or an
# object ({$type: ...}). Every other BSON type is rejected with BadValue.
# ---------------------------------------------------------------------------

VALUE_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="currentDate_value",
        msg="$currentDate typeSpecification value type",
        keyword="$currentDate",
        valid_types=[BsonType.BOOL, BsonType.OBJECT],
        valid_inputs={BsonType.OBJECT: {"$type": "date"}},
        default_error_code=BAD_VALUE_ERROR,
    ),
]

VALUE_TYPE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(VALUE_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", VALUE_TYPE_ACCEPTANCE_CASES)
def test_currentDate_value_type_accepted(collection, bson_type, sample_value, spec):
    """Test $currentDate accepts boolean and object typeSpecification values."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"field": sample_value}}}],
        },
    )
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")


VALUE_TYPE_REJECTION_CASES = generate_bson_rejection_test_cases(VALUE_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", VALUE_TYPE_REJECTION_CASES)
def test_currentDate_value_type_rejected(collection, bson_type, sample_value, spec):
    """Test $currentDate rejects non-boolean/non-object typeSpecification values."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"field": sample_value}}}],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


# ---------------------------------------------------------------------------
# Property [$type Value Type]: inside the {$type: ...} form, the $type value
# must be a string. Every other BSON type is rejected with BadValue.
# ---------------------------------------------------------------------------

TYPE_VALUE_PARAMS = [
    BsonTypeTestCase(
        id="currentDate_type_value",
        msg="$currentDate $type value type",
        keyword="$type",
        valid_types=[BsonType.STRING],
        valid_inputs={BsonType.STRING: "date"},
        default_error_code=BAD_VALUE_ERROR,
    ),
]

TYPE_VALUE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(TYPE_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", TYPE_VALUE_ACCEPTANCE_CASES)
def test_currentDate_type_value_accepted(collection, bson_type, sample_value, spec):
    """Test $currentDate accepts a string $type value (content checked elsewhere)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"field": {"$type": sample_value}}}}
            ],
        },
    )
    assertNotError(result, msg=f"{spec.msg} should accept {bson_type.value}")


TYPE_VALUE_REJECTION_CASES = generate_bson_rejection_test_cases(TYPE_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", TYPE_VALUE_REJECTION_CASES)
def test_currentDate_type_value_rejected(collection, bson_type, sample_value, spec):
    """Test $currentDate rejects non-string $type values."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"field": {"$type": sample_value}}}}
            ],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


# ---------------------------------------------------------------------------
# Property [Invalid $type Edge Cases]: a string $type value must be exactly
# "date" or "timestamp" (case-sensitive), and the spec object must contain only
# the $type key. These string-content and object-structure checks cannot be
# expressed via BSON type generation, so they are covered explicitly here.
# ---------------------------------------------------------------------------

INVALID_TYPE_EDGE_CASES: list[UpdateTestCase] = [
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


@pytest.mark.parametrize("test", pytest_params(INVALID_TYPE_EDGE_CASES))
def test_currentDate_invalid_type_edge_cases(collection, test: UpdateTestCase):
    """Test $currentDate rejects invalid $type strings and malformed spec objects."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)
