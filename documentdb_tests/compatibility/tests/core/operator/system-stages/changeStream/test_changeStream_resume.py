"""Tests for $changeStream resume-token repositioning behavior.

Each behavior is written as a standalone, self-contained test. Each test
captures the token it needs inline, opens the resumed stream inline, and asserts
inline, so the precondition, action, and expectation are all visible in one
place.
"""

from __future__ import annotations

import pytest
from bson import Binary
from utils.changeStream_common import change_stream_command, get_more_command

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    CHANGE_STREAM_FATAL_ERROR,
    CHANGE_STREAM_HISTORY_LOST_ERROR,
    INVALID_RESUME_TOKEN_ERROR,
    OVERFLOW_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len

pytestmark = [pytest.mark.replica_set, pytest.mark.aggregate]


# Token capture helpers. A resume token must be captured from a real stream
# before it can be used, so each helper opens a stream, optionally seeds events,
# and returns a token from the response.


def _open_stream(collection, spec=None):
    """Open a $changeStream and return the open response."""
    return execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": spec or {}}]),
    )


def _drain(collection, opened):
    """Return the next batch of events from an already-open stream."""
    result = execute_command(collection, get_more_command(collection, opened["cursor"]["id"]))
    return result["cursor"]["nextBatch"]


def _first_event_token(collection, seed, spec=None):
    """Open a stream, seed events, and return the first event's resume token."""
    opened = _open_stream(collection, spec)
    seed(collection)
    return _drain(collection, opened)[0]["_id"]


def _event_token_of_type(collection, operation_type, seed, spec=None):
    """Open a stream, seed events, and return the token of the first matching event."""
    opened = _open_stream(collection, spec)
    seed(collection)
    batch = _drain(collection, opened)
    return next(e["_id"] for e in batch if e["operationType"] == operation_type)


def _high_water_mark(collection):
    """Return the postBatchResumeToken of a freshly opened, idle stream."""
    return _open_stream(collection)["cursor"]["postBatchResumeToken"]


def _evicted_token(collection):
    """Return a token whose captured cluster time predates the oplog window.

    Rewrites the cluster-time seconds (four bytes after the version byte) of a
    high-water-mark token's _data hex to a near-zero value.
    """
    data = _high_water_mark(collection)["_data"]
    return {"_data": data[:2] + "00000001" + data[10:]}


# Property [Resume After Event]: resumeAfter an event token delivers the events that follow it.
def test_resume_after_event_token(collection):
    """Test $changeStream resumeAfter from an event token."""
    token = _first_event_token(
        collection, lambda c: c.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    )

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"resumeAfter": token}}]),
    )

    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(2)},
            "cursor.firstBatch.0.documentKey._id": Eq(2),
            "cursor.firstBatch.1.documentKey._id": Eq(3),
        },
        msg="$changeStream resumeAfter should resume after the captured event token",
        raw_res=True,
    )


# Property [Start After Event]: startAfter an event token delivers the events that follow it.
def test_start_after_event_token(collection):
    """Test $changeStream startAfter from an event token."""
    token = _first_event_token(
        collection, lambda c: c.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    )

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"startAfter": token}}]),
    )

    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(2)},
            "cursor.firstBatch.0.documentKey._id": Eq(2),
            "cursor.firstBatch.1.documentKey._id": Eq(3),
        },
        msg="$changeStream startAfter should resume after the captured event token",
        raw_res=True,
    )


# Property [Resume After Drop]: resumeAfter a drop token positions the stream at the invalidate.
def test_resume_after_drop_token(collection):
    """Test $changeStream resumeAfter from a drop-event token."""

    def seed(c):
        c.insert_one({"_id": 1})
        c.drop()

    token = _event_token_of_type(collection, "drop", seed)

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"resumeAfter": token}}]),
    )

    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(1)},
            "cursor.firstBatch.0.operationType": Eq("invalidate"),
        },
        msg="$changeStream resumeAfter should accept a drop-event token, positioned at invalidate",
        raw_res=True,
    )


