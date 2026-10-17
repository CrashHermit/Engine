"""Continuous elevation contributions from retained spherical boundary sources."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from src.worldgen.elevation.collision import collision_value
from src.worldgen.elevation.config import DeformationConfig
from src.worldgen.elevation.divergence import divergence_value
from src.worldgen.elevation.sources import boundary_source_rows
from src.worldgen.elevation.subduction import subduction_value
from src.worldgen.elevation.transform import transform_strength, transform_value
from src.worldgen.field.noise import noise_multiplier
from src.worldgen.geometry.boundary import arc_distances
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.utilities.curves import smoothstep_scalar

if TYPE_CHECKING:
    from src.worldgen.geometry.boundary import BoundaryNetwork
    from src.worldgen.geology.model import GeologyResult

_PERCENT_PER_RADIAN = 100.0 / (2.0 * np.pi)


def _source_weights(
    distances: np.ndarray, segment_lengths: np.ndarray, blend_radius: float
) -> tuple[float, np.ndarray]:
    """Blend nearby sources by compact distance kernel and arc length."""
    nearest = float(distances.min())
    weights = np.asarray(
        [
            smoothstep_scalar((nearest + blend_radius - float(distance)) / blend_radius)
            * float(length)
            for distance, length in zip(distances, segment_lengths)
        ]
    )
    weights /= float(weights.sum())
    return nearest, weights


class TectonicField:
    """Indexed tectonic profiles evaluated continuously at arbitrary positions.

    Motion is reevaluated from retained plate rotations at each closest arc point.
    Collision and subduction combine coherent section profiles by extrema.
    Divergence uses one nearest coherent source distance with compact, normalized
    blending; transform uses the same blend for signed source strength. This avoids
    graph propagation, per-edge stacking, and distant divergent flanks filling axes.
    """

    def __init__(
        self,
        mesh: Mesh,
        geology: GeologyResult,
        config: DeformationConfig,
        *,
        boundary: BoundaryNetwork,
        arc_noise_seed: int,
    ) -> None:
        self.mesh = mesh
        self.geology = geology
        self.config = config
        self.boundary = boundary
        self.arc_noise_seed = arc_noise_seed
        self._segment_rows, self._section_ids = boundary_source_rows(boundary, geology)
        delta_omega = (
            geology.plate_rotation[boundary.right_labels]
            - geology.plate_rotation[boundary.left_labels]
        )
        self.max_motion = float(np.linalg.norm(delta_omega, axis=1).max(initial=0.0))
        edges = mesh.edges[boundary.edge_indices]
        self._left_continental = geology.crust.continental_mask[edges[:, 0]]
        self._right_continental = geology.crust.continental_mask[edges[:, 1]]
        arc_normals = np.cross(boundary.starts, boundary.ends)
        self._positive_side_is_left = (
            np.sum(arc_normals * mesh.vertices[edges[:, 0]], axis=1) >= 0.0
        )
        self._segment_lengths = (
            np.arctan2(
                np.linalg.norm(np.cross(boundary.starts, boundary.ends), axis=1),
                np.sum(boundary.starts * boundary.ends, axis=1),
            )
            * _PERCENT_PER_RADIAN
        )
        rows = self._segment_rows
        self._divergent_sources = geology.boundary_divergence[rows] > 0.0
        self._transform_sources = (
            transform_strength(
                geology.boundary_convergence[rows] - geology.boundary_divergence[rows],
                geology.boundary_shear[rows],
            )
            != 0.0
        )

    def sample(self, points: np.ndarray, radius_m: float) -> np.ndarray:
        points = np.asarray(points, dtype=np.float64)
        shape = points.shape[:-1]
        flat = points.reshape((-1, 3))
        if len(flat) == 0:
            return np.empty(shape, dtype=np.float64)
        cfg = self.config
        subduction_support = cfg.subduction.width_percent * max(
            1.0,
            cfg.subduction.trench_width_fraction,
            cfg.subduction.arc_offset_fraction + cfg.subduction.arc_width_fraction,
        )
        support_widths = (
            cfg.collision.width_percent,
            subduction_support,
            cfg.divergence.width_percent,
            cfg.transform.width_percent,
        )
        max_width = max(support_widths)
        result = np.zeros(len(flat), dtype=np.float64)
        if max_width <= 0.0 or len(self.boundary.edge_indices) == 0:
            return result.reshape(shape)
        blend_radii = tuple(max(0.0, min(0.2 * width, 0.5)) for width in support_widths)
        max_blend_radius = max(blend_radii)
        candidate_sets = self.boundary.candidates(flat, max_width + max_blend_radius)
        rotations = self.geology.plate_rotation
        sections = self.geology.boundary_sections
        peak_scale = radius_m / 100.0
        subduction = cfg.subduction
        if subduction.width_percent > 0.0 and subduction.height_percent != 0.0:
            arc_variation = noise_multiplier(
                flat,
                seed=self.arc_noise_seed,
                frequency=subduction.arc_noise_frequency,
                strength=subduction.arc_variation_strength,
            )
        else:
            arc_variation = np.ones(len(flat), dtype=np.float64)

        for point_id, candidate_ids in enumerate(candidate_sets):
            if not len(candidate_ids):
                continue
            segment_ids = candidate_ids
            query = flat[point_id]
            distances, closest = arc_distances(
                np.broadcast_to(query, (len(segment_ids), 3)),
                self.boundary.starts[segment_ids],
                self.boundary.ends[segment_ids],
            )
            section_ids = self._section_ids[segment_ids]
            left_plate = self.boundary.left_labels[segment_ids]
            right_plate = self.boundary.right_labels[segment_ids]
            delta_omega = rotations[right_plate] - rotations[left_plate]
            arc_normals = np.cross(
                self.boundary.starts[segment_ids], self.boundary.ends[segment_ids]
            )
            arc_normals /= np.linalg.norm(arc_normals, axis=1, keepdims=True)
            signed_side = (
                np.arcsin(np.clip(arc_normals @ query, -1.0, 1.0)) * _PERCENT_PER_RADIAN
            )
            positive_side_is_left = self._positive_side_is_left[segment_ids]
            signed_side = np.where(positive_side_is_left, signed_side, -signed_side)

            edge_ends = self.mesh.vertices[
                self.mesh.edges[self.boundary.edge_indices[segment_ids]]
            ]
            across = edge_ends[:, 1] - edge_ends[:, 0]
            across -= np.sum(across * closest, axis=1, keepdims=True) * closest
            across /= np.linalg.norm(across, axis=1, keepdims=True)
            along = np.cross(closest, across)
            relative_velocity = np.cross(delta_omega, closest)
            opening = np.sum(relative_velocity * across, axis=1)
            convergence = np.maximum(-opening, 0.0)
            divergence = np.maximum(opening, 0.0)
            shear = np.abs(np.sum(relative_velocity * along, axis=1))
            positive = 0.0
            negative = 0.0
            divergent_relief = 0.0
            transform_relief = 0.0

            if (
                cfg.collision.width_percent > 0.0
                and cfg.collision.height_percent != 0.0
            ):
                for section_id in np.unique(section_ids):
                    if not sections.continental_sides[section_id].all():
                        continue
                    ids = np.flatnonzero(section_ids == section_id)
                    nearest, weights = _source_weights(
                        distances[ids],
                        self._segment_lengths[segment_ids[ids]],
                        blend_radii[0],
                    )
                    strength = float(np.dot(weights, convergence[ids]))
                    value = float(
                        collision_value(
                            np.asarray([nearest]),
                            cfg.collision,
                            np.asarray([peak_scale * strength]),
                        )[0]
                    )
                    positive = max(positive, value)

            if (
                cfg.subduction.width_percent > 0.0
                and cfg.subduction.height_percent != 0.0
            ):
                for section_id in np.unique(section_ids):
                    descending = int(sections.subducting_plate_ids[section_id])
                    if descending < 0:
                        continue
                    ids = np.flatnonzero(section_ids == section_id)
                    nearest, weights = _source_weights(
                        distances[ids],
                        self._segment_lengths[segment_ids[ids]],
                        blend_radii[1],
                    )
                    strength = float(np.dot(weights, convergence[ids]))
                    if strength <= 0.0:
                        continue
                    transition = min(0.1 * subduction.width_percent, 0.15)
                    left_weights = np.asarray(
                        [
                            smoothstep_scalar(
                                0.5 + float(signed_side[index]) / (2.0 * transition)
                            )
                            for index in ids
                        ]
                    )
                    descending_is_left = left_plate[ids] == descending
                    descending_weights = np.where(
                        descending_is_left, left_weights, 1.0 - left_weights
                    )
                    descending_weight = float(np.dot(weights, descending_weights))
                    value_positive = float(
                        subduction_value(
                            np.asarray([nearest]),
                            subduction,
                            np.asarray([peak_scale * strength]),
                            np.asarray([arc_variation[point_id]]),
                        )[0]
                    )
                    value_negative = float(
                        subduction_value(
                            np.asarray([-nearest]),
                            subduction,
                            np.asarray([peak_scale * strength]),
                            np.asarray([arc_variation[point_id]]),
                        )[0]
                    )
                    value = (
                        descending_weight * value_negative
                        + (1.0 - descending_weight) * value_positive
                    )
                    positive = max(positive, value)
                    negative = min(negative, value)

            if (
                cfg.divergence.width_percent > 0.0
                and cfg.divergence.height_percent != 0.0
            ):
                source_ids = np.flatnonzero(self._divergent_sources[segment_ids])
                if len(source_ids):
                    nearest, weights = _source_weights(
                        distances[source_ids],
                        self._segment_lengths[segment_ids[source_ids]],
                        blend_radii[2],
                    )
                    transition = min(0.1 * cfg.divergence.width_percent, 0.15)
                    left_weights = np.asarray(
                        [
                            smoothstep_scalar(
                                0.5 + float(signed_side[index]) / (2.0 * transition)
                            )
                            for index in source_ids
                        ]
                    )
                    source_scale = peak_scale * divergence[source_ids] * weights
                    profile_distances = np.full(len(source_ids), nearest)
                    left_values = divergence_value(
                        profile_distances,
                        cfg.divergence,
                        source_scale * left_weights,
                        self._left_continental[segment_ids[source_ids]],
                    )
                    right_values = divergence_value(
                        profile_distances,
                        cfg.divergence,
                        source_scale * (1.0 - left_weights),
                        self._right_continental[segment_ids[source_ids]],
                    )
                    divergent_relief = float((left_values + right_values).sum())

            if (
                cfg.transform.width_percent > 0.0
                and cfg.transform.height_percent != 0.0
            ):
                source_ids = np.flatnonzero(self._transform_sources[segment_ids])
                if len(source_ids):
                    nearest, weights = _source_weights(
                        distances[source_ids],
                        self._segment_lengths[segment_ids[source_ids]],
                        blend_radii[3],
                    )
                    strength = float(
                        np.dot(
                            weights,
                            transform_strength(-opening[source_ids], shear[source_ids]),
                        )
                    )
                    transform_relief = float(
                        transform_value(
                            np.asarray([nearest]),
                            cfg.transform,
                            np.asarray([peak_scale * strength]),
                        )[0]
                    )

            result[point_id] = positive + negative + divergent_relief + transform_relief
        return result.reshape(shape)
