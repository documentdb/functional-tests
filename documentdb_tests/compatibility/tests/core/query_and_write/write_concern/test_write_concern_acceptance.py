"""
writeConcern acceptance tests.

Tests that valid writeConcern values are accepted across write commands, including
w sub-field coercions, j truthiness, wtimeout acceptance, and sub-field combinations.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.query_and_write.write_concern.utils import (
    WRITE_COMMANDS,
    build_cmd,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertNotError
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX

_VALID_WC_VALUES = [
    ("null", None),
    ("empty_doc", {}),
    ("w_1", {"w": 1}),
    ("w_0", {"w": 0}),
    ("w_majority", {"w": "majority"}),
    ("w_double_coerced", {"w": 1.0}),
    ("w_int64_coerced", {"w": Int64(1)}),
    ("w_decimal128_coerced", {"w": Decimal128("1")}),
    ("w_tagged_object", {"w": {"dc1": 1}}),
    ("w_negative_zero", {"w": -0.0}),
    ("w_decimal128_neg_zero", {"w": Decimal128("-0")}),
    ("w_decimal128_zero_exponent", {"w": Decimal128("0E+3")}),
    ("w_decimal128_one_exponent", {"w": Decimal128("1E+0")}),
    ("w_decimal128_one_decimal", {"w": Decimal128("1.0")}),
    ("w_int64_0", {"w": Int64(0)}),
    ("w_fractional_1_5", {"w": 1.5}),
    ("w_fractional_0_5", {"w": 0.5}),
]

# Property [writeConcern Acceptance]: write commands accept valid writeConcern values.
WC_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_accepts_wc_{val_name}",
        docs=[{"_id": 1}],
        command=lambda ctx, _wc=value, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        msg=f"{cmd} should accept writeConcern {val_name}.",
    )
    for cmd in WRITE_COMMANDS
    for val_name, value in _VALID_WC_VALUES
]


@pytest.mark.parametrize("test", pytest_params(WC_ACCEPTANCE_TESTS))
def test_write_concern_accepted(collection, test: CommandTestCase):
    """Test write commands accept valid writeConcern values."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertNotError(result, msg=test.msg)


_VALID_J_VALUES = [
    ("j_true", {"w": 1, "j": True}),
    ("j_false", {"w": 1, "j": False}),
    ("j_null", {"w": 1, "j": None}),
    ("j_int32", {"w": 1, "j": 42}),
    ("j_int64", {"w": 1, "j": Int64(1)}),
    ("j_double", {"w": 1, "j": 3.14}),
    ("j_decimal128", {"w": 1, "j": Decimal128("1")}),
]

# Property [j Acceptance]: j accepts boolean and numeric types via truthiness coercion.
J_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_accepts_{val_name}",
        docs=[{"_id": 1}],
        command=lambda ctx, _wc=value, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        msg=f"{cmd} should accept writeConcern {val_name}.",
    )
    for cmd in WRITE_COMMANDS
    for val_name, value in _VALID_J_VALUES
]


@pytest.mark.parametrize("test", pytest_params(J_ACCEPTANCE_TESTS))
def test_write_concern_j_accepted(collection, test: CommandTestCase):
    """Test j sub-field accepts boolean and numeric types."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertNotError(result, msg=test.msg)


_VALID_WTIMEOUT_VALUES = [
    ("int", {"w": 1, "wtimeout": 5_000}),
    ("int64", {"w": 1, "wtimeout": Int64(5_000)}),
    ("double", {"w": 1, "wtimeout": 5000.0}),
    ("decimal128", {"w": 1, "wtimeout": Decimal128("5000")}),
    ("string", {"w": 1, "wtimeout": "hello"}),
    ("bool", {"w": 1, "wtimeout": True}),
    ("array", {"w": 1, "wtimeout": [1, 2]}),
    ("object", {"w": 1, "wtimeout": {"a": 1}}),
    ("null", {"w": 1, "wtimeout": None}),
    ("objectId", {"w": 1, "wtimeout": ObjectId()}),
    ("binary", {"w": 1, "wtimeout": Binary(b"x")}),
    ("date", {"w": 1, "wtimeout": datetime(2024, 1, 1, tzinfo=timezone.utc)}),
    ("regex", {"w": 1, "wtimeout": Regex("x")}),
    ("code", {"w": 1, "wtimeout": Code("function(){}")}),
    ("timestamp", {"w": 1, "wtimeout": Timestamp(1, 1)}),
    ("minKey", {"w": 1, "wtimeout": MinKey()}),
    ("maxKey", {"w": 1, "wtimeout": MaxKey()}),
    ("int32_max", {"w": 1, "wtimeout": INT32_MAX}),
]

# Property [wtimeout Acceptance]: wtimeout accepts all BSON types.
WTIMEOUT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_accepts_wtimeout_{val_name}",
        docs=[{"_id": 1}],
        command=lambda ctx, _wc=value, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        msg=f"{cmd} should accept wtimeout of type {val_name}.",
    )
    for cmd in WRITE_COMMANDS
    for val_name, value in _VALID_WTIMEOUT_VALUES
]


@pytest.mark.parametrize("test", pytest_params(WTIMEOUT_ACCEPTANCE_TESTS))
def test_write_concern_wtimeout_accepted(collection, test: CommandTestCase):
    """Test wtimeout sub-field accepts all BSON types."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertNotError(result, msg=test.msg)


