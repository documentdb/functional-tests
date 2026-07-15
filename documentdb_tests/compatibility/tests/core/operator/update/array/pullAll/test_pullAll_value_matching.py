"""Tests for $pullAll value matching behavior.

Covers: array element matching (order-sensitive), document matching
(field-order-sensitive), input correlation, mixed-type exact matching.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

PULLALL_VALUE_MATCHING_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "array_exact_match_removes",
        setup_docs=[{"_id": 1, "a": [[1, 2, 3], [4, 5, 6]]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [[1, 2, 3]]}},
        expected={"_id": 1, "a": [[4, 5, 6]]},
        msg="Should remove exact array matches",
    ),
    UpdateTestCase(
        "array_different_order_no_remove",
        setup_docs=[{"_id": 1, "a": [[1, 2, 3], [4, 5, 6]]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [[3, 2, 1]]}},
        expected={"_id": 1, "a": [[1, 2, 3], [4, 5, 6]]},
        msg="Should NOT remove array with different order",
    ),
    UpdateTestCase(
        "values_list_removes_individual_not_subarray",
        setup_docs=[{"_id": 1, "a": [1, 2, 3, [1, 2, 3]]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [1, 2, 3]}},
        expected={"_id": 1, "a": [[1, 2, 3]]},
        msg="Should remove individual elements, not the subarray",
    ),
    UpdateTestCase(
        "doc_exact_match_removes",
        setup_docs=[{"_id": 1, "a": [{"a": 1, "b": 2}, {"c": 3}]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [{"a": 1, "b": 2}]}},
        expected={"_id": 1, "a": [{"c": 3}]},
        msg="Should remove document with exact field order match",
    ),
    UpdateTestCase(
        "doc_different_field_order_no_remove",
        setup_docs=[{"_id": 1, "a": [{"a": 1, "b": 2}, {"c": 3}]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [{"b": 2, "a": 1}]}},
        expected={"_id": 1, "a": [{"a": 1, "b": 2}, {"c": 3}]},
        msg="Should NOT remove document with different field order (unlike $pull)",
    ),
    UpdateTestCase(
        "nested_doc_field_order_must_match",
        setup_docs=[{"_id": 1, "a": [{"x": {"a": 1, "b": 2}}]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [{"x": {"b": 2, "a": 1}}]}},
        expected={"_id": 1, "a": [{"x": {"a": 1, "b": 2}}]},
        msg="Nested document field order must match at all levels",
    ),
    UpdateTestCase(
        "nested_doc_exact_match_removes",
        setup_docs=[{"_id": 1, "a": [{"x": {"a": 1, "b": 2}}]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [{"x": {"a": 1, "b": 2}}]}},
        expected={"_id": 1, "a": []},
        msg="Should remove nested document with exact match",
    ),
    UpdateTestCase(
        "only_exact_field_order_removed",
        setup_docs=[{"_id": 1, "a": [{"a": 1, "b": 2}, {"b": 2, "a": 1}, {"a": 1, "b": 2}]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [{"a": 1, "b": 2}]}},
        expected={"_id": 1, "a": [{"b": 2, "a": 1}]},
        msg="Should only remove exact field-order matches",
    ),
    UpdateTestCase(
        "only_exact_element_order_removed",
        setup_docs=[{"_id": 1, "a": [[1, 2], [2, 1], [1, 2]]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [[1, 2]]}},
        expected={"_id": 1, "a": [[2, 1]]},
        msg="Should only remove exact element-order matches",
    ),
    UpdateTestCase(
        "array_values_mixed_types_exact_match",
        setup_docs=[{"_id": 1, "a": [[1, "two", True], [True, "two", 1]]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [[1, "two", True]]}},
        expected={"_id": 1, "a": [[True, "two", 1]]},
        msg="Should use exact match for array values with mixed types",
    ),
    UpdateTestCase(
        "partial_doc_does_not_match",
        setup_docs=[{"_id": 1, "a": [{"a": 1, "b": 2, "c": 3}, {"d": 4}]}],
        query={"_id": 1},
        update={"$pullAll": {"a": [{"a": 1, "b": 2}]}},
        expected={"_id": 1, "a": [{"a": 1, "b": 2, "c": 3}, {"d": 4}]},
        msg="Partial document should NOT match (unlike $pull which does subset matching)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PULLALL_VALUE_MATCHING_TESTS))
def test_pullAll_value_matching(collection, test: UpdateTestCase):
    """Test $pullAll value matching semantics."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
