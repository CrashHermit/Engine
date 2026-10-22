import numpy as np
import pytest
from PIL import Image

from src.worldgen.config import PlanetConfig, WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.render.layers import layer_style
from src.worldgen.render.viewer import WorldgenViewer
from src.worldgen.world import WorldSample


def test_terrain_relief_is_radial_reversible_and_data_preserving() -> None:
    world = generate_world(
        WorldgenConfig(
            seed=17,
            subdivision_frequency=2,
            planet=PlanetConfig(radius_m=1.0),
        )
    )
    original_elevation = world.elevation.elevation.copy()
    original_dual_vertices = world.mesh.dual_vertices.copy()
    viewer = WorldgenViewer(
        world, field_frequency=5, off_screen=True, terrain_relief=False
    )

    try:
        flat_points = viewer.dense_polydata.points.copy()
        flat_hex_points = viewer.polydata.points.copy()
        dense_elevation = world.field.sample_world(flat_points).elevation.elevation
        dense_radius = 1.0 + dense_elevation
        hex_elevation = world.elevation.elevation[world.mesh.faces].mean(axis=1)
        hex_radius = 1.0 + hex_elevation
        np.testing.assert_allclose(np.linalg.norm(flat_points, axis=1), 1.0)

        viewer.set_terrain_relief(True)
        np.testing.assert_allclose(
            viewer.dense_polydata.points,
            flat_points * dense_radius[:, np.newaxis],
        )
        np.testing.assert_allclose(
            viewer.polydata.points,
            world.mesh.dual_vertices * hex_radius[:, np.newaxis],
        )
        np.testing.assert_allclose(
            np.linalg.norm(viewer.dense_polydata.points, axis=1), dense_radius
        )

        viewer.set_vertical_exaggeration(7.5)
        exaggerated_radius = 1.0 + dense_elevation * 7.5
        exaggerated_hex_radius = 1.0 + hex_elevation * 7.5
        np.testing.assert_allclose(
            viewer.dense_polydata.points,
            flat_points * exaggerated_radius[:, np.newaxis],
        )
        np.testing.assert_allclose(
            viewer.polydata.points,
            world.mesh.dual_vertices * exaggerated_hex_radius[:, np.newaxis],
        )
        viewer.set_terrain_relief(False)
        np.testing.assert_array_equal(viewer.dense_polydata.points, flat_points)
        np.testing.assert_array_equal(viewer.polydata.points, flat_hex_points)
        viewer.set_terrain_relief(True)
        viewer.set_vertical_exaggeration(1.0)
        np.testing.assert_allclose(
            viewer.dense_polydata.points,
            flat_points * dense_radius[:, np.newaxis],
        )
        np.testing.assert_allclose(
            viewer.polydata.points,
            world.mesh.dual_vertices * hex_radius[:, np.newaxis],
        )
        np.testing.assert_array_equal(world.elevation.elevation, original_elevation)
        np.testing.assert_array_equal(world.mesh.dual_vertices, original_dual_vertices)
    finally:
        viewer.plotter.close()


def test_sea_surface_facets_stay_within_shallow_water_depth_at_true_scale():
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    viewer = WorldgenViewer(
        world, field_frequency=5, off_screen=True, terrain_relief=True, sea_level=True
    )
    try:
        viewer.select_layer("elevation")
        shell = viewer.actors[0].mapper.dataset
        np.testing.assert_allclose(np.linalg.norm(shell.points, axis=1), 1.0, atol=1e-7)
        facet_depths = (
            1.0 - np.linalg.norm(shell.cell_centers().points, axis=1)
        ) * world.radius_m
        # The former coarse shell cut through kilometres of ocean at true scale.
        assert facet_depths.max() < 200.0
    finally:
        viewer.plotter.close()


def test_water_button_toggles_surface_and_enables_terrain_relief():
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    viewer = WorldgenViewer(world, field_frequency=5, off_screen=True)
    try:
        viewer.select_layer("elevation")
        viewer.add_layer_controls()
        water_widget = viewer.widgets["water"]
        water_widget.GetRepresentation().SetState(1)
        water_widget.InvokeEvent("StateChangedEvent")

        assert viewer.sea_level
        assert viewer.terrain_relief
        assert viewer.widgets["terrain-relief"].GetRepresentation().GetState() == 1
        assert len(viewer.actors) == 2
        water_surface = viewer.actors[0].mapper.dataset
        np.testing.assert_allclose(
            np.linalg.norm(water_surface.points, axis=1), 1.0, atol=1e-7
        )

        water_widget.GetRepresentation().SetState(0)
        water_widget.InvokeEvent("StateChangedEvent")
        assert not viewer.sea_level
        assert viewer.terrain_relief
        assert len(viewer.actors) == 1
        viewer.set_sea_level(True)
        assert water_widget.GetRepresentation().GetState() == 1
        viewer.set_terrain_relief(False)
        assert not viewer.terrain_relief
        assert not viewer.sea_level
        assert water_widget.GetRepresentation().GetState() == 0
        assert viewer.widgets["terrain-relief"].GetRepresentation().GetState() == 0
        assert len(viewer.actors) == 1
    finally:
        viewer.plotter.close()


