"""
Core behavior tests for $sortArray expression.

Tests sort by value (ascending/descending), sort by document field,
sort by subfield, sort by multiple fields, whole-value document sorting,
empty array, single element, duplicate values, numeric cross-type sorts,
large arrays, null input and null/missing-field handling, and edge cases
(no array traversal, stable order of field-less scalars).
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Literal-path parity]: representative cases from each group below
# also run through the literal-value path (not just via inserted documents),
# and are appended to ALL_TESTS below so they also get insert coverage.
LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="asc_ints",
        expression={"$sortArray": {"input": {"$literal": [3, 1, 2]}, "sortBy": 1}},
        expected=[1, 2, 3],
        msg="Should sort ints ascending",
    ),
    ExpressionTestCase(
        id="desc_ints",
        expression={"$sortArray": {"input": {"$literal": [3, 1, 2]}, "sortBy": -1}},
        expected=[3, 2, 1],
        msg="Should sort ints descending",
    ),
    ExpressionTestCase(
        id="sort_by_name_asc",
        expression={
            "$sortArray": {
                "input": {
                    "$literal": [
                        {"name": "peter", "age": 30},
                        {"name": "dorothy", "age": 36},
                        {"name": "chloe", "age": 42},
                    ]
                },
                "sortBy": {"name": 1},
            }
        },
        expected=[
            {"name": "chloe", "age": 42},
            {"name": "dorothy", "age": 36},
            {"name": "peter", "age": 30},
        ],
        msg="Should sort documents by name ascending",
    ),
    ExpressionTestCase(
        id="empty_array_value_sort",
        expression={"$sortArray": {"input": {"$literal": []}, "sortBy": 1}},
        expected=[],
        msg="Should return empty array for empty input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_sortArray_literal(collection, test):
    """Test $sortArray with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Value sort direction]: a plain array of scalars is sorted
# ascending or descending by value, correctly handling already-sorted,
# reverse-sorted, and negative-number inputs.
SORT_ASC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="asc_ints",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [3, 1, 2]},
        expected=[1, 2, 3],
        msg="Should sort ints ascending",
    ),
    ExpressionTestCase(
        id="asc_strings",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": ["banana", "apple", "cherry"]},
        expected=["apple", "banana", "cherry"],
        msg="Should sort strings ascending",
    ),
    ExpressionTestCase(
        id="asc_doubles",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [3.3, 1.1, 2.2]},
        expected=[1.1, 2.2, 3.3],
        msg="Should sort doubles ascending",
    ),
    ExpressionTestCase(
        id="asc_already_sorted",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="Should preserve already sorted array",
    ),
    ExpressionTestCase(
        id="asc_reverse_sorted",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [3, 2, 1]},
        expected=[1, 2, 3],
        msg="Should reverse descending array",
    ),
    ExpressionTestCase(
        id="asc_negative_numbers",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [0, -3, 2, -1]},
        expected=[-3, -1, 0, 2],
        msg="Should sort negative numbers ascending",
    ),
]

# Property [Value sort direction]: sortBy -1 sorts scalars descending, the
# mirror counterpart to SORT_ASC_TESTS above.
SORT_DESC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="desc_ints",
        expression={"$sortArray": {"input": "$arr", "sortBy": -1}},
        doc={"arr": [3, 1, 2]},
        expected=[3, 2, 1],
        msg="Should sort ints descending",
    ),
    ExpressionTestCase(
        id="desc_strings",
        expression={"$sortArray": {"input": "$arr", "sortBy": -1}},
        doc={"arr": ["banana", "apple", "cherry"]},
        expected=["cherry", "banana", "apple"],
        msg="Should sort strings descending",
    ),
    ExpressionTestCase(
        id="desc_doubles",
        expression={"$sortArray": {"input": "$arr", "sortBy": -1}},
        doc={"arr": [1.1, 3.3, 2.2]},
        expected=[3.3, 2.2, 1.1],
        msg="Should sort doubles descending",
    ),
]

# Property [Sort by field]: with a document sortBy spec, an array of
# documents is ordered by the named top-level field's value, ascending or
# descending.
SORT_BY_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sort_by_name_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"name": 1}}},
        doc={
            "arr": [
                {"name": "peter", "age": 30},
                {"name": "dorothy", "age": 36},
                {"name": "chloe", "age": 42},
            ]
        },
        expected=[
            {"name": "chloe", "age": 42},
            {"name": "dorothy", "age": 36},
            {"name": "peter", "age": 30},
        ],
        msg="Should sort documents by name ascending",
    ),
    ExpressionTestCase(
        id="sort_by_age_desc",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"age": -1}}},
        doc={
            "arr": [
                {"name": "peter", "age": 30},
                {"name": "dorothy", "age": 36},
                {"name": "chloe", "age": 42},
            ]
        },
        expected=[
            {"name": "chloe", "age": 42},
            {"name": "dorothy", "age": 36},
            {"name": "peter", "age": 30},
        ],
        msg="Should sort documents by age descending",
    ),
    ExpressionTestCase(
        id="sort_by_age_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"age": 1}}},
        doc={
            "arr": [
                {"name": "chloe", "age": 42},
                {"name": "peter", "age": 30},
                {"name": "dorothy", "age": 36},
            ]
        },
        expected=[
            {"name": "peter", "age": 30},
            {"name": "dorothy", "age": 36},
            {"name": "chloe", "age": 42},
        ],
        msg="Should sort documents by age ascending",
    ),
]

