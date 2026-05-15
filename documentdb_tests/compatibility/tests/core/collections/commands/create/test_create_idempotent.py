"""Tests for the create command input/output contract."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    NAMESPACE_EXISTS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    CustomCollection,
    NamedCollection,
    ViewCollection,
)

# Property [Idempotent Creation (Success)]: re-creating an existing
# collection with identical or equivalent options returns success.
CREATE_IDEMPOTENT_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="identical_no_options",
        target_collection=NamedCollection(suffix="_idem"),
        command=lambda ctx: {"create": ctx.collection},
        expected={"ok": 1.0},
        msg="Re-creating with identical options should succeed",
    ),
    CommandTestCase(
        id="storage_engine_empty",
        target_collection=NamedCollection(suffix="_idem_se"),
        command=lambda ctx: {"create": ctx.collection, "storageEngine": {}},
        expected={"ok": 1.0},
        msg="storageEngine:{} is equivalent to omitted for idempotency",
    ),
    CommandTestCase(
        id="index_option_defaults_empty",
        target_collection=NamedCollection(suffix="_idem_iod"),
        command=lambda ctx: {"create": ctx.collection, "indexOptionDefaults": {}},
        expected={"ok": 1.0},
        msg="indexOptionDefaults:{} is equivalent to omitted for idempotency",
    ),
    CommandTestCase(
        id="change_stream_pre_post_images_disabled",
        target_collection=NamedCollection(suffix="_idem_cspi"),
        command=lambda ctx: {
            "create": ctx.collection,
            "changeStreamPreAndPostImages": {"enabled": False},
        },
        expected={"ok": 1.0},
        msg="changeStreamPreAndPostImages:{enabled:false} is equivalent to omitted",
    ),
    CommandTestCase(
        id="write_concern_ignored",
        target_collection=NamedCollection(suffix="_idem_wc"),
        command=lambda ctx: {"create": ctx.collection, "writeConcern": {"w": 1}},
        expected={"ok": 1.0},
        msg="writeConcern is not part of stored options",
    ),
    CommandTestCase(
        id="comment_ignored",
        target_collection=NamedCollection(suffix="_idem_cmt"),
        command=lambda ctx: {"create": ctx.collection, "comment": "hello"},
        expected={"ok": 1.0},
        msg="comment is not part of stored options",
    ),
    CommandTestCase(
        id="capped_truthy_numeric",
        target_collection=CappedCollection(size=4096),
        command=lambda ctx: {"create": ctx.collection, "capped": 42, "size": 4096},
        expected={"ok": 1.0},
        msg="Truthy numeric capped value matches existing capped:True",
    ),
    CommandTestCase(
        id="locale_simple_equivalent_to_no_collation",
        target_collection=NamedCollection(suffix="_idem_loc"),
        command=lambda ctx: {
            "create": ctx.collection,
            "collation": {"locale": "simple"},
        },
        expected={"ok": 1.0},
        msg="locale:'simple' collation is equivalent to no collation",
    ),
]

# Property [Idempotent Creation (Errors)]: re-creating an existing
# collection with different options produces NAMESPACE_EXISTS_ERROR.
CREATE_IDEMPOTENT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="different_options",
        target_collection=NamedCollection(suffix="_idem_diff"),
        command=lambda ctx: {
            "create": ctx.collection,
            "validator": {"x": {"$exists": True}},
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="Same name with different options should fail",
    ),
    CommandTestCase(
        id="regular_exists_create_as_view",
        target_collection=NamedCollection(suffix="_idem_rv"),
        command=lambda ctx: {
            "create": ctx.collection,
            "viewOn": "other",
            "pipeline": [],
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="Regular collection exists, create as view should fail",
    ),
    CommandTestCase(
        id="view_exists_create_as_collection",
        target_collection=ViewCollection(),
        command=lambda ctx: {"create": ctx.collection},
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="View exists, create as regular collection should fail",
    ),
    CommandTestCase(
        id="omit_collation_when_existing_has_one",
        target_collection=CustomCollection(options={"collation": {"locale": "en"}}),
        command=lambda ctx: {"create": ctx.collection},
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="Omitting collation when existing collection has one should fail",
    ),
    CommandTestCase(
        id="explicit_strict_validation_level_vs_omitted",
        target_collection=NamedCollection(suffix="_idem_vl"),
        command=lambda ctx: {
            "create": ctx.collection,
            "validationLevel": "strict",
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="Explicit 'strict' validationLevel vs omitted should fail",
    ),
    CommandTestCase(
        id="explicit_error_validation_action_vs_omitted",
        target_collection=NamedCollection(suffix="_idem_va"),
        command=lambda ctx: {
            "create": ctx.collection,
            "validationAction": "error",
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="Explicit 'error' validationAction vs omitted should fail",
    ),
]

CREATE_IDEMPOTENT_TESTS: list[CommandTestCase] = (
    CREATE_IDEMPOTENT_SUCCESS_TESTS + CREATE_IDEMPOTENT_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_IDEMPOTENT_TESTS))
def test_create_idempotent(database_client, collection, test):
    """Test create command idempotent behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
