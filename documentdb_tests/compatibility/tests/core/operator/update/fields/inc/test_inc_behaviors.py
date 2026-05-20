"""
Behavior coverage for the $inc update operator.

Oracle: MongoDB 7.0 (per functional-tests CI baseline). The operator
mutates a numeric field by adding an increment; tests assert on (a) the
structural update-command response (n / nModified / ok), (b) the
post-update document state via assertProperties (value + BSON type), or
(c) the documented error code via assertFailureCode.

Coverage walks the case matrix in the write-compat-functional-test skill,
Step 2:
- Operator-value type matrix (top-level operand must be a document).
- Field-value type matrix (numeric accepted, non-numeric rejected).
- Existing-field type-overwrite matrix (non-numeric existing field rejected).
- Boundary values (0, negative, NaN, Infinity, Int32.MAX→Int64 promotion,
  Int64.MAX overflow error).
- Path semantics (top-level, dotted, dotted-into-array-by-index,
  dotted-past-array-end, dotted-through-scalar, _id target).
- Composition matrix (compose on different paths; conflict on same path).
- Command-path matrix (update, findAndModify, multi:true, upsert:true).
"""

from datetime import datetime

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, Len

pytestmark = pytest.mark.update


# ---------------------------------------------------------------------------
# Operator-value type matrix (top-level operand must be a document)
# Every non-document operand must fail with FailedToParse (9).
# ---------------------------------------------------------------------------


def test_inc_errors_when_operand_is_null(collection):
    """Inc errors when operand is null."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": None}}]},
    )
    assertFailureCode(result, 9, msg="Null operand to $inc must fail with code 9")


def test_inc_errors_when_operand_is_array(collection):
    """Inc errors when operand is array."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": [1, 2]}}]},
    )
    assertFailureCode(result, 9, msg="Array operand to $inc must fail with code 9")


def test_inc_errors_when_operand_is_string(collection):
    """Inc errors when operand is string."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": "5"}}]},
    )
    assertFailureCode(result, 9, msg="String operand to $inc must fail with code 9")


def test_inc_errors_when_operand_is_bool(collection):
    """Inc errors when operand is bool."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": True}}]},
    )
    assertFailureCode(result, 9, msg="Bool operand to $inc must fail with code 9")


def test_inc_errors_when_operand_is_integer(collection):
    """Inc errors when operand is integer."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": 42}}]},
    )
    assertFailureCode(result, 9, msg="Integer operand to $inc must fail with code 9")


def test_inc_empty_operand_is_noop(collection):
    """Empty operand `{$inc: {}}` matches but does not modify (n=1, nModified=0)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {}}}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Empty $inc operand must be a no-op",
    )


# ---------------------------------------------------------------------------
# Field-value type matrix — numeric (accepted)
# ---------------------------------------------------------------------------


