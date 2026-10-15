"""
Behavior coverage for the $currentDate update operator.

Oracle: MongoDB 7.0 (per functional-tests CI baseline). Each test asserts on
either (a) the structural update-command response (n / nModified / ok) or
(b) field presence / BSON type via assertProperties on a follow-up find —
never on the time value itself, which is server-injected and volatile.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, Len

pytestmark = pytest.mark.update


# ---------------------------------------------------------------------------
# Type-specification behavior
# ---------------------------------------------------------------------------


def test_currentDate_true_returns_match_counts(collection):
    """`true` shorthand reports n=1 / nModified=1 / ok=1.0."""
    collection.insert_one({"_id": 1, "name": "test"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"lastModified": True}}}
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$currentDate with true must report n=1 / nModified=1",
    )


def test_currentDate_true_sets_date_typed_field(collection):
    """`true` injects a BSON Date into the named field."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"lastModified": True}}}
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"lastModified": IsType("date")},
        msg="lastModified must be a BSON Date after $currentDate with true",
    )


def test_currentDate_explicit_type_date_returns_match_counts(collection):
    """`{$type: 'date'}` long-form reports n=1 / nModified=1 / ok=1.0."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"lastModified": {"$type": "date"}}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$currentDate with {$type:'date'} must report n=1 / nModified=1",
    )


def test_currentDate_type_timestamp_returns_match_counts(collection):
    """`{$type: 'timestamp'}` reports n=1 / nModified=1 / ok=1.0."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"ts": {"$type": "timestamp"}}},
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$currentDate with {$type:'timestamp'} must report n=1 / nModified=1",
    )


def test_currentDate_type_timestamp_sets_field(collection):
    """`{$type: 'timestamp'}` creates the named field on the document."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"ts": {"$type": "timestamp"}}},
                }
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"ts": Exists()},
        msg="ts must be present after $currentDate with {$type:'timestamp'}",
    )


def test_currentDate_multiple_fields_returns_match_counts(collection):
    """One $currentDate stage with multiple fields reports n=1 / nModified=1."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$currentDate": {
                            "a": True,
                            "b": {"$type": "timestamp"},
                        }
                    },
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$currentDate must succeed when setting multiple fields in one operator",
    )


def test_currentDate_multiple_fields_sets_date_typed_field(collection):
    """The 'true'-typed field in a multi-field stage is a BSON Date."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$currentDate": {
                            "a": True,
                            "b": {"$type": "timestamp"},
                        }
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"a": IsType("date"), "b": Exists()},
        msg="Mixed-type $currentDate must inject Date for a and any value for b",
    )


# ---------------------------------------------------------------------------
# Path / structural behavior
# ---------------------------------------------------------------------------


def test_currentDate_creates_missing_field(collection):
    """$currentDate auto-creates the target field when it does not exist."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"newField": True}}}
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="Missing field must be auto-created",
    )


def test_currentDate_dotted_path_creates_intermediate_subdoc(collection):
    """Dotted path creates the intermediate subdocument and the leaf field."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"meta.lastModified": True}},
                }
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"meta.lastModified": IsType("date")},
        msg="Dotted path must create the intermediate subdocument with a Date leaf",
    )


def test_currentDate_overwrites_scalar_field_with_date(collection):
    """$currentDate replaces a string scalar — the new value is a Date."""
    collection.insert_one({"_id": 1, "field": "scalar string"})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"field": True}}}
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"field": IsType("date")},
        msg="String scalar must be replaced with a Date value",
    )


def test_currentDate_overwrites_existing_date_returns_match_counts(collection):
    """$currentDate on an existing Date reports n=1 / nModified=1."""
    collection.insert_one({"_id": 1, "ts": datetime(2020, 1, 1)})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"ts": True}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$currentDate must overwrite an existing Date value",
    )


def test_currentDate_multi_true_returns_n_3_nModified_3(collection):
    """multi:true reports n=3 / nModified=3 when matching all three documents."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {}, "u": {"$currentDate": {"ts": True}}, "multi": True}
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 3, "nModified": 3, "ok": 1.0},
        msg="multi:true must update every matching document",
    )


def test_currentDate_multi_true_sets_field_on_all_documents(collection):
    """After multi:true, every matched document has the field present."""
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {}, "u": {"$currentDate": {"ts": True}}, "multi": True}
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {
            "cursor.firstBatch": Len(3),
            "cursor.firstBatch.0.ts": IsType("date"),
            "cursor.firstBatch.1.ts": IsType("date"),
            "cursor.firstBatch.2.ts": IsType("date"),
        },
        raw_res=True,
        msg="multi:true must inject a Date into every matched document",
    )


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