# Property [Sort by dotted subfield]: the sortBy field name may be a dotted
# path into a nested subdocument, not just a top-level field.
SORT_BY_SUBFIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sort_by_subfield_desc",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"address.city": -1}}},
        doc={
            "arr": [
                {"name": "peter", "address": {"city": "Long Beach"}},
                {"name": "dorothy", "address": {"city": "Portland"}},
                {"name": "chloe", "address": {"city": "New York"}},
            ]
        },
        expected=[
            {"name": "dorothy", "address": {"city": "Portland"}},
            {"name": "chloe", "address": {"city": "New York"}},
            {"name": "peter", "address": {"city": "Long Beach"}},
        ],
        msg="Should sort by subfield descending",
    ),
    ExpressionTestCase(
        id="sort_by_subfield_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"address.city": 1}}},
        doc={
            "arr": [
                {"name": "peter", "address": {"city": "Long Beach"}},
                {"name": "dorothy", "address": {"city": "Portland"}},
                {"name": "chloe", "address": {"city": "New York"}},
            ]
        },
        expected=[
            {"name": "peter", "address": {"city": "Long Beach"}},
            {"name": "chloe", "address": {"city": "New York"}},
            {"name": "dorothy", "address": {"city": "Portland"}},
        ],
        msg="Should sort by subfield ascending",
    ),
]

# Property [Compound sortBy]: multiple fields in the sortBy document are
# applied in declared order, with later fields acting as tiebreakers for
# equal values in earlier fields.
SORT_MULTIPLE_FIELDS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="compound_age_desc_name_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"age": -1, "name": 1}}},
        doc={
            "arr": [
                {"name": "peter", "age": 30},
                {"name": "dorothy", "age": 36},
                {"name": "chloe", "age": 42},
            ]
        },
        expected=[
            {"name": "chloe", "age": 42},
            {"name": "dorothy", "age": 36},
            {"name": "peter", "age": 30},
        ],
        msg="Should sort by age desc then name asc",
    ),
    ExpressionTestCase(
        id="compound_tiebreaker",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"score": -1, "name": 1}}},
        doc={
            "arr": [
                {"name": "bob", "score": 90},
                {"name": "alice", "score": 90},
                {"name": "chloe", "score": 80},
            ]
        },
        expected=[
            {"name": "alice", "score": 90},
            {"name": "bob", "score": 90},
            {"name": "chloe", "score": 80},
        ],
        msg="Should use second field as tiebreaker",
    ),
]

# Property [Degenerate lengths]: empty and single-element arrays are handled
# correctly under both a scalar (whole-value) and a field-document sortBy.
DEGENERATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="empty_array_value_sort",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": []},
        expected=[],
        msg="Should return empty array for empty input",
    ),
    ExpressionTestCase(
        id="empty_array_field_sort",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 1}}},
        doc={"arr": []},
        expected=[],
        msg="Should return empty array for empty input with field sort",
    ),
    ExpressionTestCase(
        id="single_element_value",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [42]},
        expected=[42],
        msg="Should return single element unchanged",
    ),
    ExpressionTestCase(
        id="single_element_doc",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 1}}},
        doc={"arr": [{"a": 1}]},
        expected=[{"a": 1}],
        msg="Should return single document unchanged",
    ),
]

# Property [Duplicate handling]: sorting groups equal/duplicate values
# together and preserves every occurrence, rather than deduplicating.
DUPLICATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="all_same_values",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [5, 5, 5]},
        expected=[5, 5, 5],
        msg="Should handle all identical values",
    ),
    ExpressionTestCase(
        id="duplicates_mixed",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [1, 4, 1, 6, 12, 5]},
        expected=[1, 1, 4, 5, 6, 12],
        msg="Should group duplicates together",
    ),
]

# Property [Numeric cross-type ordering]: numbers of different BSON numeric
# types (int, Int64, Decimal128) compare and interleave by numeric value,
# not by their BSON type tag.
NUMERIC_CROSS_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int_and_double",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [3, 1.5, 2]},
        expected=[1.5, 2, 3],
        msg="Should sort ints and doubles together",
    ),
    ExpressionTestCase(
        id="int_and_int64",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [3, Int64(1), 2]},
        expected=[Int64(1), 2, 3],
        msg="Should sort ints and int64 together",
    ),
    ExpressionTestCase(
        id="int_and_decimal128",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [3, Decimal128("1.5"), 2]},
        expected=[Decimal128("1.5"), 2, 3],
        msg="Should sort ints and decimal128 together",
    ),
]

_LARGE = list(range(1000, 0, -1))

