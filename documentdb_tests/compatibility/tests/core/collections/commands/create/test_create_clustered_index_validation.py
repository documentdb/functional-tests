"""Tests for the create command clustered index validation behavior."""

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
    CLUSTERED_INDEX_CAPPED_CONFLICT_ERROR,
    CLUSTERED_INDEX_INVALID_VERSION_ERROR,
    CLUSTERED_INDEX_LEGACY_FORMAT_ERROR,
    CLUSTERED_INDEX_MAX_CONFLICT_ERROR,
    CLUSTERED_INDEX_UNIQUE_REQUIRED_ERROR,
    CLUSTERED_INDEX_VIEW_CONFLICT_ERROR,
    INVALID_INDEX_SPEC_OPTION_ERROR,
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [Clustered Index Truthy Non-Document]: bool or numeric truthy
# (non-document) values for clusteredIndex produce
# CLUSTERED_INDEX_LEGACY_FORMAT_ERROR.
CREATE_CLUSTERED_LEGACY_FORMAT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="clustered_index_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": True,
        },
        error_code=CLUSTERED_INDEX_LEGACY_FORMAT_ERROR,
        msg="clusteredIndex:True (truthy non-document) should fail",
    ),
    CommandTestCase(
        id="clustered_index_int_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": 1,
        },
        error_code=CLUSTERED_INDEX_LEGACY_FORMAT_ERROR,
        msg="clusteredIndex:1 (truthy non-document) should fail",
    ),
    CommandTestCase(
        id="clustered_index_int64_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": Int64(1),
        },
        error_code=CLUSTERED_INDEX_LEGACY_FORMAT_ERROR,
        msg="clusteredIndex:Int64(1) (truthy non-document) should fail",
    ),
    CommandTestCase(
        id="clustered_index_double_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": 1.0,
        },
        error_code=CLUSTERED_INDEX_LEGACY_FORMAT_ERROR,
        msg="clusteredIndex:1.0 (truthy non-document) should fail",
    ),
]

# Property [Clustered Index Type Validation]: null, string, array,
# ObjectId, datetime, and other non-bool/non-numeric/non-document types
# for clusteredIndex produce TYPE_MISMATCH_ERROR.
CREATE_CLUSTERED_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"clustered_index_{label}",
        command=lambda ctx, val=val: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"clusteredIndex:{label} should fail with type mismatch",
    )
    for label, val in [
        ("null", None),
        ("string", "hello"),
        ("array", [{"key": {"_id": 1}, "unique": True}]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"x")),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Clustered Index Missing Required Fields]: missing or null
# key or unique in the clusteredIndex document produces
# MISSING_FIELD_ERROR.
CREATE_CLUSTERED_MISSING_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="missing_key",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"unique": True},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="Missing key should fail",
    ),
    CommandTestCase(
        id="missing_unique",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="Missing unique should fail",
    ),
    CommandTestCase(
        id="null_key",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": None, "unique": True},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="Null key should fail",
    ),
    CommandTestCase(
        id="null_unique",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": None},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="Null unique should fail",
    ),
]

# Property [Clustered Index Key Validation]: non-object key produces
# TYPE_MISMATCH_ERROR; key pattern other than {_id:1} produces
# INVALID_INDEX_SPEC_OPTION_ERROR.
CREATE_CLUSTERED_KEY_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            id=f"non_object_key_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "clusteredIndex": {"key": v, "unique": True},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"non-object key ({tid}) should fail with type mismatch",
        )
        for tid, val in [
            ("string", "hello"),
            ("int", 1),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [{"_id": 1}]),
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
        id="key_pattern_not_id",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"x": 1}, "unique": True},
        },
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="Key pattern other than {_id:1} should fail",
    ),
]

# Property [Clustered Index Unique Validation]: unique:false or falsy
# numeric produces CLUSTERED_INDEX_UNIQUE_REQUIRED_ERROR; non-numeric
# and non-bool unique produces TYPE_MISMATCH_ERROR.
CREATE_CLUSTERED_UNIQUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="unique_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": False},
        },
        error_code=CLUSTERED_INDEX_UNIQUE_REQUIRED_ERROR,
        msg="unique:false should fail",
    ),
    CommandTestCase(
        id="unique_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": 0},
        },
        error_code=CLUSTERED_INDEX_UNIQUE_REQUIRED_ERROR,
        msg="unique:0 (falsy numeric) should fail",
    ),
    *[
        CommandTestCase(
            id=f"unique_type_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "clusteredIndex": {"key": {"_id": 1}, "unique": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"non-numeric/non-bool unique ({tid}) should fail with type mismatch",
        )
        for tid, val in [
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
    ],
]

