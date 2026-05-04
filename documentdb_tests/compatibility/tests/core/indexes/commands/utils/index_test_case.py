"""
Shared test case for index command tests.
"""

from dataclasses import dataclass
from typing import Any, Optional

from documentdb_tests.framework.test_case import BaseTestCase


def index_created_response(num_indexes_before=1, num_indexes_after=2):
    """Build expected createIndexes response with ok and index counts.

    Defaults assume a fresh collection (_id only) with one new index created.
    Override for cases like multiple indexes, noop, or setup_indexes.
    """
    return {"ok": 1.0, "numIndexesBefore": num_indexes_before, "numIndexesAfter": num_indexes_after}


@dataclass(frozen=True)
class IndexTestCase(BaseTestCase):
    """Test case for index command tests (createIndexes, dropIndexes, etc).

    Attributes:
        indexes: Index specs for the operation under test.
        doc: Optional documents to insert before the operation.
        setup_indexes: Optional indexes to create before the main operation
            (for conflict/duplicate tests).
        comment: Optional comment field for the command.
        write_concern: Optional writeConcern for the command.
        invalid_input: Optional invalid BSON value for type-rejection tests.
        command_options: Optional additional command options.
    """

    indexes: Optional[tuple] = ()
    doc: Optional[tuple] = None
    setup_indexes: Optional[list] = None
    comment: Optional[Any] = None
    write_concern: Optional[dict] = None
    invalid_input: Optional[Any] = None
    command_options: Optional[dict] = None
