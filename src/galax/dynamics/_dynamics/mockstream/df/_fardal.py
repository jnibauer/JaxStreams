"""galax: Galactic Dynamix in Jax."""

__all__ = ["FardalStreamDF"]


from functools import partial
from typing import final

import jax
import jax.numpy as jnp
import quax.examples.prng as jr
from jax import grad

import quaxed.array_api as xp

import galax.typing as gt
from ._base import AbstractStreamDF
from galax.potential import AbstractPotentialBase
from galax.potential._potential.base import AbstractPotentialBase


@final
class FardalStreamDF(AbstractStreamDF):
    """Fardal Stream Distribution Function.

    A class for representing the Fardal+2015 distribution function for
    generating stellar streams based on Fardal et al. 2015
    https://ui.adsabs.harvard.edu/abs/2015MNRAS.452..301F/abstract
    """

    @partial(jax.jit, static_argnums=(0,))
    def _sample(
        self,
        rng: jr.PRNG,
        potential: AbstractPotentialBase,
        x: gt.Vec3,
        v: gt.Vec3,
        prog_mass: gt.FloatQScalar,
        t: gt.FloatQScalar,
    ) -> tuple[gt.Vec3, gt.Vec3, gt.Vec3, gt.Vec3]:
        """Generate stream particle initial conditions."""
        # Random number generation
        rng1, rng2, rng3, rng4 = rng.split(4)

        # ---------------------------

        mprog = prog_mass.to_value(potential.units["mass"])

        omega_val = orbital_angular_velocity_mag(x, v)

        r = xp.linalg.vector_norm(x)
        r_hat = x / r
        r_tidal = tidal_radius(potential, x, v, mprog, t)
        rel_v = omega_val * r_tidal  # relative velocity

        # circlar_velocity
        v_circ = rel_v

        L_vec = jnp.cross(x, v)
        z_hat = L_vec / xp.linalg.vector_norm(L_vec)

        phi_vec = v - xp.sum(v * r_hat) * r_hat
        phi_hat = phi_vec / xp.linalg.vector_norm(phi_vec)

        kr_bar = 2.0
        kvphi_bar = 0.3

        kz_bar = 0.0
        kvz_bar = 0.0

        sigma_kr = 0.5
        sigma_kvphi = 0.5
        sigma_kz = 0.5
        sigma_kvz = 0.5

        kr_samp = kr_bar + jr.normal(rng1, shape=(1,)) * sigma_kr
        kvphi_samp = kr_samp * (kvphi_bar + jr.normal(rng2, shape=(1,)) * sigma_kvphi)
        kz_samp = kz_bar + jr.normal(rng3, shape=(1,)) * sigma_kz
        kvz_samp = kvz_bar + jr.normal(rng4, shape=(1,)) * sigma_kvz

        # Trailing arm
        x_trail = (
            x + (kr_samp * r_hat * (r_tidal)) + (z_hat * kz_samp * (r_tidal / 1.0))
        )
        v_trail = (
            v
            + (0.0 + kvphi_samp * v_circ * (1.0)) * phi_hat
            + (kvz_samp * v_circ * (1.0)) * z_hat
        )

        # Leading arm
        x_lead = (
            x + (kr_samp * r_hat * (-r_tidal)) + (z_hat * kz_samp * (-r_tidal / 1.0))
        )
        v_lead = (
            v
            + (0.0 + kvphi_samp * v_circ * (-1.0)) * phi_hat
            + (kvz_samp * v_circ * (-1.0)) * z_hat
        )

        return x_lead, x_trail, v_lead, v_trail


#####################################################################
# TODO: move this to a more general location.


@partial(jax.jit)
def dphidr(potential: AbstractPotentialBase, x: gt.Vec3, t: gt.FloatScalar) -> gt.Vec3:
    """Compute the derivative of the potential at a position x.

    Parameters
    ----------
    potential: AbstractPotentialBase
        The gravitational potential.
    x: Array[Any, (3,)]
        3d position (x, y, z) in [kpc]
    t: Numeric
        Time in [Myr]

    Returns
    -------
    Array:
        Derivative of potential in [1/Myr]
    """
    r_hat = x / xp.linalg.vector_norm(x)
    return xp.sum(potential.gradient(x, t) * r_hat)