# Property [Start After Drop]: startAfter a drop token positions the stream at the invalidate.
def test_start_after_drop_token(collection):
    """Test $changeStream startAfter from a drop-event token."""

    def seed(c):
        c.insert_one({"_id": 1})
        c.drop()

    token = _event_token_of_type(collection, "drop", seed)

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"startAfter": token}}]),
    )

    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(1)},
            "cursor.firstBatch.0.operationType": Eq("invalidate"),
        },
        msg="$changeStream startAfter should accept a drop-event token, positioned at invalidate",
        raw_res=True,
    )


# Property [Resume Regular Under Expanded]: a regular-event token resumes under showExpandedEvents.
def test_resume_regular_token_under_show_expanded_events(collection):
    """Test $changeStream resuming a regular-event token under showExpandedEvents true."""
    token = _first_event_token(
        collection, lambda c: c.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
    )

    result = execute_command(
        collection,
        change_stream_command(
            collection,
            pipeline=[{"$changeStream": {"resumeAfter": token, "showExpandedEvents": True}}],
        ),
    )

    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(2)},
            "cursor.firstBatch.0.documentKey._id": Eq(2),
            "cursor.firstBatch.1.documentKey._id": Eq(3),
        },
        msg="$changeStream should resume a regular-event token under showExpandedEvents true",
        raw_res=True,
    )


# Property [Resume After Evicted]: resumeAfter an evicted token fails as history lost.
def test_resume_after_evicted_token(collection):
    """Test $changeStream resumeAfter from an evicted token."""
    token = _evicted_token(collection)

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"resumeAfter": token}}]),
    )

    assertResult(
        result,
        error_code=CHANGE_STREAM_HISTORY_LOST_ERROR,
        msg="$changeStream resumeAfter should reject an evicted token as history lost",
        raw_res=True,
    )


# Property [Start After Evicted]: startAfter an evicted token fails as history lost.
def test_start_after_evicted_token(collection):
    """Test $changeStream startAfter from an evicted token."""
    token = _evicted_token(collection)

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"startAfter": token}}]),
    )

    assertResult(
        result,
        error_code=CHANGE_STREAM_HISTORY_LOST_ERROR,
        msg="$changeStream startAfter should reject an evicted token as history lost",
        raw_res=True,
    )


# Property [Resume After Invalidate]: resumeAfter an invalidate token is rejected.
def test_resume_after_invalidate_token(collection):
    """Test $changeStream resumeAfter from an invalidate-event token."""

    def seed(c):
        c.insert_one({"_id": 1})
        c.drop()

    token = _event_token_of_type(collection, "invalidate", seed)

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"resumeAfter": token}}]),
    )

    assertResult(
        result,
        error_code=INVALID_RESUME_TOKEN_ERROR,
        msg="$changeStream resumeAfter should reject an invalidate-event token",
        raw_res=True,
    )


# Property [Resume After Two-Byte Truncated]: resumeAfter a two-byte-truncated token fails.
def test_resume_after_two_byte_truncated_token(collection):
    """Test $changeStream resumeAfter from a two-byte-truncated token."""
    token = dict(_first_event_token(collection, lambda c: c.insert_one({"_id": 1})))
    # One byte is tolerated; two bytes leave the KeyString unable to decode.
    token["_data"] = token["_data"][:-4]

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"resumeAfter": token}}]),
    )

    assertResult(
        result,
        error_code=OVERFLOW_ERROR,
        msg="$changeStream resumeAfter should reject a two-byte-truncated token as overflow",
        raw_res=True,
    )


# Property [Start After Two-Byte Truncated]: startAfter a two-byte-truncated token fails.
def test_start_after_two_byte_truncated_token(collection):
    """Test $changeStream startAfter from a two-byte-truncated token."""
    token = dict(_first_event_token(collection, lambda c: c.insert_one({"_id": 1})))
    token["_data"] = token["_data"][:-4]

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"startAfter": token}}]),
    )

    assertResult(
        result,
        error_code=OVERFLOW_ERROR,
        msg="$changeStream startAfter should reject a two-byte-truncated token as overflow",
        raw_res=True,
    )


