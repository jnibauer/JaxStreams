"""Tests for `galdynamix.potential._potential.utils` package."""

from dataclasses import replace

import astropy.units as u
import pytest

from galdynamix.potential._potential.utils import (
    UnitSystem,
    converter_to_usys,
    dimensionless,
    galactic,
    solarsystem,
)


class TestConverterToUtils:
    """Tests for `galdynamix.potential._potential.utils.converter_to_usys`."""

    def test_invalid(self):
        """Test conversion from unsupported value."""
        with pytest.raises(NotImplementedError):
            converter_to_usys(1234567890)

    def test_from_usys(self):
        """Test conversion from UnitSystem."""
        usys = UnitSystem(u.km, u.s, u.Msun, u.radian)
        assert converter_to_usys(usys) == usys

    def test_from_none(self):
        """Test conversion from None."""
        assert converter_to_usys(None) == dimensionless

    def test_from_args(self):
        """Test conversion from tuple."""
        value = UnitSystem(u.km, u.s, u.Msun, u.radian)
        assert converter_to_usys(value) == value

    def test_from_name(self):
        """Test conversion from named string."""
        assert converter_to_usys("dimensionless") == dimensionless
        assert converter_to_usys("solarsystem") == solarsystem
        assert converter_to_usys("galactic") == galactic

        with pytest.raises(NotImplementedError):
            converter_to_usys("invalid_value")


# ============================================================================


class FieldUnitSystemMixin:
    """Mixin for testing the ``units`` field on a ``Potential``."""

    def test_init_units_invalid(self, pot):
        """Test invalid unit system."""
        msg = "cannot convert 1234567890 to a UnitSystem"
        with pytest.raises(NotImplementedError, match=msg):
            replace(pot, units=1234567890)

    def test_init_units_from_usys(self, pot):
        """Test unit system from UnitSystem."""
        usys = UnitSystem(u.km, u.s, u.Msun, u.radian)
        assert replace(pot, units=usys).units == usys

    def test_init_units_from_args(self, pot):
        """Test unit system from None."""
        assert replace(pot, units=None).units == dimensionless

    def test_init_units_from_tuple(self, pot):
        """Test unit system from tuple."""
        units = (u.km, u.s, u.Msun, u.radian)
        assert replace(pot, units=units).units == UnitSystem(*units)

    def test_init_units_from_name(self, pot):
        """Test unit system from named string."""
        pot = replace(pot, units="dimensionless")
        assert pot.units == dimensionless

        pot = replace(pot, units="solarsystem")
        assert pot.units == solarsystem

        pot = replace(pot, units="galactic")
        assert pot.units == galactic

        msg = "cannot convert invalid_value to a UnitSystem"
        with pytest.raises(NotImplementedError, match=msg):
            replace(pot, units="invalid_value")