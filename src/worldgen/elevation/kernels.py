"""Allocation-bounded compiled reductions for batches of nearby boundary arcs."""

from typing import NamedTuple

import numpy as np
from numba import njit
from numba.extending import register_jitable

from src.worldgen.elevation.collision import collision_value
from src.worldgen.elevation.divergence import divergence_value
from src.worldgen.elevation.subduction import subduction_value
from src.worldgen.elevation.transform import transform_value
from src.worldgen.elevation.profiles import (
    collision_profile,
    divergent_profile,
    divergent_response,
    subduction_profile,
    transform_profile,
)
from src.worldgen.utilities.curves import clamp_unit, smoothstep_scalar

# Register the existing scalar mathematics without changing its Python interface.
for _function in (
    clamp_unit,
    smoothstep_scalar,
    collision_profile,
    divergent_response,
    divergent_profile,
    subduction_profile,
    transform_profile,
):
    register_jitable(_function)


class TectonicSources(NamedTuple):
    delta_rotation: np.ndarray
    arc_normals: np.ndarray
    positive_side_is_left: np.ndarray
    across_vectors: np.ndarray
    lengths: np.ndarray
    section_ids: np.ndarray
    left_plates: np.ndarray
    left_continental: np.ndarray
    right_continental: np.ndarray
    descending_plates: np.ndarray
    collision_sections: np.ndarray
    divergent: np.ndarray
    transform: np.ndarray


class TectonicParameters(NamedTuple):
    collision: tuple[float, float, float, float]
    subduction: tuple[float, float, float, float, float, float, float]
    divergence: tuple[float, float, float, float, float]
    transform: tuple[float, float]
    blend_radii: tuple[float, float, float, float]


@register_jitable
def _weight(distance, nearest, radius, length):
    return smoothstep_scalar((nearest + radius - distance) / radius) * length


@register_jitable
def _strength(normal, shear):
    denominator = abs(normal) + shear
    return normal * shear / denominator if denominator != 0.0 else 0.0


