# Infrastructure exception types that indicate environment issues, not test failures.
# Used by both framework/assertions.py (isinstance checks) and
# result_analyzer/analyzer.py (string name checks in JSON crash info).

INFRA_EXCEPTION_NAMES = {
    # Python built-in
    "ConnectionError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "ConnectionAbortedError",
    "TimeoutError",
    "OSError",
    "socket.timeout",
    "socket.error",
    # PyMongo
    "pymongo.errors.ConnectionFailure",
    "pymongo.errors.ServerSelectionTimeoutError",
    "pymongo.errors.NetworkTimeout",
    "pymongo.errors.AutoReconnect",
    "pymongo.errors.ExecutionTimeout",
}


def _resolve_types():
    """Resolve exception names to actual types for isinstance() checks."""
    import builtins
    types = []
    for name in INFRA_EXCEPTION_NAMES:
        if hasattr(builtins, name):
            types.append(getattr(builtins, name))
        elif "." in name:
            parts = name.rsplit(".", 1)
            try:
                mod = __import__(parts[0], fromlist=[parts[1]])
                types.append(getattr(mod, parts[1]))
            except (ImportError, AttributeError):
                pass
    return tuple(types)


INFRA_EXCEPTION_TYPES = _resolve_types()
