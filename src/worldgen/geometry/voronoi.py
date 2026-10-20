"""Analytic faces of volumetric Euclidean Voronoi partitions."""

from dataclasses import dataclass

import numba
import numpy as np
from scipy.optimize import linprog

_FACE_TOLERANCE = 1e-10


@dataclass(frozen=True, slots=True)
class _VoronoiFace:
    """A clipped Voronoi face expressed in a local orthonormal chart."""

    origin: np.ndarray
    normal: np.ndarray
    basis: np.ndarray
    constraint_normals: np.ndarray
    constraint_bounds: np.ndarray
    edge_origins: np.ndarray
    edge_directions: np.ndarray
    edge_lowers: np.ndarray
    edge_uppers: np.ndarray

    def __post_init__(self) -> None:
        for name in (
            "origin",
            "normal",
            "basis",
            "constraint_normals",
            "constraint_bounds",
            "edge_origins",
            "edge_directions",
            "edge_lowers",
            "edge_uppers",
        ):
            value = np.array(getattr(self, name), dtype=np.float64, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class VoronoiBoundaryGeometry:
    """Stable pair ordering and the corresponding clipped Voronoi faces."""

    region_pairs: np.ndarray
    faces: tuple[_VoronoiFace, ...]

    def __post_init__(self) -> None:
        region_pairs = np.array(self.region_pairs, dtype=np.int64, copy=True)
        region_pairs.setflags(write=False)
        object.__setattr__(self, "region_pairs", region_pairs)
        object.__setattr__(self, "faces", tuple(self.faces))


def _face_constraints(
    seeds: np.ndarray,
    first: int,
    second: int,
    origin: np.ndarray,
    basis: np.ndarray,
) -> tuple[np.ndarray, np.ndarray] | None:
    normals: list[np.ndarray] = []
    bounds: list[float] = []
    first_seed = seeds[first]
    first_squared = np.dot(first_seed, first_seed)

    for other in range(len(seeds)):
        if other == first or other == second:
            continue
        other_seed = seeds[other]
        difference = other_seed - first_seed
        normal = difference @ basis
        bound = 0.5 * (np.dot(other_seed, other_seed) - first_squared) - np.dot(
            difference, origin
        )
        magnitude = np.linalg.norm(normal)
        if magnitude <= _FACE_TOLERANCE:
            if bound < -_FACE_TOLERANCE:
                return None
            continue

        normal /= magnitude
        bound /= magnitude
        if any(
            np.all(np.abs(normal - existing) <= _FACE_TOLERANCE)
            and abs(bound - existing_bound) <= _FACE_TOLERANCE
            for existing, existing_bound in zip(normals, bounds, strict=True)
        ):
            continue
        normals.append(normal)
        bounds.append(float(bound))

    if not normals:
        return np.empty((0, 2), dtype=np.float64), np.empty(0, dtype=np.float64)
    return np.asarray(normals), np.asarray(bounds, dtype=np.float64)


def _has_two_dimensional_interior(normals: np.ndarray, bounds: np.ndarray) -> bool:
    if len(normals) == 0:
        return True

    inequalities = np.column_stack((normals, np.ones(len(normals))))
    result = linprog(
        c=np.array([0.0, 0.0, -1.0]),
        A_ub=inequalities,
        b_ub=bounds,
        bounds=((None, None), (None, None), (0.0, 1.0)),
        method="highs",
        options={
            "primal_feasibility_tolerance": _FACE_TOLERANCE,
            "dual_feasibility_tolerance": _FACE_TOLERANCE,
        },
    )
    if result.status == 2:
        return False
    if not result.success:
        raise RuntimeError("Voronoi face construction failed")
    return result.x[2] > _FACE_TOLERANCE


def _face_edges(
    normals: np.ndarray, bounds: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    origins: list[np.ndarray] = []
    directions: list[np.ndarray] = []
    lowers: list[float] = []
    uppers: list[float] = []

    for edge_index, (normal, bound) in enumerate(zip(normals, bounds, strict=True)):
        origin = bound * normal
        direction = np.array([-normal[1], normal[0]])
        lower = -np.inf
        upper = np.inf
        exists = True

        for constraint_index, (constraint_normal, constraint_bound) in enumerate(
            zip(normals, bounds, strict=True)
        ):
            value = np.dot(constraint_normal, origin)
            rate = np.dot(constraint_normal, direction)
            if abs(rate) <= _FACE_TOLERANCE:
                if value > constraint_bound + _FACE_TOLERANCE:
                    exists = False
                    break
                continue

            crossing = (constraint_bound - value) / rate
            if rate > 0.0:
                upper = min(upper, crossing)
            else:
                lower = max(lower, crossing)

        if not exists or upper - lower <= _FACE_TOLERANCE:
            continue
        origins.append(origin)
        directions.append(direction)
        lowers.append(lower)
        uppers.append(upper)

    if not origins:
        return (
            np.empty((0, 2), dtype=np.float64),
            np.empty((0, 2), dtype=np.float64),
            np.empty(0, dtype=np.float64),
            np.empty(0, dtype=np.float64),
        )
    return (
        np.asarray(origins),
        np.asarray(directions),
        np.asarray(lowers, dtype=np.float64),
        np.asarray(uppers, dtype=np.float64),
    )


def _build_face(seeds: np.ndarray, first: int, second: int) -> _VoronoiFace | None:
    first_seed = seeds[first]
    second_seed = seeds[second]
    difference = second_seed - first_seed
    normal = difference / np.linalg.norm(difference)
    axis = np.zeros(3, dtype=np.float64)
    axis[int(np.argmin(np.abs(normal)))] = 1.0
    first_basis = np.cross(normal, axis)
    first_basis /= np.linalg.norm(first_basis)
    second_basis = np.cross(normal, first_basis)
    basis = np.column_stack((first_basis, second_basis))
    origin = 0.5 * (first_seed + second_seed)

    constraints = _face_constraints(seeds, first, second, origin, basis)
    if constraints is None:
        return None
    normals, bounds = constraints
    if not _has_two_dimensional_interior(normals, bounds):
        return None
    edge_data = _face_edges(normals, bounds)
    return _VoronoiFace(
        origin=origin,
        normal=normal,
        basis=basis,
        constraint_normals=normals,
        constraint_bounds=bounds,
        edge_origins=edge_data[0],
        edge_directions=edge_data[1],
        edge_lowers=edge_data[2],
        edge_uppers=edge_data[3],
    )


@numba.njit(cache=True)
def _sample_face_distances(
    positions: np.ndarray,
    origin: np.ndarray,
    normal: np.ndarray,
    basis: np.ndarray,
    constraint_normals: np.ndarray,
    constraint_bounds: np.ndarray,
    edge_origins: np.ndarray,
    edge_directions: np.ndarray,
    edge_lowers: np.ndarray,
    edge_uppers: np.ndarray,
    output: np.ndarray,
) -> None:
    for point_index in range(len(positions)):
        x = positions[point_index, 0] - origin[0]
        y = positions[point_index, 1] - origin[1]
        z = positions[point_index, 2] - origin[2]
        local_x = x * basis[0, 0] + y * basis[1, 0] + z * basis[2, 0]
        local_y = x * basis[0, 1] + y * basis[1, 1] + z * basis[2, 1]
        plane_distance = x * normal[0] + y * normal[1] + z * normal[2]
        inside = True

        for constraint_index in range(len(constraint_bounds)):
            if (
                constraint_normals[constraint_index, 0] * local_x
                + constraint_normals[constraint_index, 1] * local_y
                > constraint_bounds[constraint_index] + _FACE_TOLERANCE
            ):
                inside = False
                break

        if inside:
            output[point_index] = abs(plane_distance)
            continue

        nearest_squared = np.inf
        for edge_index in range(len(edge_lowers)):
            edge_x = edge_origins[edge_index, 0]
            edge_y = edge_origins[edge_index, 1]
            direction_x = edge_directions[edge_index, 0]
            direction_y = edge_directions[edge_index, 1]
            parameter = (local_x - edge_x) * direction_x + (
                local_y - edge_y
            ) * direction_y
            parameter = max(parameter, edge_lowers[edge_index])
            parameter = min(parameter, edge_uppers[edge_index])
            delta_x = local_x - (edge_x + parameter * direction_x)
            delta_y = local_y - (edge_y + parameter * direction_y)
            squared = delta_x * delta_x + delta_y * delta_y
            nearest_squared = min(nearest_squared, squared)
        output[point_index] = np.sqrt(plane_distance * plane_distance + nearest_squared)


def build_voronoi_boundary_geometry(seeds: np.ndarray) -> VoronoiBoundaryGeometry:
    """Construct genuine clipped planar faces between distinct Voronoi seeds."""
    seed_points = np.asarray(seeds, dtype=np.float64)
    pairs: list[tuple[int, int]] = []
    faces: list[_VoronoiFace] = []

    for first in range(len(seed_points)):
        for second in range(first + 1, len(seed_points)):
            face = _build_face(seed_points, first, second)
            if face is not None:
                pairs.append((first, second))
                faces.append(face)

    return VoronoiBoundaryGeometry(
        region_pairs=np.asarray(pairs, dtype=np.int64).reshape((-1, 2)),
        faces=tuple(faces),
    )


def voronoi_boundary_distances(
    positions: np.ndarray,
    geometry: VoronoiBoundaryGeometry,
) -> np.ndarray:
    """Return source-space distances from XYZ points to each closed Voronoi face."""
    query_points = np.asarray(positions, dtype=np.float64)
    distances = np.empty((len(query_points), len(geometry.faces)), dtype=np.float64)

    for face_index, face in enumerate(geometry.faces):
        _sample_face_distances(
            query_points,
            face.origin,
            face.normal,
            face.basis,
            face.constraint_normals,
            face.constraint_bounds,
            face.edge_origins,
            face.edge_directions,
            face.edge_lowers,
            face.edge_uppers,
            distances[:, face_index],
        )

    distances.setflags(write=False)
    return distances
