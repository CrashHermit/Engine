"""PyVista viewer for sampled continuous world fields."""

import numpy as np
import pyvista as pv

from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.model import GeneratedWorld
from src.worldgen.render.layers import LAYERS, common_elevation_range, layer_style
from src.worldgen.world import WorldSample


class WorldgenViewer:
    """Display hex samples or a dense continuous field without regenerating it."""

    def __init__(
        self,
        world: GeneratedWorld,
        *,
        field_frequency: int = 80,
        off_screen: bool = False,
        terrain_relief: bool = False,
        vertical_exaggeration: float = 1.0,
        sea_level: bool = False,
        elevation_range: tuple[float, float] | None = None,
        hex_edges: bool = True,
        continuous_field: bool = True,
    ) -> None:
        self.world = world
        self.field_frequency = field_frequency
        self.off_screen = off_screen
        self.terrain_relief = terrain_relief or sea_level
        self.vertical_exaggeration = vertical_exaggeration
        self.sea_level = sea_level
        self.elevation_range = elevation_range
        self.hex_edges = hex_edges
        self.continuous_field = continuous_field
        vertices, faces = generate_icosphere(field_frequency)
        self._dense_directions = vertices
        self._dense_faces = faces
        self._dense_sample: WorldSample = world.field.sample_world(vertices)
        self.elevation_range = elevation_range or common_elevation_range(
            WorldSample(world.geology, world.elevation),
            radius_m=world.radius_m,
            other_sample=self._dense_sample,
        )
        self.plotter = pv.Plotter(off_screen=off_screen)
        self.polydata = self._hex_polydata()
        self.dense_polydata = self._dense_polydata()
        self.actors = []
        self.widgets = {}
        self.layer: str | None = None
        self._sea_level_mesh: pv.PolyData | None = None
        self._sea_level_actor = None
        self.annotation = None

    def _hex_polydata(self) -> pv.PolyData:
        mesh = self.world.mesh
        counts = [len(face) for face in mesh.dual_faces]
        cells = np.empty(sum(count + 1 for count in counts), dtype=np.int64)
        offset = 0
        for face in mesh.dual_faces:
            cells[offset] = len(face)
            cells[offset + 1 : offset + 1 + len(face)] = face
            offset += 1 + len(face)
        poly = pv.PolyData(mesh.dual_vertices, cells)
        poly.points = self._dual_points()
        return poly

    def _dual_points(self) -> np.ndarray:
        mesh = self.world.mesh
        fraction = self.world.elevation.elevation[mesh.faces].mean(axis=1)
        radius = 1.0 + fraction * self.vertical_exaggeration
        return (
            mesh.dual_vertices * radius[:, None]
            if self.terrain_relief
            else mesh.dual_vertices.copy()
        )

    def _dense_polydata(self) -> pv.PolyData:
        cells = np.column_stack(
            (np.full(len(self._dense_faces), 3), self._dense_faces)
        ).ravel()
        poly = pv.PolyData(self._dense_directions.copy(), cells)
        poly.points = self._dense_points()
        return poly

    def _dense_points(self) -> np.ndarray:
        fraction = self._dense_sample.elevation.elevation
        radius = (
            1.0 + fraction * self.vertical_exaggeration
            if self.terrain_relief
            else np.ones(len(fraction))
        )
        return self._dense_directions * radius[:, None]

    def _update_geometry(self) -> None:
        self.polydata.points = self._dual_points()
        self.dense_polydata.points = self._dense_points()
        if self.layer is not None:
            self.select_layer(self.layer)
        self._update_annotation()

    def _update_annotation(self) -> None:
        text = f"Radius {self.world.radius_m:,.0f} m · exaggeration {self.vertical_exaggeration:g}×"
        if self.annotation is not None:
            self.plotter.remove_actor(self.annotation, reset_camera=False, render=False)
        self.annotation = self.plotter.add_text(
            text, position="upper_right", font_size=10
        )

    def set_terrain_relief(self, enabled: bool) -> None:
        self.terrain_relief = enabled
        relief_widget = self.widgets.get("terrain-relief")
        if relief_widget is not None:
            relief_widget.GetRepresentation().SetState(enabled)
        if not enabled and self.sea_level:
            self.sea_level = False
            water_widget = self.widgets.get("water")
            if water_widget is not None:
                water_widget.GetRepresentation().SetState(0)
        self._update_geometry()

    def set_vertical_exaggeration(self, exaggeration: float) -> None:
        self.vertical_exaggeration = exaggeration
        self._update_geometry()

    def set_sea_level(self, enabled: bool) -> None:
        self.sea_level = enabled
        water_widget = self.widgets.get("water")
        if water_widget is not None:
            water_widget.GetRepresentation().SetState(enabled)
        if enabled and not self.terrain_relief:
            self.terrain_relief = True
            relief_widget = self.widgets.get("terrain-relief")
            if relief_widget is not None:
                relief_widget.GetRepresentation().SetState(1)
            self._update_geometry()
        elif self.layer is not None:
            self.select_layer(self.layer)

    def set_hex_edges(self, enabled: bool) -> None:
        self.hex_edges = enabled
        if self.layer is not None:
            self.select_layer(self.layer)

    def set_continuous_field(self, enabled: bool) -> None:
        self.continuous_field = enabled
        if self.layer is not None:
            self.select_layer(self.layer)

    def _hex_only(self, layer: str) -> bool:
        return layer in (
            "plates",
            "crust",
            "crust-regions",
            "land-height",
            "water-depth",
            "slope",
            "local-relief",
            "roughness",
        )

    def select_layer(self, layer: str) -> None:
        if layer not in LAYERS:
            raise KeyError(layer)
        camera = self.plotter.camera_position
        for actor in self.actors:
            self.plotter.remove_actor(actor, reset_camera=False, render=False)
        self.actors.clear()
        hex_display = not self.continuous_field or self._hex_only(layer)
        sample = (
            WorldSample(self.world.geology, self.world.elevation)
            if hex_display
            else self._dense_sample
        )
        surface = self.world.surface if hex_display else None
        style = layer_style(
            sample,
            layer,
            radius_m=self.world.radius_m,
            elevation_range=self.elevation_range,
            surface=surface,
        )
        mesh = self.polydata if hex_display else self.dense_polydata
        # PolyData cell values are one per sampled hex; dense triangles use vertex values.
        if hex_display:
            mesh.cell_data[layer] = style.values
            scalar_mode = "cell"
        else:
            mesh.point_data[layer] = style.values
            scalar_mode = "point"
        if layer == "elevation" and self.terrain_relief and self.sea_level:
            if self._sea_level_mesh is None:
                self._sea_level_mesh = pv.Sphere(
                    radius=1.0, theta_resolution=512, phi_resolution=512
                )
            self._sea_level_actor = self.plotter.add_mesh(
                self._sea_level_mesh,
                color="royalblue",
                opacity=0.35,
                show_edges=False,
                reset_camera=False,
            )
            self.actors.append(self._sea_level_actor)
        cmap = style.cmap
        kwargs = dict(
            scalars=layer,
            preference=scalar_mode,
            cmap=cmap,
            clim=style.clim,
            show_edges=hex_display and self.hex_edges,
            reset_camera=False,
            smooth_shading=True,
            scalar_bar_args={"title": style.title},
        )
        if style.categorical:
            kwargs["categories"] = True
            if style.annotations:
                kwargs["annotations"] = style.annotations
        count = getattr(cmap, "N", None)
        if count is not None:
            kwargs["n_colors"] = int(count)
        self.actors.append(self.plotter.add_mesh(mesh, **kwargs))
        self.layer = layer
        self._update_annotation()
        for name, widget in self.widgets.items():
            if name in LAYERS:
                widget.GetRepresentation().SetState(name == layer)
        self.plotter.render()
        self.plotter.camera_position = camera

    def prepare_camera(self) -> None:
        self.plotter.camera.parallel_projection = True
        self.plotter.reset_camera()
        self.plotter.camera.parallel_scale *= 1.08

    def write_rotation_gif(
        self, path: str, *, frames: int = 120, fps: float = 24.0
    ) -> None:
        initial_camera = self.plotter.camera_position
        parallel_scale = self.plotter.camera.parallel_scale
        self.plotter.open_gif(path, fps=fps)
        try:
            self.plotter.write_frame()
            for _ in range(1, frames):
                self.plotter.camera.Azimuth(360.0 / frames)
                self.plotter.write_frame()
        finally:
            if self.plotter.mwriter is not None:
                self.plotter.mwriter.close()
                self.plotter.mwriter = None
            self.plotter.camera_position = initial_camera
            self.plotter.camera.parallel_scale = parallel_scale

    def add_layer_controls(self) -> None:
        rows = (len(LAYERS) + 1) // 2
        for index, name in enumerate(LAYERS):
            column, row = divmod(index, rows)
            position = (10 + 240 * column, 130 + 26 * row)
            label_position = (40 + 240 * column, 135 + 26 * row)

            def toggle(enabled, selected=name):
                if enabled:
                    self.select_layer(selected)
                elif selected in self.widgets:
                    self.widgets[selected].GetRepresentation().SetState(
                        self.layer == selected
                    )

            self.widgets[name] = self.plotter.add_checkbox_button_widget(
                toggle, value=name == self.layer, position=position, size=20
            )
            self.plotter.add_text(name, position=label_position, font_size=10)
        for key, callback, value, label, x in (
            (
                "terrain-relief",
                self.set_terrain_relief,
                self.terrain_relief,
                "terrain relief",
                220,
            ),
            ("water", self.set_sea_level, self.sea_level, "water", 450),
            ("hex-edges", self.set_hex_edges, self.hex_edges, "hex outlines", 680),
            (
                "continuous-field",
                self.set_continuous_field,
                self.continuous_field,
                "continuous field",
                910,
            ),
        ):
            self.widgets[key] = self.plotter.add_checkbox_button_widget(
                callback, value=value, position=(x, 10), size=20
            )
            self.plotter.add_text(label, position=(x + 30, 15), font_size=10)
        self.plotter.add_slider_widget(
            self.set_vertical_exaggeration,
            rng=(1.0, 100.0),
            value=self.vertical_exaggeration,
            title="Vertical exaggeration",
            pointa=(0.22, 0.12),
            pointb=(0.42, 0.12),
            style="modern",
        )


