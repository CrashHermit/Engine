from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field
from src.worldgen.elevation.volcanism import VolcanicField, VolcanismConfig
from src.worldgen.field.noise import NoiseConfig, normalized_noise


def _noise_free_config(**overrides):
    config = replace(
        VolcanismConfig(),
        arc_strength=0.0,
        hotspot_count=1,
        hotspot_width_noise_strength=0.0,
        hotspot_height_noise_strength=0.0,
    )
    return replace(config, **overrides)


def test_hotspot_rods_are_retained_seeded_and_sampled_at_rod_centerlines():
    geology = generate_world_field(WorldgenConfig(seed=31415)).geology
    config = _noise_free_config()
    global_state = np.random.get_state()
    field = VolcanicField(geology, 9182, config)
    same = VolcanicField(geology, 9182, config)
    different = VolcanicField(geology, 9183, config)
    np.testing.assert_array_equal(field.hotspots.directions, same.hotspots.directions)
    np.testing.assert_array_equal(field.hotspots.widths, same.hotspots.widths)
    np.testing.assert_array_equal(field.hotspots.heights, same.hotspots.heights)
    assert not np.array_equal(field.hotspots.directions, different.hotspots.directions)
    np.testing.assert_array_equal(global_state[1], np.random.get_state()[1])
    assert global_state[0] == np.random.get_state()[0]
    assert global_state[2:] == np.random.get_state()[2:]

    original_definitions = tuple(
        getattr(field.hotspots, name).copy()
        for name in ("directions", "widths", "lengths", "heights")
    )
    direction = field.hotspots.directions[0]
    midpoint = direction * (field.hotspots.lengths[0] * 0.5)
    across = np.cross(direction, [0.0, 0.0, 1.0])
    if np.linalg.norm(across) < 1e-8:
        across = np.cross(direction, [0.0, 1.0, 0.0])
    across /= np.linalg.norm(across)
    outside = midpoint + across * field.hotspots.widths[0] * 1.01
    query = np.array([midpoint, outside, -midpoint])
    first = field.sample(query)
    second = field.sample(query)
    assert first.strength[0] > 0
    assert first.strength[1] == 0
    assert first.strength[2] == 0
    np.testing.assert_array_equal(first.relief, second.relief)
    for name, original in zip(
        ("directions", "widths", "lengths", "heights"), original_definitions
    ):
        np.testing.assert_array_equal(getattr(field.hotspots, name), original)
    assert not field.sample_intraplate(query).flags.writeable


def test_hotspot_count_zero_removes_only_intraplate_relief_and_length_sets_support():
    geology = generate_world_field(WorldgenConfig(seed=2026)).geology
    p = np.random.default_rng(73).uniform(-1.2, 1.2, (193, 3))
    without_hotspots = VolcanicField(
        geology,
        70,
        replace(VolcanismConfig(), hotspot_count=0),
    )
    np.testing.assert_array_equal(
        without_hotspots.sample_intraplate(p), np.zeros(len(p))
    )
    # Arc volcanism remains active when the independent hotspot set is empty.
    assert np.any(without_hotspots.sample(p).potential > 0)

    short = VolcanicField(
        geology,
        71,
        _noise_free_config(hotspot_length_percent=80.0),
    )
    long = VolcanicField(
        geology,
        71,
        _noise_free_config(hotspot_length_percent=120.0),
    )
    short_direction = short.hotspots.directions[0]
    long_direction = long.hotspots.directions[0]
    assert short.sample_intraplate(short_direction[None, :])[0] == 0
    assert long.sample_intraplate(long_direction[None, :])[0] > 0


