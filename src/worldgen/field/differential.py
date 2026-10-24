"""Cartesian differential sampling contracts shared by continuous fields."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class ScalarSample:
    """Scalar values (N,) and input-coordinate gradients (N, 3)."""

    values: np.ndarray
    gradients: np.ndarray

    def __post_init__(self) -> None:
        self.values.setflags(write=False)
        self.gradients.setflags(write=False)


@dataclass(frozen=True, slots=True)
class VectorSample:
    """Vectors/coordinates (N, 3) and Jacobians (N, output_axis, input_axis)."""

    values: np.ndarray
    jacobians: np.ndarray

    def __post_init__(self) -> None:
        self.values.setflags(write=False)
        self.jacobians.setflags(write=False)


@dataclass(frozen=True, slots=True)
class ScalarHessianSample:
    """Scalar values, gradients, and Hessians (query, input_axis, input_axis)."""

    values: np.ndarray
    gradients: np.ndarray
    hessians: np.ndarray

    def __post_init__(self) -> None:
        self.values.setflags(write=False)
        self.gradients.setflags(write=False)
        self.hessians.setflags(write=False)


@dataclass(frozen=True, slots=True)
class VectorHessianSample:
    """Map values, Jacobians, and Hessians (query, output_axis, input, input)."""

    values: np.ndarray
    jacobians: np.ndarray
    hessians: np.ndarray

    def __post_init__(self) -> None:
        self.values.setflags(write=False)
        self.jacobians.setflags(write=False)
        self.hessians.setflags(write=False)


type ScalarGradientSampler = Callable[[np.ndarray], ScalarSample]
type VectorJacobianSampler = Callable[[np.ndarray], VectorSample]
type ScalarHessianSampler = Callable[[np.ndarray], ScalarHessianSample]
type VectorHessianSampler = Callable[[np.ndarray], VectorHessianSample]


def sum_indexed_scalar_samples(
    query_indices: np.ndarray, sample: ScalarSample, query_count: int
) -> ScalarSample:
    """Reduce sparse scalar contributions and gradients into their query rows."""
    values = np.asarray(
        np.bincount(query_indices, weights=sample.values, minlength=query_count),
        dtype=np.float64,
    )
    gradients = np.empty((query_count, 3), dtype=np.float64)
    for axis in range(3):
        gradients[:, axis] = np.bincount(
            query_indices, weights=sample.gradients[:, axis], minlength=query_count
        )
    return ScalarSample(values, gradients)
