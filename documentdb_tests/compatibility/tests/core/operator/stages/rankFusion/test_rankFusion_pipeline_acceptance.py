"""Tests for accepted $rankFusion input pipeline declarations: names and counts."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.rankFusion.utils.rankFusion_common import (  # noqa: E501
    rrf_score,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Accepted Pipeline Names]: a pipeline name is accepted regardless of
# its character class or length as long as it is non-empty, does not start with
# $, and contains no ASCII dot, and the named pipeline contributes its rank to
# the score.
RANKFUSION_PIPELINE_NAME_ACCEPTED_TESTS: list[StageTestCase] = [
    *(
        StageTestCase(
            f"name_{tid}",
            docs=[{"_id": 1, "a": 1}],
            pipeline=[
                {"$rankFusion": {"input": {"pipelines": {name: [{"$sort": {"a": -1}}]}}}},
                {"$project": {"_id": 1, "score": {"$meta": "score"}}},
            ],
            expected=[{"_id": 1, "score": rrf_score(1)}],
            msg=f"$rankFusion should accept a {tid} pipeline name",
        )
        for tid, name in [
            ("mid_dollar", "a$b"),
            ("only_whitespace", "  "),
            ("inner_space", "a b"),
            ("trailing_space", "p1 "),
            ("tab", "a\tb"),
            ("newline", "a\nb"),
            ("carriage_return", "a\rb"),
            # U+0001, a low control character.
            ("control_char", "a\x01b"),
            # U+00A0 non-breaking space.
            ("nbsp", "a\u00a0b"),
            # U+2002 en space.
            ("en_space", "a\u2002b"),
            ("backslash", "a\\b"),
            ("braces", "a{}b"),
            ("brackets", "a[]b"),
            ("double_quote", 'a"b'),
            ("punctuation", "!@#%^&*()"),
            # U+FEFF byte-order mark.
            ("bom", "a\ufeffb"),
            # U+200B zero-width space.
            ("zwsp", "a\u200bb"),
            # U+200D zero-width joiner.
            ("zwj", "a\u200db"),
            # U+200E left-to-right mark.
            ("ltr_mark", "a\u200eb"),
            # U+1F468 U+200D U+1F469, a ZWJ emoji sequence.
            ("zwj_emoji", "\U0001f468\u200d\U0001f469"),
            # U+2024 one dot leader, a Unicode dot-like.
            ("unicode_dot_leader", "a\u2024b"),
            # 2-byte UTF-8.
            ("two_byte", "é"),
            # 3-byte UTF-8.
            ("three_byte", "中文"),
            # 4-byte UTF-8.
            ("four_byte", "\U0001f600"),
            ("single_char", "x"),
            ("pure_digits", "12345"),
            ("leading_digit", "1abc"),
        ]
    ),
    StageTestCase(
        "name_very_long",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"x" * 10_000: [{"$sort": {"a": -1}}]}}}},
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1)}],
        msg="$rankFusion should accept a very long pipeline name with no length limit",
    ),
]

# Property [Pipeline Count]: the stage accepts any number of named input
# pipelines, from the documented minimum of one up to several hundred, summing
# each pipeline's contribution to the score.
RANKFUSION_PIPELINE_COUNT_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"pipeline_count_{count}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {f"p{i}": [{"$sort": {"a": -1}}] for i in range(count)}}
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[{"_id": 1, "score": rrf_score(1, weights=(count,))}],
        msg=f"$rankFusion should accept {count} input pipelines and sum their contributions",
    )
    for count in [1, 2, 500]
]

# Property [Multi-Stage Input Pipeline]: an input pipeline that contains several
# stages is accepted and returns its documents.
RANKFUSION_MULTI_STAGE_PIPELINE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multi_stage_input_pipeline",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}] + [{"$skip": 0}] * 9}}
                }
            },
        ],
        expected=[{"_id": 1, "a": 1}],
        msg="$rankFusion should accept an input pipeline that contains several stages",
    ),
]

# Property [Pipeline Name Echoed Verbatim]: an accepted pipeline name appears in
# scoreDetails.details[].inputPipelineName exactly as declared, with no trimming,
# whitespace collapsing, or Unicode normalization.
RANKFUSION_PIPELINE_NAME_ECHO_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"name_echo_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {name: [{"$sort": {"a": -1}}]}},
                    "scoreDetails": True,
                }
            },
            {"$project": {"_id": 1, "sd": {"$meta": "scoreDetails"}}},
        ],
        expected={"sd.details.0.inputPipelineName": Eq(name)},
        msg=f"$rankFusion should echo a {tid} pipeline name verbatim into scoreDetails",
    )
    for tid, name in [
        # No trailing-whitespace trimming.
        ("trailing_space", "p1 "),
        # No collapsing of repeated whitespace.
        ("inner_double_space", "a  b"),
        # U+0065 U+0301, an NFD form that is not normalized to U+00E9.
        ("nfd_combining", "e\u0301"),
    ]
]

RANKFUSION_PIPELINE_ACCEPTANCE_TESTS = (
    RANKFUSION_PIPELINE_NAME_ACCEPTED_TESTS
    + RANKFUSION_PIPELINE_COUNT_TESTS
    + RANKFUSION_MULTI_STAGE_PIPELINE_TESTS
    + RANKFUSION_PIPELINE_NAME_ECHO_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_PIPELINE_ACCEPTANCE_TESTS))
def test_rankFusion_pipeline_acceptance(collection, test_case: StageTestCase):
    """Test accepted $rankFusion input pipeline declarations: names and counts."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