# Property [Start After Invalidate Advances]: startAfter an invalidate delivers later events.
def test_start_after_resumes_after_invalidate(collection):
    """Test $changeStream startAfter past an invalidate event."""

    def seed(c):
        c.insert_one({"_id": 1})
        c.drop()

    token = _event_token_of_type(collection, "invalidate", seed)

    opened = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"startAfter": token}}]),
    )
    collection.insert_one({"_id": 2})
    result = execute_command(collection, get_more_command(collection, opened["cursor"]["id"]))

    assertResult(
        result,
        expected={
            "cursor": {"nextBatch": Len(1)},
            "cursor.nextBatch.0.operationType": Eq("insert"),
            "cursor.nextBatch.0.documentKey._id": Eq(2),
        },
        msg="$changeStream startAfter should deliver events after an invalidate",
        raw_res=True,
    )


# Property [Expanded-Only Token Fails Advance]: an expanded-only token fails to advance unexpanded.
def test_expanded_only_token_fails_on_advance(collection):
    """Test $changeStream resumeAfter from an expanded-only event token without expansion."""

    def seed(c):
        c.insert_one({"_id": 0})
        execute_command(c, {"createIndexes": c.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]})

    token = _event_token_of_type(
        collection, "createIndexes", seed, spec={"showExpandedEvents": True}
    )

    opened = execute_command(
        collection,
        change_stream_command(
            collection,
            pipeline=[{"$changeStream": {"resumeAfter": token, "showExpandedEvents": False}}],
        ),
    )
    collection.insert_one({"_id": 1})
    result = execute_command(collection, get_more_command(collection, opened["cursor"]["id"]))

    assertResult(
        result,
        error_code=CHANGE_STREAM_FATAL_ERROR,
        msg="$changeStream should fail to advance past an expanded-only token without expansion",
        raw_res=True,
    )


# Property [Resume After Foreign Token]: resumeAfter a foreign-collection token fails to advance.
def test_resume_after_foreign_collection_token(collection, database_client):
    """Test $changeStream resumeAfter from a foreign-collection token."""
    other = database_client[f"{collection.name}_other"]
    database_client.create_collection(other.name)
    token = _first_event_token(other, lambda c: c.insert_one({"_id": 1}))

    opened = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"resumeAfter": token}}]),
    )
    collection.insert_one({"_id": 99})
    result = execute_command(collection, get_more_command(collection, opened["cursor"]["id"]))

    assertResult(
        result,
        error_code=CHANGE_STREAM_FATAL_ERROR,
        msg="$changeStream resumeAfter should fail to advance past a foreign-collection token",
        raw_res=True,
    )


# Property [Start After Foreign Token]: startAfter a foreign-collection token fails to advance.
def test_start_after_foreign_collection_token(collection, database_client):
    """Test $changeStream startAfter from a foreign-collection token."""
    other = database_client[f"{collection.name}_other"]
    database_client.create_collection(other.name)
    token = _first_event_token(other, lambda c: c.insert_one({"_id": 1}))

    opened = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"startAfter": token}}]),
    )
    collection.insert_one({"_id": 99})
    result = execute_command(collection, get_more_command(collection, opened["cursor"]["id"]))

    assertResult(
        result,
        error_code=CHANGE_STREAM_FATAL_ERROR,
        msg="$changeStream startAfter should fail to advance past a foreign-collection token",
        raw_res=True,
    )


def _resume_after_mutated(collection, mutate):
    """Capture a first-event token, apply ``mutate``, and resume from it.

    The tolerance tests mutate the token in ways that do not change its
    interpreted position, so each resume should behave identically to resuming
    from the unmutated token.
    """
    token = dict(
        _first_event_token(
            collection, lambda c: c.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])
        )
    )
    mutated = mutate(token)
    return execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {"resumeAfter": mutated}}]),
    )


# Property [Tolerance Lowercase Hex]: a lower-cased _data hex resumes identically.
def test_tolerance_lowercase_hex(collection):
    """Test $changeStream resumeAfter from a lower-cased _data token."""
    result = _resume_after_mutated(collection, lambda t: {**t, "_data": t["_data"].lower()})
    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(2)},
            "cursor.firstBatch.0.documentKey._id": Eq(2),
            "cursor.firstBatch.1.documentKey._id": Eq(3),
        },
        msg="$changeStream resumeAfter should resume identically when the token is lower-cased hex",
        raw_res=True,
    )


