"""PyVista diagnostics for generated geology fields."""

from collections import defaultdict

import numpy as np
import pyvista as pv

from src.worldgen.model import GeneratedWorld


def _dual_polydata(world: GeneratedWorld) -> pv.PolyData:
    mesh = world.mesh
    counts = [len(face) for face in mesh.dual_faces]
    cells = np.empty(sum(count + 1 for count in counts), dtype=np.int64)
    offset = 0
    for face in mesh.dual_faces:
        cells[offset] = len(face)
        cells[offset + 1 : offset + 1 + len(face)] = face
        offset += 1 + len(face)
    return pv.PolyData(mesh.dual_vertices, cells)


def _dual_edge_lines(world: GeneratedWorld) -> np.ndarray:
    edge_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    for face_index, face in enumerate(world.mesh.faces):
        for index in range(3):
            left = int(face[index])
            right = int(face[(index + 1) % 3])
            edge_faces[(min(left, right), max(left, right))].append(face_index)
    segments: list[np.ndarray] = []
    dual_vertices = world.mesh.dual_vertices
    for edge_index in world.geology.boundary_edge_indices:
        left, right = world.mesh.edges[edge_index]
        faces = edge_faces[(int(left), int(right))]
        segments.extend((dual_vertices[faces[0]], dual_vertices[faces[1]]))
    return np.asarray(segments)


def render_geology(
    world: GeneratedWorld,
    *,
    layer: str = "plates",
    arrow_scale: float = 0.08,
    off_screen: bool = False,
    screenshot: str | None = None,
) -> None:
    """Display or save one generated geology diagnostic layer."""
    plotter = pv.Plotter(off_screen=off_screen)
    polydata = _dual_polydata(world)
    geology = world.geology
    interaction_layers = {
        "convergence": geology.boundary_convergence,
        "divergence": geology.boundary_divergence,
        "shear": geology.boundary_shear,
    }
    if layer in interaction_layers:
        plotter.add_mesh(polydata, color="lightgray", show_edges=False)
        points = _dual_edge_lines(world)
        segments = np.arange(len(points), dtype=np.int64).reshape(-1, 2)
        connectivity = np.column_stack(
            (np.full(len(segments), 2, dtype=np.int64), segments)
        ).ravel()
        boundaries = pv.PolyData(points, lines=connectivity)
        boundaries.cell_data[layer] = interaction_layers[layer]
        maximum = max(values.max() for values in interaction_layers.values())
        plotter.add_mesh(
            boundaries,
            scalars=layer,
            cmap="inferno",
            clim=(0.0, maximum),
            line_width=5,
            scalar_bar_args={"title": f"{layer} (rotation units)"},
        )
    elif layer == "plates":
        polydata.cell_data["plate_id"] = geology.plate_ids
        plotter.add_mesh(polydata, scalars="plate_id", cmap="tab10", show_edges=True)
    elif layer == "intensity":
        polydata.cell_data["magma_intensity"] = geology.magma_intensity
        plotter.add_mesh(
            polydata,
            scalars="magma_intensity",
            cmap="viridis",
            show_edges=True,
        )
    elif layer in ("magma", "velocity"):
        vectors = geology.magma_velocity if layer == "magma" else geology.plate_velocity
        polydata.cell_data["magnitude"] = np.linalg.norm(vectors, axis=1)
        plotter.add_mesh(polydata, scalars="magnitude", cmap="viridis", show_edges=True)
        plotter.add_arrows(
            cent=world.mesh.vertices,
            direction=vectors,
            mag=arrow_scale,
            color="white",
        )
    else:
        raise KeyError(layer)

    lines = _dual_edge_lines(world)
    if len(lines) > 0 and layer not in interaction_layers:
        plotter.add_lines(lines, color="black", width=4)
    if screenshot is None:
        plotter.show()
    else:
        plotter.show(screenshot=screenshot)
    plotter.close()
