"""
BSON wiring tests for $max update field operator.

Tests $max behavior with cross-type BSON comparisons and complex values
(arrays, objects). Verifies $max correctly delegates to BSON comparison order.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_TEST_DATE = datetime(2023, 6, 1, tzinfo=timezone.utc)
_TIMESTAMP = Timestamp(1672531200, 1)

TESTS: list[UpdateTestCase] = [
    # Upward transitions in BSON order (should update)
    UpdateTestCase(
        "null_to_number_updates",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": 1}},
        expected={"_id": 1, "val": 1},
        msg="Number > Null in BSON order, should update",
    ),
    UpdateTestCase(
        "number_to_string_updates",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$max": {"val": "a"}},
        expected={"_id": 1, "val": "a"},
        msg="String > Number in BSON order, should update",
    ),
    UpdateTestCase(
        "string_to_object_updates",
        setup_docs=[{"_id": 1, "val": "zzz"}],
        query={"_id": 1},
        update={"$max": {"val": {"key": 1}}},
        expected={"_id": 1, "val": {"key": 1}},
        msg="Object > String in BSON order, should update",
    ),
    UpdateTestCase(
        "object_to_array_updates",
        setup_docs=[{"_id": 1, "val": {"key": 999}}],
        query={"_id": 1},
        update={"$max": {"val": [1]}},
        expected={"_id": 1, "val": [1]},
        msg="Array > Object in BSON order, should update",
    ),
    UpdateTestCase(
        "string_to_binary_updates",
        setup_docs=[{"_id": 1, "val": "hello"}],
        query={"_id": 1},
        update={"$max": {"val": Binary(b"data")}},
        expected={"_id": 1, "val": b"data"},
        msg="Binary > String in BSON order, should update",
    ),
    UpdateTestCase(
        "binary_to_objectid_updates",
        setup_docs=[{"_id": 1, "val": Binary(b"data")}],
        query={"_id": 1},
        update={"$max": {"val": ObjectId("000000000000000000000001")}},
        expected={"_id": 1, "val": ObjectId("000000000000000000000001")},
        msg="ObjectId > Binary in BSON order, should update",
    ),
    UpdateTestCase(
        "objectid_to_boolean_updates",
        setup_docs=[{"_id": 1, "val": ObjectId("000000000000000000000001")}],
        query={"_id": 1},
        update={"$max": {"val": True}},
        expected={"_id": 1, "val": True},
        msg="Boolean > ObjectId in BSON order, should update",
    ),
    UpdateTestCase(
        "boolean_to_date_updates",
        setup_docs=[{"_id": 1, "val": True}],
        query={"_id": 1},
        update={"$max": {"val": _TEST_DATE}},
        expected={"_id": 1, "val": _TEST_DATE},
        msg="Date > Boolean in BSON order, should update",
    ),
    UpdateTestCase(
        "date_to_timestamp_updates",
        setup_docs=[{"_id": 1, "val": datetime(2023, 1, 1, tzinfo=timezone.utc)}],
        query={"_id": 1},
        update={"$max": {"val": _TIMESTAMP}},
        expected={"_id": 1, "val": _TIMESTAMP},
        msg="Timestamp > Date in BSON order, should update",
    ),
    UpdateTestCase(
        "timestamp_to_regex_updates",
        setup_docs=[{"_id": 1, "val": Timestamp(100, 1)}],
        query={"_id": 1},
        update={"$max": {"val": Regex("abc", "i")}},
        expected={"_id": 1, "val": Regex("abc", "i")},
        msg="Regex > Timestamp in BSON order, should update",
    ),
    UpdateTestCase(
        "minkey_to_null_updates",
        setup_docs=[{"_id": 1, "val": MinKey()}],
        query={"_id": 1},
        update={"$max": {"val": None}},
        expected={"_id": 1, "val": None},
        msg="Null > MinKey in BSON order, should update",
    ),
    UpdateTestCase(
        "any_to_maxkey_updates",
        setup_docs=[{"_id": 1, "val": "anything"}],
        query={"_id": 1},
        update={"$max": {"val": MaxKey()}},
        expected={"_id": 1, "val": MaxKey()},
        msg="MaxKey is greatest BSON value, should always update",
    ),
    UpdateTestCase(
        "minkey_to_any_updates",
        setup_docs=[{"_id": 1, "val": MinKey()}],
        query={"_id": 1},
        update={"$max": {"val": 1}},
        expected={"_id": 1, "val": 1},
        msg="MinKey is smallest, any value should update",
    ),
    UpdateTestCase(
        "number_to_boolean_updates",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$max": {"val": True}},
        expected={"_id": 1, "val": True},
        msg="Boolean > Number in BSON order, should update",
    ),
    UpdateTestCase(
        "null_byte_string_vs_number_updates",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$max": {"val": "abc\x00def"}},
        expected={"_id": 1, "val": "abc\x00def"},
        msg="String with null byte > number in BSON order, should update",
    ),
    # Downward transitions in BSON order (should NOT update)
    UpdateTestCase(
        "maxkey_to_any_unchanged",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$max": {"val": 999999}},
        expected={"_id": 1, "val": MaxKey()},
        msg="MaxKey is greatest, should not update to any other type",
    ),
    UpdateTestCase(
        "string_vs_objectid_unchanged",
        setup_docs=[{"_id": 1, "val": ObjectId("000000000000000000000001")}],
        query={"_id": 1},
        update={"$max": {"val": "zzz"}},
        expected={"_id": 1, "val": ObjectId("000000000000000000000001")},
        msg="String < ObjectId in BSON order, should not update",
    ),
    UpdateTestCase(
        "number_vs_string_unchanged",
        setup_docs=[{"_id": 1, "val": "hello"}],
        query={"_id": 1},
        update={"$max": {"val": 99999}},
        expected={"_id": 1, "val": "hello"},
        msg="Number < String in BSON order, should not update",
    ),
    UpdateTestCase(
        "null_vs_number_unchanged",
        setup_docs=[{"_id": 1, "val": 1}],
        query={"_id": 1},
        update={"$max": {"val": None}},
        expected={"_id": 1, "val": 1},
        msg="Null < Number in BSON order, should not update",
    ),
    UpdateTestCase(
        "timestamp_less_unchanged",
        setup_docs=[{"_id": 1, "val": Timestamp(100, 1)}],
        query={"_id": 1},
        update={"$max": {"val": Timestamp(0, 0)}},
        expected={"_id": 1, "val": Timestamp(100, 1)},
        msg="Timestamp(0,0) < Timestamp(100,1), should not update",
    ),
    # Array and object comparisons
    UpdateTestCase(
        "array_element_greater_updates",
        setup_docs=[{"_id": 1, "val": [1, 2, 3]}],
        query={"_id": 1},
        update={"$max": {"val": [1, 2, 4]}},
        expected={"_id": 1, "val": [1, 2, 4]},
        msg="$max with arrays [1,2,3] vs [1,2,4] should update (element-wise)",
    ),
    UpdateTestCase(
        "empty_array_to_nonempty_updates",
        setup_docs=[{"_id": 1, "val": []}],
        query={"_id": 1},
        update={"$max": {"val": [1]}},
        expected={"_id": 1, "val": [1]},
        msg="$max with [] vs [1] should update (non-empty > empty)",
    ),
    UpdateTestCase(
        "longer_array_unchanged",
        setup_docs=[{"_id": 1, "val": [1, 2, 3]}],
        query={"_id": 1},
        update={"$max": {"val": [1, 2]}},
        expected={"_id": 1, "val": [1, 2, 3]},
        msg="$max [1,2,3] > [1,2], should not update",
    ),
    UpdateTestCase(
        "object_field_value_greater_updates",
        setup_docs=[{"_id": 1, "val": {"a": 1}}],
        query={"_id": 1},
        update={"$max": {"val": {"a": 2}}},
        expected={"_id": 1, "val": {"a": 2}},
        msg="$max with objects {a:1} vs {a:2} should update",
    ),
    UpdateTestCase(
        "object_field_value_less_unchanged",
        setup_docs=[{"_id": 1, "val": {"a": 2}}],
        query={"_id": 1},
        update={"$max": {"val": {"a": 1}}},
        expected={"_id": 1, "val": {"a": 2}},
        msg="$max {a:2} > {a:1}, should not update",
    ),
    UpdateTestCase(
        "nested_array_inner_greater_updates",
        setup_docs=[{"_id": 1, "val": [[1, 2], [3, 4]]}],
        query={"_id": 1},
        update={"$max": {"val": [[1, 2], [3, 5]]}},
        expected={"_id": 1, "val": [[1, 2], [3, 5]]},
        msg="$max with nested arrays should compare element-wise recursively",
    ),
    UpdateTestCase(
        "nested_array_inner_less_unchanged",
        setup_docs=[{"_id": 1, "val": [[1, 2], [3, 5]]}],
        query={"_id": 1},
        update={"$max": {"val": [[1, 2], [3, 4]]}},
        expected={"_id": 1, "val": [[1, 2], [3, 5]]},
        msg="$max nested array where inner is less should not update",
    ),
    UpdateTestCase(
        "mixed_type_array_string_vs_number_updates",
        setup_docs=[{"_id": 1, "val": [1, 2, 3]}],
        query={"_id": 1},
        update={"$max": {"val": [1, 2, "a"]}},
        expected={"_id": 1, "val": [1, 2, "a"]},
        msg="$max with mixed-type arrays: string element > number in BSON order",
    ),
    UpdateTestCase(
        "mixed_type_array_number_vs_string_unchanged",
        setup_docs=[{"_id": 1, "val": [1, 2, "a"]}],
        query={"_id": 1},
        update={"$max": {"val": [1, 2, 3]}},
        expected={"_id": 1, "val": [1, 2, "a"]},
        msg="$max current has string > number element, should not update",
    ),
    UpdateTestCase(
        "object_more_fields_updates",
        setup_docs=[{"_id": 1, "val": {"a": 1}}],
        query={"_id": 1},
        update={"$max": {"val": {"a": 1, "b": 1}}},
        expected={"_id": 1, "val": {"a": 1, "b": 1}},
        msg="$max with objects: more fields > fewer fields with same prefix",
    ),
    UpdateTestCase(
        "object_field_order_matters",
        setup_docs=[{"_id": 1, "val": {"a": 1, "b": 1}}],
        query={"_id": 1},
        update={"$max": {"val": {"a": 1, "c": 1}}},
        expected={"_id": 1, "val": {"a": 1, "c": 1}},
        msg="$max with objects compared by field name order: 'c' > 'b'",
    ),
    UpdateTestCase(
        "equal_arrays_unchanged",
        setup_docs=[{"_id": 1, "val": [1, 2, 3]}],
        query={"_id": 1},
        update={"$max": {"val": [1, 2, 3]}},
        expected={"_id": 1, "val": [1, 2, 3]},
        msg="$max with identical arrays should not update",
    ),
    UpdateTestCase(
        "equal_objects_unchanged",
        setup_docs=[{"_id": 1, "val": {"a": 1, "b": 2}}],
        query={"_id": 1},
        update={"$max": {"val": {"a": 1, "b": 2}}},
        expected={"_id": 1, "val": {"a": 1, "b": 2}},
        msg="$max with identical objects should not update",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_max_bson_wiring(collection, test: UpdateTestCase):
    """Test $max BSON cross-type and complex value comparisons."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
