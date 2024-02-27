"""galax: Galactic Dynamix in Jax."""

__all__ = ["AbstractPhaseSpaceTimePosition", "PhaseSpaceTimePosition"]

from dataclasses import replace
from functools import partial
from typing import TYPE_CHECKING, Any, final

import array_api_jax_compat as xp
import equinox as eqx
import jax
import jax.numpy as jnp
from jaxtyping import Array, Float
from plum import convert

from jax_quantity import Quantity
from vector import (
    Abstract3DVector,
    Abstract3DVectorDifferential,
    Cartesian3DVector,
)

from .base import AbstractPhaseSpacePositionBase, _p_converter, _q_converter
from .utils import getitem_broadscalartime_index
from galax.typing import BatchFloatQScalar, BatchVec7, BroadBatchFloatScalar, Vec1
from galax.units import UnitSystem, unitsystem
from galax.utils._shape import batched_shape, expand_batch_dims, vector_batched_shape
from galax.utils.dataclasses import converter_float_array

if TYPE_CHECKING:
    from typing import Self

    from galax.potential._potential.base import AbstractPotentialBase


class AbstractPhaseSpaceTimePosition(AbstractPhaseSpacePositionBase):
    r"""Abstract base class of Phase-Space Positions with time.

    The phase-space position is a point in the 7-dimensional phase space
    :math:`\mathbb{R}^7` of a dynamical system. It is composed of the position
    :math:`\boldsymbol{q}`, the conjugate momentum :math:`\boldsymbol{p}`, and
    the time :math:`t`.

    See Also
    --------
    :class:`~galax.coordinates.PhaseSpacePosition`
        A phase-space position without time.
    """

    # TODO: shape Float[Array, "*#batch #time 3"]
    q: eqx.AbstractVar[Abstract3DVector]
    """Positions."""

    # TODO: shape Float[Array, "*#batch #time 3"]
    p: eqx.AbstractVar[Abstract3DVector]
    """Conjugate momenta at positions ``q``."""

    t: eqx.AbstractVar[Float[Array, "*#batch"]]
    """Time corresponding to the positions and momenta."""

    # ==========================================================================
    # Array methods

    def __getitem__(self, index: Any) -> "Self":
        """Return a new object with the given slice applied."""
        # Compute subindex
        subindex = getitem_broadscalartime_index(index, self.t)
        # Apply slice
        return replace(self, q=self.q[index], p=self.p[index], t=self.t[subindex])

    # ==========================================================================
    # Convenience methods

    def wt(self, *, units: UnitSystem) -> BatchVec7:
        """Phase-space position as an Array[float, (*batch, 1+Q+P)].

        This is the full phase-space position, including the time.

        Parameters
        ----------
        units : `galax.units.UnitSystem`, keyword-only
            The unit system If ``None``, use the current unit system.

        Returns
        -------
        wt : Array[float, (*batch, 1+Q+P)]
            The full phase-space position, including time on the first axis.

        Examples
        --------
        We assume the following imports:

        >>> from jax_quantity import Quantity
        >>> from vector import Cartesian3DVector, CartesianDifferential3D
        >>> from galax.coordinates import PhaseSpaceTimePosition
        >>> import galax.units as gu

        We can create a phase-space position:

        >>> psp = PhaseSpaceTimePosition(q=Quantity([1, 2, 3], "m"),
        ...                              p=Quantity([4, 5, 6], "m/s"), t=7.0)
        >>> psp.wt(units=gu.galactic)
        Array([7.00000000e+00, 3.24077929e-20, 6.48155858e-20, 9.72233787e-20,
               4.09084866e-06, 5.11356083e-06, 6.13627299e-06], dtype=float64)
        """
        batch_shape, comp_shapes = self._shape_tuple
        cart = self.represent_as(Cartesian3DVector)
        q = xp.broadcast_to(convert(cart.q, Quantity), (*batch_shape, comp_shapes[0]))
        p = xp.broadcast_to(convert(cart.p, Quantity), (*batch_shape, comp_shapes[1]))
        t = xp.broadcast_to(self.t, batch_shape)[..., None]
        return xp.concat(
            (t, q.decompose(units).value, p.decompose(units).value), axis=-1
        )

    # ==========================================================================
    # Dynamical quantities

    def potential_energy(
        self, potential: "AbstractPotentialBase"
    ) -> Quantity["specific energy"]:
        r"""Return the specific potential energy.

        .. math::

            E_\Phi = \Phi(\boldsymbol{q})

        Parameters
        ----------
        potential : `galax.potential.AbstractPotentialBase`
            The potential object to compute the energy from.

        Returns
        -------
        E : Array[float, (*batch,)]
            The specific potential energy.

        Examples
        --------
        We assume the following imports:

        >>> from jax_quantity import Quantity
        >>> from vector import Cartesian3DVector, CartesianDifferential3D
        >>> from galax.coordinates import PhaseSpaceTimePosition
        >>> from galax.potential import MilkyWayPotential

        We can construct a phase-space position:

        >>> q = Cartesian3DVector(
        ...     x=Quantity(1, "kpc"),
        ...     y=Quantity([[1.0, 2, 3, 4], [1.0, 2, 3, 4]], "kpc"),
        ...     z=Quantity(2, "kpc"))
        >>> p = CartesianDifferential3D(
        ...     d_x=Quantity(0, "km/s"),
        ...     d_y=Quantity([[1.0, 2, 3, 4], [1.0, 2, 3, 4]], "km/s"),
        ...     d_z=Quantity(0, "km/s"))
        >>> w = PhaseSpaceTimePosition(q, p, t=0)

        We can compute the kinetic energy:

        >>> pot = MilkyWayPotential()
        >>> w.potential_energy(pot)
        Quantity['specific energy'](Array(..., dtype=float64), unit='kpc2 / Myr2')
        """
        x = convert(self.q, Quantity).decompose(potential.units).value  # Cartesian
        return potential.potential_energy(x, t=self.t)

    @partial(jax.jit)
    def energy(self, potential: "AbstractPotentialBase") -> BatchFloatQScalar:
        r"""Return the specific total energy.

        .. math::

            E_K = \frac{1}{2} \\, |\boldsymbol{v}|^2
            E_\Phi = \Phi(\boldsymbol{q})
            E = E_K + E_\Phi

        Parameters
        ----------
        potential : `galax.potential.AbstractPotentialBase`
            The potential object to compute the energy from.

        Returns
        -------
        E : Array[float, (*batch,)]
            The kinetic energy.

        Examples
        --------
        We assume the following imports:

        >>> from jax_quantity import Quantity
        >>> from vector import Cartesian3DVector, CartesianDifferential3D
        >>> from galax.coordinates import PhaseSpaceTimePosition
        >>> from galax.potential import MilkyWayPotential

        We can construct a phase-space position:

        >>> q = Cartesian3DVector(
        ...     x=Quantity(1, "kpc"),
        ...     y=Quantity([[1.0, 2, 3, 4], [1.0, 2, 3, 4]], "kpc"),
        ...     z=Quantity(2, "kpc"))
        >>> p = CartesianDifferential3D(
        ...     d_x=Quantity(0, "km/s"),
        ...     d_y=Quantity([[1.0, 2, 3, 4], [1.0, 2, 3, 4]], "km/s"),
        ...     d_z=Quantity(0, "km/s"))
        >>> w = PhaseSpaceTimePosition(q, p, t=0)

        We can compute the kinetic energy:

        >>> pot = MilkyWayPotential()
        >>> w.energy(pot)
        Quantity['specific energy'](Array(..., dtype=float64), unit='km2 / s2')
        """
        return self.kinetic_energy() + self.potential_energy(potential)