def test_currentDate_upsert_returns_n_1_nModified_0(collection):
    """Upsert with $currentDate reports n=1 / nModified=0 on the insert path."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 99},
                    "u": {"$currentDate": {"ts": True}},
                    "upsert": True,
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Upsert must report n=1 / nModified=0 on the insert path",
    )


def test_currentDate_upsert_creates_document_with_date_field(collection):
    """The upserted document contains the new field as a Date."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 99},
                    "u": {"$currentDate": {"ts": True}},
                    "upsert": True,
                }
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 99}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"ts": IsType("date")},
        msg="Upserted document must contain a Date in ts",
    )


# ---------------------------------------------------------------------------
# No-op edge case
# ---------------------------------------------------------------------------


def test_currentDate_empty_operand_is_noop(collection):
    """`{$currentDate: {}}` matches the document but modifies nothing."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Empty $currentDate operand must be a no-op (matched, not modified)",
    )


# ---------------------------------------------------------------------------
# Shared-error cases (both engines must fail with the same code)
# ---------------------------------------------------------------------------


def test_currentDate_errors_on_invalid_type_string(collection):
    """`{$type: 'string'}` (not 'date'/'timestamp') must fail with BadValue (2)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"ts": {"$type": "string"}}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$currentDate $type other than 'date'/'timestamp' must fail with code 2",
    )


def test_currentDate_errors_on_type_with_wrong_case(collection):
    """`{$type: 'Date'}` (capital D) must fail — type strings are case-sensitive."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"ts": {"$type": "Date"}}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$currentDate $type is case-sensitive; 'Date' must fail with code 2",
    )


def test_currentDate_errors_on_integer_value(collection):
    """Integer values are not allowed — must fail with BadValue (2)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"ts": 42}}}],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$currentDate integer value must fail with code 2",
    )


def test_currentDate_errors_on_string_value(collection):
    """String values are not allowed — must fail with BadValue (2)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"ts": "now"}}}
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$currentDate string value must fail with code 2",
    )


def test_currentDate_errors_on_type_value_as_number(collection):
    """`{$type: 1}` (non-string) must fail with BadValue (2)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"ts": {"$type": 1}}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$currentDate $type non-string value must fail with code 2",
    )


def test_currentDate_errors_on_empty_type_spec(collection):
    """`{}` (empty type spec — missing required $type) must fail with code 2."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"ts": {}}}}
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$currentDate with empty type spec must fail with code 2",
    )


def test_currentDate_errors_on_unknown_modifier_in_spec(collection):
    """Any modifier other than $type in the spec must fail with code 2."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"ts": {"$weird": "x"}}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$currentDate unknown modifier in spec must fail with code 2",
    )


def test_currentDate_errors_on_conflicting_set_on_same_path(collection):
    """$currentDate and $set on the same path must conflict (code 40)."""
    collection.insert_one({"_id": 1, "ts": "x"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"ts": True}, "$set": {"ts": "y"}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        40,
        msg="Same-path $currentDate + $set must conflict with code 40",
    )


def test_currentDate_errors_on_dotted_path_through_scalar(collection):
    """$currentDate on a dotted path through a scalar must fail with PathNotViable (28)."""
    collection.insert_one({"_id": 1, "name": "John"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"name.first": True}}}
            ],
        },
    )
    assertFailureCode(
        result,
        28,
        msg="$currentDate through a scalar intermediate must fail with code 28",
    )


def test_currentDate_errors_on_id_target(collection):
    """$currentDate targeting _id must fail with ImmutableField (66)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"_id": True}}}
            ],
        },
    )
    assertFailureCode(
        result,
        66,
        msg="$currentDate against _id must fail with ImmutableField (66)",
    )


# ---------------------------------------------------------------------------
# Engine divergence
# ---------------------------------------------------------------------------


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason=(
        "$currentDate spec with an extra field alongside $type: native "
        "MongoDB rejects with code 2 ('Unrecognized $currentDate option: "
        "<name>'); documentdb silently accepts the extra field and applies "
        "the operator."
    ),
    raises=AssertionError,
)
def test_currentDate_errors_on_extra_field_in_type_spec(collection):
    """Any field alongside $type in the spec must fail with code 2."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$currentDate": {
                            "ts": {"$type": "date", "extra": 1}
                        }
                    },
                }
            ],
        },
    )
    assertFailureCode(
        result,
        2,
        msg="$currentDate $type spec with extra field must fail with code 2",
    )


# ---------------------------------------------------------------------------
# Operator-value type matrix (the $currentDate value must be a document)
# Every non-document operand must fail with FailedToParse (9).
# ---------------------------------------------------------------------------


def test_currentDate_errors_when_operand_is_null(collection):
    """`{$currentDate: null}` must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": None}}],
        },
    )
    assertFailureCode(
        result,
        9,
        msg="Null operand to $currentDate must fail with FailedToParse (9)",
    )


def test_currentDate_errors_when_operand_is_array(collection):
    """`{$currentDate: [...]}` must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": [1, 2]}}],
        },
    )
    assertFailureCode(
        result,
        9,
        msg="Array operand to $currentDate must fail with FailedToParse (9)",
    )


