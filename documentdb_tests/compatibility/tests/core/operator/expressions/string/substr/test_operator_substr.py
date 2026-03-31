# $substr is a deprecated alias for $substrBytes. All tests in the $substrBytes
# test file are parametrized over both operator names.
import pytest

SUBSTR_OPERATOR = pytest.param("$substr", id="substr")

__all__ = ["SUBSTR_OPERATOR"]
