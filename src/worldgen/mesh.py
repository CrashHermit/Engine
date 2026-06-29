import numpy as np
from icosphere import icosphere
from src.core.model.worldgen.tile import Tile


class Mesh:
    def __init__(self, subdivisions: int):
        self.subdivisions = subdivisions
        self.tiles: dict[int, Tile] = {}

    def generate(self):
        print(f"Generating sphere mesh with {self.subdivisions} subdivisions...")

        vertices, faces = icosphere(nu=self.subdivisions)
        num_vertices = len(vertices)

        adjacency_sets = [set() for _ in range(num_vertices)]

        for face in faces:
            v1, v2, v3 = face

            adjacency_sets[v1].update([v2, v3])
            adjacency_sets[v2].update([v1, v3])
            adjacency_sets[v3].update([v1, v2])

        for i in range(num_vertices):
            x, y, z = vertices[i]

            new_tile = Tile(id=i, x=float(x), y=float(y), z=float(z), neighbors=list(int(n) for n in adjacency_sets[i]))

            self.tiles[i] = new_tile

    print("Mesh generated successfully.\n")


if __name__ == "__main__":
    # Create a world with 4 subdivisions (approx 2,500 tiles)
    world = Mesh(subdivisions=20)
    world.generate()
    
    # Let's verify the math!
    pentagon_count = 0
    hexagon_count = 0
    
    for tile in world.tiles.values():
        num_neighbors = len(tile.neighbors)
        if num_neighbors == 5:
            pentagon_count += 1
        elif num_neighbors == 6:
            hexagon_count += 1
            
    print("--- PLANET TOPOLOGY REPORT ---")
    print(f"Total Tiles: {len(world.tiles)}")
    print(f"Hexagons (6 neighbors): {hexagon_count}")
    print(f"Pentagons (5 neighbors): {pentagon_count}")
    
    if pentagon_count == 12:
        print("SUCCESS: Euler's Polyhedron Formula holds! The planet is perfectly spherical.")
        
    # Let's peek at a single tile
    print("\n--- SAMPLE TILE (Tile #0) ---")
    print(world.tiles[0])
