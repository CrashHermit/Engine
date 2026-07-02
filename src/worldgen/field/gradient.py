import numpy as np


class Gradient:
    """Gradient sampler over a mesh on the unit sphere.

    Binds the static mesh geometry (positions, adjacency) once, then
    evaluates per-vertex gradients on demand.
    """

    def __init__(
        self,
        positions: np.ndarray,
        neighbors: list[list[int]],
    ) -> None:
        self.positions: np.ndarray = positions
        self.neighbors: list[list[int]] = neighbors

    def at(self, idx: int, scalar: np.ndarray, descending: bool = False) -> np.ndarray:
        """Gradient at a single vertex.

        Args:
            idx: Vertex index.
            scalar: Per-cell scalar values, shape ``(n,)``.
            descending: If True, flip gradient direction (steepest descent).

        Returns:
            Tangent-plane gradient vector, shape ``(3,)``.
        """
        base_val: float = float(scalar[idx])
        pos: np.ndarray = self.positions[idx]

        vx: float = 0.0
        vy: float = 0.0
        vz: float = 0.0

        for nid in self.neighbors[idx]:
            delta: float = float(scalar[nid] - base_val)
            if descending:
                delta = -delta

            nb_pos: np.ndarray = self.positions[nid]
            dx: float = float(nb_pos[0] - pos[0])
            dy: float = float(nb_pos[1] - pos[1])
            dz: float = float(nb_pos[2] - pos[2])

            vx += dx * delta
            vy += dy * delta
            vz += dz * delta

        dot: float = (vx * pos[0]) + (vy * pos[1]) + (vz * pos[2])

        return np.array([
            vx - (dot * pos[0]),
            vy - (dot * pos[1]),
            vz - (dot * pos[2]),
        ])

    def batch(self, scalar: np.ndarray, descending: bool = False) -> np.ndarray:
        """Gradient at every vertex.

        Args:
            scalar: Per-cell scalar values, shape ``(n,)``.
            descending: If True, flip gradient direction (steepest descent).

        Returns:
            Tangent-plane gradient vectors, shape ``(n, 3)``.
        """
        n: int = len(self.positions)
        gradient: np.ndarray = np.zeros((n, 3), dtype=np.float64)

        for i in range(n):
            gradient[i] = self.at(i, scalar=scalar, descending=descending)

        return gradient
