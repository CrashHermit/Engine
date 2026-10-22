import numpy as np

from src.worldgen.field.rod import RodScalarField, rod_relief


def test_rod_relief_has_radial_support_and_smooth_axial_tapers() -> None:
    field = RodScalarField(
        directions=np.array([[0.0, 0.0, 7.0]]),
        widths=np.array([0.2]),
        lengths=np.array([2.0]),
        heights=np.array([3.0]),
        taper_fraction=0.1,
        profile_power=2.0,
    )
    points = np.array(
        [
            [0.0, 0.0, 1.0],
            [0.1, 0.0, 1.0],
            [0.2, 0.0, 1.0],
            [0.0, 0.0, -1.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 2.0],
            [0.0, 0.0, 0.1],
            [0.0, 0.0, 1.9],
        ]
    )
    np.testing.assert_allclose(
        field.sample(points), [3.0, 1.6875, 0.0, 0.0, 0.0, 0.0, 1.5, 1.5]
    )

    # Position remains source-space Cartesian data; it is not projected to a sphere.
    np.testing.assert_allclose(field.sample(np.array([[0.0, 0.0, 0.5]])), [3.0])
    np.testing.assert_allclose(
        rod_relief(
            np.array([1.0]),
            np.array([0.01]),
            width=0.2,
            length=2.0,
            height=3.0,
        ),
        [1.6875],
    )


def test_raw_direction_scale_does_not_change_rod_geometry() -> None:
    points = np.array([[0.04, 0.0, 1.0], [0.0, 0.0, 1.0]])
    fields = [
        RodScalarField(
            directions=np.array([[0.0, 0.0, scale]]),
            widths=np.array([0.2]),
            lengths=np.array([2.0]),
            heights=np.array([3.0]),
        )
        for scale in (0.01, 1.0, 97.0)
    ]
    for field in fields[1:]:
        np.testing.assert_array_equal(field.sample(points), fields[0].sample(points))


def test_rods_add_independently_and_zero_or_empty_samples_are_immutable() -> None:
    points = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 1.0], [0.0, 0.1, 0.1]])
    both = RodScalarField(
        directions=np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]),
        widths=np.array([0.4, 0.4]),
        lengths=np.array([2.0, 2.0]),
        heights=np.array([2.0, 5.0]),
    )
    components = [
        RodScalarField(
            directions=np.array([direction]),
            widths=np.array([0.4]),
            lengths=np.array([2.0]),
            heights=np.array([height]),
        ).sample(points)
        for direction, height in (([0.0, 0.0, 1.0], 2.0), ([0.0, 1.0, 0.0], 5.0))
    ]
    np.testing.assert_array_equal(both.sample(points), components[0] + components[1])
    assert components[0][-1] > 0 and components[1][-1] > 0

    empty_rods = RodScalarField(
        directions=np.empty((0, 3)),
        widths=np.empty(0),
        lengths=np.empty(0),
        heights=np.empty(0),
    )
    no_rods = empty_rods.sample(points)
    no_points = both.sample(np.empty((0, 3)))
    for result, shape in ((no_rods, (3,)), (no_points, (0,))):
        assert result.dtype == np.float64
        assert result.shape == shape
        assert not result.flags.writeable
        np.testing.assert_array_equal(result, np.zeros(shape, dtype=np.float64))


def test_multipliers_modulate_width_length_and_height() -> None:
    base = RodScalarField(
        directions=np.array([[0.0, 0.0, 1.0]]),
        widths=np.array([0.2]),
        lengths=np.array([2.0]),
        heights=np.array([3.0]),
    )
    width_changed = RodScalarField(
        directions=np.array([[0.0, 0.0, 1.0]]),
        widths=np.array([0.2]),
        lengths=np.array([2.0]),
        heights=np.array([3.0]),
        sample_width_multiplier=lambda query: np.full(len(query), 2.0),
    )
    height_changed = RodScalarField(
        directions=np.array([[0.0, 0.0, 1.0]]),
        widths=np.array([0.2]),
        lengths=np.array([2.0]),
        heights=np.array([3.0]),
        sample_height_multiplier=lambda query: np.full(len(query), 0.5),
    )
    length_changed = RodScalarField(
        directions=np.array([[0.0, 0.0, 1.0]]),
        widths=np.array([0.2]),
        lengths=np.array([2.0]),
        heights=np.array([3.0]),
        sample_length_multiplier=lambda query: np.full(len(query), 2.0),
    )
    np.testing.assert_allclose(
        width_changed.sample([[0.2, 0.0, 1.0]]), base.sample([[0.1, 0.0, 1.0]])
    )
    np.testing.assert_allclose(height_changed.sample([[0.0, 0.0, 1.0]]), [1.5])
    np.testing.assert_allclose(base.sample([[0.0, 0.0, 3.0]]), [0.0])
    assert length_changed.sample(np.array([[0.0, 0.0, 3.0]]))[0] > 0.0


def test_callbacks_are_once_per_nonempty_batch_and_split_sampling_is_stable() -> None:
    calls = {"width": 0, "length": 0, "height": 0}

    def callback(name: str):
        def sample(query: np.ndarray) -> np.ndarray:
            calls[name] += 1
            return 1.0 + query[:, 0] * 0.1

        return sample

    directions = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    widths = np.array([0.2, 0.3])
    lengths = np.array([2.0, 2.0])
    heights = np.array([2.0, 3.0])
    field = RodScalarField(
        directions,
        widths,
        lengths,
        heights,
        sample_width_multiplier=callback("width"),
        sample_length_multiplier=callback("length"),
        sample_height_multiplier=callback("height"),
    )
    points = np.array([[0.01, 0.0, 1.0], [0.0, 0.01, 1.0], [0.02, 0.0, 1.2]])
    original_points = points.copy()
    expected = field.sample(points)
    assert calls == {"width": 1, "length": 1, "height": 1}
    calls.update(width=0, length=0, height=0)
    split = np.concatenate([field.sample(points[:1]), field.sample(points[1:])])
    np.testing.assert_allclose(split, expected)
    assert calls == {"width": 2, "length": 2, "height": 2}
    reordered = field.sample(points[[2, 0, 1]])
    np.testing.assert_allclose(reordered[[1, 2, 0]], expected)
    np.testing.assert_array_equal(points, original_points)

    calls.update(width=0, length=0, height=0)
    field.sample(np.empty((0, 3)))
    empty = RodScalarField(
        np.empty((0, 3)),
        np.empty(0),
        np.empty(0),
        np.empty(0),
        sample_width_multiplier=callback("width"),
        sample_length_multiplier=callback("length"),
        sample_height_multiplier=callback("height"),
    )
    empty.sample(points)
    assert calls == {"width": 0, "length": 0, "height": 0}


def test_rod_definition_arrays_are_owned_and_read_only() -> None:
    inputs = [
        np.array([[0.0, 0.0, 3.0]]),
        np.array([0.2]),
        np.array([2.0]),
        np.array([3.0]),
    ]
    field = RodScalarField(*inputs)
    inputs[0][0, 2] = 100.0
    inputs[1][0] = 99.0
    np.testing.assert_array_equal(field.directions, [[0.0, 0.0, 1.0]])
    np.testing.assert_array_equal(field.widths, [0.2])
    for array in (field.directions, field.widths, field.lengths, field.heights):
        assert not array.flags.writeable
        try:
            array[0] = 1.0
        except ValueError:
            pass
        else:
            raise AssertionError("rod definitions must be immutable")
