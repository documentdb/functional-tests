"""Tests for $pull update operator core behavior.

Covers: exact value removal, removal by condition, empty array behavior,
multiple occurrences, argument handling, null/missing fields, and value matching.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

PULL_CORE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "remove_exact_value",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 2, 4]}],
        query={"_id": 1},
        update={"$pull": {"arr": 2}},
        expected={"_id": 1, "arr": [1, 3, 4]},
        msg="Should remove all instances of exact value from array",
    ),
    UpdateTestCase(
        "value_not_present_noop",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": 99}},
        expected={"_id": 1, "arr": [1, 2, 3]},
        msg="Should be no-op when value not present in array",
    ),
    UpdateTestCase(
        "remove_string_value",
        setup_docs=[{"_id": 1, "arr": ["a", "b", "c", "b"]}],
        query={"_id": 1},
        update={"$pull": {"arr": "b"}},
        expected={"_id": 1, "arr": ["a", "c"]},
        msg="Should remove all instances of string value",
    ),
    UpdateTestCase(
        "empty_array_noop",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$pull": {"arr": 1}},
        expected={"_id": 1, "arr": []},
        msg="Should be no-op on empty array",
    ),
    UpdateTestCase(
        "all_elements_removed_leaves_empty_array",
        setup_docs=[{"_id": 1, "arr": [3, 3, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": 3}},
        expected={"_id": 1, "arr": []},
        msg="Should leave empty array when all elements removed",
    ),
    UpdateTestCase(
        "nested_array_not_removed_by_scalar",
        setup_docs=[{"_id": 1, "arr": [1, [1, 2], 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": 1}},
        expected={"_id": 1, "arr": [[1, 2], 3]},
        msg="Should not remove nested arrays containing the scalar value",
    ),
    UpdateTestCase(
        "missing_field_noop",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$pull": {"arr": 1}},
        expected={"_id": 1, "x": 1},
        msg="Should be no-op when target field does not exist",
    ),
    UpdateTestCase(
        "empty_operand_noop_scalar_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": {}}},
        expected={"_id": 1, "arr": [1, 2, 3]},
        msg="Should be no-op with empty operand expression {} on scalar array",
    ),
    UpdateTestCase(
        "empty_operand_on_doc_array",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}, {"b": 2}, {"a": 3}]}],
        query={"_id": 1},
        update={"$pull": {"arr": {}}},
        expected={"_id": 1, "arr": []},
        msg="Empty condition {} should match all embedded docs (removes all elements)",
    ),
    UpdateTestCase(
        "multiple_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": ["x", "y", "z"]}],
        query={"_id": 1},
        update={"$pull": {"a": 2, "b": "y"}},
        expected={"_id": 1, "a": [1, 3], "b": ["x", "z"]},
        msg="Should process each field independently in multi-field $pull",
    ),
    UpdateTestCase(
        "pull_eq_null",
        setup_docs=[{"_id": 1, "arr": [1, None, 3, None]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"$eq": None}}},
        expected={"_id": 1, "arr": [1, 3]},
        msg="Should remove null elements with $eq: null condition",
    ),
    UpdateTestCase(
        "array_exact_match_removes",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4], [1, 2]]}],
        query={"_id": 1},
        update={"$pull": {"arr": [1, 2]}},
        expected={"_id": 1, "arr": [[3, 4]]},
        msg="Should remove exact array matches (order-sensitive)",
    ),
    UpdateTestCase(
        "empty_array_condition_removes_empty_arrays_only",
        setup_docs=[{"_id": 1, "arr": [1, [], 2, [], 3]}],
        query={"_id": 1},
        update={"$pull": {"arr": []}},
        expected={"_id": 1, "arr": [1, 2, 3]},
        msg="Should only remove embedded empty array elements, not all elements",
    ),
    UpdateTestCase(
        "array_different_order_no_remove",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [2, 1], [3, 4]]}],
        query={"_id": 1},
        update={"$pull": {"arr": [1, 2]}},
        expected={"_id": 1, "arr": [[2, 1], [3, 4]]},
        msg="Should NOT remove array with different element order",
    ),
    UpdateTestCase(
        "nested_array_exact_match",
        setup_docs=[{"_id": 1, "arr": [[1, [2, 3]], [4, 5]]}],
        query={"_id": 1},
        update={"$pull": {"arr": [1, [2, 3]]}},
        expected={"_id": 1, "arr": [[4, 5]]},
        msg="Should remove nested array exact matches",
    ),
    UpdateTestCase(
        "multi_element_array_only_exact",
        setup_docs=[{"_id": 1, "arr": [[1, 2, 3], [1, 2], [2, 3]]}],
        query={"_id": 1},
        update={"$pull": {"arr": [1, 2]}},
        expected={"_id": 1, "arr": [[1, 2, 3], [2, 3]]},
        msg="Should only remove exact length and order array matches",
    ),
    UpdateTestCase(
        "doc_field_order_independent",
        setup_docs=[{"_id": 1, "arr": [{"a": 1, "b": 2}, {"b": 2, "a": 1}, {"c": 3}]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"a": 1, "b": 2}}},
        expected={"_id": 1, "arr": [{"c": 3}]},
        msg="Should remove docs regardless of field order in the document",
    ),
    UpdateTestCase(
        "doc_partial_match_subset_not_removed",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}, {"a": 1, "b": 2, "c": 3}]}],
        query={"_id": 1},
        update={"$pull": {"arr": {"a": 1, "b": 2}}},
        expected={"_id": 1, "arr": [{"a": 1}]},
        msg="Should not remove docs that only have subset of condition fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PULL_CORE_TESTS))
def test_pull_core(collection, test: UpdateTestCase):
    """Test $pull operator core behavior."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


def test_pull_large_array(collection):
    """Test $pull removing many elements from large array (1000+ elements)."""
    large_arr = list(range(1000))
    collection.insert_one({"_id": 1, "arr": large_arr})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"arr": {"$gte": 500}}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "arr": list(range(500))}],
        msg="Should handle large arrays with many elements removed",
    )
