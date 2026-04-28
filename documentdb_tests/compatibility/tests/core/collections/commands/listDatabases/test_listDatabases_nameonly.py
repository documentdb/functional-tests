"""Tests for listDatabases nameOnly parameter."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.listDatabases.utils.listDatabases_common import (  # noqa: E501
    full_structure_success,
    name_only_success,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Eq, Len
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [nameOnly Response Structure]: when nameOnly is true, the
# response contains only databases and ok, and each database entry
# contains only the name field.
name_only_success_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": True},
        expected=name_only_success,
        msg="nameOnly=true should produce only databases and ok at top level",
        id="name_only_top_level_keys",
    ),
]

# Property [nameOnly Boolean Coercion - Falsy]: zero numeric values
# passed to nameOnly are coerced to false, producing the full response
# with size information.
NAME_ONLY_FALSY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": 0},
        expected=full_structure_success,
        msg="int32 0 should be falsy for nameOnly",
        id="name_only_int32_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": INT64_ZERO},
        expected=full_structure_success,
        msg="Int64 0 should be falsy for nameOnly",
        id="name_only_int64_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": DOUBLE_ZERO},
        expected=full_structure_success,
        msg="double 0.0 should be falsy for nameOnly",
        id="name_only_double_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": DOUBLE_NEGATIVE_ZERO},
        expected=full_structure_success,
        msg="double -0.0 should be falsy for nameOnly",
        id="name_only_double_neg_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": DECIMAL128_ZERO},
        expected=full_structure_success,
        msg="Decimal128 '0' should be falsy for nameOnly",
        id="name_only_decimal128_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": DECIMAL128_NEGATIVE_ZERO},
        expected=full_structure_success,
        msg="Decimal128 '-0' should be falsy for nameOnly",
        id="name_only_decimal128_neg_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": Decimal128("-0.0")},
        expected=full_structure_success,
        msg="Decimal128 '-0.0' should be falsy for nameOnly",
        id="name_only_decimal128_neg_zero_dot",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": Decimal128("-0E+10")},
        expected=full_structure_success,
        msg="Decimal128 '-0E+10' should be falsy for nameOnly",
        id="name_only_decimal128_neg_zero_exp",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": Decimal128("0E-10")},
        expected=full_structure_success,
        msg="Decimal128 '0E-10' should be falsy for nameOnly",
        id="name_only_decimal128_zero_neg_exp",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": Decimal128("0." + "0" * 32),
        },
        expected=full_structure_success,
        msg="Decimal128 '0.000...0' (32 trailing zeros) should be falsy",
        id="name_only_decimal128_zero_trailing",
    ),
]

# Property [nameOnly Boolean Coercion - Truthy]: all non-zero numeric
# values passed to nameOnly are coerced to true, producing the
# name-only response without size information.
NAME_ONLY_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": 1},
        expected=name_only_success,
        msg="int32 1 should be truthy for nameOnly",
        id="name_only_int32_one",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": INT32_MAX},
        expected=name_only_success,
        msg="max 32-bit integer should be truthy for nameOnly",
        id="name_only_int32_max",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": INT32_MIN},
        expected=name_only_success,
        msg="min 32-bit integer should be truthy for nameOnly",
        id="name_only_int32_min",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": INT64_MAX},
        expected=name_only_success,
        msg="max 64-bit integer should be truthy for nameOnly",
        id="name_only_int64_max",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": INT64_MIN},
        expected=name_only_success,
        msg="min 64-bit integer should be truthy for nameOnly",
        id="name_only_int64_min",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": FLOAT_NAN},
        expected=name_only_success,
        msg="double NaN should be truthy for nameOnly",
        id="name_only_double_nan",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": FLOAT_INFINITY},
        expected=name_only_success,
        msg="double Infinity should be truthy for nameOnly",
        id="name_only_double_inf",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": FLOAT_NEGATIVE_INFINITY},
        expected=name_only_success,
        msg="double -Infinity should be truthy for nameOnly",
        id="name_only_double_neg_inf",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": DOUBLE_MIN_SUBNORMAL},
        expected=name_only_success,
        msg="min subnormal double should be truthy for nameOnly",
        id="name_only_double_subnormal",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": 0.5},
        expected=name_only_success,
        msg="double 0.5 should be truthy for nameOnly",
        id="name_only_double_half",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": 0.1},
        expected=name_only_success,
        msg="double 0.1 should be truthy for nameOnly",
        id="name_only_double_tenth",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": DECIMAL128_NAN},
        expected=name_only_success,
        msg="Decimal128 NaN should be truthy for nameOnly",
        id="name_only_decimal128_nan",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": DECIMAL128_INFINITY},
        expected=name_only_success,
        msg="Decimal128 Infinity should be truthy for nameOnly",
        id="name_only_decimal128_inf",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": DECIMAL128_NEGATIVE_INFINITY,
        },
        expected=name_only_success,
        msg="Decimal128 -Infinity should be truthy for nameOnly",
        id="name_only_decimal128_neg_inf",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": DECIMAL128_MAX},
        expected=name_only_success,
        msg="Decimal128 max value should be truthy for nameOnly",
        id="name_only_decimal128_max",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": DECIMAL128_MIN_POSITIVE},
        expected=name_only_success,
        msg="Decimal128 min positive should be truthy for nameOnly",
        id="name_only_decimal128_min_positive",
    ),
]

# Property [nameOnly Type Strictness]: nameOnly rejects non-bool,
# non-numeric types with a TypeMismatch error.
NAME_ONLY_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": "true"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with string should produce TypeMismatch",
        id="name_only_type_string",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with array should produce TypeMismatch",
        id="name_only_type_array",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with object should produce TypeMismatch",
        id="name_only_type_object",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with ObjectId should produce TypeMismatch",
        id="name_only_type_objectid",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": datetime.datetime(2024, 1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with datetime should produce TypeMismatch",
        id="name_only_type_datetime",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with Timestamp should produce TypeMismatch",
        id="name_only_type_timestamp",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": Binary(b"\x01")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with Binary should produce TypeMismatch",
        id="name_only_type_binary",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": Binary(
                b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10", subtype=4
            ),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with Binary UUID subtype should produce TypeMismatch",
        id="name_only_type_binary_uuid",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": Regex("^x")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with Regex should produce TypeMismatch",
        id="name_only_type_regex",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with Code should produce TypeMismatch",
        id="name_only_type_code",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": Code("function(){}", {"x": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with CodeWithScope should produce TypeMismatch",
        id="name_only_type_code_with_scope",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with MinKey should produce TypeMismatch",
        id="name_only_type_minkey",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="nameOnly with MaxKey should produce TypeMismatch",
        id="name_only_type_maxkey",
    ),
]

# Property [nameOnly Filter Projection]: when nameOnly is true, the
# filter operates on the projected document containing only the name
# field, so filtering on sizeOnDisk or empty returns zero results,
# $expr references to those fields resolve to missing, and
# $exists:false on sizeOnDisk matches all databases.
PARAM_INTERACTION_NAMEONLY_FILTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": True,
            "filter": {"sizeOnDisk": {"$gte": 0}},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="nameOnly=true should hide sizeOnDisk from filter, returning 0 results",
        id="param_nameonly_filter_sizeondisk",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": True,
            "filter": {"empty": False},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="nameOnly=true should hide empty from filter, returning 0 results",
        id="param_nameonly_filter_empty",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": True,
            "filter": {"$expr": "$sizeOnDisk"},
        },
        expected={"ok": Eq(1.0), "databases": Len(0)},
        msg="nameOnly=true should make $sizeOnDisk resolve to missing (falsy) in $expr",
        id="param_nameonly_expr_sizeondisk",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": True,
            "filter": {"$expr": {"$eq": [{"$ifNull": ["$empty", "was_missing"]}, "was_missing"]}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="nameOnly=true should make $empty resolve to missing in $expr",
        id="param_nameonly_expr_empty",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": True,
            "filter": {"sizeOnDisk": {"$exists": False}},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="nameOnly=true with $exists:false on sizeOnDisk should match all databases",
        id="param_nameonly_exists_false_sizeondisk",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "nameOnly": True,
            "filter": {"name": "admin"},
        },
        expected={"ok": Eq(1.0), "databases": Contains("name", "admin")},
        msg="Name-based filter should work with nameOnly=true",
        id="param_nameonly_filter_name",
    ),
]

NAMEONLY_TESTS: list[CommandTestCase] = (
    name_only_success_TESTS
    + NAME_ONLY_FALSY_TESTS
    + NAME_ONLY_TRUTHY_TESTS
    + NAME_ONLY_TYPE_ERROR_TESTS
    + PARAM_INTERACTION_NAMEONLY_FILTER_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(NAMEONLY_TESTS))
def test_listDatabases_nameonly(collection, test):
    """Test listDatabases nameOnly parameter behavior."""
    ctx = CommandContext.from_collection(collection)
    collection.database.create_collection(collection.name)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
