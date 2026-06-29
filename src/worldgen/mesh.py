import numpy as np
from icosphere import icosphere
from src.core.model.worldgen.tile import Tile


class Mesh:
    def __init__(self, subdivisions: int):
        self.subdivisions: int = subdivisions
        self.tiles: dict[int, Tile] = {}

    def generate(self):
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

    print("Mesh generated successfully.\n")
