"""writeConcern rejection: invalid w/j/wtimeout values, case-sensitive w strings,
invalid provenance, and unknown fields, plus the w:1 case where a per-operation
error surfaces. Each is expected to fail with a specific error code. BSON-type
rejection lives in test_write_concern_bson_type_validation.py.
"""

from typing import Any, Dict, cast

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_MIN,
)

# These cases are only rejected on standalone; a quorum target treats them as
# custom tag names (valid), so they are deselected there.
_STANDALONE_ONLY = (pytest.mark.requires(quorum_write_concern=False),)

WRITE_CONCERN_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_null",
        command={"updates": [{"q": {}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": None}},
        error_code=BAD_VALUE_ERROR,
        msg="w:null should be rejected on standalone.",
        marks=_STANDALONE_ONLY,
    ),
    CommandTestCase(
        "w_negative",
        command={"updates": [{"q": {}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:-1 should be rejected.",
    ),
    CommandTestCase(
        "w_exceeds_50",
        command={"updates": [{"q": {}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": 51}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:51 should be rejected.",
    ),
    CommandTestCase(
        "w_float_nan",
        command={"updates": [{"q": {}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": FLOAT_NAN}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as NaN should be rejected.",
    ),
    CommandTestCase(
        "w_float_neg_nan",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": FLOAT_NEGATIVE_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as -NaN should be rejected.",
    ),
    CommandTestCase(
        "w_decimal128_nan",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": DECIMAL128_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as Decimal128 NaN should be rejected.",
    ),
    CommandTestCase(
        "w_decimal128_neg_nan",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": DECIMAL128_NEGATIVE_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as Decimal128 -NaN should be rejected.",
    ),
    CommandTestCase(
        "w_float_inf",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": FLOAT_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as +Infinity should be rejected.",
    ),
    CommandTestCase(
        "w_float_neg_inf",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as -Infinity should be rejected.",
    ),
    CommandTestCase(
        "w_decimal128_inf",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": DECIMAL128_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as Decimal128 +Infinity should be rejected.",
    ),
    CommandTestCase(
        "w_decimal128_neg_inf",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": DECIMAL128_NEGATIVE_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as Decimal128 -Infinity should be rejected.",
    ),
    CommandTestCase(
        "w_tagged_non_numeric",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": {"dc1": "hello"}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w tagged object with non-numeric value should be rejected.",
    ),
    CommandTestCase(
        "w_int64_max",
        command={"updates": [{"q": {}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": INT64_MAX}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as Int64 max should be rejected.",
    ),
    CommandTestCase(
        "w_int64_min",
        command={"updates": [{"q": {}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": INT64_MIN}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w as Int64 min should be rejected.",
    ),
    CommandTestCase(
        "w_tagged_empty_object",
        command={"updates": [{"q": {}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": {}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="empty object w should be rejected (tagged write concern requires tags).",
    ),
    CommandTestCase(
        "w_tagged_nested_object",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": {"dc1": {"nested": 1}}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="tagged w with nested object value should be rejected.",
    ),
    CommandTestCase(
        "wtimeout_int64_overflow",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": Int64(INT32_MAX + 1)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Int64 wtimeout exceeding INT32_MAX should be rejected.",
    ),
    CommandTestCase(
        "wtimeout_double_overflow",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": float(INT32_OVERFLOW)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="double wtimeout exceeding INT32_MAX should be rejected.",
    ),
    CommandTestCase(
        "wtimeout_decimal128_overflow",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": Decimal128(str(INT32_OVERFLOW))},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Decimal128 wtimeout exceeding INT32_MAX should be rejected.",
    ),
    CommandTestCase(
        "wtimeout_float_infinity",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": FLOAT_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="+Infinity wtimeout (exceeds INT32_MAX) should be rejected.",
    ),
    # Property [Unknown Field Rejection]: unrecognized fields in writeConcern are rejected.
    CommandTestCase(
        "unknown_field",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="writeConcern should reject unrecognized fields.",
    ),
    CommandTestCase(
        "provenance_invalid_string",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "provenance": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="provenance with an unknown string value should be rejected.",
    ),
    CommandTestCase(
        "provenance_wrong_type",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "provenance": 42},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="provenance with a non-string value should be rejected.",
    ),
    # A valid writeConcern (w:1) surfaces a per-operation error: multi:true with a
    # replacement doc is invalid. The w:0 "suppresses" counterpart lives in
    # test_write_concern_behavior.py (w0_suppresses_operation_error).
    CommandTestCase(
        "w1_surfaces_operation_error",
        docs=[{"_id": 1, "a": 1}],
        command={
            "updates": [{"q": {}, "u": {"a": 2}, "multi": True}],
            "writeConcern": {"w": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="update with w:1 should surface the operation error.",
    ),
    # w "majority" is case-sensitive and an empty string is a custom tag; both are
    # only rejected on standalone (see _STANDALONE_ONLY).
    CommandTestCase(
        "w_wrong_case_Majority",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": "Majority"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w:'Majority' should be rejected (case-sensitive).",
        marks=_STANDALONE_ONLY,
    ),
    CommandTestCase(
        "w_all_caps_MAJORITY",
        command={
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": "MAJORITY"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w:'MAJORITY' should be rejected (case-sensitive).",
        marks=_STANDALONE_ONLY,
    ),
    CommandTestCase(
        "w_empty_string",
        command={"updates": [{"q": {}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="w:'' (empty string custom tag) should be rejected on standalone.",
        marks=_STANDALONE_ONLY,
    ),
]


@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_REJECTION_TESTS))
def test_write_concern_rejected(collection, test: CommandTestCase):
    """Test writeConcern rejects invalid sub-field values and unknown fields."""
    collection = test.prepare(collection.database, collection)
    update_body = cast(Dict[str, Any], test.command)
    result = execute_command(collection, {"update": collection.name, **update_body})
    assertResult(result, error_code=test.error_code, msg=test.msg)
