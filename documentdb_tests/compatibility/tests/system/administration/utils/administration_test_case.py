from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AdministrationTestCase(BaseTestCase):
    """Test case for administration command tests.

    Administration commands often require runtime-discovered values (e.g. a
    valid cluster parameter name). Fields that need these values accept a
    callable that receives the discovered value at execution time.

    Attributes:
        setup: Commands to run before the test command to establish state.
        command: A callable ``(param: str) -> dict`` for commands that need a
            runtime-discovered value, or a plain dict.
        checks: Mapping of dotted field paths to property check objects, or a
            callable that receives the same runtime values as ``build_command``
            and returns such a mapping.
    """

    setup: List[Dict[str, Any]] = field(default_factory=list)
    command: Optional[Dict[str, Any] | Callable[..., Dict[str, Any]]] = None
    checks: Dict[str, Any] | Callable[..., Dict[str, Any]] = field(default_factory=dict)

    def build_command(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Resolve the command dict from a callable or plain dict.

        Pass any runtime-discovered values as positional or keyword arguments;
        they are forwarded to the callable unchanged.
        """
        if self.command is None:
            raise ValueError(f"AdministrationTestCase '{self.id}' has no command defined")
        if callable(self.command):
            return self.command(*args, **kwargs)
        return self.command

    def build_checks(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Resolve the checks dict from a callable or plain dict.

        Pass the same runtime-discovered values used for ``build_command``.
        """
        if callable(self.checks):
            return self.checks(*args, **kwargs)
        return self.checks
