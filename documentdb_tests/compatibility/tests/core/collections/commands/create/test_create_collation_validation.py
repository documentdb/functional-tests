"""Tests for the create command collation validation behavior."""

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

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INCOMPATIBLE_COLLATION_VERSION_ERROR,
    MISSING_FIELD_ERROR,
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
)

# Property [Collation Type Validation]: non-object types for the
# collation option produce TYPE_MISMATCH_ERROR.
CREATE_COLLATION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"collation_{label}",
        command=lambda ctx, val=val: {
            "create": f"{ctx.collection}_custom",
            "collation": val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{label} collation should fail with type mismatch",
    )
    for label, val in [
        ("string", "en"),
        ("int", 1),
        ("bool", True),
        ("array", [{"locale": "en"}]),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Collation Missing Locale]: an empty collation document
# (missing locale) produces MISSING_FIELD_ERROR.
CREATE_COLLATION_MISSING_LOCALE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_empty_document",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="Empty collation document (missing locale) should fail",
    ),
]

# Property [Collation Locale Validation]: an invalid locale string
# produces BAD_VALUE_ERROR; a non-string locale produces
# TYPE_MISMATCH_ERROR.
CREATE_COLLATION_LOCALE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_invalid_locale",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "invalid_locale_xyz"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid locale string should fail",
    ),
    *[
        CommandTestCase(
            id=f"collation_non_string_locale_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "collation": {"locale": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-string locale ({tid}) should fail",
        )
        for tid, val in [
            ("int", 123),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [Collation Strength Out of Range]: strength values outside
# [1, 5] after coercion produce BAD_VALUE_ERROR.
CREATE_COLLATION_STRENGTH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_strength_0",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": 0},
        },
        error_code=BAD_VALUE_ERROR,
        msg="strength=0 is below range [1,5]",
    ),
    CommandTestCase(
        id="collation_strength_6",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": 6},
        },
        error_code=BAD_VALUE_ERROR,
        msg="strength=6 is above range [1,5]",
    ),
    CommandTestCase(
        id="collation_strength_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": FLOAT_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="NaN strength coerces to 0, which is below range",
    ),
    CommandTestCase(
        id="collation_strength_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": FLOAT_NEGATIVE_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="-NaN strength coerces to 0, which is below range",
    ),
    CommandTestCase(
        id="collation_strength_decimal128_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": DECIMAL128_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 NaN strength coerces to 0, which is below range",
    ),
    CommandTestCase(
        id="collation_strength_decimal128_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": DECIMAL128_NEGATIVE_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 -NaN strength coerces to 0, which is below range",
    ),
    CommandTestCase(
        id="collation_strength_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": FLOAT_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Infinity strength is above range [1,5]",
    ),
    CommandTestCase(
        id="collation_strength_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="-Infinity strength is below range [1,5]",
    ),
    CommandTestCase(
        id="collation_strength_decimal128_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": DECIMAL128_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 Infinity strength is above range [1,5]",
    ),
    CommandTestCase(
        id="collation_strength_decimal128_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": DECIMAL128_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 -Infinity strength is below range [1,5]",
    ),
    CommandTestCase(
        id="collation_strength_decimal128_5_5_rounds_to_6",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": Decimal128("5.5")},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128('5.5') banker's rounds to 6, which is above range",
    ),
    CommandTestCase(
        id="collation_strength_negative",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": -1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="strength=-1 is below range [1,5]",
    ),
]

# Property [Collation Strength Type Strictness]: non-numeric types for
# strength produce TYPE_MISMATCH_ERROR.
CREATE_COLLATION_STRENGTH_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"collation_strength_non_numeric_{tid}",
        command=lambda ctx, v=val: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"Non-numeric strength ({tid}) should fail with type mismatch",
    )
    for tid, val in [
        ("string", "3"),
        ("bool", True),
        ("array", [3]),
        ("document", {"x": 1}),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Collation Backwards Null]: backwards:null produces
# TYPE_MISMATCH_ERROR unlike other boolean fields which accept null.
CREATE_COLLATION_BACKWARDS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_backwards_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "backwards": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="backwards:null should fail (unlike other boolean fields)",
    ),
]

# Property [Collation Boolean Sub-Field Type Strictness]: non-bool types for
# caseLevel, normalization, numericOrdering, and backwards produce
# TYPE_MISMATCH_ERROR.
CREATE_COLLATION_BOOLEAN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"collation_{field_id}_non_bool_{tid}",
        command=lambda ctx, f=field_key, v=val: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", f: v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"Non-bool {field_key} ({tid}) should fail with type mismatch",
    )
    for field_id, field_key in [
        ("case_level", "caseLevel"),
        ("normalization", "normalization"),
        ("numeric_ordering", "numericOrdering"),
        ("backwards", "backwards"),
    ]
    for tid, val in [
        ("int", 1),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("string", "yes"),
        ("array", [1]),
        ("document", {"x": 1}),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Collation CaseFirst Requires CaseLevel or Strength > 2]: caseFirst
