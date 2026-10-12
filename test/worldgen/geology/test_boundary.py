import numpy as np
import pytest

from src.worldgen.geology.boundary import boundary_interactions
from src.worldgen.geometry.mesh import Mesh


@pytest.mark.parametrize(
    ("rotation", "expected"),
    [
        ([0.0, 0.0, 2.0], (0.0, 2.0, 0.0)),
        ([0.0, 0.0, -2.0], (2.0, 0.0, 0.0)),
        ([0.0, -3.0, 0.0], (0.0, 0.0, 3.0)),
        ([0.0, -3.0, -2.0], (2.0, 0.0, 3.0)),
    ],
)
def test_boundary_components_at_shared_midpoint(rotation, expected) -> None:
    mesh = Mesh(
        np.array([[0.8, -0.6, 0.0], [0.8, 0.6, 0.0], [0.0, 0.0, 1.0]]),
        np.array([[0, 1, 2]]),
    )
    result = boundary_interactions(
        mesh,
        np.array([0, 1, 0]),
        np.array([[0.0, 0.0, 0.0], rotation]),
        np.array([0]),
    )
    np.testing.assert_allclose(np.array(result).ravel(), expected)


def test_identical_rotations_have_no_relative_boundary_motion() -> None:
    mesh = Mesh(
        np.array([[0.8, -0.6, 0.0], [0.8, 0.6, 0.0], [0.0, 0.0, 1.0]]),
        np.array([[0, 1, 2]]),
    )
    rotation = np.array([[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]])
    result = boundary_interactions(mesh, np.array([0, 1, 0]), rotation, np.array([0]))
    np.testing.assert_array_equal(np.array(result), np.zeros((3, 1)))
