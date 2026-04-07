from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class BaseTestCase:
    """Base dataclass for all parametrized test cases.

    Sub-classes must include `@dataclass(frozen=True)`.

    Attributes:
        id: Unique identifier for the test case
        expected: Expected result value (None for error cases)
        error_code: Expected error code (None for success cases)
        msg: Description of expected behavior for assertion messages (required)
    """

    id: str
    expected: Any = None
    error_code: Optional[int] = None
    msg: Optional[str] = None

    def __post_init__(self):
        if self.msg is None:
            raise ValueError(
                f"BaseTestCase '{self.id}' must have a msg describing expected behavior"
            )
