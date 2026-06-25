"""Shared helpers for getClusterParameter tests.

Cluster parameter values and the exact set of available parameters vary by
deployment, so tests derive a valid parameter name at runtime from the
wildcard form rather than hard-coding one.
"""

from documentdb_tests.framework.executor import execute_admin_command


def all_cluster_parameters(collection):
    """Return the ``clusterParameters`` list from ``getClusterParameter: '*'``.

    Raises the underlying exception if the command did not succeed, so callers
    fail loudly during setup rather than asserting against an error object.
    """
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    if isinstance(result, Exception):
        raise result
    return result["clusterParameters"]


def valid_parameter_names(collection, count=1):
    """Return up to ``count`` valid cluster parameter names for this deployment."""
    params = all_cluster_parameters(collection)
    names = [p["_id"] for p in params]
    if len(names) < count:
        raise AssertionError(
            f"deployment exposes only {len(names)} cluster parameter(s), "
            f"need {count} for this test"
        )
    return names[:count]