def test_inc_with_int32_value_returns_match_counts(collection):
    """Inc with int32 value returns match counts."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 5}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 1, "ok": 1.0})


def test_inc_with_int32_value_adds_correctly(collection):
    """Inc with int32 value adds correctly."""
    collection.insert_one({"_id": 1, "n": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 5}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(15)}, msg="10 + 5 must equal 15")


def test_inc_with_int64_value_adds_correctly(collection):
    """Inc with int64 value adds correctly."""
    collection.insert_one({"_id": 1, "n": Int64(10)})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": Int64(5)}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": IsType("long")}, msg="Int64 + Int64 must remain Int64")


def test_inc_with_double_value_adds_correctly(collection):
    """Inc with double value adds correctly."""
    collection.insert_one({"_id": 1, "n": 10.0})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 5.5}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(15.5)}, msg="10.0 + 5.5 must equal 15.5")


def test_inc_with_decimal128_value_adds_correctly(collection):
    """Inc with decimal128 value adds correctly."""
    collection.insert_one({"_id": 1, "n": Decimal128("10")})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": Decimal128("5.5")}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": IsType("decimal")}, msg="Decimal128 sum must remain Decimal128")


# ---------------------------------------------------------------------------
# Cross-numeric-type arithmetic — type promotion
# ---------------------------------------------------------------------------


def test_inc_int_plus_double_promotes_to_double(collection):
    """Inc int plus double promotes to double."""
    collection.insert_one({"_id": 1, "n": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 1.5}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": IsType("double")}, msg="Int + Double must promote to Double")


def test_inc_int_plus_decimal128_promotes_to_decimal128(collection):
    """Inc int plus decimal128 promotes to decimal128."""
    collection.insert_one({"_id": 1, "n": 10})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": Decimal128("1.5")}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": IsType("decimal")}, msg="Int + Decimal128 must promote to Decimal128")


def test_inc_double_plus_int_stays_double(collection):
    """Inc double plus int stays double."""
    collection.insert_one({"_id": 1, "n": 10.5})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 1}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": IsType("double")}, msg="Double + Int must remain Double")


# ---------------------------------------------------------------------------
# Field-value type matrix — non-numeric (must error, code 14)
# ---------------------------------------------------------------------------


def test_inc_errors_when_value_is_string(collection):
    """Inc errors when value is string."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": "x"}}}],
        },
    )
    assertFailureCode(result, 14, msg="String value to $inc must fail with TypeMismatch (14)")


def test_inc_errors_when_value_is_bool(collection):
    """Inc errors when value is bool."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": True}}}],
        },
    )
    assertFailureCode(result, 14, msg="Bool value to $inc must fail with TypeMismatch (14)")


def test_inc_errors_when_value_is_date(collection):
    """Inc errors when value is date."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$inc": {"n": datetime(2024, 1, 1)}}}
            ],
        },
    )
    assertFailureCode(result, 14, msg="Date value to $inc must fail with TypeMismatch (14)")


def test_inc_errors_when_value_is_array(collection):
    """Inc errors when value is array."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": [1, 2]}}}],
        },
    )
    assertFailureCode(result, 14, msg="Array value to $inc must fail with TypeMismatch (14)")


def test_inc_errors_when_value_is_document(collection):
    """Inc errors when value is document."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": {"a": 1}}}}],
        },
    )
    assertFailureCode(result, 14, msg="Document value to $inc must fail with TypeMismatch (14)")