# Property [Clustered Index Version Validation]: v values that do not
# coerce to 2 (including NaN and Infinity) produce
# CLUSTERED_INDEX_INVALID_VERSION_ERROR.
CREATE_CLUSTERED_VERSION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="v_equals_1",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True, "v": 1},
        },
        error_code=CLUSTERED_INDEX_INVALID_VERSION_ERROR,
        msg="v=1 should fail",
    ),
    CommandTestCase(
        id="v_equals_0",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True, "v": 0},
        },
        error_code=CLUSTERED_INDEX_INVALID_VERSION_ERROR,
        msg="v=0 should fail",
    ),
    CommandTestCase(
        id="v_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "v": FLOAT_NAN,
            },
        },
        error_code=CLUSTERED_INDEX_INVALID_VERSION_ERROR,
        msg="v=NaN coerces to 0, which is not 2",
    ),
    CommandTestCase(
        id="v_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "v": FLOAT_NEGATIVE_NAN,
            },
        },
        error_code=CLUSTERED_INDEX_INVALID_VERSION_ERROR,
        msg="v=-NaN coerces to 0, which is not 2",
    ),
    CommandTestCase(
        id="v_decimal128_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "v": DECIMAL128_NAN,
            },
        },
        error_code=CLUSTERED_INDEX_INVALID_VERSION_ERROR,
        msg="v=Decimal128 NaN coerces to 0, which is not 2",
    ),
    CommandTestCase(
        id="v_decimal128_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "v": DECIMAL128_NEGATIVE_NAN,
            },
        },
        error_code=CLUSTERED_INDEX_INVALID_VERSION_ERROR,
        msg="v=Decimal128 -NaN coerces to 0, which is not 2",
    ),
    CommandTestCase(
        id="v_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "v": FLOAT_INFINITY,
            },
        },
        error_code=CLUSTERED_INDEX_INVALID_VERSION_ERROR,
        msg="v=Infinity coerces to INT32_MAX, which is not 2",
    ),
    CommandTestCase(
        id="v_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "v": FLOAT_NEGATIVE_INFINITY,
            },
        },
        error_code=CLUSTERED_INDEX_INVALID_VERSION_ERROR,
        msg="v=-Infinity coerces to negative, which is not 2",
    ),
    CommandTestCase(
        id="v_decimal128_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "v": DECIMAL128_INFINITY,
            },
        },
        error_code=CLUSTERED_INDEX_INVALID_VERSION_ERROR,
        msg="v=Decimal128 Infinity is not 2",
    ),
]

# Property [Clustered Index Unknown Sub-Fields]: unknown fields in the
# clusteredIndex document produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
CREATE_CLUSTERED_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="unknown_sub_field",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "unknownField": "x",
            },
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown sub-fields should fail",
    ),
]

# Property [Clustered Index Incompatibilities]: clusteredIndex is
# incompatible with capped (even when clusteredIndex is falsy),
# timeseries, viewOn, idIndex, and max without capped.
CREATE_CLUSTERED_INCOMPATIBILITY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="incompatible_with_capped",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "capped": True,
            "size": 4096,
        },
        error_code=CLUSTERED_INDEX_CAPPED_CONFLICT_ERROR,
        msg="Clustered + capped should fail",
    ),
    CommandTestCase(
        id="incompatible_with_timeseries",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "timeseries": {"timeField": "ts"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Clustered + timeseries should fail",
    ),
    CommandTestCase(
        id="incompatible_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "viewOn": "other",
            "pipeline": [],
        },
        error_code=CLUSTERED_INDEX_VIEW_CONFLICT_ERROR,
        msg="Clustered + viewOn should fail",
    ),
    CommandTestCase(
        id="max_on_clustered_collection",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "max": 100,
        },
        error_code=CLUSTERED_INDEX_MAX_CONFLICT_ERROR,
        msg="max on clustered collection should fail",
    ),
    CommandTestCase(
        id="clustered_false_with_capped",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": False,
            "capped": True,
            "size": 4096,
        },
        error_code=CLUSTERED_INDEX_CAPPED_CONFLICT_ERROR,
        msg="clusteredIndex:false + capped still triggers conflict",
    ),
    CommandTestCase(
        id="incompatible_with_id_index",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "idIndex": {"key": {"_id": 1}, "name": "_id_"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Clustered + idIndex should fail",
    ),
]

CREATE_CLUSTERED_ERROR_TESTS: list[CommandTestCase] = (
    CREATE_CLUSTERED_LEGACY_FORMAT_ERROR_TESTS
    + CREATE_CLUSTERED_TYPE_ERROR_TESTS
    + CREATE_CLUSTERED_MISSING_FIELD_ERROR_TESTS
    + CREATE_CLUSTERED_KEY_ERROR_TESTS
    + CREATE_CLUSTERED_UNIQUE_ERROR_TESTS
    + CREATE_CLUSTERED_VERSION_ERROR_TESTS
    + CREATE_CLUSTERED_UNKNOWN_FIELD_ERROR_TESTS
    + CREATE_CLUSTERED_INCOMPATIBILITY_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_CLUSTERED_ERROR_TESTS))
def test_create_clustered_index_validation(database_client, collection, test):
    """Test create command clustered index validation behavior."""
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
