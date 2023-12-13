from collections import OrderedDict
from types import MappingProxyType

import pytest

from galax.utils import ImmutableDict


class TestImmutableDict:
    @pytest.fixture(scope="class")
    def d(self):
        return ImmutableDict(a=1, b=2)

    @pytest.mark.parametrize(
        ("arg", "kwargs"),
        [
            ((), {}),
            ({"a": 1, "b": 2}, {}),
            ([("a", 1), ("b", 2)], {}),
            ((("a", 1), ("b", 2)), {}),
        ],
    )
    def test_init(self, arg, kwargs):
        """Test initialization.

        Should be able to initialize with all the same input types as a regular
        dictionary.
        """
        d = ImmutableDict(arg, **kwargs)
        assert isinstance(d, ImmutableDict)
        assert d._data == dict(arg, **kwargs)

    def test_getitem(self, d):
        """Test `__getitem__`."""
        assert d["a"] == 1
        assert d["b"] == 2

    def test_iter(self, d):
        """Test `__iter__`."""
        assert list(d) == ["a", "b"]

    def test_len(self, d):
        """Test `__len__`."""
        assert len(d) == 2

    def test_hash(self, d):
        """Test `__hash__`."""
        assert hash(d) == hash(tuple(d.items()))

        # Not hashable if values aren't hashable.
        d = ImmutableDict(a=1, b={"c"})
        with pytest.raises(TypeError, match="unhashable type: 'set'"):
            hash(d)

    def test_keys(self, d):
        """Test `keys`."""
        assert list(d.keys()) == ["a", "b"]

    def test_values(self, d):
        """Test `values`."""
        assert list(d.values()) == [1, 2]

    def test_items(self, d):
        """Test `items`."""
        assert list(d.items()) == [("a", 1), ("b", 2)]

    def test_repr(self, d):
        """Test `__repr__`."""
        assert repr(d) == "ImmutableDict({'a': 1, 'b': 2})"

    def test_or(self, d):
        """Test `__or__`."""
        assert d | ImmutableDict(c=3) == ImmutableDict(a=1, b=2, c=3)
        assert d | {"c": 3} == ImmutableDict(a=1, b=2, c=3)
        assert d | OrderedDict([("c", 3)]) == ImmutableDict(a=1, b=2, c=3)
        assert d | MappingProxyType({"c": 3}) == ImmutableDict(a=1, b=2, c=3)

    def test_ror(self, d):
        """Test `__ror__`."""
        # Reverse order
        assert {"c": 3} | d == {"c": 3, "a": 1, "b": 2}
        assert OrderedDict([("c", 3)]) | d == OrderedDict(
            [("c", 3), ("a", 1), ("b", 2)]
        )

    # === Test pytree methods ===

    def test_tree_flatten(self, d):
        """Test `tree_flatten`."""
        assert d.tree_flatten() == ((1, 2), ("a", "b"))

    def test_tree_unflatten(self, d):
        """Test `tree_unflatten`."""
        d1 = ImmutableDict.tree_unflatten(("a", "b"), (1, 2))
        assert d1 == ImmutableDict(a=1, b=2)

        # round-trip
        d = ImmutableDict(a=1, b=2)
        flattened = d.tree_flatten()
        d2 = ImmutableDict.tree_unflatten(flattened[1], flattened[0])
        assert d2 == d
