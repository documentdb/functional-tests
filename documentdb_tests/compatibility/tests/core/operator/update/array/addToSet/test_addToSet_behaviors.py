"""
Behavior coverage for the $addToSet update operator.

Oracle: MongoDB 7.0. Each test asserts the structural response shape
(n / nModified / ok / writeErrors[].code) so the test stays deterministic
and engine-agnostic. Server-injected fields (modified array contents, upsert
ids that we control via `q`) are read back through a follow-up find when
necessary.
"""

import pytest
from bson import Binary, Decimal128, ObjectId
from datetime import datetime, timezone

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.update


# ---------------------------------------------------------------------------
# Dedup semantics
# ---------------------------------------------------------------------------


def test_addToSet_no_op_when_value_already_in_array(collection):
    """$addToSet of an existing value reports nModified=0 (set semantics)."""
    collection.insert_one({"_id": 1, "tags": ["A", "B"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"tags": "A"}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Re-adding existing value must be a no-op",
    )


def test_addToSet_creates_array_on_missing_field(collection):
    """$addToSet on a missing field creates a new single-element array."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"tags": "A"}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="Missing field is created as a new array",
    )


def test_addToSet_value_that_is_array_added_as_single_element(collection):
    """An array value (without $each) is added as a single element, not flattened."""
    collection.insert_one({"_id": 1, "tags": ["A"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$addToSet": {"tags": ["B", "C"]}}}
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="Array argument (no $each) is one element, not flattened",
    )


def test_addToSet_dotted_path_adds_to_nested_array(collection):
    """$addToSet works on a dotted path into a nested document."""
    collection.insert_one({"_id": 1, "profile": {"tags": ["A"]}})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$addToSet": {"profile.tags": "B"}}}
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="Dotted-path target must modify the nested array",
    )


def test_addToSet_dedups_subdocuments_by_deep_equality(collection):
    """Adding an equal subdocument is a no-op."""
    collection.insert_one({"_id": 1, "items": [{"k": 1, "v": "a"}]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"items": {"k": 1, "v": "a"}}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Equal subdocument must not be re-added",
    )


def test_addToSet_treats_reordered_subdocument_keys_as_distinct(collection):
    """{k:1,v:'a'} and {v:'a',k:1} are different documents — both kept."""
    collection.insert_one({"_id": 1, "items": [{"k": 1, "v": "a"}]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"items": {"v": "a", "k": 1}}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="Field ordering must matter for subdocument equality",
    )


def test_addToSet_dedups_int_and_double_numerically_equal(collection):
    """Int(1) and Double(1.0) are equal — second add is a no-op."""
    collection.insert_one({"_id": 1, "n": [1]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"n": 1.0}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Int 1 and Double 1.0 must dedup",
    )


def test_addToSet_dedups_decimal128_independent_of_trailing_zeros(collection):
    """Decimal128('1.0') and Decimal128('1.00') compare equal — no-op."""
    collection.insert_one({"_id": 1, "n": [Decimal128("1.0")]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$addToSet": {"n": Decimal128("1.00")}}}
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Decimal128 dedup must ignore trailing-zero representation",
    )


def test_addToSet_dedups_null_value(collection):
    """Adding null when null already present is a no-op."""
    collection.insert_one({"_id": 1, "vals": [None]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"vals": None}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Null is a value that dedups against itself",
    )


# ---------------------------------------------------------------------------
# $each modifier
# ---------------------------------------------------------------------------


def test_addToSet_each_adds_only_new_values(collection):
    """$each with mix of new and existing values adds only the new ones."""
    collection.insert_one({"_id": 1, "tags": ["A"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": {"$each": ["B", "C", "A"]}}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$each must add new values and skip duplicates",
    )


def test_addToSet_each_empty_array_is_noop(collection):
    """$each with an empty array must be a no-op (nModified=0)."""
    collection.insert_one({"_id": 1, "tags": ["A"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$addToSet": {"tags": {"$each": []}}}}
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="$each: [] must not modify the document",
    )


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_addToSet_errors_on_non_array_field(collection):
    """$addToSet onto a scalar field returns code 2 (BadValue)."""
    collection.insert_one({"_id": 1, "tags": "scalar"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"tags": "X"}}}],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$addToSet against non-array field must fail with BadValue (2)",
    )


def test_addToSet_errors_on_non_array_each_argument(collection):
    """$each argument must be an array — string argument returns code 14 (TypeMismatch)."""
    collection.insert_one({"_id": 1, "tags": ["A"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": {"$each": "B"}}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        14,
        msg="$each with non-array value must fail with TypeMismatch (14)",
    )


def test_addToSet_errors_on_conflicting_set_on_same_path(collection):
    """$addToSet and $set on the same path conflict — code 40."""
    collection.insert_one({"_id": 1, "tags": ["A"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": "B"}, "$set": {"tags": ["X"]}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        40,
        msg="Same-path $addToSet + $set must conflict (code 40)",
    )


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason=(
        "documentdb silently accepts unknown modifiers (e.g. $slice) "
        "alongside $each in $addToSet; native MongoDB rejects with code 2."
    ),
    raises=AssertionError,
)
def test_addToSet_each_with_unknown_modifier_errors(collection):
    """$each combined with an unknown modifier ($slice) must fail with code 2."""
    collection.insert_one({"_id": 1, "tags": ["A"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$addToSet": {
                            "tags": {"$each": ["B"], "$slice": 2},
                        }
                    },
                }
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$each + unknown modifier in $addToSet must fail with code 2",
    )


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


def test_addToSet_upsert_reports_inserted_via_response(collection):
    """Upsert with $addToSet reports n=1 and nModified=0 on the insert path."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 99},
                    "u": {"$addToSet": {"tags": "A"}},
                    "upsert": True,
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Upsert reports n=1 and nModified=0 on insert path",
    )