@partial(jax.jit)
def d2phidr2(
    potential: AbstractPotentialBase, x: gt.Vec3, /, t: gt.RealScalarLike
) -> gt.FloatScalar:
    """Compute the second derivative of the potential.

    At a position x (in the simulation frame).

    Parameters
    ----------
    potential: AbstractPotentialBase
        The gravitational potential.
    x: Array[Any, (3,)]
        3d position (x, y, z) in [kpc]
    t: Numeric
        Time in [Myr]

    Returns
    -------
    Array:
        Second derivative of force (per unit mass) in [1/Myr^2]

    Examples
    --------
    >>> from unxt import Quantity
    >>> from galax.potential import NFWPotential
    >>> pot = NFWPotential(m=1e12, r_s=20.0, units="galactic")
    >>> d2phidr2(pot, xp.asarray([8.0, 0.0, 0.0]), t=0)
    Array(-0.0001747, dtype=float64)
    """
    r_hat = x / xp.linalg.vector_norm(x)

    def dphi_dr_func(x: gt.Vec3) -> gt.FloatScalar:
        return xp.sum(potential.gradient(x, t).value * r_hat)

    return xp.sum(grad(dphi_dr_func)(x) * r_hat)


@partial(jax.jit)
def orbital_angular_velocity(x: gt.Vec3, v: gt.Vec3, /) -> gt.Vec3:
    """Compute the orbital angular velocity about the origin.

    Arguments:
    ---------
    x: Array[Any, (3,)]
        3d position (x, y, z) in [length]
    v: Array[Any, (3,)]
        3d velocity (v_x, v_y, v_z) in [length/time]

    Returns
    -------
    Array
        Angular velocity in [rad/time]

    Examples
    --------
    >>> x = xp.asarray([8.0, 0.0, 0.0])
    >>> v = xp.asarray([8.0, 0.0, 0.0])
    >>> orbital_angular_velocity(x, v)
    Array([0., 0., 0.], dtype=float64)
    """
    r = xp.linalg.vector_norm(x)
    return jnp.cross(x, v) / r**2


@partial(jax.jit)
def orbital_angular_velocity_mag(x: gt.Vec3, v: gt.Vec3, /) -> gt.FloatScalar:
    """Compute the magnitude of the angular momentum in the simulation frame.

    Arguments:
    ---------
    x: Array[Any, (3,)]
        3d position (x, y, z) in [kpc]
    v: Array[Any, (3,)]
        3d velocity (v_x, v_y, v_z) in [kpc/Myr]

    Returns
    -------
    Array
        Magnitude of angular momentum in [rad/Myr]

    Examples
    --------
    >>> x = xp.asarray([8.0, 0.0, 0.0])
    >>> v = xp.asarray([8.0, 0.0, 0.0])
    >>> orbital_angular_velocity_mag(x, v)
    Array(0., dtype=float64)
    """
    return xp.linalg.vector_norm(orbital_angular_velocity(x, v))


@partial(jax.jit)
def tidal_radius(
    potential: AbstractPotentialBase,
    x: gt.Vec3,
    v: gt.Vec3,
    /,
    prog_mass: gt.FloatScalar,
    t: gt.RealScalarLike,
) -> gt.FloatScalar:
    """Compute the tidal radius of a cluster in the potential.

    Parameters
    ----------
    potential: AbstractPotentialBase
        The gravitational potential of the host.
    x: Array[float, (3,)]
        3d position (x, y, z) in [kpc]
    v: Array[float, (3,)]
        3d velocity (v_x, v_y, v_z) in [kpc/Myr]
    prog_mass : Array[float, ()]
        Cluster mass in [Msol]
    t: Array[float | int, ()] | float | int
        Time in [Myr]

    Returns
    -------
    Array[float, ""]] :
        Tidal radius of the cluster in [kpc]

    Examples
    --------
    >>> from galax.potential import NFWPotential
    >>> pot = NFWPotential(m=1e12, r_s=20.0, units="galactic")
    >>> x=xp.asarray([8.0, 0.0, 0.0])
    >>> v=xp.asarray([8.0, 0.0, 0.0])
    >>> tidal_radius(pot, x, v, prog_mass=1e4, t=0)
    Array(0.06362008, dtype=float64)
    """
    return (
        potential.constants["G"].value
        * prog_mass
        / (orbital_angular_velocity_mag(x, v) ** 2 - d2phidr2(potential, x, t))
    ) ** (1.0 / 3.0)


@partial(jax.jit)
def lagrange_points(
    potential: AbstractPotentialBase,
    x: gt.Vec3,
    v: gt.Vec3,
    prog_mass: gt.FloatScalar,
    t: gt.FloatScalar,
) -> tuple[gt.Vec3, gt.Vec3]:
    """Compute the lagrange points of a cluster in a host potential.

    Parameters
    ----------
    potential: AbstractPotentialBase
        The gravitational potential of the host.
    x: Array
        3d position (x, y, z)
    v: Array
        3d velocity (v_x, v_y, v_z)
    prog_mass: Array
        Cluster mass.
    t: Array
        Time.
    """
    r_t = tidal_radius(potential, x, v, prog_mass, t)
    r_hat = x / xp.linalg.vector_norm(x)
    L_1 = x - r_hat * r_t  # close
    L_2 = x + r_hat * r_t  # far
    return L_1, L_2