###############################################################################


@final
class PhaseSpaceTimePosition(AbstractPhaseSpaceTimePosition):
    r"""Phase-Space Position with time.

    The phase-space position is a point in the 7-dimensional phase space
    :math:`\\mathbb{R}^7` of a dynamical system. It is composed of the position
    :math:`\boldsymbol{q}`, the time :math:`t`, and the conjugate momentum
    :math:`\boldsymbol{p}`.

    Parameters
    ----------
    q : :class:`~vector.Abstract3DVector`
        Positions.
    p : :class:`~vector.Abstract3DVectorDifferential`
        Conjugate momenta at positions ``q``.
    t : Array[float, (*batch,)]
        The time corresponding to the positions.

    Examples
    --------
    We assume the following imports:

    >>> from jax_quantity import Quantity
    >>> from vector import Cartesian3DVector, CartesianDifferential3D
    >>> from galax.coordinates import PhaseSpaceTimePosition

    We can create a phase-space position:

    >>> q = Cartesian3DVector(x=Quantity(1, "m"), y=Quantity(2, "m"),
    ...                       z=Quantity(3, "m"))
    >>> p = CartesianDifferential3D(d_x=Quantity(4, "m/s"), d_y=Quantity(5, "m/s"),
    ...                             d_z=Quantity(6, "m/s"))
    >>> t = 7.0

    >>> psp = PhaseSpaceTimePosition(q=q, p=p, t=t)
    >>> psp
    PhaseSpaceTimePosition(
      q=Cartesian3DVector(
        x=Quantity[PhysicalType('length')](value=f64[], unit=Unit("m")),
        y=Quantity[PhysicalType('length')](value=f64[], unit=Unit("m")),
        z=Quantity[PhysicalType('length')](value=f64[], unit=Unit("m"))
      ),
      p=CartesianDifferential3D(
        d_x=Quantity[PhysicalType({'speed', 'velocity'})](
          value=f64[],
          unit=Unit("m / s")
        ),
        d_y=Quantity[PhysicalType({'speed', 'velocity'})](
          value=f64[],
          unit=Unit("m / s")
        ),
        d_z=Quantity[PhysicalType({'speed', 'velocity'})](
          value=f64[],
          unit=Unit("m / s")
        )
      ),
      t=f64[]
    )
    """

    q: Abstract3DVector = eqx.field(converter=_q_converter)
    """Positions, e.g Cartesian3DVector.

    This is a 3-vector with a batch shape allowing for vector inputs.
    """

    p: Abstract3DVectorDifferential = eqx.field(converter=_p_converter)
    r"""Conjugate momenta, e.g. CartesianDifferential3D.

    This is a 3-vector with a batch shape allowing for vector inputs.
    """

    t: BroadBatchFloatScalar | Vec1 = eqx.field(converter=converter_float_array)
    """The time corresponding to the positions.

    This is a scalar with the same batch shape as the positions and velocities.
    If `t` is a scalar it will be broadcast to the same batch shape as `q` and
    `p`.
    """

    def __post_init__(self) -> None:
        """Post-initialization."""
        # Need to ensure t shape is correct. Can be Vec0.
        if self.t.ndim in (0, 1):
            t = expand_batch_dims(self.t, ndim=self.q.ndim - self.t.ndim)
            object.__setattr__(self, "t", t)

    # ==========================================================================
    # Array properties

    @property
    def _shape_tuple(self) -> tuple[tuple[int, ...], tuple[int, int, int]]:
        """Batch, component shape."""
        qbatch, qshape = vector_batched_shape(self.q)
        pbatch, pshape = vector_batched_shape(self.p)
        tbatch, _ = batched_shape(self.t, expect_ndim=0)
        batch_shape = jnp.broadcast_shapes(qbatch, pbatch, tbatch)
        array_shape = qshape + pshape + (1,)
        return batch_shape, array_shape

    # ==========================================================================
    # Convenience methods

    def wt(self, *, units: Any) -> BatchVec7:
        """Phase-space position as an Array[float, (*batch, 1+Q+P)].

        This is the full phase-space position, including the time.

        Parameters
        ----------
        units : `galax.units.UnitSystem`, optional keyword-only
            The unit system If ``None``, use the current unit system.

        Returns
        -------
        wt : Array[float, (*batch, 1+Q+P)]
            The full phase-space position, including time.

        Examples
        --------
        Assuming the following imports:

        >>> from jax_quantity import Quantity
        >>> from galax.coordinates import PhaseSpaceTimePosition

        We can create a phase-space position and convert it to a 6-vector:

        >>> psp = PhaseSpaceTimePosition(q=Quantity([1, 2, 3], "kpc"),
        ...                              p=Quantity([4, 5, 6], "km/s"),
        ...                              t=7.0)
        >>> psp.wt(units="galactic")
         Array([7.00000000e+00, 1.00000000e+00, 2.00000000e+00, 3.00000000e+00,
                4.09084866e-03, 5.11356083e-03, 6.13627299e-03], dtype=float64)
        """
        usys = unitsystem(units)
        batch_shape, comp_shapes = self._shape_tuple
        cart = self.represent_as(Cartesian3DVector)
        q = xp.broadcast_to(convert(cart.q, Quantity), (*batch_shape, comp_shapes[0]))
        p = xp.broadcast_to(convert(cart.p, Quantity), (*batch_shape, comp_shapes[1]))
        t = xp.broadcast_to(self.t, batch_shape)[..., None]
        return xp.concat((t, q.decompose(usys).value, p.decompose(usys).value), axis=-1)