def test_currentDate_errors_when_operand_is_string(collection):
    """`{$currentDate: 'now'}` must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": "now"}}],
        },
    )
    assertFailureCode(
        result,
        9,
        msg="String operand to $currentDate must fail with FailedToParse (9)",
    )


def test_currentDate_errors_when_operand_is_bool(collection):
    """`{$currentDate: true}` (top-level bool) must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": True}}],
        },
    )
    assertFailureCode(
        result,
        9,
        msg="Bool operand to $currentDate must fail with FailedToParse (9)",
    )


def test_currentDate_errors_when_operand_is_integer(collection):
    """`{$currentDate: 42}` must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": 42}}],
        },
    )
    assertFailureCode(
        result,
        9,
        msg="Integer operand to $currentDate must fail with FailedToParse (9)",
    )


# ---------------------------------------------------------------------------
# Composition with other update operators
# ---------------------------------------------------------------------------


def test_currentDate_composes_with_set_on_different_path(collection):
    """$currentDate and $set on different paths combine without conflict."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$currentDate": {"ts": True},
                        "$set": {"x": 1},
                    },
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$currentDate must compose with $set on a different path",
    )


def test_currentDate_composes_with_inc_on_different_path(collection):
    """$currentDate and $inc on different paths combine without conflict."""
    collection.insert_one({"_id": 1, "n": 0})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$currentDate": {"ts": True},
                        "$inc": {"n": 1},
                    },
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="$currentDate must compose with $inc on a different path",
    )


def test_currentDate_errors_on_conflicting_unset_on_same_path(collection):
    """$currentDate and $unset on the same path must conflict (code 40)."""
    collection.insert_one({"_id": 1, "ts": "x"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$currentDate": {"ts": True},
                        "$unset": {"ts": ""},
                    },
                }
            ],
        },
    )
    assertFailureCode(
        result,
        40,
        msg="Same-path $currentDate + $unset must conflict with code 40",
    )


# ---------------------------------------------------------------------------
# Surprising-but-shared field-value behavior
# ---------------------------------------------------------------------------


def test_currentDate_field_value_false_also_sets_date(collection):
    """Both engines treat `false` field value the same as `true` — sets a Date."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"ts": False}}}
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg="Boolean false at the field-value level is accepted; pins shared engine behavior",
    )


# ---------------------------------------------------------------------------
# Path semantics: dotted into / past array
# ---------------------------------------------------------------------------


def test_currentDate_dotted_into_array_element_by_index_sets_field(collection):
    """`tags.0.ts` updates the subdocument at index 0 of the array."""
    collection.insert_one({"_id": 1, "tags": [{"a": 1}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"tags.0.ts": True}}}
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"tags.0.ts": IsType("date")},
        msg="Dotted path through array index must add a Date to that element",
    )


def test_currentDate_dotted_past_array_end_pads_with_nulls(collection):
    """`tags.10` on a 2-element array pads with nulls and sets the Date at index 10."""
    collection.insert_one({"_id": 1, "tags": [10, 20]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"tags.10": True}}}
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {
            "tags": Len(11),
            "tags.0": Exists(),
            "tags.1": Exists(),
            "tags.10": IsType("date"),
        },
        msg="Dotted path past end of array must pad with nulls and set the Date",
    )


# ---------------------------------------------------------------------------
# Overwrite matrix: replacing every existing BSON type with a Date
# ---------------------------------------------------------------------------


def test_currentDate_overwrites_array_field_with_date(collection):
    """$currentDate replaces a whole array field with a Date scalar."""
    collection.insert_one({"_id": 1, "field": [1, 2, 3]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"field": True}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"field": IsType("date")},
        msg="An array field must be replaced with a Date by $currentDate",
    )


def test_currentDate_overwrites_subdocument_field_with_date(collection):
    """$currentDate replaces a whole subdocument field with a Date scalar."""
    collection.insert_one({"_id": 1, "field": {"a": 1}})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"field": True}}}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}},
    )
    assertProperties(
        result,
        {"field": IsType("date")},
        msg="A subdocument field must be replaced with a Date by $currentDate",
    )


# ---------------------------------------------------------------------------
# Command-path coverage: findAndModify
# ---------------------------------------------------------------------------


def test_currentDate_via_findAndModify_returns_updated_doc(collection):
    """`findAndModify` applies $currentDate and returns the updated document."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$currentDate": {"ts": True}},
            "new": True,
        },
    )
    assertProperties(
        result,
        {
            "ok": Eq(1.0),
            "lastErrorObject.n": Eq(1),
            "lastErrorObject.updatedExisting": Eq(True),
            "value._id": Eq(1),
            "value.ts": IsType("date"),
        },
        raw_res=True,
        msg="findAndModify with $currentDate must return the updated document",
    )