def test_addToSet_upsert_creates_array_field(collection):
    """Upserted document contains the new array populated with the value."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 99},
                    "u": {"$addToSet": {"tags": "A"}},
                    "upsert": True,
                }
            ],
        },
    )
    docs = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 99}, "sort": {"_id": 1}},
    )
    assertSuccess(
        docs,
        [{"_id": 99, "tags": ["A"]}],
        msg="Upserted document must contain the new array",
    )


# ---------------------------------------------------------------------------
# $each extra dedup semantics
# ---------------------------------------------------------------------------


def test_addToSet_each_collapses_internal_duplicates(collection):
    """Duplicates inside the $each argument are deduped against each other and the field."""
    collection.insert_one({"_id": 1, "tags": ["A"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": {"$each": ["B", "B", "A", "C", "C"]}}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$each must dedup internally and against existing values",
    )


def test_addToSet_each_all_existing_values_is_noop(collection):
    """$each containing only values already present must report nModified=0."""
    collection.insert_one({"_id": 1, "tags": ["A", "B"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": {"$each": ["A", "B"]}}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="$each with only existing values must not modify the document",
    )


# ---------------------------------------------------------------------------
# Empty / first-element / special-value semantics
# ---------------------------------------------------------------------------


def test_addToSet_to_empty_array_adds_first_element(collection):
    """$addToSet against an empty array reports nModified=1 with one new element."""
    collection.insert_one({"_id": 1, "tags": []})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"tags": "X"}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="Empty array must accept the first element",
    )


def test_addToSet_NaN_dedups_against_NaN(collection):
    """NaN compares equal to NaN under $addToSet set semantics (no-op)."""
    collection.insert_one({"_id": 1, "n": [float("nan")]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"n": float("nan")}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="NaN must dedup against NaN inside $addToSet",
    )


def test_addToSet_positive_and_negative_infinity_distinct(collection):
    """+Infinity and -Infinity are different set elements."""
    collection.insert_one({"_id": 1, "n": [float("inf")]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"n": float("-inf")}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="+Infinity and -Infinity must be treated as distinct values",
    )


def test_addToSet_nested_array_dedups_by_value(collection):
    """An array-as-element is deduped against an equal array-as-element."""
    collection.insert_one({"_id": 1, "arrs": [[1, 2]]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"arrs": [1, 2]}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Nested-array element must dedup by value",
    )


def test_addToSet_objectid_dedups_by_value(collection):
    """Equal ObjectIds compare equal — second add is a no-op."""
    oid = ObjectId("64b5e4f0a1b2c3d4e5f60001")
    collection.insert_one({"_id": 1, "oids": [oid]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"oids": oid}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Equal ObjectId must dedup",
    )


def test_addToSet_date_dedups_by_value(collection):
    """Equal Date values compare equal — second add is a no-op."""
    d = datetime(2024, 1, 1, tzinfo=timezone.utc)
    collection.insert_one({"_id": 1, "ds": [d]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"ds": d}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Equal Date must dedup",
    )


def test_addToSet_binary_dedups_by_value(collection):
    """Equal Binary values (same subtype + payload) dedup."""
    b = Binary(b"hello", 0)
    collection.insert_one({"_id": 1, "bs": [b]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"bs": b}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Equal Binary must dedup",
    )


# ---------------------------------------------------------------------------
# Multi-document update
# ---------------------------------------------------------------------------


def test_addToSet_multi_true_modifies_only_docs_that_change(collection):
    """multi:true reports n equal to matched docs and nModified only for changed."""
    collection.insert_many(
        [{"_id": 1, "tags": ["A"]}, {"_id": 2, "tags": ["A", "B"]}]
    )
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$addToSet": {"tags": "B"}}, "multi": True}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 2, "nModified": 1, "ok": 1.0},
        msg="multi:true must match both but only modify the doc that gained an element",
    )


# ---------------------------------------------------------------------------
# Shared-error cases (must fail with the same code on native and on documentdb)
# ---------------------------------------------------------------------------


def test_addToSet_errors_on_scalar_number_field(collection):
    """$addToSet onto a numeric scalar must fail with BadValue (2)."""
    collection.insert_one({"_id": 1, "n": 5})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"n": 7}}}],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$addToSet against a numeric scalar must fail with BadValue (2)",
    )


def test_addToSet_errors_on_scalar_date_field(collection):
    """$addToSet onto a Date scalar must fail with BadValue (2)."""
    collection.insert_one(
        {"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}
    )
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"d": "x"}}}],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$addToSet against a Date scalar must fail with BadValue (2)",
    )


def test_addToSet_errors_on_null_field(collection):
    """$addToSet onto a field whose value is BSON null must fail with BadValue (2)."""
    collection.insert_one({"_id": 1, "tags": None})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"tags": "X"}}}],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$addToSet against a null-valued field must fail with BadValue (2)",
    )


def test_addToSet_errors_on_dotted_path_through_scalar(collection):
    """$addToSet on a dotted path whose intermediate is a scalar must fail with PathNotViable (28)."""
    collection.insert_one({"_id": 1, "name": "John"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$addToSet": {"name.first": "X"}}}
            ],
        },
    )
    assertFailureCode(
        result,
        28,
        msg="$addToSet through a scalar intermediate must fail with PathNotViable (28)",
    )


def test_addToSet_errors_on_id_target_as_non_array(collection):
    """$addToSet targeting the _id field (a non-array scalar) must fail with BadValue (2)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"_id": 99}}}],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$addToSet against _id (a non-array scalar) must fail with BadValue (2)",
    )


