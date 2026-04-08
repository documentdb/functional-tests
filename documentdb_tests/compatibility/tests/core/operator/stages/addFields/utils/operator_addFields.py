# $addFields is an alias for $set. All tests in the $set test file are
# parametrized over both stage names.
import pytest

ADD_FIELDS_OPERATOR = pytest.param("$addFields", id="addFields")

__all__ = ["ADD_FIELDS_OPERATOR"]
