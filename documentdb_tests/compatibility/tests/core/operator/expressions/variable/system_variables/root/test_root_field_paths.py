"""
Field path resolution tests for the $$ROOT aggregation system variable.

Covers $$ROOT.<path> lookups and projections: nested/array paths, missing
vs null, and the namespace distinction between $$ROOT and a field named ROOT.

Multi-document pipeline field path cases live in test_root_pipeline_contexts.py.
The representative $project/$addFields/$cond and nested-path ($$ROOT.a.b) wiring
lives in ../test_system-variables_root_expression_engine.py (shared expression
engine); this file keeps the thorough $$ROOT-specific field-path matrix.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Path Resolution]: $$ROOT.<path> resolves dotted paths against the
# current root document, mapping over arrays rather than indexing into them (collecting
# only matched elements), omitting missing paths while preserving explicit nulls, and
# keeping the $$ROOT variable namespace separate from a field literally named ROOT.
FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="simple_field",
        expression={"result": "$$ROOT.a"},
        doc={"_id": 1, "a": 10},
        expected=[{"result": 10}],
        msg="$$ROOT.<field> should resolve a top-level field",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"result": "$$ROOT.a.b.c.d"},
        doc={"_id": 1, "a": {"b": {"c": {"d": "leaf"}}}},
        expected=[{"result": "leaf"}],
        msg="$$ROOT should resolve a deeply nested scalar",
    ),
    ExpressionTestCase(
        id="array_field",
        expression={"result": "$$ROOT.arr"},
        doc={"_id": 1, "arr": [1, 2, 3]},
        expected=[{"result": [1, 2, 3]}],
        msg="$$ROOT.<arrayField> should return the array intact",
    ),
    ExpressionTestCase(
        id="empty_object_field",
        expression={"result": "$$ROOT.emptyObj"},
        doc={"_id": 1, "emptyObj": {}},
        expected=[{"result": {}}],
        msg="$$ROOT.<emptyObjectField> should return an empty object",
    ),
    ExpressionTestCase(
        id="empty_array_field",
        expression={"result": "$$ROOT.emptyArr"},
        doc={"_id": 1, "emptyArr": []},
        expected=[{"result": []}],
        msg="$$ROOT.<emptyArrayField> should return an empty array",
    ),
    ExpressionTestCase(
        id="numeric_string_key",
        expression={"result": "$$ROOT.obj.0"},
        doc={"_id": 1, "obj": {"0": "zeroKey"}},
        expected=[{"result": "zeroKey"}],
        msg="$$ROOT should resolve an object key that is a numeric string",
    ),
    ExpressionTestCase(
        id="numeric_index_on_array",
        expression={"result": "$$ROOT.arr.0"},
        doc={"_id": 1, "arr": [10, 20, 30]},
        expected=[{"result": []}],
        msg="Numeric path on an array resolves to an empty array in expression context",
    ),
    ExpressionTestCase(
        id="array_index_path_on_array_of_objects",
        expression={"result": "$$ROOT.a.0.b"},
        doc={"_id": 1, "a": [{"b": 1}, {"b": 2}]},
        expected=[{"result": []}],
        msg="$$ROOT.<a>.0.<b> on an array of objects resolves to an empty array",
    ),
    ExpressionTestCase(
        id="array_index_path_on_object_key",
        expression={"result": "$$ROOT.a.0.b"},
        doc={"_id": 1, "a": {"0": {"b": 5}}},
        expected=[{"result": 5}],
        msg="$$ROOT.<a>.0.<b> resolves the literal key '0' on an object",
    ),
    ExpressionTestCase(
        id="composite_array_path",
        expression={"result": "$$ROOT.a.b"},
        doc={"_id": 1, "a": [{"b": 1}, {"b": 2}]},
        expected=[{"result": [1, 2]}],
        msg="Composite path over an array of objects should collect each element's value",
    ),
    ExpressionTestCase(
        id="composite_array_path_skips_unmatched_elements",
        expression={"result": "$$ROOT.a.b"},
        doc={"_id": 1, "a": [{"b": 1}, {"c": 2}]},
        expected=[{"result": [1]}],
        msg="Composite path should skip array elements lacking the field, not pad with null",
    ),
    ExpressionTestCase(
        id="deep_composite_array_path",
        expression={"result": "$$ROOT.a.b.c.d"},
        doc={"_id": 1, "a": {"b": [{"c": [{"d": 1}]}]}},
        expected=[{"result": [[1]]}],
        msg="Deep traversal through arrays of objects should preserve nesting depth",
    ),
    ExpressionTestCase(
        id="null_field_distinct_from_missing_field",
        expression={"fromNull": "$$ROOT.nullField", "fromMissing": "$$ROOT.absent"},
        doc={"_id": 1, "nullField": None},
        expected=[{"fromNull": None}],
        msg="null should be projected while missing should be omitted",
    ),
    ExpressionTestCase(
        id="nested_path_through_missing_parent_is_omitted",
        expression={"v": "$$ROOT.x.y"},
        doc={"_id": 1, "a": 1},
        expected=[{}],
        msg="$$ROOT path through a missing parent should resolve to missing",
    ),
    ExpressionTestCase(
        id="nested_path_through_null_parent_is_omitted",
        expression={"v": "$$ROOT.nullField.x"},
        doc={"_id": 1, "nullField": None},
        expected=[{}],
        msg="$$ROOT path continuing through a null value should resolve to missing, not null",
    ),
    ExpressionTestCase(
        id="multiple_field_accesses_in_one_projection",
        expression={"first": "$$ROOT.a", "second": "$$ROOT.b.c", "third": "$$ROOT.d"},
        doc={"_id": 1, "a": 1, "b": {"c": 2}, "d": [3, 4]},
        expected=[{"first": 1, "second": 2, "third": [3, 4]}],
        msg="Each $$ROOT reference in a projection should resolve independently",
    ),
    ExpressionTestCase(
        id="bare_field_path_named_root_is_distinct",
        expression={"viaFieldPath": "$ROOT", "viaVariable": "$$ROOT"},
        doc={"_id": 1, "ROOT": "fieldValue"},
        expected=[{"viaFieldPath": "fieldValue", "viaVariable": {"_id": 1, "ROOT": "fieldValue"}}],
        msg="$ROOT should read the ROOT field while $$ROOT resolves to the whole document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_PATH_TESTS))
def test_root_field_path(collection, test):
    """$$ROOT field paths and projections resolve against the current root document."""
    result = execute_project_with_insert(collection, test.doc, test.expression)
    assertSuccess(result, test.expected, msg=test.msg)
