from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

import pytest
from plum import convert
from typing_extensions import override

import quaxed.numpy as qnp
from unxt import Quantity
from unxt.unitsystems import galactic

import galax.typing as gt
from ...test_composite import AbstractCompositePotential_Test
from galax.potential import MilkyWayPotential2022

if TYPE_CHECKING:
    from galax.potential import AbstractPotentialBase


##############################################################################


class TestMilkyWayPotential2022(AbstractCompositePotential_Test):
    """Test the `galax.potential.MilkyWayPotential2022` class."""

    @pytest.fixture(scope="class")
    def pot_cls(self) -> type[MilkyWayPotential2022]:
        return MilkyWayPotential2022

    @pytest.fixture(scope="class")
    def pot_map(
        self, pot_cls: type[MilkyWayPotential2022]
    ) -> dict[str, dict[str, Quantity]]:
        """Composite potential."""
        return {
            "disk": pot_cls._default_disk,
            "halo": pot_cls._default_halo,
            "bulge": pot_cls._default_bulge,
            "nucleus": pot_cls._default_nucleus,
        }

    @pytest.fixture(scope="class")
    def pot_map_unitless(self, pot_map) -> Mapping[str, AbstractPotentialBase]:
        """Composite potential."""
        return {k: {kk: vv.value for kk, vv in v.items()} for k, v in pot_map.items()}

    # ==========================================================================

    @override
    def test_init_units_from_args(
        self,
        pot_cls: type[MilkyWayPotential2022],
        pot_map: Mapping[str, AbstractPotentialBase],
    ) -> None:
        """Test unit system from None."""
        pot = pot_cls(**pot_map, units=None)
        assert pot.units == galactic

    # ==========================================================================

    def test_potential(self, pot: MilkyWayPotential2022, x: gt.QVec3) -> None:
        """Test the :meth:`MilkyWayPotential2022.potential` method."""
        expect = Quantity(-0.1906119, pot.units["specific energy"])
        assert qnp.isclose(
            pot.potential(x, t=0), expect, atol=Quantity(1e-8, expect.unit)
        )

    def test_gradient(self, pot: MilkyWayPotential2022, x: gt.QVec3) -> None:
        """Test the :meth:`MilkyWayPotential2022.gradient` method."""
        expect = Quantity(
            [0.00235500422114, 0.00471000844229, 0.0101667940117],
            pot.units["acceleration"],
        )
        got = convert(pot.gradient(x, t=0), Quantity)
        assert qnp.allclose(got, expect, atol=Quantity(1e-8, expect.unit))

    def test_density(self, pot: MilkyWayPotential2022, x: gt.QVec3) -> None:
        """Test the :meth:`MilkyWayPotential2022.density` method."""
        expect = Quantity(33_807_052.01837142, pot.units["mass density"])
        assert qnp.isclose(
            pot.density(x, t=0), expect, atol=Quantity(1e-8, expect.unit)
        )

    def test_hessian(self, pot: MilkyWayPotential2022, x: gt.QVec3) -> None:
        """Test the :meth:`MilkyWayPotential2022.hessian` method."""
        expect = Quantity(
            [
                [0.0021196, -0.00047082, -0.0008994],
                [-0.00047082, 0.00141337, -0.0017988],
                [-0.0008994, -0.0017988, -0.00162186],
            ],
            "1/Myr2",
        )
        assert qnp.allclose(
            pot.hessian(x, t=0), expect, atol=Quantity(1e-8, expect.unit)
        )

    # ---------------------------------
    # Convenience methods

    def test_tidal_tensor(self, pot: AbstractPotentialBase, x: gt.QVec3) -> None:
        """Test the `AbstractPotentialBase.tidal_tensor` method."""
        expect = Quantity(
            [
                [0.00148256, -0.00047082, -0.0008994],
                [-0.00047082, 0.00077633, -0.0017988],
                [-0.0008994, -0.0017988, -0.00225889],
            ],
            "1/Myr2",
        )
        assert qnp.allclose(
            pot.tidal_tensor(x, t=0), expect, atol=Quantity(1e-8, expect.unit)
        )