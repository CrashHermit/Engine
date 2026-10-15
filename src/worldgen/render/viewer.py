"""PyVista diagnostics for generated geology and terrain fields."""

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


LAYERS = (
    "plates",
    "intensity",
    "magma",
    "velocity",
    "convergence",
    "divergence",
    "shear",
    "crust",
    "crust-regions",
    "crust-field",
    "base-elevation",
    "margin-distance",
)


class WorldgenViewer:
    """One generated world with mutually exclusive, clickable display layers."""

    def __init__(
        self,
        world: GeneratedWorld,
        *,
        arrow_scale: float = 0.08,
        off_screen: bool = False,
    ) -> None:
        self.world = world
        self.arrow_scale = arrow_scale
        self.plotter = pv.Plotter(off_screen=off_screen)
        self.polydata = _dual_polydata(world)
        points = _dual_edge_lines(world)
        segments = np.arange(len(points), dtype=np.int64).reshape(-1, 2)
        connectivity = np.column_stack(
            (np.full(len(segments), 2, dtype=np.int64), segments)
        ).ravel()
        self.boundaries = pv.PolyData(points, lines=connectivity)
        self.actors = []
        self.widgets = {}
        self.layer = None

    def select_layer(self, layer: str) -> None:
        """Replace display actors without regenerating data or resetting camera."""
        for actor in self.actors:
            self.plotter.remove_actor(actor, reset_camera=False, render=False)
        self.actors.clear()
        geology = self.world.geology
        crust = geology.crust
        interactions = {
            "convergence": geology.boundary_convergence,
            "divergence": geology.boundary_divergence,
            "shear": geology.boundary_shear,
        }
        if layer in interactions:
            self.actors.append(
                self.plotter.add_mesh(
                    self.polydata,
                    color="lightgray",
                    reset_camera=False,
                )
            )
            self.boundaries.cell_data[layer] = interactions[layer]
            self.actors.append(
                self.plotter.add_mesh(
                    self.boundaries,
                    scalars=layer,
                    cmap="inferno",
                    clim=(0, max(values.max() for values in interactions.values())),
                    line_width=5,
                    reset_camera=False,
                )
            )
        else:
            vectors = None
            clim = None
            if layer == "plates":
                values, cmap = geology.plate_ids, "tab20"
            elif layer == "intensity":
                values, cmap, clim = geology.magma_intensity, "viridis", (0, 1)
            elif layer in ("magma", "velocity"):
                vectors = (
                    geology.magma_velocity
                    if layer == "magma"
                    else geology.plate_velocity
                )
                values, cmap, clim = np.linalg.norm(vectors, axis=1), "viridis", (0, 1)
            elif layer == "crust":
                values = crust.continental_mask.astype(np.int64)
                cmap, clim = ["royalblue", "tan"], (0, 1)
            elif layer == "crust-regions":
                values, cmap = crust.region_ids, "tab20"
            elif layer == "crust-field":
                values, cmap, clim = crust.shaping_field, "viridis", (0, 1)
            elif layer == "base-elevation":
                values, cmap, clim = (
                    self.world.terrain.base_elevation,
                    "terrain",
                    self.world.terrain.elevation_range_m,
                )
            elif layer == "margin-distance":
                values = self.world.terrain.margin_distance
                cmap = "coolwarm"
                extent = np.max(np.abs(values))
                clim = (-extent, extent)
            else:
                raise KeyError(layer)
            self.polydata.cell_data[layer] = values
            self.actors.append(
                self.plotter.add_mesh(
                    self.polydata,
                    scalars=layer,
                    cmap=cmap,
                    clim=clim,
                    show_edges=True,
                    reset_camera=False,
                    scalar_bar_args={
                        "title": "Base elevation (m; sea level 0)"
                        if layer == "base-elevation"
                        else "Margin distance (% circumference; positive continental)"
                        if layer == "margin-distance"
                        else "Crust: 0 oceanic, 1 continental"
                        if layer == "crust"
                        else layer
                    },
                )
            )
            if vectors is not None:
                self.actors.append(
                    self.plotter.add_arrows(
                        self.world.mesh.vertices,
                        vectors,
                        mag=self.arrow_scale,
                        color="white",
                        reset_camera=False,
                    )
                )
            if layer in ("plates", "intensity", "magma", "velocity"):
                self.actors.append(
                    self.plotter.add_mesh(
                        self.boundaries,
                        color="black",
                        line_width=4,
                        reset_camera=False,
                    )
                )
        self.layer = layer
        for name, widget in self.widgets.items():
            widget.GetRepresentation().SetState(name == layer)
        self.plotter.render()

    def add_layer_controls(self) -> None:
        for index, name in enumerate(LAYERS):

            def toggle(enabled, selected=name):
                if enabled:
                    self.select_layer(selected)
                else:
                    self.widgets[selected].GetRepresentation().SetState(
                        self.layer == selected
                    )

            widget = self.plotter.add_checkbox_button_widget(
                toggle,
                value=name == self.layer,
                position=(10, 15 + index * 32),
                size=22,
                color_on="royalblue",
            )
            self.widgets[name] = widget
            self.plotter.add_text(name, position=(40, 15 + index * 32), font_size=10)


def render_geology(
    world: GeneratedWorld,
    *,
    layer: str = "plates",
    arrow_scale: float = 0.08,
    off_screen: bool = False,
    screenshot: str | None = None,
) -> None:
    """Display a selectable world viewer or save the chosen diagnostic layer."""
    viewer = WorldgenViewer(world, arrow_scale=arrow_scale, off_screen=off_screen)
    viewer.select_layer(layer)
    viewer.plotter.reset_camera()
    if not off_screen:
        viewer.add_layer_controls()
    viewer.plotter.show(screenshot=screenshot)
    viewer.plotter.close()
