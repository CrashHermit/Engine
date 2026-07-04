import numpy as np


class Gradient:
    """Gradient sampler over a mesh on the unit sphere.

    Binds the static mesh geometry once, then evaluates per-vertex
    gradients on demand for static assets or dynamic turns.
    """

    def __init__(
        self,
        positions: np.ndarray,
        neighbors: list[list[int]],
    ) -> None:
        self.positions: np.ndarray = positions
        self.neighbors: list[list[int]] = neighbors
        self.num_vertices: int = len(positions)

        # Pre-compute static geometry data once. This never changes.
        self.source_idx: np.ndarray = np.array(
            [u for u, nbs in enumerate(neighbors) for _ in nbs], dtype=np.intp
        )
        self.target_idx: np.ndarray = np.array(
            [v for nbs in neighbors for v in nbs], dtype=np.intp
        )
        self.edge_deltas: np.ndarray = (
            self.positions[self.target_idx] - self.positions[self.source_idx]
        )

    def generate(self, values: np.ndarray, descending: bool = False) -> np.ndarray:
        """Gradient at every vertex based on the current turn's values.

        Args:
            values: Per-cell scalar values, shape ``(n,)``.
            descending: If True, flip gradient direction (steepest descent).

        Returns:
            Tangent-plane gradient vectors, shape ``(n, 3)``.
        """
        # 1. Calculate scalar differences across all edges using current turn data
        delta: np.ndarray = values[self.target_idx] - values[self.source_idx]
        if descending:
            delta = -delta

        # 2. Multiply pre-cached edge displacements by current scalar weights
        weighted_edges: np.ndarray = self.edge_deltas * delta[:, np.newaxis]

        # 3. Accumulate weighted edges into vx, vy, vz components
        v: np.ndarray = np.zeros((self.num_vertices, 3), dtype=np.float64)
        np.add.at(v, self.source_idx, weighted_edges)

        # 4. Extract component arrays to calculate the batch dot product
        vx: np.ndarray = v[:, 0]
        vy: np.ndarray = v[:, 1]
        vz: np.ndarray = v[:, 2]

        pos_x: np.ndarray = self.positions[:, 0]
        pos_y: np.ndarray = self.positions[:, 1]
        pos_z: np.ndarray = self.positions[:, 2]

        dot: np.ndarray = (vx * pos_x) + (vy * pos_y) + (vz * pos_z)

        # 5. Construct final tangent-plane vectors
        return np.column_stack(
            (
                vx - (dot * pos_x),
                vy - (dot * pos_y),
                vz - (dot * pos_z),
            )
        )
