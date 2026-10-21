"""
Behavior coverage for the $min update operator.

Oracle: MongoDB 7.0 (per functional-tests CI baseline). $min sets the
field to the smaller of the current value and the supplied value (BSON
type-aware: per the canonical type ordering, Null < Number < String <
Document < Array < Binary < ObjectId < Bool < Date < Timestamp < Regex).

Coverage walks the case matrix in the write-compat-functional-test skill,
Step 2: operator-value type matrix, field-value comparison behaviour
(greater/lesser/equal), numeric-type cross-comparison, non-numeric
comparisons (string, date), cross-BSON-type comparisons, path semantics,
composition matrix, command-path matrix.
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
from documentdb_tests.framework.property_checks import Eq, IsType, Len

pytestmark = pytest.mark.update


# ---------------------------------------------------------------------------
# Operator-value type matrix (top-level operand must be a document)
# ---------------------------------------------------------------------------


def test_min_errors_when_operand_is_null(collection):
    """Null operand to $min must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": None}}]},
    )
    assertFailureCode(result, 9, msg="Null operand to $min must fail with code 9")


def test_min_errors_when_operand_is_array(collection):
    """Array operand to $min must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": [1]}}]},
    )
    assertFailureCode(result, 9, msg="Array operand to $min must fail with code 9")


def test_min_errors_when_operand_is_string(collection):
    """String operand to $min must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": "x"}}]},
    )
    assertFailureCode(result, 9, msg="String operand to $min must fail with code 9")


def test_min_errors_when_operand_is_bool(collection):
    """Bool operand to $min must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": True}}]},
    )
    assertFailureCode(result, 9, msg="Bool operand to $min must fail with code 9")


def test_min_errors_when_operand_is_integer(collection):
    """Integer operand to $min must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": 5}}]},
    )
    assertFailureCode(result, 9, msg="Integer operand to $min must fail with code 9")


def test_min_empty_operand_is_noop(collection):
    """Empty operand `{$min: {}}` matches but does not modify (n=1, nModified=0)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {}}}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Empty $min operand must be a no-op",
    )


# ---------------------------------------------------------------------------
# Core comparison contract: smaller wins, equal is no-op, larger is no-op
# ---------------------------------------------------------------------------


def test_min_existing_greater_than_supplied_updates_value(collection):
    """When existing value > supplied value, $min replaces with supplied."""
    collection.insert_one({"_id": 1, "s": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"s": 5}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"s": Eq(5)}, msg="existing 10 > supplied 5 must replace with 5")


def test_min_existing_greater_reports_nModified_1(collection):
    """The response reports nModified=1 when $min actually replaces a value."""
    collection.insert_one({"_id": 1, "s": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"s": 5}}}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="An actual replacement must report nModified=1",
    )


def test_min_existing_less_than_supplied_is_noop_value(collection):
    """When existing value < supplied value, $min keeps the existing value."""
    collection.insert_one({"_id": 1, "s": 3})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"s": 5}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"s": Eq(3)}, msg="existing 3 < supplied 5 must keep 3")


def test_min_existing_less_than_supplied_reports_nModified_0(collection):
    """The response reports nModified=0 when $min is a no-op."""
    collection.insert_one({"_id": 1, "s": 3})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"s": 5}}}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="A no-op must report nModified=0 (matched but unchanged)",
    )


def test_min_existing_equal_to_supplied_reports_nModified_0(collection):
    """When existing == supplied, $min is a no-op (nModified=0)."""
    collection.insert_one({"_id": 1, "s": 5})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"s": 5}}}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Equal values must report nModified=0",
    )


# ---------------------------------------------------------------------------
# Numeric type comparisons (same type)
# ---------------------------------------------------------------------------


def test_min_int_vs_smaller_int_picks_smaller(collection):
    """Int32 vs smaller Int32: picks the smaller."""
    collection.insert_one({"_id": 1, "n": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": 3}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(3)}, msg="Int 10 vs Int 3 → picks 3")


def test_min_int64_vs_smaller_int64_picks_smaller(collection):
    """Int64 vs smaller Int64: picks the smaller (preserves Int64 type)."""
    collection.insert_one({"_id": 1, "n": Int64(10)})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": Int64(3)}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": IsType("long")}, msg="Int64 vs Int64 → result is Int64")


def test_min_double_vs_smaller_double_picks_smaller(collection):
    """Double vs smaller Double: picks the smaller."""
    collection.insert_one({"_id": 1, "n": 10.5})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": 3.2}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(3.2)}, msg="Double 10.5 vs Double 3.2 → picks 3.2")


def test_min_decimal128_vs_smaller_decimal128_picks_smaller(collection):
    """Decimal128 vs smaller Decimal128: picks the smaller (preserves Decimal128 type)."""
    collection.insert_one({"_id": 1, "n": Decimal128("10.5")})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": Decimal128("3.2")}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": IsType("decimal")}, msg="Decimal128 result must remain Decimal128")


# ---------------------------------------------------------------------------
# Cross-numeric-type comparisons
# ---------------------------------------------------------------------------


def test_min_int_numerically_equal_to_double_is_noop(collection):
    """Int 5 and Double 5.0 are numerically equal — no-op."""
    collection.insert_one({"_id": 1, "n": 5})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": 5.0}}}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Numerically-equal cross-type values must be a no-op",
    )


def test_min_int_vs_smaller_double_picks_double(collection):
    """Int existing vs smaller Double supplied: picks Double (replaces type)."""
    collection.insert_one({"_id": 1, "n": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": 3.5}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(3.5)}, msg="Int 10 vs Double 3.5 → picks 3.5")


# ---------------------------------------------------------------------------
# Special numeric values: NaN, Infinity
# ---------------------------------------------------------------------------


def test_min_existing_nan_keeps_nan(collection):
    """Existing NaN remains NaN — NaN is treated as the smallest numeric value."""
    collection.insert_one({"_id": 1, "n": float("nan")})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": 10}}}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Existing NaN must remain — NaN is the smallest numeric",
    )


def test_min_negative_infinity_supplied_replaces_int(collection):
    """-Infinity is smaller than any finite number; $min replaces with -Infinity."""
    collection.insert_one({"_id": 1, "n": 10})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": float("-inf")}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(float("-inf"))}, msg="-Infinity wins over Int 10")


def test_min_positive_infinity_supplied_is_noop(collection):
    """+Infinity is larger than any finite number; $min is a no-op."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": float("inf")}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="+Infinity vs existing finite int must be a no-op",
    )


