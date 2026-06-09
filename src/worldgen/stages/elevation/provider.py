from __future__ import annotations

from typing import Protocol


class ElevationProvider(Protocol):
    """Interface for base-elevation strategies.

    A provider defines only the *macrostructure* of the height field
    (continent placement, broad-scale shape) by answering "what is the raw
    elevation at this point?".  Domain warping, normalisation, and
    redistribution are applied by ``ElevationStage`` around the provider, so
    providers never need to implement those themselves.

    Implementations receive their config and the ``WorldContext`` at
    construction time (so they can pre-place anchors, build noise fields,
    etc.) and expose a single per-point query.
    """

    def elevation_at(self, x: float, y: float) -> float:
        """Return the raw elevation at world coordinate ``(x, y)``.

        The value may be in any range; the caller normalises across all
        cells.  ``(x, y)`` may fall slightly outside ``[0, width)`` after
        domain warping, which periodic providers handle naturally.
        """
        ...