def render_world(
    world: GeneratedWorld,
    *,
    layer: str = "elevation",
    off_screen: bool = False,
    terrain_relief: bool = False,
    vertical_exaggeration: float = 1.0,
    sea_level: bool = False,
    elevation_range: tuple[float, float] | None = None,
    hex_edges: bool = True,
    field_frequency: int = 80,
    continuous_field: bool = True,
    screenshot: str | None = None,
    rotation_gif: str | None = None,
    rotation_frames: int = 120,
    rotation_fps: float = 24.0,
) -> None:
    viewer = WorldgenViewer(
        world,
        field_frequency=field_frequency,
        off_screen=off_screen or rotation_gif is not None,
        terrain_relief=terrain_relief,
        vertical_exaggeration=vertical_exaggeration,
        sea_level=sea_level,
        elevation_range=elevation_range,
        hex_edges=hex_edges,
        continuous_field=continuous_field,
    )
    viewer.select_layer(layer)
    viewer.prepare_camera()
    if rotation_gif is not None:
        viewer.write_rotation_gif(
            rotation_gif, frames=rotation_frames, fps=rotation_fps
        )
    else:
        if not off_screen:
            viewer.add_layer_controls()
        viewer.plotter.show(screenshot=screenshot)
    viewer.plotter.close()