# ---------------------------------------------------------------------------
# Missing-field behavior — creates with supplied value
# ---------------------------------------------------------------------------


def test_min_missing_field_creates_with_supplied_value(collection):
    """When the field is absent, $min creates it with the supplied value."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"newf": 5}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"newf": Eq(5)}, msg="Missing field must be created with supplied value")


# ---------------------------------------------------------------------------
# Non-numeric same-type comparisons (string lex, date chronological)
# ---------------------------------------------------------------------------


def test_min_string_vs_lex_smaller_string_picks_smaller(collection):
    """String values are compared lexicographically; $min picks the smaller."""
    collection.insert_one({"_id": 1, "s": "banana"})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"s": "apple"}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"s": Eq("apple")}, msg="'banana' vs 'apple' → picks 'apple' (lex)")


def test_min_string_vs_lex_greater_string_is_noop(collection):
    """When the supplied string is lex-greater, $min is a no-op."""
    collection.insert_one({"_id": 1, "s": "apple"})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"s": "banana"}}}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="'apple' < 'banana' lex; supplied is larger so no-op",
    )


def test_min_date_vs_earlier_date_picks_earlier(collection):
    """Date comparison is chronological; earlier wins."""
    collection.insert_one({"_id": 1, "d": datetime(2024, 1, 1)})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"d": datetime(2020, 1, 1)}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"d": IsType("date")}, msg="$min on Date keeps a Date result")


def test_min_date_vs_later_date_is_noop(collection):
    """When supplied date is later, $min is a no-op."""
    collection.insert_one({"_id": 1, "d": datetime(2020, 1, 1)})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"d": datetime(2024, 1, 1)}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Existing 2020 < supplied 2024 → no-op",
    )


# ---------------------------------------------------------------------------
# Cross-BSON-type comparisons (per canonical type order: Null < Number < String < ...)
# ---------------------------------------------------------------------------


def test_min_int_vs_string_keeps_int(collection):
    """BSON type order: Number < String; existing Int wins over supplied String."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": "abc"}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Int < String in BSON type order; existing Int must win",
    )


def test_min_string_vs_int_replaces_with_int(collection):
    """BSON type order: Number < String; supplied Int wins over existing String."""
    collection.insert_one({"_id": 1, "n": "abc"})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": 10}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"n": Eq(10)}, msg="Int < String in BSON order; supplied Int replaces String")


def test_min_null_vs_int_keeps_null(collection):
    """BSON type order: Null < Number; existing Null wins over supplied Int."""
    collection.insert_one({"_id": 1, "n": None})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": 10}}}]},
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Null < Number in BSON type order; existing Null must win",
    )


# ---------------------------------------------------------------------------
# Path semantics
# ---------------------------------------------------------------------------


