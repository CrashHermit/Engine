import numpy as np


class Mesh:
    def __init__(self, subdivisions: int) -> None:
        self.subdivisions: int = subdivisions
        self.vertex_map: dict[tuple[float, ...], int] = {}
        self.final_vertices: list[np.ndarray] = []

    def _add_vertex(self, vertex: np.ndarray, final_vertices: list[np.ndarray], radius: float) -> int:
        normalized_vertex = vertex / np.linalg.norm(vertex)

        key = tuple(np.round(normalized_vertex, 6))

        if key not in self.vertex_map:
            self.vertex_map[key] = len(self.final_vertices)
            self.final_vertices.append(normalized_vertex * radius)

        vertex_index = self.vertex_map[key]
        
        return vertex_index

    def generate_frequency_icosphere(self, nu: int, radius: float):
        phi = (1.0 + np.sqrt(5.0)) / 2.0

        v0 = [-1, phi, 0]
        v1 = [1, phi, 0]
        v2 = [-1, -phi, 0]
        v3 = [1, -phi, 0]
        v4 = [0, -1, phi]
        v5 = [0, 1, phi]
        v6 = [0, -1, -phi]
        v7 = [0, 1, -phi]
        v8 = [phi, 0, -1]
        v9 = [phi, 0, 1]
        v10 = [-phi, 0, -1]
        v11 = [-phi, 0, 1]

        base_vertices = np.array([v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11])

        f0 = [0, 11, 5]
        f1 = [0, 5, 1]
        f2 = [0, 1, 7]
        f3 = [0, 7, 10]
        f4 = [0, 10, 11]
        f5 = [1, 5, 9]
        f6 = [5, 11, 4]
        f7 = [11, 10, 2]
        f8 = [10, 7, 6]
        f9 = [7, 1, 8]
        f10 = [3, 9, 4]
        f11 = [3, 4, 2]
        f12 = [3, 2, 6]
        f13 = [3, 6, 8]
        f14 = [3, 8, 9]
        f15 = [4, 9, 5]
        f16 = [2, 4, 11]
        f17 = [6, 2, 10]
        f18 = [8, 6, 7]
        f19 = [9, 8, 1]

        base_faces = np.array(
            [
                f0,
                f1,
                f2,
                f3,
                f4,
                f5,
                f6,
                f7,
                f8,
                f9,
                f10,
                f11,
                f12,
                f13,
                f14,
                f15,
                f16,
                f17,
                f18,
                f19,
            ]
        )

        for face in base_faces:
            a = base_vertices[face[0]]
            b = base_vertices[face[1]]
            c = base_vertices[face[2]]

            grid: dict = {}
            for i in range(nu + 1):
                for j in range(nu + 1 - i):
                    k: int = nu - i - j
                    vertex: float = ((i * a) + (j * b) + (k * c)) / nu
                    grid[(i, j)] = self._add_vertex(vertex=vertex)

    def generate(self) -> tuple[np.ndarray, list[list[int]]]:
        print(f"Generating sphere mesh with {self.subdivisions} subdivisions...")

        vertices, faces = icosphere(nu=self.subdivisions)
        num_vertices: int = len(vertices)

        adjacency_sets: list = [set() for _ in range(num_vertices)]

        for face in faces:
            v1, v2, v3 = face

            adjacency_sets[v1].update([v2, v3])
            adjacency_sets[v2].update([v1, v3])
            adjacency_sets[v3].update([v1, v2])

        for i in range(num_vertices):
            x, y, z = vertices[i]

            new_tile: Tile = Tile(
                id=i,
                x=float(x),
                y=float(y),
                z=float(z),
                neighbors=list(int(n) for n in adjacency_sets[i]),
            )

            self.tiles[i] = new_tile

        positions: np.ndarray = np.array(vertices, dtype=np.float64)
        neighbors: list[list[int]] = [
            list(adjacency_sets[i]) for i in range(num_vertices)
        ]

        print("Mesh generated successfully.\n")

        return positions, neighbors
