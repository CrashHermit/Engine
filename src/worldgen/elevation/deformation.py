"""Batched continuous tectonic queries with retained geometry and compiled profiles."""

import numpy as np

from src.worldgen.elevation.config import DeformationConfig
from src.worldgen.elevation.kernels import (
    TectonicParameters,
    TectonicSources,
    evaluate_tectonic_batch,
)
from src.worldgen.elevation.sources import boundary_source_rows
from src.worldgen.elevation.transform import transform_strength
from src.worldgen.field.noise import noise_multiplier
from src.worldgen.geometry.boundary import BoundaryNetwork, arc_distances
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.model import GeologyResult


_QUERY_BATCH_SIZE = 1024
_PERCENT_PER_RADIAN = 100.0 / (2.0 * np.pi)


def _parameters(config: DeformationConfig) -> tuple[TectonicParameters, float]:
    """Pack immutable settings once for the compiled evaluator."""
    collision, subduction = config.collision, config.subduction
    divergence, transform = config.divergence, config.transform
    support = (
        collision.width_percent,
        subduction.width_percent
        * max(
            1.0,
            subduction.trench_width_fraction,
            subduction.arc_offset_fraction + subduction.arc_width_fraction,
        ),
        divergence.width_percent,
        transform.width_percent,
    )
    blend = tuple(max(0.0, min(0.2 * width, 0.5)) for width in support)
    parameters = TectonicParameters(
        tuple(
            float(value)
            for value in (
                collision.width_percent,
                collision.height_percent,
                collision.crest_width_fraction,
                collision.crest_height_multiplier,
            )
        ),
        tuple(
            float(value)
            for value in (
                subduction.width_percent,
                subduction.height_percent,
                subduction.trench_width_fraction,
                subduction.arc_offset_fraction,
                subduction.arc_width_fraction,
                subduction.arc_height_multiplier,
                subduction.trench_depth_multiplier,
            )
        ),
        tuple(
            float(value)
            for value in (
                divergence.width_percent,
                divergence.height_percent,
                divergence.axial_width_fraction,
                divergence.axial_depth_multiplier,
                divergence.shoulder_height_multiplier,
            )
        ),
        (float(transform.width_percent), float(transform.height_percent)),
        blend,
    )
    return parameters, max(support) + max(blend)


class TectonicField:
    """Indexed source definitions; query batches never regenerate their geography."""

    def __init__(
        self,
        mesh: Mesh,
        geology: GeologyResult,
        config: DeformationConfig,
        *,
        boundary: BoundaryNetwork,
        arc_noise_seed: int,
    ) -> None:
        self.config = config
        self.boundary = boundary
        self.arc_noise_seed = arc_noise_seed
        rows, section_ids = boundary_source_rows(boundary, geology)
        edges = mesh.edges[boundary.edge_indices]
        endpoints = mesh.vertices[edges]
        delta = (
            geology.plate_rotation[boundary.right_labels]
            - geology.plate_rotation[boundary.left_labels]
        )
        self.max_motion = float(np.linalg.norm(delta, axis=1).max(initial=0.0))
        normals = np.cross(boundary.starts, boundary.ends)
        normal_lengths = np.linalg.norm(normals, axis=1)
        positive_side_is_left = np.sum(normals * endpoints[:, 0], axis=1) >= 0.0
        normals = normals / normal_lengths[:, None]
        lengths = (
            np.arctan2(normal_lengths, np.sum(boundary.starts * boundary.ends, axis=1))
            * _PERCENT_PER_RADIAN
        )
        across = endpoints[:, 1] - endpoints[:, 0]
        self._sources = TectonicSources(
            delta_rotation=delta,
            arc_normals=normals,
            positive_side_is_left=positive_side_is_left,
            across_vectors=across,
            lengths=lengths,
            section_ids=section_ids,
            left_plates=boundary.left_labels,
            left_continental=geology.crust.continental_mask[edges[:, 0]],
            right_continental=geology.crust.continental_mask[edges[:, 1]],
            descending_plates=geology.boundary_sections.subducting_plate_ids,
            collision_sections=geology.boundary_sections.continental_sides.all(axis=1),
            divergent=geology.boundary_divergence[rows] > 0.0,
            transform=transform_strength(
                geology.boundary_convergence[rows] - geology.boundary_divergence[rows],
                geology.boundary_shear[rows],
            )
            != 0.0,
        )
        for array in self._sources:
            array.setflags(write=False)
        self._parameters, self._query_radius = _parameters(config)
        self._enabled = any(
            process.width_percent > 0.0 and process.height_percent != 0.0
            for process in (
                config.collision,
                config.subduction,
                config.divergence,
                config.transform,
            )
        )

    def sample(self, points: np.ndarray, radius_m: float) -> np.ndarray:
        """Evaluate exact finite-arc geometry in bounded batches, then compiled reductions."""
        points = np.asarray(points, dtype=np.float64)
        shape = points.shape[:-1]
        flat = points.reshape((-1, 3))
        result = np.zeros(len(flat), dtype=np.float64)
        if not len(flat) or not len(self.boundary.edge_indices) or not self._enabled:
            return result.reshape(shape)
        subduction = self.config.subduction
        if subduction.width_percent > 0.0 and subduction.height_percent != 0.0:
            arc_variation = noise_multiplier(
                flat,
                seed=self.arc_noise_seed,
                frequency=subduction.arc_noise_frequency,
                strength=subduction.arc_variation_strength,
            )
        else:
            arc_variation = np.ones(len(flat), dtype=np.float64)
        for start in range(0, len(flat), _QUERY_BATCH_SIZE):
            end = min(start + _QUERY_BATCH_SIZE, len(flat))
            batch = flat[start:end]
            candidates = self.boundary.candidates(batch, self._query_radius)
            counts = np.fromiter(
                (len(ids) for ids in candidates), dtype=np.int64, count=len(batch)
            )
            offsets = np.empty(len(batch) + 1, dtype=np.int64)
            offsets[0] = 0
            np.cumsum(counts, out=offsets[1:])
            if offsets[-1] == 0:
                continue
            segments = np.concatenate(candidates)
            point_ids = np.repeat(np.arange(len(batch)), counts)
            distances, closest = arc_distances(
                batch[point_ids],
                self.boundary.starts[segments],
                self.boundary.ends[segments],
            )
            evaluate_tectonic_batch(
                batch,
                offsets,
                segments,
                distances,
                closest,
                arc_variation[start:end],
                self._sources,
                self._parameters,
                radius_m / 100.0,
                result[start:end],
            )
        return result.reshape(shape)
