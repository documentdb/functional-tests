"""Helpers for hidden index property tests."""

from typing import Any, Iterator, List, Optional


def _walk(node: Any) -> Iterator[dict]:
    """Yield every dict node in a nested structure."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def ixscan_index_names(explain_result: dict) -> List[str]:
    """Return index names of all IXSCAN stages in the winning plan."""
    query_planner = explain_result.get("queryPlanner", {})
    winning_plan = query_planner.get("winningPlan", {})
    return [
        node["indexName"]
        for node in _walk(winning_plan)
        if node.get("stage") == "IXSCAN" and "indexName" in node
    ]


def all_plan_index_names(explain_result: dict) -> List[str]:
    """Return index names from the winning plan and rejected plans."""
    query_planner = explain_result.get("queryPlanner", {})
    return [
        node["indexName"]
        for node in _walk(query_planner)
        if node.get("stage") == "IXSCAN" and "indexName" in node
    ]


def all_plans_execution_index_names(explain_result: dict) -> List[str]:
    """Return index names from executionStats.allPlansExecution candidate plans."""
    execution_stats = explain_result.get("executionStats", {})
    all_plans_execution = execution_stats.get("allPlansExecution", [])
    return [
        node["indexName"]
        for candidate in all_plans_execution
        for node in _walk(candidate.get("executionStages", {}))
        if node.get("stage") == "IXSCAN" and "indexName" in node
    ]


def uses_index(explain_result: dict, index_name: Optional[str] = None) -> bool:
    """Return True if the winning plan uses an IXSCAN (optionally a specific one)."""
    names = ixscan_index_names(explain_result)
    if index_name is None:
        return bool(names)
    return index_name in names


def uses_collscan(explain_result: dict) -> bool:
    """Return True if the winning plan contains a COLLSCAN stage."""
    query_planner = explain_result.get("queryPlanner", {})
    winning_plan = query_planner.get("winningPlan", {})
    return any(node.get("stage") == "COLLSCAN" for node in _walk(winning_plan))


def is_covered(explain_result: dict) -> bool:
    """Return True if the winning plan is a covered query (no FETCH)."""
    wp = explain_result.get("queryPlanner", {}).get("winningPlan", {})
    return bool(
        wp.get("stage") == "IXSCAN"
        or (
            wp.get("stage") == "PROJECTION_COVERED"
            and wp.get("inputStage", {}).get("stage") == "IXSCAN"
        )
    )


def get_index_spec(list_indexes_result: dict, index_name: str) -> Optional[Any]:
    """Return the index spec for the given name, or None if not found."""
    if isinstance(list_indexes_result, Exception):
        return None
    for spec in list_indexes_result["cursor"]["firstBatch"]:
        if spec.get("name") == index_name:
            return spec
    return None


def hidden_field(list_indexes_result: dict, index_name: str) -> Any:
    """Return the hidden field value for an index, or "__ABSENT__" if not present."""
    spec = get_index_spec(list_indexes_result, index_name)
    if spec is None:
        return "__NO_SUCH_INDEX__"
    return spec.get("hidden", "__ABSENT__")


def get_index_doc(result, index_name):
    """Extract the $indexStats document for a given index name, or None if not found."""
    for doc in result["cursor"]["firstBatch"]:
        if doc.get("name") == index_name:
            return doc
    return None


def get_index_ops(result, index_name):
    """Extract the accesses.ops value for a given index name, or None if not found."""
    doc = get_index_doc(result, index_name)
    if doc is None:
        return None
    return doc["accesses"]["ops"]
