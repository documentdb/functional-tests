"""
Unified execution and assertion utilities for tests.
"""

from __future__ import annotations

from datetime import timezone
from typing import Any, Dict

from bson.codec_options import CodecOptions

TZ_AWARE_CODEC = CodecOptions(tz_aware=True, tzinfo=timezone.utc)


def execute_command(collection, command: Dict, codec_options=TZ_AWARE_CODEC, session=None) -> Any:
    """
    Execute a DocumentDB command and return result or exception.

    Args:
        collection: DocumentDB collection
        command: Command to execute via runCommand
        codec_options: CodecOptions for result decoding.
            Defaults to UTC-aware datetime decoding.
        session: Optional ClientSession for session-aware commands.

    Returns:
        Result if successful, Exception if failed
    """
    try:
        db = collection.database
        result = db.command(command, codec_options=codec_options, session=session)
        return result
    except Exception as e:
        return e


def execute_admin_command(collection, command: Dict) -> Any:
    """
    Execute a DocumentDB command on admin database and return result or exception.

    Args:
        collection: DocumentDB collection
        command: Command to execute via runCommand

    Returns:
        Result if successful, Exception if failed
    """
    try:
        db = collection.database.client.admin
        result = db.command(command)
        return result
    except Exception as e:
        return e


def execute_session_command(collection, test_case) -> Any:
    """Execute a SessionTestCase: seed, transact, commit, and return the result.

    Runs the full transaction lifecycle described by *test_case*:

    1. Seed ``test_case.docs`` into *collection* (via ``prepare``).
    2. Open a client session and start a transaction.
    3. Execute each ``SessionOperation`` in ``test_case.ops``.
    4. Commit — either via ``session.commit_transaction()`` or by sending
       ``test_case.commit_command`` as a raw admin command.
    5. Return the appropriate result for assertion:
       - If ``test_case.expected_response`` is set, return the commit
         command response (a dict).
       - Otherwise, return the readback query result via
         ``execute_command``.

    Args:
        collection: The pytest ``collection`` fixture.
        test_case: A ``SessionTestCase`` instance.

    Returns:
        Result dict (commit response or readback) or Exception.
    """
    from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_test_case import (  # noqa: E501
        SessionTestCase,
    )

    assert isinstance(test_case, SessionTestCase)

    # 1. Seed documents.
    if test_case.docs is not None:
        if test_case.docs:
            collection.insert_many(test_case.docs)

    # 2-4. Transaction lifecycle.
    client = collection.database.client
    commit_result = None
    with client.start_session() as session:
        session.start_transaction()
        for op in test_case.ops:
            op.execute(collection, session)
        if test_case.commit_command is not None:
            try:
                commit_result = client.admin.command(test_case.commit_command, session=session)
            except Exception as e:
                commit_result = e
        else:
            session.commit_transaction()

    # 5. Return commit response or readback.
    if test_case.expected_response is not None:
        execute_command(collection, {"find": collection.name, "filter": {}})
        return commit_result

    return execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test_case.readback_filter,
            "sort": test_case.readback_sort,
        },
    )


def execute_abort_session_command(collection, test_case) -> Any:
    """Execute a SessionTestCase as an abort: seed, transact, abort, and return the result.

    Runs the full transaction lifecycle described by *test_case*:

    1. Seed ``test_case.docs`` into *collection* (via ``prepare``).
    2. Open a client session and start a transaction.
    3. Execute each ``SessionOperation`` in ``test_case.ops``.
    4. Abort — either via ``session.abort_transaction()`` or by sending
       ``test_case.commit_command`` as a raw admin command.
    5. Return the appropriate result for assertion:
       - If ``test_case.expected_response`` is set, return the abort
         command response (a dict).
       - Otherwise, return the readback query result via
         ``execute_command``.

    Args:
        collection: The pytest ``collection`` fixture.
        test_case: A ``SessionTestCase`` instance.

    Returns:
        Result dict (abort response or readback) or Exception.
    """
    from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_test_case import (  # noqa: E501
        SessionTestCase,
    )

    assert isinstance(test_case, SessionTestCase)

    # 1. Seed documents.
    if test_case.docs is not None:
        if test_case.docs:
            collection.insert_many(test_case.docs)

    # 2-4. Transaction lifecycle.
    client = collection.database.client
    abort_result = None
    with client.start_session() as session:
        session.start_transaction()
        for op in test_case.ops:
            op.execute(collection, session)
        if test_case.commit_command is not None:
            try:
                abort_result = client.admin.command(test_case.commit_command, session=session)
            except Exception as e:
                abort_result = e
        else:
            session.abort_transaction()

    # 5. Return abort response or readback.
    if test_case.expected_response is not None:
        # Verify that aborted data did NOT persist (the raw admin
        # command path bypasses pymongo's session bookkeeping; we
        # assert rollback explicitly by checking that transacted
        # inserts are not visible after abort).
        if not isinstance(abort_result, Exception) and test_case.ops:
            readback = execute_command(
                collection,
                {"find": collection.name, "filter": test_case.readback_filter},
            )
            assert not isinstance(readback, Exception), f"Readback after abort failed: {readback}"
            cursor = readback.get("cursor", {})
            docs = cursor.get("firstBatch", [])
            seed_count = len(test_case.docs) if test_case.docs else 0
            assert len(docs) == seed_count, (
                f"Aborted transaction data persisted — "
                f"expected {seed_count} docs (seed only), got {len(docs)}"
            )
        return abort_result

    return execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test_case.readback_filter,
            "sort": test_case.readback_sort,
        },
    )
