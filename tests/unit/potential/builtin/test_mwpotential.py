from typing import Any

import jax.numpy as jnp
import jax.numpy as xp
import pytest
from jax_quantity import Quantity
from quax import quaxify

from galax.potential import AbstractPotentialBase, MilkyWayPotential
from galax.typing import Vec3
from galax.units import galactic

from ..test_core import TestAbstractPotential

allclose = quaxify(jnp.allclose)


class TestMilkyWayPotentialDefault(TestAbstractPotential):
    """Test the Milky Way potential with default parameters."""

    @pytest.fixture(scope="class")
    def pot_cls(self) -> type[MilkyWayPotential]:
        return MilkyWayPotential

    @pytest.fixture(scope="class")
    def fields_(self, field_units) -> dict[str, Any]:
        return {"units": field_units}

    # ==========================================================================

    def test_init_units_from_args(self, pot_cls, fields_unitless):
        """Test unit system from None."""
        # strip the units from the fields otherwise the test will fail
        # because the units are not equal and we just want to check that
        # when the units aren't specified, the default is dimensionless
        # and a numeric value works.
        fields_unitless.pop("units")
        pot = pot_cls(**fields_unitless, units=None)
        assert pot.units == galactic

    # ==========================================================================

    def test_potential_energy(self, pot: MilkyWayPotential, x: Vec3) -> None:
        assert xp.isclose(pot.potential_energy(x, t=0), xp.array(-0.19386052))

    def test_gradient(self, pot: MilkyWayPotential, x: Vec3) -> None:
        expected = Quantity(
            [0.00256403, 0.00512806, 0.01115272], pot.units["acceleration"]
        )
        assert xp.allclose(pot.gradient(x, t=0).value, expected.value)

    def test_density(self, pot: MilkyWayPotential, x: Vec3) -> None:
        assert xp.isclose(pot.density(x, t=0).value, 33_365_858.46361218)

    def test_hessian(self, pot: MilkyWayPotential, x: Vec3) -> None:
        assert xp.allclose(
            pot.hessian(x, t=0),
            xp.array(
                [
                    [0.00231054, -0.00050698, -0.00101273],
                    [-0.00050698, 0.00155006, -0.00202546],
                    [-0.00101273, -0.00202546, -0.00197444],
                ]
            ),
        )

    # ---------------------------------
    # Convenience methods

    def test_tidal_tensor(self, pot: AbstractPotentialBase, x: Vec3) -> None:
        """Test the `AbstractPotentialBase.tidal_tensor` method."""
        expect = [
            [0.00168182, -0.00050698, -0.00101273],
            [-0.00050698, 0.00092134, -0.00202546],
            [-0.00101273, -0.00202546, -0.00260316],
        ]
        assert allclose(pot.tidal_tensor(x, t=0), xp.asarray(expect))
