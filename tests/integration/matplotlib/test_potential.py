"""Test the `galax.potential` package contents."""

import jax.numpy as jnp
import pytest

from unxt import Quantity

import galax.potential as gp


@pytest.mark.mpl_image_compare(deterministic=True)
def test_kepler_potential_contours():
    """Test plotting Kepler potential contours."""
    pot = gp.KeplerPotential(
        m_tot=Quantity(1e11, "Msun"),
        units="galactic",
    )

    grid = Quantity(jnp.linspace(-7, 7, 64), "kpc")

    fig = pot.plot.potential_contours(grid=(grid, grid, 0), cmap="Blues")

    return fig


@pytest.mark.mpl_image_compare(deterministic=True)
def test_kernel_density_contours():
    """Test plotting kernel density contours."""
    pot = gp.KeplerPotential(
        m_tot=Quantity(1e11, "Msun"),
        units="galactic",
    )

    grid = Quantity(jnp.linspace(-7, 7, 64), "kpc")

    fig = pot.plot.density_contours(grid=(grid, grid, 0), cmap="Blues")

    return fig
