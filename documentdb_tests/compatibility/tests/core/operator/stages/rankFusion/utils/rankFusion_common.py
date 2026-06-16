"""Shared scoring helpers for $rankFusion stage tests."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

# Reciprocal Rank Fusion: each pipeline contributes weight / (RANK_CONSTANT + rank),
# where rank is the document's 1-based position in that pipeline's output and
# RANK_CONSTANT is the server's fixed default. The stage sums one term per pipeline.
RANK_CONSTANT = 60


def rrf_score(*ranks: int, weights: Sequence[float] | None = None) -> object:
    """Expected $rankFusion score for a document.

    Each positional argument is the document's 1-based rank in one pipeline.
    ``weights`` is an optional sequence aligned with ``ranks`` (defaults to 1
    per pipeline), mirroring the stage's own ``combination.weights`` field.

    Returns a pytest.approx wrapper so call sites compare with float tolerance.
    """
    if weights is None:
        weights = [1] * len(ranks)
    if len(weights) != len(ranks):
        raise ValueError("weights must align one-to-one with ranks")
    total = sum(w / (RANK_CONSTANT + r) for r, w in zip(ranks, weights))
    return pytest.approx(total)
