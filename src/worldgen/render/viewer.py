"""PyVista viewer for sampled continuous world fields."""

import numpy as np
import pyvista as pv

from src.worldgen.config import WorldgenConfig
from src.worldgen.geometry.icosphere import generate_icosphere
from src.worldgen.model import GeneratedWorld
from src.worldgen.render.layers import LAYERS, common_elevation_range, layer_style
from src.worldgen.world import WorldSample


class WorldgenViewer:
    """Display and replace sampled continuous worlds without resetting the view."""

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
        plotter: pv.BasePlotter | None = None,
    ) -> None:
        self.plotter = (
            plotter if plotter is not None else pv.Plotter(off_screen=off_screen)
        )
        self.world = world
        self.field_frequency = field_frequency
        self.off_screen = off_screen
        self.terrain_relief = terrain_relief or sea_level
        self.vertical_exaggeration = vertical_exaggeration
        self.sea_level = sea_level
        self.elevation_range = elevation_range
        self._fixed_elevation_range = elevation_range
        self.hex_edges = hex_edges
        self.continuous_field = continuous_field
        vertices, faces = generate_icosphere(field_frequency)
        self._dense_directions = vertices
        self._dense_faces = faces
        self._dense_sample: WorldSample = world.field.sample_world(vertices)
        self.elevation_range = elevation_range or common_elevation_range(
            WorldSample(world.geology, world.elevation, world.climate),
            radius_m=world.radius_m,
            other_sample=self._dense_sample,
        )
        self.polydata = self._hex_polydata()
        self.dense_polydata = self._dense_polydata()
        self.actors = []
        self.layer: str | None = None
        self._scalar_bar_title: str | None = None
        self._sea_level_mesh: pv.PolyData | None = None
        self._sea_level_actor = None
        self.annotation = None

    def replace_world(self, world: GeneratedWorld) -> None:
        """Resample the display and refresh the selected layer, retaining the camera."""
        dense_sample = world.field.sample_world(self._dense_directions)
        self.world = world
        self._dense_sample = dense_sample
        self.elevation_range = self._fixed_elevation_range or common_elevation_range(
            WorldSample(world.geology, world.elevation, world.climate),
            radius_m=world.radius_m,
            other_sample=dense_sample,
        )
        self.polydata = self._hex_polydata()
        self.dense_polydata = self._dense_polydata()
        if self.layer is not None:
            self.select_layer(self.layer)

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
        if not enabled and self.sea_level:
            self.sea_level = False
        self._update_geometry()

    def set_vertical_exaggeration(self, exaggeration: float) -> None:
        self.vertical_exaggeration = exaggeration
        self._update_geometry()

    def set_sea_level(self, enabled: bool) -> None:
        self.sea_level = enabled
        if enabled and not self.terrain_relief:
            self.terrain_relief = True
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
        if self._scalar_bar_title is not None:
            self.plotter.remove_scalar_bar(self._scalar_bar_title, render=False)
        for actor in self.actors:
            self.plotter.remove_actor(actor, reset_camera=False, render=False)
        self.actors.clear()
        hex_display = not self.continuous_field or self._hex_only(layer)
        sample = (
            WorldSample(self.world.geology, self.world.elevation, self.world.climate)
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
            scalar_bar_args={
                "title": style.title,
                "n_labels": 3,
                "title_font_size": 14,
                "label_font_size": 11,
                "unconstrained_font_size": True,
                "fmt": "%.3g",
                "position_x": 0.125,
                "position_y": 0.04,
                "width": 0.75,
                "height": 0.04,
            },
        )
        if style.categorical:
            kwargs["categories"] = True
            if style.annotations:
                kwargs["annotations"] = style.annotations
        count = getattr(cmap, "N", None)
        if count is not None:
            kwargs["n_colors"] = int(count)
        self.actors.append(self.plotter.add_mesh(mesh, **kwargs))
        if layer == "wind-vectors":
            self._add_wind_arrows(sample, hex_display=hex_display)
        self._scalar_bar_title = style.title
        self.layer = layer
        self._update_annotation()
        self.plotter.camera_position = camera
        self.plotter.render()

    def _add_wind_arrows(self, sample: WorldSample, *, hex_display: bool) -> None:
        """Decimate glyphs for display without changing the sampled wind field."""
        directions = self.world.mesh.vertices if hex_display else self._dense_directions
        indices = np.linspace(
            0, len(directions) - 1, min(400, len(directions)), dtype=np.int64
        )
        radius = (
            1.0 + sample.elevation.elevation[indices] * self.vertical_exaggeration
            if self.terrain_relief
            else np.ones(len(indices))
        )
        centers = directions[indices] * (radius[:, None] + 0.008)
        vectors = sample.climate.circulation.wind_vectors_m_s[indices]
        display_speed = max(
            float(np.max(np.linalg.norm(vectors, axis=1), initial=0.0)), 1.0
        )
        self.actors.append(
            self.plotter.add_arrows(
                centers,
                vectors,
                mag=0.1 / display_speed,
                color="black",
                reset_camera=False,
            )
        )

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
    rebuild_config: WorldgenConfig | None = None,
) -> None:
    if not off_screen and rotation_gif is None:
        from src.worldgen.render.window import show_world_window

        show_world_window(
            world=world,
            layer=layer,
            terrain_relief=terrain_relief,
            vertical_exaggeration=vertical_exaggeration,
            sea_level=sea_level,
            elevation_range=elevation_range,
            hex_edges=hex_edges,
            field_frequency=field_frequency,
            continuous_field=continuous_field,
            screenshot=screenshot,
            rebuild_config=rebuild_config,
        )
        return

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
        viewer.plotter.show(screenshot=screenshot)
    viewer.plotter.close()