# without caseLevel:true and with strength <= 2 produces
# BAD_VALUE_ERROR.
CREATE_COLLATION_CASE_FIRST_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_case_first_without_case_level_strength_2",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": 2, "caseFirst": "upper"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="caseFirst without caseLevel:true and strength <= 2 should fail",
    ),
    CommandTestCase(
        id="collation_case_first_without_case_level_strength_1",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": 1, "caseFirst": "lower"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="caseFirst without caseLevel:true and strength=1 should fail",
    ),
]

# Property [Collation CaseFirst Type and Value Validation]: non-string types
# produce TYPE_MISMATCH_ERROR; invalid string values produce BAD_VALUE_ERROR.
CREATE_COLLATION_CASE_FIRST_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            id=f"collation_case_first_non_string_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "collation": {"locale": "en", "caseLevel": True, "caseFirst": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-string caseFirst ({tid}) should fail with type mismatch",
        )
        for tid, val in [
            ("int", 1),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        id="collation_case_first_invalid_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "caseLevel": True, "caseFirst": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid caseFirst string should fail",
    ),
]

# Property [Collation Alternate Type and Value Validation]: non-string types
# produce TYPE_MISMATCH_ERROR; invalid string values produce BAD_VALUE_ERROR.
CREATE_COLLATION_ALTERNATE_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            id=f"collation_alternate_non_string_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "collation": {"locale": "en", "alternate": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-string alternate ({tid}) should fail with type mismatch",
        )
        for tid, val in [
            ("int", 1),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        id="collation_alternate_invalid_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "alternate": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid alternate string should fail",
    ),
]

# Property [Collation MaxVariable Type and Value Validation]: non-string types
# produce TYPE_MISMATCH_ERROR; invalid string values produce BAD_VALUE_ERROR.
CREATE_COLLATION_MAX_VARIABLE_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            id=f"collation_max_variable_non_string_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "collation": {"locale": "en", "maxVariable": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-string maxVariable ({tid}) should fail with type mismatch",
        )
        for tid, val in [
            ("int", 1),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        id="collation_max_variable_invalid_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "maxVariable": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid maxVariable string should fail",
    ),
]

# Property [Collation Version Validation]: non-string version produces
# TYPE_MISMATCH_ERROR; invalid version string produces
# INCOMPATIBLE_COLLATION_VERSION_ERROR.
CREATE_COLLATION_VERSION_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            id=f"collation_version_non_string_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "collation": {"locale": "en", "version": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"Non-string version ({tid}) should fail with type mismatch",
        )
        for tid, val in [
            ("int", 57),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("regex", Regex("x")),
            ("code", Code("f()")),
            ("code_with_scope", Code("f()", {"x": 1})),
            ("timestamp", Timestamp(0, 0)),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        id="collation_version_invalid_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "version": "invalid"},
        },
        error_code=INCOMPATIBLE_COLLATION_VERSION_ERROR,
        msg="Invalid version string should fail",
    ),
]

# Property [Collation Unknown Fields]: unknown fields in the collation
# document produce UNRECOGNIZED_COMMAND_FIELD_ERROR; the check is
# case-sensitive.
CREATE_COLLATION_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_unknown_field",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "unknownField": "x"},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown fields in collation should fail",
    ),
    CommandTestCase(
        id="collation_case_sensitive_field_name",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "Strength": 3},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Case-sensitive field name check (uppercase 'Strength') should fail",
    ),
]

CREATE_COLLATION_ERROR_TESTS: list[CommandTestCase] = (
    CREATE_COLLATION_TYPE_ERROR_TESTS
    + CREATE_COLLATION_MISSING_LOCALE_ERROR_TESTS
    + CREATE_COLLATION_LOCALE_ERROR_TESTS
    + CREATE_COLLATION_STRENGTH_ERROR_TESTS
    + CREATE_COLLATION_STRENGTH_TYPE_ERROR_TESTS
    + CREATE_COLLATION_BACKWARDS_ERROR_TESTS
    + CREATE_COLLATION_BOOLEAN_TYPE_ERROR_TESTS
    + CREATE_COLLATION_CASE_FIRST_ERROR_TESTS
    + CREATE_COLLATION_CASE_FIRST_TYPE_ERROR_TESTS
    + CREATE_COLLATION_ALTERNATE_ERROR_TESTS
    + CREATE_COLLATION_MAX_VARIABLE_ERROR_TESTS
    + CREATE_COLLATION_VERSION_ERROR_TESTS
    + CREATE_COLLATION_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_COLLATION_ERROR_TESTS))
def test_create_collation_validation(database_client, collection, test):
    """Test create command collation validation behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