def test_addToSet_errors_on_conflicting_subpath(collection):
    """$addToSet on `tags` and `tags.0` in the same update must conflict (40)."""
    collection.insert_one({"_id": 1, "tags": ["A", "B"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"tags": "C", "tags.0": "Z"}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        40,
        msg="Updates on tags and tags.0 in the same operator must conflict (40)",
    )


# ---------------------------------------------------------------------------
# Engine divergences ($push modifiers leaking into $addToSet)
# ---------------------------------------------------------------------------


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason=(
        "$position is a $push modifier; native MongoDB rejects it in $addToSet "
        "with code 2 ('Found unexpected fields after $each'). documentdb "
        "silently ignores the modifier and succeeds."
    ),
    raises=AssertionError,
)
def test_addToSet_each_with_position_modifier_errors(collection):
    """$each combined with $position must fail with BadValue (2)."""
    collection.insert_one({"_id": 1, "tags": ["A"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$addToSet": {
                            "tags": {"$each": ["B"], "$position": 0},
                        }
                    },
                }
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$each + $position in $addToSet must fail with BadValue (2)",
    )


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason=(
        "$sort is a $push modifier; native MongoDB rejects it in $addToSet "
        "with code 2 ('Found unexpected fields after $each'). documentdb "
        "silently ignores the modifier and succeeds."
    ),
    raises=AssertionError,
)
def test_addToSet_each_with_sort_modifier_errors(collection):
    """$each combined with $sort must fail with BadValue (2)."""
    collection.insert_one({"_id": 1, "tags": ["A"]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$addToSet": {
                            "tags": {"$each": ["B"], "$sort": 1},
                        }
                    },
                }
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$each + $sort in $addToSet must fail with BadValue (2)",
    )
