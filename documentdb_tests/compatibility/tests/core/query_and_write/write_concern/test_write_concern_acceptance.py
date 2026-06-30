"""writeConcern acceptance: valid w/j/wtimeout/provenance values and their
combinations, plus writeConcern:null behaving like an omitted writeConcern.
"""

from typing import Any, Dict, cast

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
)

W_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_0",
        command={"updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}], "writeConcern": {"w": 0}},
        expected={"ok": Eq(1.0)},
        msg="w:0 should be accepted.",
    ),
    CommandTestCase(
        "w_double_coerced",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1.0},
        },
        expected={"ok": Eq(1.0)},
        msg="w:1.0 should coerce and be accepted.",
    ),
    CommandTestCase(
        "w_int64_coerced",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": Int64(1)},
        },
        expected={"ok": Eq(1.0)},
        msg="w as Int64 should coerce and be accepted.",
    ),
    CommandTestCase(
        "w_decimal128_coerced",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": Decimal128("1")},
        },
        expected={"ok": Eq(1.0)},
        msg="w as Decimal128 should coerce and be accepted.",
    ),
    CommandTestCase(
        "w_int64_0",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": Int64(0)},
        },
        expected={"ok": Eq(1.0)},
        msg="w as Int64(0) should be accepted.",
    ),
    CommandTestCase(
        "w_negative_zero",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": -0.0},
        },
        expected={"ok": Eq(1.0)},
        msg="w:-0.0 should be accepted.",
    ),
    CommandTestCase(
        "w_fractional_0_5",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 0.5},
        },
        expected={"ok": Eq(1.0)},
        msg="w:0.5 should be accepted.",
    ),
    CommandTestCase(
        "w_fractional_1_5",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1.5},
        },
        expected={"ok": Eq(1.0)},
        msg="w:1.5 should be accepted.",
    ),
]


WTIMEOUT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "int32_max",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": INT32_MAX},
        },
        expected={"ok": Eq(1.0)},
        msg="wtimeout INT32_MAX ok.",
    ),
    CommandTestCase(
        "int32_min",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": INT32_MIN},
        },
        expected={"ok": Eq(1.0)},
        msg="wtimeout INT32_MIN ok.",
    ),
    CommandTestCase(
        "negative_inf",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": FLOAT_NEGATIVE_INFINITY},
        },
        expected={"ok": Eq(1.0)},
        msg="wtimeout -Infinity ok.",
    ),
    CommandTestCase(
        "decimal128_neg_inf",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": DECIMAL128_NEGATIVE_INFINITY},
        },
        expected={"ok": Eq(1.0)},
        msg="wtimeout Decimal128 -Infinity ok.",
    ),
    CommandTestCase(
        "zero",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": 0},
        },
        expected={"ok": Eq(1.0)},
        msg="wtimeout 0 ok.",
    ),
    CommandTestCase(
        "negative",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "wtimeout": -1},
        },
        expected={"ok": Eq(1.0)},
        msg="wtimeout negative ok.",
    ),
    CommandTestCase(
        "with_w0",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 0, "wtimeout": 5_000},
        },
        expected={"ok": Eq(1.0)},
        msg="wtimeout with w:0 ok.",
    ),
]


# Sub-fields compose in one writeConcern document.
COMBINATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "all_three",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "j": True, "wtimeout": 5_000},
        },
        expected={"ok": Eq(1.0)},
        msg="w + j + wtimeout together should be accepted.",
    ),
]


# provenance acceptance (a representative value plus null).
PROVENANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "clientSupplied",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "provenance": "clientSupplied"},
        },
        expected={"ok": Eq(1.0)},
        msg="provenance:'clientSupplied' should be accepted.",
    ),
    CommandTestCase(
        "null",
        command={
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 1, "provenance": None},
        },
        expected={"ok": Eq(1.0)},
        msg="provenance:null should be accepted.",
    ),
]

WRITE_CONCERN_ACCEPTANCE_TESTS = (
    W_ACCEPTANCE_TESTS + WTIMEOUT_ACCEPTANCE_TESTS + COMBINATION_TESTS + PROVENANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_ACCEPTANCE_TESTS))
def test_write_concern_accepted(collection, test: CommandTestCase):
    """Test writeConcern accepts valid sub-field values and combinations."""
    collection.insert_one({"_id": 1, "a": 0})
    update_body = cast(Dict[str, Any], test.command)
    result = execute_command(collection, {"update": collection.name, **update_body})
    assertResult(result, expected=test.expected, msg=test.msg, raw_res=True)


def test_write_concern_null_equivalent_to_omitted(collection):
    """Test writeConcern null produces the same response as omitting writeConcern."""
    collection.insert_many([{"_id": 1, "a": 0}, {"_id": 2, "a": 0}])
    omitted = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
        },
    )
    explicit_null = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 2}, "u": {"$set": {"a": 1}}}],
            "writeConcern": None,
        },
    )
    expected = {k: omitted[k] for k in ("ok", "n", "nModified") if k in omitted}
    assertSuccessPartial(
        explicit_null,
        expected,
        msg="update with writeConcern:null should match an omitted writeConcern.",
    )
