"""Shared infrastructure for $set / $addFields tests."""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.addFields.utils.operator_addFields import (  # noqa: E501
    ADD_FIELDS_OPERATOR,
)

STAGE_NAMES = [
    pytest.param("$set", id="set"),
    ADD_FIELDS_OPERATOR,
]


def replace_stage_name(
    pipeline: list[dict[str, Any]] | None, stage_name: str
) -> list[dict[str, Any]]:
    """Swap $set for the given stage name so tests run against both aliases."""
    assert pipeline is not None, "test case must define a pipeline"
    result = []
    for stage in pipeline:
        if "$set" in stage:
            stage_content = stage["$set"]
            result.append({stage_name: stage_content})
        else:
            result.append(stage)
    return result
