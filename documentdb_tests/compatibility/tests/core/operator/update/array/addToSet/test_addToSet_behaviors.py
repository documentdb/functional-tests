"""
Behavior coverage for the $addToSet update operator.

Oracle: MongoDB 7.0. Each test asserts the structural response shape
(n / nModified / ok / writeErrors[].code) so the test stays deterministic
and engine-agnostic. Server-injected fields (modified array contents, upsert
ids that we control via `q`) are read back through a follow-up find when
necessary.
"""

import pytest
from bson import Decimal128

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
    engine="documentdb",
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