def test_inc_errors_when_value_is_null(collection):
    """Inc errors when value is null."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": None}}}],
        },
    )
    assertFailureCode(result, 14, msg="Null value to $inc must fail with TypeMismatch (14)")


# ---------------------------------------------------------------------------
# Existing-field type-overwrite matrix — non-numeric field rejected (code 14)
# ---------------------------------------------------------------------------


def test_inc_errors_when_existing_field_is_string(collection):
    """Inc errors when existing field is string."""
    collection.insert_one({"_id": 1, "n": "hi"})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 1}}}]},
    )
    assertFailureCode(result, 14, msg="$inc against string field must fail with code 14")


@pytest.mark.engine_xfail(
    engine="documentdb",
    reason=(
        "$inc against a bool-typed field: native MongoDB rejects with code 14 "
        "('non-numeric type bool'); documentdb coerces the bool to 0/1 and "
        "applies the increment, producing an Int32 result."
    ),
    raises=AssertionError,
)
def test_inc_errors_when_existing_field_is_bool(collection):
    """Inc errors when existing field is bool."""
    collection.insert_one({"_id": 1, "n": True})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 1}}}]},
    )
    assertFailureCode(result, 14, msg="$inc against bool field must fail with code 14")


def test_inc_errors_when_existing_field_is_date(collection):
    """Inc errors when existing field is date."""
    collection.insert_one({"_id": 1, "n": datetime(2024, 1, 1)})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 1}}}]},
    )
    assertFailureCode(result, 14, msg="$inc against Date field must fail with code 14")


def test_inc_errors_when_existing_field_is_array(collection):
    """Inc errors when existing field is array."""
    collection.insert_one({"_id": 1, "n": [1, 2]})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 1}}}]},
    )
    assertFailureCode(result, 14, msg="$inc against array field must fail with code 14")


def test_inc_errors_when_existing_field_is_document(collection):
    """Inc errors when existing field is document."""
    collection.insert_one({"_id": 1, "n": {"a": 1}})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 1}}}]},
    )
    assertFailureCode(result, 14, msg="$inc against document field must fail with code 14")


def test_inc_errors_when_existing_field_is_null(collection):
    """Inc errors when existing field is null."""
    collection.insert_one({"_id": 1, "n": None})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 1}}}]},
    )
    assertFailureCode(result, 14, msg="$inc against null field must fail with code 14")


# ---------------------------------------------------------------------------
# Boundary values
# ---------------------------------------------------------------------------


def test_inc_by_negative_subtracts(collection):
    """Inc by negative subtracts."""
    collection.insert_one({"_id": 1, "n": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": -3}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(7)}, msg="$inc by -3 must subtract")


def test_inc_by_nan_yields_nan(collection):
    """Adding NaN to a numeric field yields NaN (per IEEE-754)."""
    collection.insert_one({"_id": 1, "n": 10.0})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": float("nan")}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": IsType("double")}, msg="NaN result must remain a Double-typed field")


def test_inc_by_positive_infinity_yields_infinity(collection):
    """Inc by positive infinity yields infinity."""
    collection.insert_one({"_id": 1, "n": 10.0})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$inc": {"n": float("inf")}}}
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(float("inf"))}, msg="$inc by +Inf must yield +Inf")


def test_inc_int32_max_overflow_promotes_to_int64(collection):
    """Incrementing Int32.MAX by 1 promotes the field to Int64 (no error)."""
    collection.insert_one({"_id": 1, "n": 2147483647})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 1}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": IsType("long")}, msg="Int32 overflow must promote to Int64")


def test_inc_int64_max_overflow_errors(collection):
    """Incrementing Int64.MAX by 1 cannot be represented; must fail with code 2."""
    collection.insert_one({"_id": 1, "n": Int64(9223372036854775807)})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": Int64(1)}}}],
        },
    )
    assertFailureCode(
        result, 2, msg="Int64 overflow on $inc must fail with code 2"
    )


# ---------------------------------------------------------------------------
# Implicit creation
# ---------------------------------------------------------------------------


def test_inc_creates_missing_field_with_value(collection):
    """$inc on a missing field creates the field with the increment as its value."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"newf": 5}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"newf": Eq(5)}, msg="Missing field must be created with the increment as value")


def test_inc_creates_missing_intermediate_documents(collection):
    """$inc on a deeply nested missing path creates the intermediate documents."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"a.b.c": 5}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"a.b.c": Eq(5)}, msg="Nested missing path must auto-create")


# ---------------------------------------------------------------------------
# Path semantics
# ---------------------------------------------------------------------------


def test_inc_dotted_into_array_element_by_index(collection):
    """`a.0.n` targets the field within the array element at index 0."""
    collection.insert_one({"_id": 1, "a": [{"n": 10}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"a.0.n": 5}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"a.0.n": Eq(15)}, msg="Dotted path through array index must increment that element")


def test_inc_dotted_past_array_end_pads_with_nulls(collection):
    """`a.10` on a 2-element array pads with nulls and sets the increment at index 10."""
    collection.insert_one({"_id": 1, "a": [10, 20]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"a.10": 5}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"a": Len(11), "a.10": Eq(5)},
        msg="Dotted path past end of array must pad with nulls and set the increment",
    )


def test_inc_errors_on_dotted_path_through_scalar(collection):
    """$inc on a dotted path whose intermediate is a scalar must fail with PathNotViable (28)."""
    collection.insert_one({"_id": 1, "name": "John"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"name.x": 1}}}],
        },
    )
    assertFailureCode(result, 28, msg="$inc through scalar intermediate must fail with PathNotViable (28)")


def test_inc_errors_on_id_target(collection):
    """$inc against _id must fail with ImmutableField (66)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"_id": 1}}}],
        },
    )
    assertFailureCode(result, 66, msg="$inc against _id must fail with ImmutableField (66)")