# Property [Tolerance Truncate One Byte]: a one-byte-truncated _data resumes identically.
def test_tolerance_truncate_one_byte(collection):
    """Test $changeStream resumeAfter from a one-byte-truncated token."""
    result = _resume_after_mutated(collection, lambda t: {**t, "_data": t["_data"][:-2]})
    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(2)},
            "cursor.firstBatch.0.documentKey._id": Eq(2),
            "cursor.firstBatch.1.documentKey._id": Eq(3),
        },
        msg="$changeStream resumeAfter should resume identically when the token is truncated by"
        " one byte",
        raw_res=True,
    )


# Property [Tolerance Append FF]: a _data extended with an FF byte resumes identically.
def test_tolerance_append_ff_byte(collection):
    """Test $changeStream resumeAfter from a token extended with an FF byte."""
    result = _resume_after_mutated(collection, lambda t: {**t, "_data": t["_data"] + "FF"})
    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(2)},
            "cursor.firstBatch.0.documentKey._id": Eq(2),
            "cursor.firstBatch.1.documentKey._id": Eq(3),
        },
        msg="$changeStream resumeAfter should resume identically when the token is extended with an"
        " FF byte",
        raw_res=True,
    )


# Property [Tolerance Append 00]: a _data extended with a 00 byte resumes identically.
def test_tolerance_append_00_byte(collection):
    """Test $changeStream resumeAfter from a token extended with a 00 byte."""
    result = _resume_after_mutated(collection, lambda t: {**t, "_data": t["_data"] + "00"})
    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(2)},
            "cursor.firstBatch.0.documentKey._id": Eq(2),
            "cursor.firstBatch.1.documentKey._id": Eq(3),
        },
        msg="$changeStream resumeAfter should resume identically when the token is extended with a"
        " 00 byte",
        raw_res=True,
    )


# Property [Tolerance Extra Fields]: a token with unknown extra fields resumes identically.
def test_tolerance_extra_fields(collection):
    """Test $changeStream resumeAfter from a token with unknown extra fields."""
    result = _resume_after_mutated(collection, lambda t: {**t, "unknownField": 1, "another": "x"})
    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(2)},
            "cursor.firstBatch.0.documentKey._id": Eq(2),
            "cursor.firstBatch.1.documentKey._id": Eq(3),
        },
        msg="$changeStream resumeAfter should resume identically when the token is augmented with"
        " unknown fields",
        raw_res=True,
    )


# Property [Tolerance Empty TypeBits]: a token with an empty _typeBits binary resumes identically.
def test_tolerance_empty_typebits(collection):
    """Test $changeStream resumeAfter from a token with an empty _typeBits binary."""
    result = _resume_after_mutated(collection, lambda t: {**t, "_typeBits": Binary(b"\x00")})
    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(2)},
            "cursor.firstBatch.0.documentKey._id": Eq(2),
            "cursor.firstBatch.1.documentKey._id": Eq(3),
        },
        msg="$changeStream resumeAfter should resume identically when the token is given an empty"
        " _typeBits binary",
        raw_res=True,
    )


# Property [High-Water-Mark Resume]: a high-water-mark token resumes, delivering later events.
@pytest.mark.parametrize("option", ["resumeAfter", "startAfter"])
def test_resume_from_high_water_mark(collection, option):
    """Test $changeStream resuming from a high-water-mark token."""
    mark = _high_water_mark(collection)
    collection.insert_many([{"_id": 1}, {"_id": 2}, {"_id": 3}])

    result = execute_command(
        collection,
        change_stream_command(collection, pipeline=[{"$changeStream": {option: mark}}]),
    )

    assertResult(
        result,
        expected={
            "cursor": {"firstBatch": Len(3)},
            "cursor.firstBatch.0.documentKey._id": Eq(1),
            "cursor.firstBatch.1.documentKey._id": Eq(2),
            "cursor.firstBatch.2.documentKey._id": Eq(3),
        },
        msg=f"$changeStream {option!r} should resume from a high-water-mark token",
        raw_res=True,
    )
