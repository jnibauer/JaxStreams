"""galax: Galactic Dynamix in Jax."""

__all__ = ["AbstractPhaseSpacePositionBase"]

from abc import abstractmethod
from functools import partial
from typing import TYPE_CHECKING, Any

import array_api_jax_compat as xp
import equinox as eqx
import jax
from jaxtyping import Shaped
from plum import convert

from jax_quantity import Quantity
from vector import (
    Abstract3DVector,
    Abstract3DVectorDifferential,
    Cartesian3DVector,
    CartesianDifferential3D,
)

from galax.typing import BatchQVec3, BatchVec6
from galax.units import UnitSystem

if TYPE_CHECKING:
    from typing import Self


class AbstractPhaseSpacePositionBase(eqx.Module, strict=True):  # type: ignore[call-arg, misc]
    """Abstract base class for all the types of phase-space positions.

    Parameters
    ----------
    q : :class:`~vector.Abstract3DVector`
        Positions.
    p : :class:`~vector.Abstract3DVectorDifferential`
        Conjugate momenta at positions ``q``.

    See Also
    --------
    :class:`~galax.coordinates.AbstractPhaseSpacePosition`
    :class:`~galax.coordinates.AbstractPhaseSpaceTimePosition`
    """

    q: eqx.AbstractVar[Abstract3DVector]
    """Positions."""

    p: eqx.AbstractVar[Abstract3DVectorDifferential]
    """Conjugate momenta at positions ``q``."""

    # ==========================================================================
    # Array properties

    @property
    @abstractmethod
    def _shape_tuple(self) -> tuple[tuple[int, ...], tuple[int, ...]]:
        """Batch, component shape."""
        raise NotImplementedError

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the position and velocity arrays."""
        return self._shape_tuple[0]

    @property
    def ndim(self) -> int:
        """Number of dimensions, not including component shape."""
        return len(self.shape)

    def __len__(self) -> int:
        """Return the number of particles."""
        return self.shape[0]

    @abstractmethod
    def __getitem__(self, index: Any) -> "Self":
        ...

    # ==========================================================================

    @property
    def full_shape(self) -> tuple[int, ...]:
        """Shape of the position and velocity arrays."""
        batch_shape, component_shapes = self._shape_tuple
        return (*batch_shape, sum(component_shapes))

    # ==========================================================================
    # Convenience methods

    def w(self, *, units: UnitSystem) -> BatchVec6:
        """Phase-space position as an Array[float, (*batch, Q + P)].

        This is the full phase-space position, not including the time.

        Parameters
        ----------
        units : `galax.units.UnitSystem`, optional keyword-only
            The unit system If ``None``, use the current unit system.

        Returns
        -------
        w : Array[float, (*batch, Q + P)]
            The phase-space position as a 6-vector in Cartesian coordinates.
        """
        batch_shape, comp_shapes = self._shape_tuple
        q = xp.broadcast_to(convert(self.q, Quantity), (*batch_shape, comp_shapes[0]))
        p = xp.broadcast_to(
            convert(self.p.represent_as(CartesianDifferential3D, self.q), Quantity),
            (*batch_shape, comp_shapes[1]),
        )
        return xp.concat((q.decompose(units).value, p.decompose(units).value), axis=-1)

    # ==========================================================================
    # Dynamical quantities

    # TODO: property?
    @partial(jax.jit)
    def kinetic_energy(self) -> Shaped[Quantity["specific energy"], "*batch"]:
        r"""Return the specific kinetic energy.

        .. math::

            E_K = \frac{1}{2} \\, |\boldsymbol{v}|^2

        Returns
        -------
        E : Array[float, (*batch,)]
            The kinetic energy.
        """
        # TODO: use a ``norm`` function so that this works for non-Cartesian.
        return 0.5 * self.p.norm(self.q) ** 2

    # TODO: property?
    @partial(jax.jit)
    def angular_momentum(self) -> BatchQVec3:
        r"""Compute the angular momentum.

        .. math::

            \boldsymbol{{L}} = \boldsymbol{{q}} \times \boldsymbol{{p}}

        See :ref:`shape-conventions` for more information about the shapes of
        input and output objects.

        Returns
        -------
        L : Array[float, (*batch,3)]
            Array of angular momentum vectors in Cartesian coordinates.

        Examples
        --------
        We assume the following imports

        >>> from jax_quantity import Quantity
        >>> from galax.coordinates import PhaseSpacePosition

        We can compute the angular momentum of a single object

        >>> pos = Quantity([1., 0, 0], "au")
        >>> vel = Quantity([0, 2., 0], "au/yr")
        >>> w = PhaseSpacePosition(pos, vel)
        >>> w.angular_momentum()
        Quantity['diffusivity'](Array([0., 0., 2.], dtype=float64), unit='AU2 / yr')
        """
        # TODO: keep as a vector.
        #       https://github.com/GalacticDynamics/vector/issues/27
        q = convert(self.q, Quantity)
        p = convert(self.p.represent_as(CartesianDifferential3D, self.q), Quantity)
        return xp.linalg.cross(q, p)


# =============================================================================
# helper functions


def _q_converter(x: Any) -> Abstract3DVector:
    """Convert input to a 3D vector."""
    return x if isinstance(x, Abstract3DVector) else Cartesian3DVector.constructor(x)


def _p_converter(x: Any) -> Abstract3DVectorDifferential:
    """Convert input to a 3D vector differential."""
    return (
        x
        if isinstance(x, Abstract3DVectorDifferential)
        else CartesianDifferential3D.constructor(x)
    )