@njit(cache=True)
def evaluate_tectonic_batch(
    points,
    offsets,
    segment_ids,
    distances,
    closest,
    arc_variation,
    sources,
    parameters,
    peak_scale,
    result,
):
    """Reduce CSR point/arc pairs; scratch storage is reused across all points."""
    section_count = len(sources.descending_plates)
    nearest_section = np.empty(section_count)
    collision_mass = np.empty(section_count)
    collision_force = np.empty(section_count)
    subduction_mass = np.empty(section_count)
    subduction_force = np.empty(section_count)
    descending_mass = np.empty(section_count)
    max_neighbors = 0
    for point in range(len(points)):
        max_neighbors = max(max_neighbors, offsets[point + 1] - offsets[point])
    visited = np.full(section_count, -1, dtype=np.int64)
    touched = np.empty(min(section_count, max_neighbors), dtype=np.int64)
    opening = np.empty(max_neighbors)
    shear = np.empty(max_neighbors)
    signed_side = np.empty(max_neighbors)
    collision = parameters.collision
    subduction = parameters.subduction
    divergence = parameters.divergence
    transform = parameters.transform
    blend = parameters.blend_radii
    collision_enabled = collision[0] > 0.0 and collision[1] != 0.0
    subduction_enabled = subduction[0] > 0.0 and subduction[1] != 0.0
    divergence_enabled = divergence[0] > 0.0 and divergence[1] != 0.0
    transform_enabled = transform[0] > 0.0 and transform[1] != 0.0
    percent_per_radian = 100.0 / (2.0 * np.pi)
    subduction_transition = 2.0 * min(0.1 * subduction[0], 0.15)
    divergence_transition = 2.0 * min(0.1 * divergence[0], 0.15)

    for point in range(len(points)):
        start, end = offsets[point], offsets[point + 1]
        if start == end:
            result[point] = 0.0
            continue
        touched_count = 0
        nearest_divergence = np.inf
        nearest_transform = np.inf
        # Query-dependent frames and motion, with all static vectors retained.
        for pair in range(start, end):
            local = pair - start
            segment = segment_ids[pair]
            section = sources.section_ids[segment]
            if visited[section] != point:
                visited[section] = point
                touched[touched_count] = section
                touched_count += 1
                nearest_section[section] = np.inf
                collision_mass[section] = 0.0
                collision_force[section] = 0.0
                subduction_mass[section] = 0.0
                subduction_force[section] = 0.0
                descending_mass[section] = 0.0
            distance = distances[pair]
            nearest_section[section] = min(nearest_section[section], distance)
            if sources.divergent[segment]:
                nearest_divergence = min(nearest_divergence, distance)
            if sources.transform[segment]:
                nearest_transform = min(nearest_transform, distance)
            qx, qy, qz = closest[pair]
            ax, ay, az = sources.across_vectors[segment]
            projection = ax * qx + ay * qy + az * qz
            ax -= projection * qx
            ay -= projection * qy
            az -= projection * qz
            norm = np.sqrt(ax * ax + ay * ay + az * az)
            ax /= norm
            ay /= norm
            az /= norm
            tx, ty, tz = qy * az - qz * ay, qz * ax - qx * az, qx * ay - qy * ax
            wx, wy, wz = sources.delta_rotation[segment]
            vx, vy, vz = wy * qz - wz * qy, wz * qx - wx * qz, wx * qy - wy * qx
            opening[local] = vx * ax + vy * ay + vz * az
            shear[local] = abs(vx * tx + vy * ty + vz * tz)
            nx, ny, nz = sources.arc_normals[segment]
            dot = nx * points[point, 0] + ny * points[point, 1] + nz * points[point, 2]
            side = np.arcsin(min(max(dot, -1.0), 1.0)) * percent_per_radian
            signed_side[local] = (
                side if sources.positive_side_is_left[segment] else -side
            )

        divergence_mass = 0.0
        divergence_sum = 0.0
        transform_mass = 0.0
        transform_sum = 0.0
        continental_profile = 0.0
        oceanic_profile = 0.0
        if divergence_enabled and nearest_divergence != np.inf:
            continental_profile = divergence_value(
                nearest_divergence, divergence, 1.0, True
            )
            oceanic_profile = divergence_value(
                nearest_divergence, divergence, 1.0, False
            )
        # The nearest distance determines the profile; neighboring source motion
        # is blended, so farther flanks cannot fill a divergent axial valley.
        for pair in range(start, end):
            local = pair - start
            segment = segment_ids[pair]
            section = sources.section_ids[segment]
            distance = distances[pair]
            length = sources.lengths[segment]
            convergence = max(-opening[local], 0.0)
            if collision_enabled and sources.collision_sections[section]:
                weight = _weight(distance, nearest_section[section], blend[0], length)
                collision_mass[section] += weight
                collision_force[section] += weight * convergence
            descending = sources.descending_plates[section]
            if subduction_enabled and descending >= 0:
                weight = _weight(distance, nearest_section[section], blend[1], length)
                left = smoothstep_scalar(
                    0.5 + signed_side[local] / subduction_transition
                )
                down = (
                    left if sources.left_plates[segment] == descending else 1.0 - left
                )
                subduction_mass[section] += weight
                subduction_force[section] += weight * convergence
                descending_mass[section] += weight * down
            if divergence_enabled and sources.divergent[segment]:
                weight = _weight(distance, nearest_divergence, blend[2], length)
                left = smoothstep_scalar(
                    0.5 + signed_side[local] / divergence_transition
                )
                scale = peak_scale * max(opening[local], 0.0) * weight
                left_profile = (
                    continental_profile
                    if sources.left_continental[segment]
                    else oceanic_profile
                )
                right_profile = (
                    continental_profile
                    if sources.right_continental[segment]
                    else oceanic_profile
                )
                value = (
                    scale * left * left_profile + scale * (1.0 - left) * right_profile
                )
                divergence_mass += weight
                divergence_sum += value
            if transform_enabled and sources.transform[segment]:
                weight = _weight(distance, nearest_transform, blend[3], length)
                transform_mass += weight
                transform_sum += weight * _strength(-opening[local], shear[local])

        positive = 0.0
        negative = 0.0
        for touched_index in range(touched_count):
            section = touched[touched_index]
            if collision_enabled and collision_mass[section] > 0.0:
                force = collision_force[section] / collision_mass[section]
                positive = max(
                    positive,
                    collision_value(
                        nearest_section[section], collision, peak_scale * force
                    ),
                )
            if subduction_enabled and subduction_mass[section] > 0.0:
                force = subduction_force[section] / subduction_mass[section]
                if force <= 0.0:
                    continue
                down = descending_mass[section] / subduction_mass[section]
                distance = nearest_section[section]
                up_value = subduction_value(
                    distance, subduction, peak_scale * force, arc_variation[point]
                )
                down_value = subduction_value(
                    -distance, subduction, peak_scale * force, arc_variation[point]
                )
                value = down * down_value + (1.0 - down) * up_value
                positive = max(positive, value)
                negative = min(negative, value)
        divergent_relief = (
            divergence_sum / divergence_mass if divergence_mass > 0.0 else 0.0
        )
        transformed = 0.0
        if transform_mass > 0.0:
            transformed = transform_value(
                nearest_transform,
                transform,
                peak_scale * (transform_sum / transform_mass),
            )
        result[point] = positive + negative + divergent_relief + transformed