# ---------------------------------------------------------------------------
# Composition matrix
# ---------------------------------------------------------------------------


def test_inc_composes_with_set_on_different_path(collection):
    """$inc and $set on different paths combine cleanly."""
    collection.insert_one({"_id": 1, "n": 0})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$inc": {"n": 1}, "$set": {"x": "y"}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$inc must compose with $set on a different path",
    )


def test_inc_errors_on_conflicting_set_on_same_path(collection):
    """$inc and $set on the same path must conflict (code 40)."""
    collection.insert_one({"_id": 1, "n": 0})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$inc": {"n": 1}, "$set": {"n": 5}},
                }
            ],
        },
    )
    assertFailureCode(result, 40, msg="Same-path $inc + $set must conflict with code 40")


def test_inc_errors_on_conflicting_mul_on_same_path(collection):
    """$inc and $mul on the same path must conflict (code 40)."""
    collection.insert_one({"_id": 1, "n": 0})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$inc": {"n": 1}, "$mul": {"n": 2}},
                }
            ],
        },
    )
    assertFailureCode(result, 40, msg="Same-path $inc + $mul must conflict with code 40")


# ---------------------------------------------------------------------------
# Command-path matrix: multi, upsert, findAndModify
# ---------------------------------------------------------------------------


def test_inc_multi_true_returns_n_2_nModified_2(collection):
    """Inc multi true returns n 2 nmodified 2."""
    collection.insert_many([{"_id": 1, "n": 0}, {"_id": 2, "n": 0}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$inc": {"n": 1}}, "multi": True}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 2, "nModified": 2, "ok": 1.0},
        msg="multi:true must increment every matching document",
    )


def test_inc_multi_true_increments_all_documents(collection):
    """Inc multi true increments all documents."""
    collection.insert_many([{"_id": 1, "n": 0}, {"_id": 2, "n": 0}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$inc": {"n": 1}}, "multi": True}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {
            "cursor.firstBatch": Len(2),
            "cursor.firstBatch.0.n": Eq(1),
            "cursor.firstBatch.1.n": Eq(1),
        },
        raw_res=True,
        msg="multi:true must set every matched n to 1",
    )


def test_inc_upsert_creates_document_with_increment(collection):
    """Inc upsert creates document with increment."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 99},
                    "u": {"$inc": {"n": 5}},
                    "upsert": True,
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Upsert with $inc must report n=1 / nModified=0",
    )


def test_inc_upsert_inserted_document_has_field_set(collection):
    """Inc upsert inserted document has field set."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 99},
                    "u": {"$inc": {"n": 5}},
                    "upsert": True,
                }
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 99}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(5)}, msg="Upserted document must contain n=5")


def test_inc_via_findAndModify_returns_updated_doc(collection):
    """`findAndModify` applies $inc and returns the updated document."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$inc": {"n": 5}},
            "new": True,
        },
    )
    assertProperties(
        result,
        {
            "ok": Eq(1.0),
            "lastErrorObject.n": Eq(1),
            "lastErrorObject.updatedExisting": Eq(True),
            "value.n": Eq(15),
        },
        raw_res=True,
        msg="findAndModify with $inc must return updated document with n=15",
    )


# ---------------------------------------------------------------------------
# Engine divergence
# ---------------------------------------------------------------------------


@pytest.mark.engine_xfail(
    engine="documentdb",
    reason=(
        "$inc by 0 against an existing numeric field: native MongoDB reports "
        "n=1 / nModified=0 (recognises the no-op); documentdb reports "
        "nModified=1 even though the document value is unchanged."
    ),
    raises=AssertionError,
)
def test_inc_by_zero_reports_nModified_0_as_noop(collection):
    """$inc by 0 leaves the value unchanged and reports nModified=0."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"n": 0}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="$inc by 0 must be reported as a no-op (nModified=0)",
    )
