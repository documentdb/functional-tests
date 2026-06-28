"""Tests for the create command idIndex validation behavior."""

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CANNOT_CREATE_INDEX_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_INDEX_SPEC_OPTION_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [IdIndex Incompatibilities]: idIndex is incompatible with viewOn,
# timeseries, and clusteredIndex.
CREATE_ID_INDEX_INCOMPATIBILITY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="incompatible_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "idIndex": {"key": {"_id": 1}, "name": "_id_"},
        },
        expected=None,
        error_code=INVALID_OPTIONS_ERROR,
        msg="idIndex with viewOn should fail",
    ),
    CommandTestCase(
        id="incompatible_with_timeseries",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "timeseries": {"timeField": "ts"},
            "idIndex": {"key": {"_id": 1}, "name": "_id_"},
        },
        expected=None,
        error_code=INVALID_OPTIONS_ERROR,
        msg="idIndex with timeseries should fail",
    ),
    CommandTestCase(
        id="incompatible_with_clustered_index",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "idIndex": {"key": {"_id": 1}, "name": "_id_"},
        },
        expected=None,
        error_code=INVALID_OPTIONS_ERROR,
        msg="idIndex with clusteredIndex should fail",
    ),
]

# Property [IdIndex Type Validation]: non-object types for idIndex produce
# TYPE_MISMATCH_ERROR.
CREATE_ID_INDEX_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"type_{tid}",
        command=lambda ctx, v=val: {
            "create": f"{ctx.collection}_custom",
            "idIndex": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{tid} idIndex should fail with type mismatch",
    )
    for tid, val in [
        ("int", 123),
        ("string", "invalid"),
        ("bool", True),
        ("array", [{"key": {"_id": 1}, "name": "_id_"}]),
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

# Property [IdIndex Missing Required Fields]: an idIndex document missing key
# or name produces FAILED_TO_PARSE_ERROR.
CREATE_ID_INDEX_MISSING_FIELDS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="empty_document",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {},
        },
        expected=None,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Empty idIndex document should fail with missing key",
    ),
    CommandTestCase(
        id="missing_name",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}},
        },
        expected=None,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="idIndex missing name should fail",
    ),
    CommandTestCase(
        id="missing_key",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"name": "_id_"},
        },
        expected=None,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="idIndex missing key should fail",
    ),
]

# Property [IdIndex Key Validation]: the key field must be exactly {_id:1}.
# Non-_id fields, compound keys, descending, hashed, and text produce
# BAD_VALUE_ERROR.
CREATE_ID_INDEX_KEY_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="key_wrong_field",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"x": 1}, "name": "_id_"},
        },
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="idIndex with key {x:1} should fail",
    ),
    CommandTestCase(
        id="key_compound",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1, "x": 1}, "name": "_id_"},
        },
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="idIndex with compound key should fail",
    ),
    CommandTestCase(
        id="key_descending",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": -1}, "name": "_id_"},
        },
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="idIndex with descending _id key should fail",
    ),
    CommandTestCase(
        id="key_hashed",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": "hashed"}, "name": "_id_"},
        },
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="idIndex with hashed _id key should fail",
    ),
    CommandTestCase(
        id="key_text",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": "text"}, "name": "_id_"},
        },
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="idIndex with text _id key should fail",
    ),
]

# Property [IdIndex Key Type Validation]: the key sub-field must be an object.
# Non-object types produce TYPE_MISMATCH_ERROR.
CREATE_ID_INDEX_KEY_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"key_type_{tid}",
        command=lambda ctx, v=val: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": v, "name": "_id_"},
        },
        expected=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"idIndex with {tid} key should fail with type mismatch",
    )
    for tid, val in [
        ("null", None),
        ("string", "invalid"),
        ("int", 123),
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
]

# Property [IdIndex Name Validation]: the name sub-field must be a non-empty
# string. Non-string types produce TYPE_MISMATCH_ERROR; empty string produces
# CANNOT_CREATE_INDEX_ERROR.
CREATE_ID_INDEX_NAME_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            id=f"name_type_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "idIndex": {"key": {"_id": 1}, "name": v},
            },
            expected=None,
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"idIndex with {tid} name should fail with type mismatch",
        )
        for tid, val in [
            ("null", None),
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
    CommandTestCase(
        id="name_empty_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": ""},
        },
        expected=None,
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="idIndex with empty name should fail",
    ),
]

