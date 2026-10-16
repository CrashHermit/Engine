import numpy as np

from src.worldgen.config import PlanetConfig, WorldgenConfig
from src.worldgen.generate import generate_world
from src.worldgen.render.viewer import WorldgenViewer


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
    viewer = WorldgenViewer(world, off_screen=True)

    try:
        flat_points = viewer.terrain_polydata.points.copy()
        original_display_points = viewer.polydata.points.copy()
        expected_elevation = world.elevation.elevation[world.mesh.faces].mean(axis=1)
        expected_radius = 1.0 + expected_elevation / world.radius_m
        np.testing.assert_allclose(np.linalg.norm(flat_points, axis=1), 1.0)

        viewer.set_terrain_relief(True)
        np.testing.assert_allclose(
            viewer.terrain_polydata.points,
            world.mesh.dual_vertices * expected_radius[:, np.newaxis],
        )
        np.testing.assert_array_equal(viewer.polydata.points, original_display_points)
        np.testing.assert_allclose(
            np.linalg.norm(viewer.terrain_polydata.points, axis=1), expected_radius
        )

        viewer.set_vertical_exaggeration(7.5)
        exaggerated_radius = 1.0 + expected_elevation / world.radius_m * 7.5
        np.testing.assert_allclose(
            viewer.terrain_polydata.points,
            world.mesh.dual_vertices * exaggerated_radius[:, np.newaxis],
        )
        viewer.set_terrain_relief(False)
        np.testing.assert_array_equal(viewer.terrain_polydata.points, flat_points)
        viewer.set_terrain_relief(True)
        viewer.set_vertical_exaggeration(1.0)
        np.testing.assert_allclose(
            viewer.terrain_polydata.points,
            world.mesh.dual_vertices * expected_radius[:, np.newaxis],
        )
        np.testing.assert_array_equal(world.elevation.elevation, original_elevation)
        np.testing.assert_array_equal(world.mesh.dual_vertices, original_dual_vertices)
    finally:
        viewer.plotter.close()


def test_sea_surface_facets_stay_within_shallow_water_depth_at_true_scale():
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    viewer = WorldgenViewer(world, off_screen=True, terrain_relief=True, sea_level=True)
    try:
        viewer.select_layer("elevation")
        shell = viewer.sea_level_actor.mapper.dataset
        np.testing.assert_allclose(np.linalg.norm(shell.points, axis=1), 1.0, atol=1e-7)
        facet_depths = (
            1.0 - np.linalg.norm(shell.cell_centers().points, axis=1)
        ) * world.radius_m
        # The former coarse shell cut through kilometres of ocean at true scale.
        assert facet_depths.max() < 200.0
    finally:
        viewer.plotter.close()


def test_hex_outlines_toggle_and_remain_hidden_across_layer_changes():
    world = generate_world(WorldgenConfig(seed=17, subdivision_frequency=2))
    viewer = WorldgenViewer(world, off_screen=True)
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