def test_min_dotted_path_creates_intermediate_doc(collection):
    """$min on a dotted path creates the intermediate subdocument."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"a.b": 5}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"a.b": Eq(5)}, msg="Dotted path must create the intermediate subdocument")


def test_min_dotted_into_array_element_by_index(collection):
    """`a.0.n` updates the subdocument at index 0 of the array."""
    collection.insert_one({"_id": 1, "a": [{"n": 10}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"a.0.n": 3}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(result, {"a.0.n": Eq(3)}, msg="Dotted-into-array-index must update that element")


def test_min_dotted_past_array_end_pads_with_nulls(collection):
    """`a.10` on a 2-element array pads with nulls and sets the supplied value at index 10."""
    collection.insert_one({"_id": 1, "a": [10, 20]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"a.10": 5}}}]},
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"a": Len(11), "a.10": Eq(5)},
        msg="Dotted past array end must pad with nulls and set value",
    )


def test_min_errors_on_dotted_path_through_scalar(collection):
    """$min through a scalar intermediate must fail with PathNotViable (28)."""
    collection.insert_one({"_id": 1, "name": "John"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"name.x": 1}}}],
        },
    )
    assertFailureCode(result, 28, msg="$min through scalar intermediate must fail with code 28")


def test_min_errors_on_id_target(collection):
    """$min targeting _id must fail with ImmutableField (66)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"_id": 0}}}],
        },
    )
    assertFailureCode(result, 66, msg="$min against _id must fail with ImmutableField (66)")


# ---------------------------------------------------------------------------
# Composition matrix
# ---------------------------------------------------------------------------


def test_min_composes_with_set_on_different_path(collection):
    """$min and $set on different paths combine without conflict."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$min": {"n": 5}, "$set": {"x": "y"}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$min must compose with $set on a different path",
    )


def test_min_errors_on_conflicting_set_on_same_path(collection):
    """$min and $set on the same path must conflict with code 40."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$min": {"n": 5}, "$set": {"n": 99}},
                }
            ],
        },
    )
    assertFailureCode(result, 40, msg="Same-path $min + $set must conflict with code 40")


def test_min_errors_on_conflicting_max_on_same_path(collection):
    """$min and $max on the same path must conflict with code 40."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$min": {"n": 5}, "$max": {"n": 20}},
                }
            ],
        },
    )
    assertFailureCode(result, 40, msg="Same-path $min + $max must conflict with code 40")


# ---------------------------------------------------------------------------
# Command-path matrix
# ---------------------------------------------------------------------------


def test_min_multi_true_modifies_only_docs_that_change(collection):
    """multi:true reports n=matched-docs and nModified=actually-replaced."""
    collection.insert_many([{"_id": 1, "n": 10}, {"_id": 2, "n": 1}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$min": {"n": 5}}, "multi": True}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 2, "nModified": 1, "ok": 1.0},
        msg="multi:true must match both but only modify the doc whose existing > 5",
    )


def test_min_multi_true_keeps_smaller_existing_values(collection):
    """After multi:true, the doc whose existing value was smaller is unchanged."""
    collection.insert_many([{"_id": 1, "n": 10}, {"_id": 2, "n": 1}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$min": {"n": 5}}, "multi": True}],
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
            "cursor.firstBatch.0.n": Eq(5),
            "cursor.firstBatch.1.n": Eq(1),
        },
        raw_res=True,
        msg="Doc 1 (was 10) becomes 5; doc 2 (was 1) stays at 1",
    )


def test_min_upsert_creates_document_with_supplied_value(collection):
    """Upsert with $min reports n=1 / nModified=0 on the insert path."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 99},
                    "u": {"$min": {"n": 5}},
                    "upsert": True,
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Upsert with $min must report n=1 / nModified=0",
    )


def test_min_upsert_inserted_document_has_supplied_value(collection):
    """The upserted document contains the field with the supplied value."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 99},
                    "u": {"$min": {"n": 5}},
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


def test_min_via_findAndModify_returns_updated_doc(collection):
    """findAndModify applies $min and returns the updated document."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$min": {"n": 3}},
            "new": True,
        },
    )
    assertProperties(
        result,
        {
            "ok": Eq(1.0),
            "lastErrorObject.n": Eq(1),
            "lastErrorObject.updatedExisting": Eq(True),
            "value.n": Eq(3),
        },
        raw_res=True,
        msg="findAndModify with $min must return updated document with n=3",
    )


# ---------------------------------------------------------------------------
# Engine divergence
# ---------------------------------------------------------------------------


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason=(
        "$min comparison against existing finite numeric when supplied is "
        "NaN: native MongoDB treats NaN as the smallest numeric (replaces "
        "with NaN, nModified=1); documentdb treats the existing finite "
        "value as smaller (no-op, nModified=0)."
    ),
    raises=AssertionError,
)
def test_min_supplied_nan_replaces_existing_finite(collection):
    """Supplied NaN should win over existing finite numeric (NaN is smallest)."""
    collection.insert_one({"_id": 1, "n": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$min": {"n": float("nan")}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="Supplied NaN must replace existing finite (NaN < any finite number)",
    )