def test_hotspot_noise_is_optional_and_height_modulation_only_attenuates():
    geology = generate_world_field(WorldgenConfig(seed=123)).geology
    noise_free = VolcanicField(geology, 505, _noise_free_config())
    modulated = VolcanicField(
        geology,
        505,
        replace(
            _noise_free_config(),
            hotspot_width_noise_strength=0.0,
            hotspot_height_noise_strength=0.4,
        ),
    )
    assert noise_free.hotspots.sample_width_multiplier is None
    assert noise_free.hotspots.sample_height_multiplier is None
    assert modulated.hotspots.sample_width_multiplier is None
    assert modulated.hotspots.sample_height_multiplier is not None
    direction = noise_free.hotspots.directions[0]
    query = np.stack([direction * 0.5, direction * 0.6, direction * 0.7])
    plain_values = noise_free.sample_intraplate(query)
    modulated_values = modulated.sample_intraplate(query)
    assert np.all(modulated_values <= plain_values)
    assert np.any(modulated_values < plain_values)


def test_volcanic_concentration_is_bounded_and_query_independent():
    geology = generate_world_field(WorldgenConfig(seed=123)).geology
    field = VolcanicField(geology, 703)
    p = np.random.default_rng(17).uniform(-1.3, 1.3, (1307, 3))
    a = field.sample(p)
    b = field.sample(p[::-1])
    for name in ("potential", "strength", "relief"):
        values = getattr(a, name)
        np.testing.assert_array_equal(getattr(b, name)[::-1], values)
        np.testing.assert_array_equal(
            field.sample(p[:31]).__getattribute__(name), values[:31]
        )
        assert not values.flags.writeable
    assert np.all((a.strength >= 0) & (a.strength <= a.potential))
    assert np.any(a.strength == 0)
    assert np.any(a.strength > 0)
    assert np.any(a.potential > a.strength)
    assert a.relief.max() <= field.config.relief_height_percent / 100
    np.testing.assert_allclose(
        a.relief, a.strength * field.config.relief_height_percent / 100
    )


def test_zero_potential_sources_produce_no_volcanism_and_height_only_scales_relief():
    geology = generate_world_field(WorldgenConfig(seed=2026)).geology
    p = np.random.default_rng(21).uniform(-1, 1, (257, 3))
    config = VolcanismConfig()
    a = VolcanicField(geology, 9, config).sample(p)
    b = VolcanicField(
        geology,
        9,
        replace(config, relief_height_percent=config.relief_height_percent * 2),
    ).sample(p)
    np.testing.assert_array_equal(a.potential, b.potential)
    np.testing.assert_array_equal(a.strength, b.strength)
    np.testing.assert_array_equal(a.relief * 2, b.relief)
    zero = VolcanicField(
        geology, 9, replace(config, arc_strength=0, intraplate_strength=0)
    ).sample(p)
    np.testing.assert_array_equal(zero.relief, np.zeros(len(p)))
    empty = VolcanicField(geology, 9).sample(np.empty((0, 3)))
    assert empty.relief.shape == (0,)
    assert not empty.relief.flags.writeable


def test_hotspot_saturation_has_no_kink_at_the_ceiling_or_knee_joins():
    geology = generate_world_field(WorldgenConfig(seed=123)).geology
    field = VolcanicField(
        geology,
        9182,
        _noise_free_config(
            intraplate_strength=3.0,
            hotspot_width_min_percent=20.0,
            hotspot_width_max_percent=20.0,
        ),
    )
    rod = field.hotspots
    direction = rod.directions[0]
    across = np.cross(direction, [0.0, 0.0, 1.0])
    across /= np.linalg.norm(across)
    midpoint = direction * (rod.lengths[0] * 0.5)
    peak = field.config.intraplate_strength * rod.heights[0]
    step = rod.widths[0] * 1e-6
    for raw_strength in (0.95, 1.0, 1.05):
        radius = rod.widths[0] * np.sqrt(1.0 - np.sqrt(raw_strength / peak))
        offsets = radius + np.array([-step, 0.0, step])
        points = midpoint + offsets[:, None] * across
        values = field.sample_intraplate(points)
        slopes = np.diff(values) / step
        np.testing.assert_allclose(slopes[0], slopes[1], atol=3e-3)
    assert field.sample_intraplate(midpoint[None, :])[0] == 1.0


