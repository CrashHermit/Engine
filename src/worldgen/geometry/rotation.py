"""Cartesian rigid-rotation primitives."""

import numpy as np


def rotation_vectors(axes: np.ndarray, signed_speeds: np.ndarray) -> np.ndarray:
    """Return angular-velocity vectors from paired axes and signed speeds."""
    axes = np.asarray(axes, dtype=np.float64)
    signed_speeds = np.asarray(signed_speeds, dtype=np.float64)
    axis_lengths = np.linalg.norm(axes, axis=1)
    if np.any(axis_lengths == 0.0):
        raise ValueError("Rotation axes must be nonzero.")
    return axes * (signed_speeds / axis_lengths)[:, None]


def rotational_velocity(
    positions: np.ndarray, angular_velocity: np.ndarray
) -> np.ndarray:
    """Return rigid-rotation velocities as angular velocity crossed with position."""
    positions = np.asarray(positions, dtype=np.float64)
    angular_velocity = np.asarray(angular_velocity, dtype=np.float64)
    return np.cross(angular_velocity, positions)
