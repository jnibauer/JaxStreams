from typing import Any

import array_api_jax_compat as xp
import jax.numpy as jnp
import pytest

from galax.potential import HernquistPotential
from galax.typing import Vec3

from ..test_core import TestAbstractPotential as AbstractPotential_Test
from .test_common import MassParameterMixin, ShapeCParameterMixin


class TestHernquistPotential(
    AbstractPotential_Test,
    # Parameters
    MassParameterMixin,
    ShapeCParameterMixin,
):
    @pytest.fixture(scope="class")
    def pot_cls(self) -> type[HernquistPotential]:
        return HernquistPotential

    @pytest.fixture(scope="class")
    def fields_(self, field_m, field_c, field_units) -> dict[str, Any]:
        return {"m": field_m, "c": field_c, "units": field_units}

    # ==========================================================================

    def test_potential_energy(self, pot: HernquistPotential, x: Vec3) -> None:
        assert jnp.isclose(pot.potential_energy(x, t=0), xp.asarray(-0.94871936))

    def test_gradient(self, pot: HernquistPotential, x: Vec3) -> None:
        assert jnp.allclose(
            pot.gradient(x, t=0), xp.asarray([0.05347411, 0.10694822, 0.16042233])
        )

    def test_density(self, pot: HernquistPotential, x: Vec3) -> None:
        assert jnp.isclose(pot.density(x, t=0), 3.989933e08)

    def test_hessian(self, pot: HernquistPotential, x: Vec3) -> None:
        assert jnp.allclose(
            pot.hessian(x, t=0),
            xp.asarray(
                [
                    [0.04362645, -0.01969533, -0.02954299],
                    [-0.01969533, 0.01408345, -0.05908599],
                    [-0.02954299, -0.05908599, -0.03515487],
                ]
            ),
        )
