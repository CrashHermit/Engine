"""PyVista diagnostics for generated geology and terrain fields."""

import numpy as np
import pyvista as pv

from src.worldgen.geometry.topology import edge_face_indices
from src.worldgen.model import GeneratedWorld
from src.worldgen.render.layers import LAYERS, layer_style


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
    segments: list[np.ndarray] = []
    dual_vertices = world.mesh.dual_vertices
    incidence = edge_face_indices(world.mesh)
    for edge_index in world.geology.boundary_edge_indices:
        faces = incidence[int(edge_index)]
        segments.extend((dual_vertices[faces[0]], dual_vertices[faces[1]]))
    if not segments:
        return np.empty((0, 3), dtype=np.float64)
    return np.asarray(segments)


class WorldgenViewer:
    """One generated world with mutually exclusive, clickable display layers."""

    def __init__(
        self,
        world: GeneratedWorld,
        *,
        arrow_scale: float = 0.08,
        off_screen: bool = False,
        terrain_relief: bool = False,
        vertical_exaggeration: float = 1.0,
        sea_level: bool = False,
        elevation_range: tuple[float, float] | None = None,
        hex_edges: bool = True,
    ) -> None:
        self.world = world
        self.arrow_scale = arrow_scale
        self.terrain_relief = terrain_relief
        self.vertical_exaggeration = vertical_exaggeration
        self.sea_level = sea_level
        self.elevation_range = elevation_range
        self.hex_edges = hex_edges
        self.plotter = pv.Plotter(off_screen=off_screen)
        self.polydata = _dual_polydata(world)
        self.terrain_polydata = self.polydata.copy(deep=True)
        self._flat_points = self.polydata.points.copy()
        self._relief_points = self._terrain_points(vertical_exaggeration)
        self.terrain_polydata.points = (
            self._relief_points if terrain_relief else self._flat_points
        )
        points = _dual_edge_lines(world)
        segments = np.arange(len(points), dtype=np.int64).reshape(-1, 2)
        connectivity = np.column_stack(
            (np.full(len(segments), 2, dtype=np.int64), segments)
        ).ravel()
        self.boundaries = pv.PolyData(points, lines=connectivity)
        self.actors = []
        self.widgets = {}
        self.layer = None
        self.sea_level_actor = None
        self._sea_level_mesh: pv.PolyData | None = None

    def _terrain_points(self, exaggeration: float) -> np.ndarray:
        mesh = self.world.mesh
        face_elevation = self.world.elevation.elevation[mesh.faces].mean(axis=1)
        radius = 1.0 + face_elevation / self.world.radius_m * exaggeration
        return mesh.dual_vertices * radius[:, np.newaxis]

    def _refresh_terrain_points(self) -> None:
        self._relief_points = self._terrain_points(self.vertical_exaggeration)
        self.terrain_polydata.points = (
            self._relief_points if self.terrain_relief else self._flat_points
        )
        if self.layer is not None:
            self.select_layer(self.layer)

    def set_terrain_relief(self, enabled: bool) -> None:
        """Enable radial displacement on the final elevation layer only."""
        self.terrain_relief = enabled
        self._refresh_terrain_points()

    def set_vertical_exaggeration(self, exaggeration: float) -> None:
        """Set the radial relief multiplier without modifying generated data."""
        self.vertical_exaggeration = exaggeration
        self._refresh_terrain_points()

    def set_sea_level(self, enabled: bool) -> None:
        """Show or hide the unit-radius sea-level shell on displaced terrain."""
        self.sea_level = enabled
        if self.layer is not None:
            self.select_layer(self.layer)

    def set_hex_edges(self, enabled: bool) -> None:
        """Show or hide cell outlines while preserving the selected layer."""
        self.hex_edges = enabled
        if self.layer is not None:
            self.select_layer(self.layer)

    def select_layer(self, layer: str) -> None:
        """Replace display actors without regenerating data or resetting camera."""
        camera_position = self.plotter.camera_position
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
            if len(geology.boundary_edge_indices) == 0:
                self.actors.append(
                    self.plotter.add_mesh(
                        self.polydata,
                        color="lightgray",
                        opacity=1.0,
                        reset_camera=False,
                    )
                )
                self.plotter.add_text("No boundaries", position="upper_left")
            else:
                self.actors.append(
                    self.plotter.add_mesh(
                        self.polydata,
                        color="lightgray",
                        reset_camera=False,
                    )
                )
                values = interactions[layer]
                self.boundaries.cell_data[layer] = values
                self.actors.append(
                    self.plotter.add_mesh(
                        self.boundaries,
                        scalars=layer,
                        cmap="inferno",
                        clim=(0, max(value.max() for value in interactions.values())),
                        line_width=5,
                        reset_camera=False,
                    )
                )
        elif layer in ("boundary-sections", "subducting-plate"):
            sections = geology.boundary_sections
            self.actors.append(
                self.plotter.add_mesh(
                    self.polydata, color="lightgray", reset_camera=False
                )
            )
            if len(sections.edge_section_ids) == 0:
                self.actors.append(
                    self.plotter.add_text("No boundaries", position="upper_left")
                )
            else:
                values = (
                    sections.edge_section_ids
                    if layer == "boundary-sections"
                    else sections.subducting_plate_ids[sections.edge_section_ids]
                )
                self.boundaries.cell_data[layer] = values
                self.actors.append(
                    self.plotter.add_mesh(
                        self.boundaries,
                        scalars=layer,
                        cmap="tab20",
                        categories=True,
                        annotations={-1: "Not subducting"}
                        if layer == "subducting-plate"
                        else None,
                        line_width=5,
                        reset_camera=False,
                        scalar_bar_args={"title": layer, "vertical": True},
                    )
                )
        else:
            style = layer_style(self.world, layer, self.elevation_range)
            values, cmap, clim = style.values, style.cmap, style.clim
            vectors = style.vectors
            terrain_layer = layer == "elevation"
            display_mesh = (
                self.terrain_polydata
                if terrain_layer and self.terrain_relief
                else self.polydata
            )
            display_mesh.cell_data[layer] = values
            if terrain_layer and self.terrain_relief and self.sea_level:
                if self._sea_level_mesh is None:
                    self._sea_level_mesh = pv.Sphere(
                        radius=1.0, theta_resolution=512, phi_resolution=512
                    )
                self.sea_level_actor = self.plotter.add_mesh(
                    self._sea_level_mesh,
                    color="royalblue",
                    opacity=0.35,
                    show_edges=False,
                    reset_camera=False,
                )
                self.actors.append(self.sea_level_actor)
            self.actors.append(
                self.plotter.add_mesh(
                    display_mesh,
                    scalars=layer,
                    cmap=cmap,
                    clim=clim,
                    show_edges=self.hex_edges,
                    reset_camera=False,
                    smooth_shading=True,
                    scalar_bar_args={
                        "title": "Elevation (m; sea level 0)"
                        if layer in ("base-elevation", "elevation")
                        else "Margin distance (% circumference; positive continental)"
                        if layer == "margin-distance"
                        else "Crust: 0 oceanic, 1 continental"
                        if layer == "crust"
                        else layer,
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
            if name in LAYERS:
                widget.GetRepresentation().SetState(name == layer)
        self.plotter.render()
        self.plotter.camera_position = camera_position

    def add_layer_controls(self) -> None:
        for index, name in enumerate(LAYERS):

            def toggle(enabled, selected=name):
                if enabled:
                    self.select_layer(selected)
                else:
                    self.widgets[selected].GetRepresentation().SetState(
                        self.layer == selected
                    )

            self.widgets[name] = self.plotter.add_checkbox_button_widget(
                toggle,
                value=name == self.layer,
                position=(10, 10 + index * 32),
                size=20,
            )
            self.plotter.add_text(name, position=(40, 15 + index * 32), font_size=10)
        self.widgets["terrain-relief"] = self.plotter.add_checkbox_button_widget(
            self.set_terrain_relief,
            value=self.terrain_relief,
            position=(220, 10),
            size=20,
        )
        self.plotter.add_text("terrain relief", position=(250, 15), font_size=10)
        self.widgets["sea-level"] = self.plotter.add_checkbox_button_widget(
            self.set_sea_level,
            value=self.sea_level,
            position=(220, 42),
            size=20,
        )
        self.plotter.add_text("sea level", position=(250, 47), font_size=10)
        self.widgets["hex-edges"] = self.plotter.add_checkbox_button_widget(
            self.set_hex_edges,
            value=self.hex_edges,
            position=(450, 10),
            size=20,
        )
        self.plotter.add_text("hex outlines", position=(480, 15), font_size=10)
        self.plotter.add_slider_widget(
            self.set_vertical_exaggeration,
            rng=(1.0, 100.0),
            value=self.vertical_exaggeration,
            title="Vertical exaggeration",
            pointa=(0.22, 0.12),
            pointb=(0.42, 0.12),
            style="modern",
        )


def render_geology(
    world: GeneratedWorld,
    *,
    layer: str = "plates",
    arrow_scale: float = 0.08,
    off_screen: bool = False,
    terrain_relief: bool = False,
    vertical_exaggeration: float = 1.0,
    sea_level: bool = False,
    elevation_range: tuple[float, float] | None = None,
    hex_edges: bool = True,
    screenshot: str | None = None,
) -> None:
    """Render one initial layer and optionally save an offscreen screenshot."""
    viewer = WorldgenViewer(
        world,
        arrow_scale=arrow_scale,
        off_screen=off_screen,
        terrain_relief=terrain_relief,
        vertical_exaggeration=vertical_exaggeration,
        sea_level=sea_level,
        elevation_range=elevation_range,
        hex_edges=hex_edges,
    )
    viewer.select_layer(layer)
    viewer.plotter.reset_camera()
    if not off_screen:
        viewer.add_layer_controls()
    viewer.plotter.show(screenshot=screenshot)
    viewer.plotter.close()
