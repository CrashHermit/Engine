import numpy as np

from src.worldgen.field.partition import weighted_regions
from src.worldgen.geometry.mesh import Mesh


def test_weighted_regions_relaxes_late_cheaper_path() -> None:
    vertices = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [-1.0, 0.0, 0.0]]
    )
    faces = np.array([[0, 1, 2], [1, 3, 2]])
    mesh = Mesh(vertices, faces)
    costs = np.array([100.0, 10.0, 100.0, 1.0, 1.0])

    regions = weighted_regions(mesh, np.array([0, 1], dtype=np.int64), costs)

    assert regions.tolist() == [0, 1, 1, 1]


def test_weighted_regions_uses_lower_plate_id_for_equal_costs() -> None:
    vertices = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    mesh = Mesh(vertices, np.array([[0, 1, 2]]))

    regions = weighted_regions(
        mesh,
        np.array([0, 1], dtype=np.int64),
        np.ones(len(mesh.edges), dtype=np.float64),
    )

    assert regions.tolist() == [0, 1, 0]
