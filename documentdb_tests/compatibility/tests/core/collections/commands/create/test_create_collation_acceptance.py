"""Tests for the create command collation acceptance behavior."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CustomCollection,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_TWO_AND_HALF,
)

# Property [Collation Locale Acceptance]: the collation option accepts a
# document with locale; null is treated as omitted; locale:"simple" is
# equivalent to no collation.
CREATE_COLLATION_LOCALE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_locale_en",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="Collation with locale 'en' should succeed",
    ),
    CommandTestCase(
        id="collation_locale_fr",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "fr"},
        },
        expected={"ok": 1.0},
        msg="Collation with locale 'fr' should succeed",
    ),
    CommandTestCase(
        id="collation_locale_zh",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "zh"},
        },
        expected={"ok": 1.0},
        msg="Collation with locale 'zh' should succeed",
    ),
    CommandTestCase(
        id="collation_locale_ar",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "ar"},
        },
        expected={"ok": 1.0},
        msg="Collation with locale 'ar' should succeed",
    ),
    CommandTestCase(
        id="collation_locale_en_us",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en_US"},
        },
        expected={"ok": 1.0},
        msg="Collation with locale 'en_US' should succeed",
    ),
    CommandTestCase(
        id="collation_locale_zh_hant",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "zh_Hant"},
        },
        expected={"ok": 1.0},
        msg="Collation with locale 'zh_Hant' should succeed",
    ),
    CommandTestCase(
        id="collation_locale_sr_latn",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "sr_Latn"},
        },
        expected={"ok": 1.0},
        msg="Collation with locale 'sr_Latn' should succeed",
    ),
    CommandTestCase(
        id="collation_locale_simple",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "simple"},
        },
        expected={"ok": 1.0},
        msg="locale:'simple' is not stored (equivalent to no collation)",
    ),
    CommandTestCase(
        id="collation_null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": None,
        },
        expected={"ok": 1.0},
        msg="null collation is treated as omitted",
    ),
]

# Property [Collation Strength Acceptance]: strength accepts numeric types
# with coercion in range [1, 5]; null uses the default.
CREATE_COLLATION_STRENGTH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_strength_1",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"ok": 1.0},
        msg="strength=1 should succeed",
    ),
    CommandTestCase(
        id="collation_strength_5",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": 5},
        },
        expected={"ok": 1.0},
        msg="strength=5 should succeed",
    ),
    CommandTestCase(
        id="collation_strength_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": Int64(3)},
        },
        expected={"ok": 1.0},
        msg="strength as Int64 should succeed",
    ),
    CommandTestCase(
        id="collation_strength_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": 3.0},
        },
        expected={"ok": 1.0},
        msg="strength as double should succeed",
    ),
    CommandTestCase(
        id="collation_strength_decimal128",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": Decimal128("3")},
        },
        expected={"ok": 1.0},
        msg="strength as Decimal128 should succeed",
    ),
    CommandTestCase(
        id="collation_strength_double_truncation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": 2.9},
        },
        expected={"ok": 1.0},
        msg="double 2.9 truncates toward zero to 2, which is valid",
    ),
    CommandTestCase(
        id="collation_strength_decimal128_rounds_up",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": Decimal128("2.9")},
        },
        expected={"ok": 1.0},
        msg="Decimal128('2.9') rounds to 3, unlike double 2.9 which truncates to 2",
    ),
    CommandTestCase(
        id="collation_strength_decimal128_bankers_rounding",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": DECIMAL128_TWO_AND_HALF},
        },
        expected={"ok": 1.0},
        msg="Decimal128('2.5') banker's rounds to 2, which is valid",
    ),
    CommandTestCase(
        id="collation_strength_null_uses_default",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": None},
        },
        expected={"ok": 1.0},
        msg="null strength uses default (3)",
    ),
]

# Property [Collation Boolean Sub-Fields]: caseLevel, normalization, and
# numericOrdering accept true, false, and null.
CREATE_COLLATION_BOOLEAN_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_case_level_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "caseLevel": True},
        },
        expected={"ok": 1.0},
        msg="caseLevel:true should succeed",
    ),
    CommandTestCase(
        id="collation_case_level_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "caseLevel": False},
        },
        expected={"ok": 1.0},
        msg="caseLevel:false should succeed",
    ),
    CommandTestCase(
        id="collation_case_level_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "caseLevel": None},
        },
        expected={"ok": 1.0},
        msg="caseLevel:null should succeed",
    ),
    CommandTestCase(
        id="collation_normalization_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "normalization": True},
        },
        expected={"ok": 1.0},
        msg="normalization:true should succeed",
    ),
    CommandTestCase(
        id="collation_normalization_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "normalization": False},
        },
        expected={"ok": 1.0},
        msg="normalization:false should succeed",
    ),
    CommandTestCase(
        id="collation_normalization_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "normalization": None},
        },
        expected={"ok": 1.0},
        msg="normalization:null should succeed",
    ),
    CommandTestCase(
        id="collation_numeric_ordering_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected={"ok": 1.0},
        msg="numericOrdering:true should succeed",
    ),
    CommandTestCase(
        id="collation_numeric_ordering_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "numericOrdering": False},
        },
        expected={"ok": 1.0},
        msg="numericOrdering:false should succeed",
    ),
    CommandTestCase(
        id="collation_numeric_ordering_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "numericOrdering": None},
        },
        expected={"ok": 1.0},
        msg="numericOrdering:null should succeed",
    ),
    CommandTestCase(
        id="collation_backwards_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "backwards": True},
        },
        expected={"ok": 1.0},
        msg="backwards:true should succeed",
    ),
    CommandTestCase(
        id="collation_backwards_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "backwards": False},
        },
        expected={"ok": 1.0},
        msg="backwards:false should succeed",
    ),
]

# Property [Collation CaseFirst Acceptance]: caseFirst accepts "upper",
# "lower", and "off" when caseLevel:true or strength > 2.
CREATE_COLLATION_CASE_FIRST_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_case_first_upper",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "caseLevel": True, "caseFirst": "upper"},
        },
        expected={"ok": 1.0},
        msg="caseFirst:'upper' with caseLevel:true should succeed",
    ),
    CommandTestCase(
        id="collation_case_first_lower",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "caseLevel": True, "caseFirst": "lower"},
        },
        expected={"ok": 1.0},
        msg="caseFirst:'lower' with caseLevel:true should succeed",
    ),
    CommandTestCase(
        id="collation_case_first_off",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "caseLevel": True, "caseFirst": "off"},
        },
        expected={"ok": 1.0},
        msg="caseFirst:'off' with caseLevel:true should succeed",
    ),
    CommandTestCase(
        id="collation_case_first_with_strength_gt_2",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "strength": 3, "caseFirst": "upper"},
        },
        expected={"ok": 1.0},
        msg="caseFirst with strength > 2 should succeed",
    ),
]

# Property [Collation Alternate and MaxVariable Acceptance]: alternate accepts
# "non-ignorable" and "shifted"; maxVariable accepts "punct" and "space".
CREATE_COLLATION_ALTERNATE_MAX_VARIABLE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_alternate_non_ignorable",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "alternate": "non-ignorable"},
        },
        expected={"ok": 1.0},
        msg="alternate:'non-ignorable' should succeed",
    ),
    CommandTestCase(
        id="collation_alternate_shifted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "alternate": "shifted"},
        },
        expected={"ok": 1.0},
        msg="alternate:'shifted' should succeed",
    ),
    CommandTestCase(
        id="collation_max_variable_punct",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "maxVariable": "punct"},
        },
        expected={"ok": 1.0},
        msg="maxVariable:'punct' should succeed",
    ),
    CommandTestCase(
        id="collation_max_variable_space",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "maxVariable": "space"},
        },
        expected={"ok": 1.0},
        msg="maxVariable:'space' should succeed",
    ),
]

# Property [Collation Version Acceptance]: version accepts valid version
# strings and null (uses default).
CREATE_COLLATION_VERSION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_version_57_1",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "version": "57.1"},
        },
        expected={"ok": 1.0},
        msg="version:'57.1' should succeed",
    ),
    CommandTestCase(
        id="collation_version_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en", "version": None},
        },
        expected={"ok": 1.0},
        msg="version:null should succeed (uses default)",
    ),
]

# Property [Collation Compatibility]: collation is compatible with views
# and supports idempotent creation with partial spec matching defaults.
CREATE_COLLATION_COMPATIBILITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_with_view",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "viewOn": ctx.collection,
            "pipeline": [],
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="Collation compatible with view",
    ),
    CommandTestCase(
        id="collation_partial_spec_matching_defaults",
        target_collection=CustomCollection(options={"collation": {"locale": "en"}}),
        command=lambda ctx: {
            "create": ctx.collection,
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="Partial spec with matching defaults succeeds for idempotent creation",
    ),
]

CREATE_COLLATION_SUCCESS_TESTS: list[CommandTestCase] = (
    CREATE_COLLATION_LOCALE_TESTS
    + CREATE_COLLATION_STRENGTH_TESTS
    + CREATE_COLLATION_BOOLEAN_FIELDS_TESTS
    + CREATE_COLLATION_CASE_FIRST_TESTS
    + CREATE_COLLATION_ALTERNATE_MAX_VARIABLE_TESTS
    + CREATE_COLLATION_VERSION_TESTS
    + CREATE_COLLATION_COMPATIBILITY_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_COLLATION_SUCCESS_TESTS))
def test_create_collation_acceptance(database_client, collection, test):
    """Test create command collation acceptance behavior."""
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
