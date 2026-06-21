from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import TS_INCREMENT_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.aggregate


@dataclass(frozen=True)
class TsIncrementTest(BaseTestCase):
    doc: dict[str, Any] | None = None


TESTS: list[TsIncrementTest] = [
    TsIncrementTest(
        "null_input",
        doc={"ts": None},
        expected=None,
        msg="null ts field returns null",
    ),
    TsIncrementTest(
        "missing_field",
        doc={},
        expected=None,
        msg="missing ts field returns null",
    ),
    TsIncrementTest(
        "ordinal_zero",
        doc={"ts": Timestamp(100, 0)},
        expected=Int64(0),
        msg="ordinal=0 is returned as Int64(0)",
    ),
    TsIncrementTest(
        "ordinal_one",
        doc={"ts": Timestamp(0, 1)},
        expected=Int64(1),
        msg="ordinal=1 is returned as Int64(1)",
    ),
    TsIncrementTest(
        "ordinal_max_uint32",
        doc={"ts": Timestamp(0, 4294967295)},
        expected=Int64(4294967295),
        msg="max uint32 ordinal (4294967295) is preserved as Int64",
    ),
    TsIncrementTest(
        "seconds_ignored",
        doc={"ts": Timestamp(4294967295, 42)},
        expected=Int64(42),
        msg="only the ordinal component is returned; seconds field is ignored",
    ),
    TsIncrementTest(
        "type_double",
        doc={"ts": 3.14},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="double input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_string",
        doc={"ts": "hello"},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="string input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_object",
        doc={"ts": {"a": 1}},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="object input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_array",
        doc={"ts": [1, 2]},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="array input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_bindata",
        doc={"ts": Binary(b"\x00\x01")},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="Binary input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_objectid",
        doc={"ts": ObjectId("000000000000000000000000")},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="ObjectId input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_bool",
        doc={"ts": True},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="bool input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_date",
        doc={"ts": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="date input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_regex",
        doc={"ts": Regex("^abc")},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="Regex input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_code",
        doc={"ts": Code("function() {}")},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="Code (JavaScript) input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_int",
        doc={"ts": 42},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="int32 input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_long",
        doc={"ts": Int64(100)},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="int64 input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_decimal128",
        doc={"ts": Decimal128("1")},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="Decimal128 input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_minkey",
        doc={"ts": MinKey()},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="MinKey input raises TS_INCREMENT_TYPE_ERROR",
    ),
    TsIncrementTest(
        "type_maxkey",
        doc={"ts": MaxKey()},
        error_code=TS_INCREMENT_TYPE_ERROR,
        msg="MaxKey input raises TS_INCREMENT_TYPE_ERROR",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TESTS))
def test_tsIncrement(collection, test_case: TsIncrementTest):
    """Test $tsIncrement operator: null propagation, boundary values, type rejection."""
    result = execute_expression_with_insert(collection, {"$tsIncrement": "$ts"}, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


def test_tsIncrement_nested_field(collection):
    """$tsIncrement resolves a nested field path ($a.b) to extract the ordinal."""
    result = execute_expression_with_insert(
        collection,
        {"$tsIncrement": "$a.b"},
        {"a": {"b": Timestamp(100, 7)}},
    )
    assert_expression_result(
        result, expected=Int64(7), msg="nested path $a.b resolves Timestamp correctly"
    )