def test_elevation_actor_preserves_hypsometric_lookup_resolution() -> None:
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    clim = (-12_000.0, 8_000.0)
    viewer = WorldgenViewer(
        world, field_frequency=5, off_screen=True, elevation_range=clim
    )

    try:
        viewer.select_layer("elevation")
        actor = viewer.actors[0]
        lookup_table = actor.mapper.lookup_table
        style = layer_style(
            world.field.sample_world(world.mesh.vertices),
            "elevation",
            radius_m=world.radius_m,
            elevation_range=clim,
        )
        zero_fraction = (0.0 - clim[0]) / (clim[1] - clim[0])
        zero_index = round(zero_fraction * (lookup_table.GetNumberOfTableValues() - 1))

        assert lookup_table.GetNumberOfTableValues() == style.cmap.N
        np.testing.assert_allclose(
            lookup_table.GetTableValue(zero_index)[:3],
            np.array([244, 241, 220]) / 255,
            atol=0.01,
        )
    finally:
        viewer.plotter.close()


@pytest.mark.parametrize(
    "elevation_range",
    ((100.0, 1_000.0), (-1_000.0, -100.0)),
)
def test_elevation_viewer_renders_one_sided_color_limits(elevation_range):
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    viewer = WorldgenViewer(
        world,
        field_frequency=5,
        off_screen=True,
        elevation_range=elevation_range,
    )
    try:
        viewer.select_layer("elevation")
        viewer.plotter.render()
        lookup_table = viewer.actors[-1].mapper.lookup_table
        sample = WorldSample(geology=world.geology, elevation=world.elevation)
        style = layer_style(
            sample,
            "elevation",
            radius_m=world.radius_m,
            elevation_range=elevation_range,
        )
        expected_colors = style.cmap(np.array([0.0, 1.0]))[:, :3]
        color_count = lookup_table.GetNumberOfTableValues()
        assert color_count >= 256
        for index, expected_color in (
            (0, expected_colors[0]),
            (color_count - 1, expected_colors[1]),
        ):
            np.testing.assert_allclose(
                lookup_table.GetTableValue(index)[:3],
                expected_color,
                atol=0.01,
            )
    finally:
        viewer.plotter.close()


def test_continuous_toggle_switches_between_dense_and_hex_sample_values():
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    viewer = WorldgenViewer(world, field_frequency=5, off_screen=True, hex_edges=False)
    try:
        viewer.select_layer("elevation")
        camera = viewer.plotter.camera_position
        dense_positions = viewer.dense_polydata.points.copy()
        dense_values = (
            world.field.sample_world(dense_positions).elevation.elevation
            * world.radius_m
        )
        np.testing.assert_allclose(
            viewer.dense_polydata.point_data["elevation"], dense_values
        )

        viewer.set_continuous_field(False)
        np.testing.assert_array_equal(
            viewer.polydata.cell_data["elevation"],
            world.elevation.elevation * world.radius_m,
        )
        assert viewer.plotter.camera_position == camera

        viewer.set_continuous_field(True)
        np.testing.assert_allclose(
            viewer.dense_polydata.point_data["elevation"], dense_values
        )
        assert viewer.plotter.camera_position == camera
    finally:
        viewer.plotter.close()


def test_rotation_gif_writes_requested_frames(tmp_path) -> None:
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    path = tmp_path / "rotation.gif"
    viewer = WorldgenViewer(world, field_frequency=5, off_screen=True)

    try:
        viewer.select_layer("elevation")
        viewer.write_rotation_gif(str(path), frames=4, fps=8)
    finally:
        viewer.plotter.close()

    with Image.open(path) as image:
        assert image.n_frames == 4
        assert image.size == (1024, 768)


def test_hex_outlines_toggle_and_remain_hidden_across_layer_changes():
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    viewer = WorldgenViewer(
        world, field_frequency=5, off_screen=True, continuous_field=False
    )
    try:
        viewer.select_layer("elevation")
        viewer.plotter.reset_camera()
        camera = viewer.plotter.camera_position
        assert viewer.actors[0].GetProperty().GetEdgeVisibility()
        viewer.set_hex_edges(False)
        for layer in ("elevation", "crust", "plates"):
            viewer.select_layer(layer)
            assert not viewer.actors[0].GetProperty().GetEdgeVisibility()
            assert viewer.plotter.camera_position == camera
        viewer.set_hex_edges(True)
        assert viewer.actors[0].GetProperty().GetEdgeVisibility()
    finally:
        viewer.plotter.close()


def test_surface_layer_checkbox_updates_scalars_and_retains_camera() -> None:
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    viewer = WorldgenViewer(world, field_frequency=5, off_screen=True, hex_edges=False)
    viewer.plotter.window_size = (800, 600)

    try:
        viewer.plotter.reset_camera()
        viewer.select_layer("slope")
        viewer.add_layer_controls()
        camera = viewer.plotter.camera_position
        slope_widget = viewer.widgets["slope"]
        roughness_widget = viewer.widgets["roughness"]
        assert slope_widget.GetRepresentation().GetState() == 1
        assert roughness_widget.GetRepresentation().GetState() == 0

        roughness_widget.GetRepresentation().SetState(1)
        roughness_widget.InvokeEvent("StateChangedEvent")

        assert viewer.layer == "roughness"
        assert slope_widget.GetRepresentation().GetState() == 0
        assert roughness_widget.GetRepresentation().GetState() == 1
        assert viewer.plotter.camera_position == camera
        np.testing.assert_array_equal(
            viewer.actors[0].mapper.dataset.cell_data["roughness"],
            world.surface.roughness,
        )
    finally:
        viewer.plotter.close()
