"""Tests for $changeStream emitted event document structure."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, DBRef, Int64, MaxKey, MinKey, ObjectId, Timestamp
from utils.changeStream_common import change_stream_command, get_more_command

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NotExists
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF


@dataclass(frozen=True)
class Mutation:
    """A change to perform against a collection, observed as one change event.

    Attributes:
        operation_type: The ``operationType`` the resulting event carries, used
            to pick the event out of the drained batch
        apply: Performs the observed change after the stream is open
        seed: Document inserted before the stream opens so the mutation has
            something to act on (None for inserts)
    """

    operation_type: str
    apply: Callable[[Any], None]
    seed: dict[str, Any] | None = None


def _insert(doc: dict[str, Any]) -> Mutation:
    """Insert ``doc`` after the stream opens; the insert is the observed event."""
    return Mutation("insert", lambda c: c.insert_one(dict(doc)))


def _update(seed: dict[str, Any], spec: Any) -> Mutation:
    """Seed ``seed``, then apply update ``spec`` to it after the stream opens."""
    return Mutation("update", lambda c: c.update_one({"_id": seed["_id"]}, spec), seed=seed)


def _replace(seed: dict[str, Any], replacement: dict[str, Any]) -> Mutation:
    """Seed ``seed``, then replace it with ``replacement`` after the stream opens."""
    return Mutation(
        "replace", lambda c: c.replace_one({"_id": seed["_id"]}, dict(replacement)), seed=seed
    )


def _delete(seed: dict[str, Any]) -> Mutation:
    """Seed ``seed``, then delete it after the stream opens."""
    return Mutation("delete", lambda c: c.delete_one({"_id": seed["_id"]}), seed=seed)


@dataclass(frozen=True)
class ChangeStreamEventTestCase(BaseTestCase):
    """Test case for $changeStream emitted event structure.

    Drives an imperative open-mutate-drain sequence: the stream is opened with
    ``pipeline`` (the full ``[{"$changeStream": ...}]`` pipeline), ``mutation``
    is performed, and the inherited ``expected`` (a property-check map) asserts
    envelope/payload fields on the resulting event.

    Attributes:
        pipeline: The full ``[{"$changeStream": ...}]`` pipeline to open with
            (required)
        mutation: Fully describes the observed write, see ``Mutation`` (required)
        pre_and_post_images: When true, enables pre/post image capture before
            the stream opens
        post_mutation: An operation run after the observed mutation and before
            the stream is drained, e.g. deleting the document so a later
            updateLookup finds nothing (None when not needed)
    """

    pipeline: list[dict[str, Any]] | None = None
    mutation: Mutation | None = None
    pre_and_post_images: bool = False
    post_mutation: Callable[[Any], None] | None = None

    def __post_init__(self):
        super().__post_init__()
        if self.pipeline is None:
            raise ValueError(f"ChangeStreamEventTestCase '{self.id}' must set pipeline")
        if self.mutation is None:
            raise ValueError(f"ChangeStreamEventTestCase '{self.id}' must set mutation")


# Property [Event Envelope Fields]: every change event carries the common
# envelope fields with their documented BSON types, and operationType equals the
# name of the operation that produced the event.
CHANGESTREAM_EVENT_ENVELOPE_TESTS: list[ChangeStreamEventTestCase] = [
    ChangeStreamEventTestCase(
        "envelope_insert",
        pipeline=[{"$changeStream": {}}],
        mutation=_insert({"_id": 1, "a": 1}),
        expected={
            "_id._data": IsType("string"),
            "operationType": Eq("insert"),
            "clusterTime": IsType("timestamp"),
            "wallTime": IsType("date"),
            "ns.db": IsType("string"),
            "ns.coll": IsType("string"),
            "documentKey": IsType("object"),
        },
        msg="$changeStream insert event should carry the common envelope fields",
    ),
    ChangeStreamEventTestCase(
        "envelope_update",
        pipeline=[{"$changeStream": {}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={
            "_id._data": IsType("string"),
            "operationType": Eq("update"),
            "clusterTime": IsType("timestamp"),
            "wallTime": IsType("date"),
            "ns.db": IsType("string"),
            "ns.coll": IsType("string"),
            "documentKey": IsType("object"),
        },
        msg="$changeStream update event should carry the common envelope fields",
    ),
    ChangeStreamEventTestCase(
        "envelope_replace",
        pipeline=[{"$changeStream": {}}],
        mutation=_replace({"_id": 1, "a": 1}, {"b": 2}),
        expected={
            "_id._data": IsType("string"),
            "operationType": Eq("replace"),
            "clusterTime": IsType("timestamp"),
            "wallTime": IsType("date"),
            "ns.db": IsType("string"),
            "ns.coll": IsType("string"),
            "documentKey": IsType("object"),
        },
        msg="$changeStream replace event should carry the common envelope fields",
    ),
    ChangeStreamEventTestCase(
        "envelope_delete",
        pipeline=[{"$changeStream": {}}],
        mutation=_delete({"_id": 1, "a": 1}),
        expected={
            "_id._data": IsType("string"),
            "operationType": Eq("delete"),
            "clusterTime": IsType("timestamp"),
            "wallTime": IsType("date"),
            "ns.db": IsType("string"),
            "ns.coll": IsType("string"),
            "documentKey": IsType("object"),
        },
        msg="$changeStream delete event should carry the common envelope fields",
    ),
]

# Property [documentKey Id Type Preservation]: documentKey._id preserves the BSON
# type and value of the source document's _id.
CHANGESTREAM_EVENT_DOCUMENT_KEY_TESTS: list[ChangeStreamEventTestCase] = [
    ChangeStreamEventTestCase(
        f"document_key_{tid}",
        pipeline=[{"$changeStream": {}}],
        mutation=_insert({"_id": val, "marker": 1}),
        expected={"documentKey._id": Eq(val)},
        msg=f"$changeStream should preserve a {tid} _id in documentKey",
    )
    for tid, val in [
        ("int32", 7),
        ("int64", Int64(7)),
        ("double", 3.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "abc"),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01" * 16, 4)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("dbref", DBRef("c", 1)),
        ("object", {"x": 1}),
        ("null", None),
    ]
]

# Property [Operation Payload Fields]: each operationType carries exactly the
# payload fields documented for it, and insert carries fullDocument regardless
# of the fullDocument option.
CHANGESTREAM_EVENT_PAYLOAD_TESTS: list[ChangeStreamEventTestCase] = [
    ChangeStreamEventTestCase(
        "payload_insert",
        pipeline=[{"$changeStream": {}}],
        mutation=_insert({"_id": 1, "a": 1}),
        expected={
            "fullDocument": Eq({"_id": 1, "a": 1}),
            "updateDescription": NotExists(),
        },
        msg="$changeStream insert event should carry fullDocument and no updateDescription",
    ),
    ChangeStreamEventTestCase(
        "payload_insert_full_document_mode",
        pipeline=[{"$changeStream": {"fullDocument": "updateLookup"}}],
        mutation=_insert({"_id": 1, "a": 1}),
        expected={
            "fullDocument": Eq({"_id": 1, "a": 1}),
            "updateDescription": NotExists(),
        },
        msg=(
            "$changeStream insert event should carry fullDocument regardless of"
            " the fullDocument option"
        ),
    ),
    ChangeStreamEventTestCase(
        "payload_replace",
        pipeline=[{"$changeStream": {}}],
        mutation=_replace({"_id": 1, "a": 1}, {"b": 2}),
        expected={
            "fullDocument": Eq({"_id": 1, "b": 2}),
            "updateDescription": NotExists(),
        },
        msg="$changeStream replace event should carry fullDocument and no updateDescription",
    ),
    ChangeStreamEventTestCase(
        "payload_delete",
        pipeline=[{"$changeStream": {}}],
        mutation=_delete({"_id": 1, "a": 1}),
        expected={
            "fullDocument": NotExists(),
            "updateDescription": NotExists(),
        },
        msg="$changeStream delete event should carry neither fullDocument nor updateDescription",
    ),
    ChangeStreamEventTestCase(
        "payload_update",
        pipeline=[{"$changeStream": {}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={
            "updateDescription": Exists(),
        },
        msg="$changeStream update event should always carry updateDescription",
    ),
]

# Property [updateDescription Structure]: an update event's updateDescription
# records changed paths in updatedFields (new nested paths as nested objects),
# removed paths in removedFields, and end-truncations in truncatedArrays,
# independently of the fullDocument mode.
CHANGESTREAM_EVENT_UPDATE_DESCRIPTION_TESTS: list[ChangeStreamEventTestCase] = [
    ChangeStreamEventTestCase(
        "update_description_set_unset",
        pipeline=[{"$changeStream": {}}],
        mutation=_update({"_id": 1, "a": 1, "b": 1}, {"$set": {"b": 2}, "$unset": {"a": ""}}),
        expected={
            "updateDescription": Eq(
                {"updatedFields": {"b": 2}, "removedFields": ["a"], "truncatedArrays": []}
            )
        },
        msg="$changeStream updateDescription should record set paths and removed fields",
    ),
    ChangeStreamEventTestCase(
        "update_description_nested_set",
        pipeline=[{"$changeStream": {}}],
        mutation=_update({"_id": 1}, {"$set": {"nested.x": 5}}),
        expected={"updateDescription.updatedFields": Eq({"nested": {"x": 5}})},
        msg="$changeStream updateDescription should represent a new nested path as a nested object",
    ),
    ChangeStreamEventTestCase(
        "update_description_truncated_arrays",
        pipeline=[{"$changeStream": {}}],
        mutation=_update(
            {"_id": 1, "arr": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
            [{"$set": {"arr": {"$slice": ["$arr", 5]}}}],
        ),
        expected={"updateDescription.truncatedArrays": Eq([{"field": "arr", "newSize": 5}])},
        msg="$changeStream updateDescription should record end-truncation in truncatedArrays",
    ),
    ChangeStreamEventTestCase(
        "update_description_with_full_document_mode",
        pipeline=[{"$changeStream": {"fullDocument": "updateLookup"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={
            "updateDescription": Eq(
                {"updatedFields": {"a": 2}, "removedFields": [], "truncatedArrays": []}
            )
        },
        msg="$changeStream updateDescription should be emitted regardless of the fullDocument mode",
    ),
]

# Property [fullDocument Event Behavior]: an update event's fullDocument field
# tracks the fullDocument mode and pre/post-image availability.
CHANGESTREAM_EVENT_FULL_DOCUMENT_TESTS: list[ChangeStreamEventTestCase] = [
    ChangeStreamEventTestCase(
        "full_document_default_omitted",
        pipeline=[{"$changeStream": {}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={"fullDocument": NotExists()},
        msg="$changeStream update event should omit fullDocument when the mode is omitted",
    ),
    ChangeStreamEventTestCase(
        "full_document_default_string",
        pipeline=[{"$changeStream": {"fullDocument": "default"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={"fullDocument": NotExists()},
        msg="$changeStream update event should omit fullDocument under the default mode",
    ),
    ChangeStreamEventTestCase(
        "full_document_null",
        pipeline=[{"$changeStream": {"fullDocument": None}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={"fullDocument": NotExists()},
        msg="$changeStream update event should omit fullDocument when the mode is null",
    ),
    ChangeStreamEventTestCase(
        "full_document_update_lookup",
        pipeline=[{"$changeStream": {"fullDocument": "updateLookup"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={"fullDocument": Eq({"_id": 1, "a": 2})},
        msg="$changeStream updateLookup should carry the current document",
    ),
    ChangeStreamEventTestCase(
        "full_document_update_lookup_deleted",
        pipeline=[{"$changeStream": {"fullDocument": "updateLookup"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        post_mutation=lambda collection: collection.delete_one({"_id": 1}),
        expected={"fullDocument": Eq(None)},
        msg="$changeStream updateLookup should carry null when the document no longer exists",
    ),
    ChangeStreamEventTestCase(
        "full_document_when_available_no_images",
        pipeline=[{"$changeStream": {"fullDocument": "whenAvailable"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={"fullDocument": Eq(None)},
        msg="$changeStream whenAvailable should carry null without pre/post images enabled",
    ),
    ChangeStreamEventTestCase(
        "full_document_when_available_with_images",
        pipeline=[{"$changeStream": {"fullDocument": "whenAvailable"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        pre_and_post_images=True,
        expected={"fullDocument": Eq({"_id": 1, "a": 2})},
        msg="$changeStream whenAvailable should carry the post-image with pre/post images enabled",
    ),
    ChangeStreamEventTestCase(
        "full_document_required_with_images",
        pipeline=[{"$changeStream": {"fullDocument": "required"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        pre_and_post_images=True,
        expected={"fullDocument": Eq({"_id": 1, "a": 2})},
        msg="$changeStream required should carry the post-image with pre/post images enabled",
    ),
]

# Property [fullDocumentBeforeChange Event Behavior]: an update event's
# fullDocumentBeforeChange tracks the fullDocumentBeforeChange mode and
# pre-image availability, independently of any fullDocument post-image.
CHANGESTREAM_EVENT_FULL_DOCUMENT_BEFORE_CHANGE_TESTS: list[ChangeStreamEventTestCase] = [
    ChangeStreamEventTestCase(
        "before_change_off",
        pipeline=[{"$changeStream": {"fullDocumentBeforeChange": "off"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={"fullDocumentBeforeChange": NotExists()},
        msg="$changeStream update event should omit fullDocumentBeforeChange under the off mode",
    ),
    ChangeStreamEventTestCase(
        "before_change_when_available_no_images",
        pipeline=[{"$changeStream": {"fullDocumentBeforeChange": "whenAvailable"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        expected={"fullDocumentBeforeChange": Eq(None)},
        msg=(
            "$changeStream whenAvailable should carry a null fullDocumentBeforeChange"
            " without pre/post images enabled"
        ),
    ),
    ChangeStreamEventTestCase(
        "before_change_when_available_with_images",
        pipeline=[{"$changeStream": {"fullDocumentBeforeChange": "whenAvailable"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        pre_and_post_images=True,
        expected={"fullDocumentBeforeChange": Eq({"_id": 1, "a": 1})},
        msg="$changeStream whenAvailable should carry the pre-image with pre/post images enabled",
    ),
    ChangeStreamEventTestCase(
        "before_change_required_with_images",
        pipeline=[{"$changeStream": {"fullDocumentBeforeChange": "required"}}],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        pre_and_post_images=True,
        expected={"fullDocumentBeforeChange": Eq({"_id": 1, "a": 1})},
        msg="$changeStream required should carry the pre-image with pre/post images enabled",
    ),
    ChangeStreamEventTestCase(
        "before_change_and_full_document_both_images",
        pipeline=[
            {
                "$changeStream": {
                    "fullDocument": "whenAvailable",
                    "fullDocumentBeforeChange": "whenAvailable",
                }
            }
        ],
        mutation=_update({"_id": 1, "a": 1}, {"$set": {"a": 2}}),
        pre_and_post_images=True,
        expected={
            "fullDocument": Eq({"_id": 1, "a": 2}),
            "fullDocumentBeforeChange": Eq({"_id": 1, "a": 1}),
        },
        msg=(
            "$changeStream should carry the post-image in fullDocument and the pre-image"
            " in fullDocumentBeforeChange independently when both modes are set"
        ),
    ),
]

CHANGESTREAM_EVENT_STRUCTURE_TESTS = (
    CHANGESTREAM_EVENT_ENVELOPE_TESTS
    + CHANGESTREAM_EVENT_DOCUMENT_KEY_TESTS
    + CHANGESTREAM_EVENT_PAYLOAD_TESTS
    + CHANGESTREAM_EVENT_UPDATE_DESCRIPTION_TESTS
    + CHANGESTREAM_EVENT_FULL_DOCUMENT_TESTS
    + CHANGESTREAM_EVENT_FULL_DOCUMENT_BEFORE_CHANGE_TESTS
)


def _emit_event(collection, test_case: ChangeStreamEventTestCase) -> dict[str, Any]:
    """Open a stream, perform the test case mutation, and return the matching event.

    The mutation happens after the stream is open, so its event is delivered by
    the first getMore.
    """
    mutation = test_case.mutation
    assert mutation is not None  # guaranteed by __post_init__
    if mutation.seed is not None:
        collection.insert_one(dict(mutation.seed))
    if test_case.pre_and_post_images:
        execute_command(
            collection,
            {"collMod": collection.name, "changeStreamPreAndPostImages": {"enabled": True}},
        )
    opened = execute_command(
        collection, change_stream_command(collection, pipeline=test_case.pipeline)
    )
    mutation.apply(collection)
    if test_case.post_mutation is not None:
        test_case.post_mutation(collection)
    batch = execute_command(collection, get_more_command(collection, opened["cursor"]["id"]))[
        "cursor"
    ]["nextBatch"]
    matching = [e for e in batch if e["operationType"] == mutation.operation_type]
    assert matching, f"no {mutation.operation_type} event in batch: {batch!r}"
    event: dict[str, Any] = matching[0]
    return event


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_EVENT_STRUCTURE_TESTS))
def test_changeStream_event_structure(collection, test_case: ChangeStreamEventTestCase):
    """Test $changeStream emitted event structure."""
    event = _emit_event(collection, test_case)
    assertProperties(event, test_case.expected, msg=test_case.msg, raw_res=True)