def test_saturated_arc_and_hotspot_overlap_preserves_strength_budget():
    geology = generate_world_field(WorldgenConfig(seed=2026)).geology
    field = VolcanicField(
        geology,
        703,
        replace(VolcanismConfig(), arc_strength=20.0, intraplate_strength=5.0),
    )
    rod_midpoints = field.hotspots.directions * (field.hotspots.lengths[:, None] * 0.5)
    random_points = np.random.default_rng(17).uniform(-1.3, 1.3, (1307, 3))
    sample = field.sample(np.concatenate((rod_midpoints, random_points)))
    assert np.any(sample.strength == 1.0)
    assert np.all(sample.strength >= 0.0)
    assert np.all(sample.strength <= sample.potential)
    assert np.all(sample.potential <= 1.0)


@pytest.mark.parametrize(
    ("raw_strength", "expected"),
    [(0.5, 0.5), (1.0, 0.9875), (2.0, 1.0)],
)
def test_isolated_hotspot_is_capped_once_in_each_exposed_output(raw_strength, expected):
    geology = generate_world_field(WorldgenConfig(seed=123)).geology
    field = VolcanicField(
        geology,
        9182,
        _noise_free_config(
            intraplate_strength=raw_strength,
            hotspot_amplitude_min=1.0,
            hotspot_amplitude_max=1.0,
        ),
    )
    midpoint = field.hotspots.directions[:1] * (field.hotspots.lengths[0] * 0.5)
    diagnostic = field.sample_intraplate(midpoint)
    sample = field.sample(midpoint)
    np.testing.assert_allclose(diagnostic, [expected])
    np.testing.assert_array_equal(sample.potential, diagnostic)
    np.testing.assert_array_equal(sample.strength, diagnostic)


def test_arc_concentration_is_applied_before_the_final_amplitude_cap():
    geology = generate_world_field(WorldgenConfig(seed=2026)).geology
    probe = VolcanicField(
        geology, 703, replace(VolcanismConfig(), arc_strength=1.0, hotspot_count=0)
    )
    points = np.random.default_rng(17).uniform(-1.3, 1.3, (1307, 3))
    potential = probe.sample(points).potential
    index = np.flatnonzero((potential > 0.0) & (potential < 0.5))[0]
    point = points[index : index + 1]
    concentration = normalized_noise(
        point,
        NoiseConfig(octaves=2, base_frequency=probe.config.concentration_frequency),
        seed=probe.noise_seed + 1,
    )[0]
    field = VolcanicField(
        geology,
        703,
        replace(
            probe.config,
            arc_strength=2.0 / potential[index],
            threshold=concentration,
        ),
    )
    sample = field.sample(point)
    # Raw potential two saturates, but the half-strength gate squared reduces
    # the raw arc to one half before the final strength cap.
    np.testing.assert_allclose(sample.potential, [1.0])
    np.testing.assert_allclose(sample.strength, [0.5])


def test_volcanic_module_can_be_imported_first_and_generate_relief_in_fresh_process():
    script = """
from src.worldgen.elevation.volcanism import VolcanicField, VolcanismConfig
import json
import numpy as np
from src.worldgen.config import WorldgenConfig
from src.worldgen.generate import generate_world_field

geology = generate_world_field(WorldgenConfig(seed=123)).geology
config = VolcanismConfig(
    arc_strength=0.0,
    intraplate_strength=2.0,
    relief_height_percent=0.02,
    hotspot_count=1,
    hotspot_amplitude_min=1.0,
    hotspot_amplitude_max=1.0,
    hotspot_width_noise_strength=0.0,
    hotspot_height_noise_strength=0.0,
)
field = VolcanicField(geology, 9182, config)
midpoint = field.hotspots.directions[0] * field.hotspots.lengths[0] * 0.5
sample = field.sample(np.stack((midpoint, -midpoint)))
print(json.dumps({
    "potential": sample.potential.tolist(),
    "strength": sample.strength.tolist(),
    "relief": sample.relief.tolist(),
}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
        check=True,
    )
    values = json.loads(result.stdout)
    np.testing.assert_allclose(values["potential"], [1.0, 0.0])
    np.testing.assert_allclose(values["strength"], [1.0, 0.0])
    np.testing.assert_allclose(values["relief"], [0.0002, 0.0])