_COMBINATION_VALUES = [
    ("w1_j_true", {"w": 1, "j": True}),
    ("w1_j_false", {"w": 1, "j": False}),
    ("majority_j_true", {"w": "majority", "j": True}),
    ("majority_wtimeout", {"w": "majority", "wtimeout": 5_000}),
    ("all_three", {"w": 1, "j": True, "wtimeout": 5_000}),
]

# Property [Sub-Field Combinations]: w, j, and wtimeout work together correctly.
COMBINATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_wc_combination_{val_name}",
        docs=[{"_id": 1}],
        command=lambda ctx, _wc=value, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        msg=f"{cmd} should accept writeConcern combination {val_name}.",
    )
    for cmd in WRITE_COMMANDS
    for val_name, value in _COMBINATION_VALUES
]


@pytest.mark.parametrize("test", pytest_params(COMBINATION_TESTS))
def test_write_concern_combinations(collection, test: CommandTestCase):
    """Test writeConcern sub-field combinations are accepted."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertNotError(result, msg=test.msg)


_WTIMEOUT_EDGE_VALUES = [
    ("zero", {"w": 1, "wtimeout": 0}),
    ("zero_with_majority", {"w": "majority", "wtimeout": 0}),
    ("negative", {"w": 1, "wtimeout": -1}),
    ("with_w0", {"w": 0, "wtimeout": 5_000}),
]

# Property [wtimeout Edge Cases]: wtimeout zero/negative/with-w:0 are accepted without error.
WTIMEOUT_EDGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_wtimeout_edge_{val_name}",
        docs=[{"_id": 1}],
        command=lambda ctx, _wc=value, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        msg=f"{cmd} should accept wtimeout edge case {val_name}.",
    )
    for cmd in WRITE_COMMANDS
    for val_name, value in _WTIMEOUT_EDGE_VALUES
]


@pytest.mark.parametrize("test", pytest_params(WTIMEOUT_EDGE_TESTS))
def test_write_concern_wtimeout_edge_cases(collection, test: CommandTestCase):
    """Test wtimeout edge cases are accepted."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertNotError(result, msg=test.msg)


_PROVENANCE_VALUES = [
    ("clientSupplied", "clientSupplied"),
    ("implicitDefault", "implicitDefault"),
    ("customDefault", "customDefault"),
    ("getLastErrorDefaults", "getLastErrorDefaults"),
    ("null", None),
]

# Property [Provenance Acceptance]: writeConcern accepts provenance sub-field.
PROVENANCE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_accepts_provenance_{val_name}",
        docs=[{"_id": 1}],
        command=lambda ctx, _prov=value, _cmd=cmd: build_cmd(
            _cmd, ctx, {"w": 1, "provenance": _prov}
        ),
        msg=f"{cmd} should accept provenance:'{value}'.",
    )
    for cmd in WRITE_COMMANDS
    for val_name, value in _PROVENANCE_VALUES
]


@pytest.mark.parametrize("test", pytest_params(PROVENANCE_ACCEPTANCE_TESTS))
def test_write_concern_provenance_accepted(collection, test: CommandTestCase):
    """Test writeConcern accepts provenance sub-field values."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertNotError(result, msg=test.msg)


def test_write_concern_null_equivalent_to_omitted(collection):
    """Test writeConcern null produces same success as omitting writeConcern."""
    collection.insert_one({"_id": 1, "a": 0})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": None,
        },
    )
    assertNotError(result, msg="update with writeConcern:null should not error.")