# Property [Scales to large arrays]: sort correctness holds for an array large
# enough (1000 elements) to rule out small-input-only implementations, in
# both directions.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="large_array_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": _LARGE},
        expected=list(range(1, 1001)),
        msg="Should sort large array ascending",
    ),
    ExpressionTestCase(
        id="large_array_desc",
        expression={"$sortArray": {"input": "$arr", "sortBy": -1}},
        doc={"arr": list(range(1, 1001))},
        expected=_LARGE,
        msg="Should sort large array descending",
    ),
]

# Property [Null propagation and null-element ordering]: a null input returns
# null (rather than an error), and null elements/fields sort as their own
# BSON type — first ascending, last descending — with null and a genuinely
# missing field treated equally.
NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="null_input_value_sort",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": None},
        expected=None,
        msg="Should return null for null input with value sort",
    ),
    ExpressionTestCase(
        id="null_input_field_sort",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 1}}},
        doc={"arr": None},
        expected=None,
        msg="Should return null for null input with field sort",
    ),
    ExpressionTestCase(
        id="null_elements_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [3, None, 1, None, 2]},
        expected=[None, None, 1, 2, 3],
        msg="Null elements should sort before numbers",
    ),
    ExpressionTestCase(
        id="null_elements_desc",
        expression={"$sortArray": {"input": "$arr", "sortBy": -1}},
        doc={"arr": [3, None, 1, None, 2]},
        expected=[3, 2, 1, None, None],
        msg="Null elements should sort last descending",
    ),
    ExpressionTestCase(
        id="null_field_in_docs",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 1}}},
        doc={"arr": [{"a": 3}, {"a": None}, {"a": 1}]},
        expected=[{"a": None}, {"a": 1}, {"a": 3}],
        msg="Null field sorts first",
    ),
    ExpressionTestCase(
        id="null_and_missing_sort_equally",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 1}}},
        doc={"arr": [{"a": 2}, {"a": None}, {"b": 1}, {"a": 1}]},
        expected=[{"a": None}, {"b": 1}, {"a": 1}, {"a": 2}],
        msg="Null and missing sort equally",
    ),
]

# Property [Comparison edge cases]: array-valued sort fields are compared as
# whole values (not traversed/flattened), sorting is stable and preserves all
# duplicate elements, scalars without the sort field keep their relative
# order, and `$`-prefixed field names in sortBy resolve normally.
EDGE_CASE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="no_array_traversal",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 1}}},
        doc={"arr": [{"a": [3, 1]}, {"a": [2]}]},
        expected=[{"a": [2]}, {"a": [3, 1]}],
        msg="Should compare arrays, not traverse into them",
    ),
    ExpressionTestCase(
        id="preserves_all_elements",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [3, 1, 2, 1, 3]},
        expected=[1, 1, 2, 3, 3],
        msg="Should preserve all elements including duplicates",
    ),
    ExpressionTestCase(
        id="scalars_doc_sort",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"x": 1}}},
        doc={"arr": [1, "a", None]},
        expected=[1, "a", None],
        msg="Scalars without sort field maintain order",
    ),
    ExpressionTestCase(
        id="dollar_prefixed_sortby",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"$a": 1}}},
        doc={"arr": [{"$a": 2}, {"$a": 1}]},
        expected=[{"$a": 1}, {"$a": 2}],
        msg="Should sort by $ prefixed field",
    ),
]

# Property [Whole-value document sort] (JS S1): with a scalar `sortBy`, an
# array of documents is ordered by whole-value BSON comparison (field-by-field:
# field name, then value; a shorter prefix document sorts before a longer one).
WHOLE_VALUE_DOC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="whole_value_docs_asc",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [{"a": 2}, {"a": 1}, {"a": 3}]},
        expected=[{"a": 1}, {"a": 2}, {"a": 3}],
        msg="Whole-value sort of documents (ascending)",
    ),
    ExpressionTestCase(
        id="whole_value_docs_desc",
        expression={"$sortArray": {"input": "$arr", "sortBy": -1}},
        doc={"arr": [{"a": 2}, {"a": 1}, {"a": 3}]},
        expected=[{"a": 3}, {"a": 2}, {"a": 1}],
        msg="Whole-value sort of documents (descending)",
    ),
    ExpressionTestCase(
        id="whole_value_docs_mismatched_keys",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": [{"b": 1}, {"a": 1}, {"a": 1, "b": 1}, {"a": 2}]},
        expected=[{"a": 1}, {"a": 1, "b": 1}, {"a": 2}, {"b": 1}],
        msg="Whole-value sort orders documents with mismatched keys by BSON key/value",
    ),
]

ALL_TESTS = (
    SORT_ASC_TESTS
    + SORT_DESC_TESTS
    + SORT_BY_FIELD_TESTS
    + SORT_BY_SUBFIELD_TESTS
    + SORT_MULTIPLE_FIELDS_TESTS
    + WHOLE_VALUE_DOC_TESTS
    + DEGENERATE_TESTS
    + DUPLICATE_TESTS
    + NUMERIC_CROSS_TYPE_TESTS
    + LARGE_ARRAY_TESTS
    + NULL_TESTS
    + EDGE_CASE_TESTS
    + LITERAL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_sortArray_insert(collection, test):
    """Test $sortArray with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