# Property [IdIndex Version Validation]: v values outside {1, 2} or
# non-integral/non-numeric types produce errors.
CREATE_ID_INDEX_VERSION_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="v_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "v": 0},
        },
        expected=None,
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="idIndex with v:0 should fail",
    ),
    CommandTestCase(
        id="v_three",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "v": 3},
        },
        expected=None,
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="idIndex with v:3 should fail",
    ),
    CommandTestCase(
        id="v_negative",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "v": -1},
        },
        expected=None,
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="idIndex with v:-1 should fail",
    ),
    CommandTestCase(
        id="v_non_integral_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "v": 2.5},
        },
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="idIndex with non-integral v should fail",
    ),
    *[
        CommandTestCase(
            id=f"v_type_{tid}",
            command=lambda ctx, v=val: {
                "create": f"{ctx.collection}_custom",
                "idIndex": {"key": {"_id": 1}, "name": "_id_", "v": v},
            },
            expected=None,
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"idIndex with {tid} v should fail with type mismatch",
        )
        for tid, val in [
            ("string", "two"),
            ("bool", True),
            ("array", [2]),
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

# Property [IdIndex Invalid Options]: index options not valid for _id indexes
# (unique, sparse, background, expireAfterSeconds, partialFilterExpression, and
# unknown fields) produce INVALID_INDEX_SPEC_OPTION_ERROR.
CREATE_ID_INDEX_INVALID_OPTIONS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="option_unique_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "unique": True},
        },
        expected=None,
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="idIndex with unique:true should fail",
    ),
    CommandTestCase(
        id="option_unique_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "unique": False},
        },
        expected=None,
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="idIndex with unique:false should fail",
    ),
    CommandTestCase(
        id="option_sparse_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "sparse": True},
        },
        expected=None,
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="idIndex with sparse:true should fail",
    ),
    CommandTestCase(
        id="option_sparse_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "sparse": False},
        },
        expected=None,
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="idIndex with sparse:false should fail",
    ),
    CommandTestCase(
        id="option_background",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "background": True},
        },
        expected=None,
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="idIndex with background:true should fail",
    ),
    CommandTestCase(
        id="option_expire_after_seconds",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "expireAfterSeconds": 3600},
        },
        expected=None,
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="idIndex with expireAfterSeconds should fail",
    ),
    CommandTestCase(
        id="option_partial_filter_expression",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "partialFilterExpression": {"x": 1}},
        },
        expected=None,
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="idIndex with partialFilterExpression should fail",
    ),
    CommandTestCase(
        id="option_unknown_field",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "unknownField": "val"},
        },
        expected=None,
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="idIndex with unknown field should fail",
    ),
]

# Property [IdIndex Collation Mismatch]: idIndex collation that does not match
# the collection collation produces BAD_VALUE_ERROR.
CREATE_ID_INDEX_COLLATION_MISMATCH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_mismatch",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en"},
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "collation": {"locale": "fr"}},
        },
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="idIndex collation mismatching collection collation should fail",
    ),
    CommandTestCase(
        id="collation_on_non_collated_collection",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "collation": {"locale": "en"}},
        },
        expected=None,
        error_code=BAD_VALUE_ERROR,
        msg="idIndex collation on non-collated collection should fail",
    ),
]

CREATE_ID_INDEX_VALIDATION_TESTS: list[CommandTestCase] = (
    CREATE_ID_INDEX_INCOMPATIBILITY_ERROR_TESTS
    + CREATE_ID_INDEX_TYPE_ERROR_TESTS
    + CREATE_ID_INDEX_MISSING_FIELDS_ERROR_TESTS
    + CREATE_ID_INDEX_KEY_VALIDATION_ERROR_TESTS
    + CREATE_ID_INDEX_KEY_TYPE_ERROR_TESTS
    + CREATE_ID_INDEX_NAME_VALIDATION_ERROR_TESTS
    + CREATE_ID_INDEX_VERSION_VALIDATION_ERROR_TESTS
    + CREATE_ID_INDEX_INVALID_OPTIONS_ERROR_TESTS
    + CREATE_ID_INDEX_COLLATION_MISMATCH_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_ID_INDEX_VALIDATION_TESTS))
def test_create_id_index_validation(database_client, collection, test):
    """Test create command idIndex validation behavior."""
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
