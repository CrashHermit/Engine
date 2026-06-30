import numpy as np


def compute_surface_gradient(
    positions: np.ndarray,
    neighbors: list[list[int]],
    scalar: np.ndarray,
    descending: bool = False,
) -> np.ndarray:
    """Surface gradient of a scalar field over points on the unit sphere.

    Computes the standard gradient (weighted by scalar difference) then
    projects each vector onto the tangent plane at that point by subtracting
    the radial component: ``g_proj = g - (g · p) * p``.

    Args:
        positions: Per-cell positions, shape ``(n, 3)``.
        neighbors: Adjacency list — ``neighbors[i]`` is the list of
            neighbor indices for cell ``i``.
        scalar: Per-cell scalar values, shape ``(n,)``.
        descending: If True, flip gradient direction (steepest descent).

    Returns:
        Tangent-plane gradient vectors, shape ``(n, 3)``.
    """
    n: int = len(positions)
    gradient: np.ndarray = np.zeros((n, 3), dtype=np.float64)

    for i in range(n):
        base_val: float = float(scalar[i])
        pos: np.ndarray = positions[i]

        vx: float = 0.0
        vy: float = 0.0
        vz: float = 0.0

        for nid in neighbors[i]:
            delta: float = float(scalar[nid] - base_val)
            if descending:
                delta = -delta

            nb_pos: np.ndarray = positions[nid]
            dx: float = float(nb_pos[0] - pos[0])
            dy: float = float(nb_pos[1] - pos[1])
            dz: float = float(nb_pos[2] - pos[2])

            vx += dx * delta
            vy += dy * delta
            vz += dz * delta

        dot: float = (vx * pos[0]) + (vy * pos[1]) + (vz * pos[2])

        gradient[i, 0] = vx - (dot * pos[0])
        gradient[i, 1] = vy - (dot * pos[1])
        gradient[i, 2] = vz - (dot * pos[2])

    return gradient
