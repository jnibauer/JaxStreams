"""Tests for `galax.potential._potential.frame` package."""

from dataclasses import replace

import jax.numpy as jnp
from quax import quaxify

import array_api_jax_compat as xp
from jax_quantity import Quantity

import galax.coordinates.operators as gco
import galax.potential as gp

array_equal = quaxify(jnp.array_equal)


def test_bar_means_of_rotation() -> None:
    """Test the equivalence of hard-coded vs operator means of rotation."""
    base_pot = gp.BarPotential(
        m=Quantity(1e9, "Msun"),
        a=Quantity(5, "kpc"),
        b=Quantity(0.1, "kpc"),
        c=Quantity(0.1, "kpc"),
        Omega=Quantity(0, "Hz"),
        units="galactic",
    )

    Omega_z_freq = Quantity(220, "1/Myr")
    Omega_z_angv = xp.multiply(Omega_z_freq, Quantity(1, "rad"))

    # Hard-coded means of rotation
    hardpot = replace(base_pot, Omega=Omega_z_freq)

    # Operator means of rotation
    op = gco.ConstantRotationZOperator(Omega_z=Omega_z_angv)
    framedpot = gp.PotentialFrame(base_pot, op)

    # They should be equivalent at t=0
    q = Quantity([5, 0, 0], "kpc")
    t = Quantity(0, "Myr")
    assert framedpot.potential_energy(q, t) == hardpot.potential_energy(q, t)
    assert array_equal(framedpot.acceleration(q, t), hardpot.acceleration(q, t))

    # They should be equivalent at t=110 Myr (1/2 period)
    t = Quantity(110, "Myr")
    assert framedpot.potential_energy(q, t) == hardpot.potential_energy(q, t)
    assert array_equal(framedpot.acceleration(q, t), hardpot.acceleration(q, t))

    # They should be equivalent at t=220 Myr (1 period)
    t = Quantity(220, "Myr")
    assert framedpot.potential_energy(q, t) == hardpot.potential_energy(q, t)
    assert array_equal(framedpot.acceleration(q, t), hardpot.acceleration(q, t))

    # They should be equivalent at t=55 Myr (1/4 period)
    t = Quantity(55, "Myr")
    assert framedpot.potential_energy(q, t) == hardpot.potential_energy(q, t)
    assert array_equal(framedpot.acceleration(q, t), hardpot.acceleration(q, t))
