"""Unit tests for sar_sim: no GPU required. torchbp-dependent tests are
skipped automatically if torchbp is not installed (see imaging/README.md
for the manual build step)."""

import math
import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sar_sim.errors import linear_drift, random_walk, sinusoidal_wobble
from sar_sim.geometry import RadarParams, straight_rail_trajectory
from sar_sim.point_targets import default_target_grid, target_polar_coords


def test_straight_rail_trajectory_shape_and_spacing():
    params = RadarParams(rail_length=5.0, altitude=20.0)
    pos = straight_rail_trajectory(params)
    assert pos.shape[1] == 3
    assert pos.dtype == torch.float32
    assert torch.allclose(pos[:, 0], torch.zeros(pos.shape[0]))
    assert torch.allclose(pos[:, 2], torch.full((pos.shape[0],), params.altitude))
    dy = torch.diff(pos[:, 1])
    assert torch.allclose(dy, torch.full_like(dy, params.sample_spacing), atol=1e-6)
    assert abs(float(pos[:, 1].mean())) < 1e-4


def test_straight_rail_trajectory_sample_count_matches_task_reference():
    # docs/tehtavat/2026-07-11_vaihe0_imaging_runko.md: "5 m -> 400 nayteta
    # lambda/4-valein" (approximated with lambda/4 ~= 12.5 mm at 6 GHz).
    params = RadarParams(rail_length=5.0)
    pos = straight_rail_trajectory(params)
    assert abs(pos.shape[0] - 400) <= 2


def test_default_target_grid_shape_and_layout():
    targets = default_target_grid(center_range=100.0, spacing=10.0, n_side=3)
    assert targets.shape == (9, 3)
    assert torch.allclose(targets[:, 2], torch.zeros(9))
    assert float(targets[:, 0].min()) == pytest.approx(90.0)
    assert float(targets[:, 0].max()) == pytest.approx(110.0)
    assert float(targets[:, 1].min()) == pytest.approx(-10.0)
    assert float(targets[:, 1].max()) == pytest.approx(10.0)


def test_target_polar_coords_matches_grid_convention():
    targets = default_target_grid(center_range=100.0, spacing=0.0, n_side=1)
    r, theta = target_polar_coords(targets)
    assert torch.allclose(r, torch.tensor([100.0]))
    assert torch.allclose(theta, torch.tensor([0.0]), atol=1e-6)


def test_simulate_point_targets_shape_and_dtype():
    pytest.importorskip("torchbp")
    from sar_sim.point_targets import simulate_point_targets

    params = RadarParams(rail_length=1.0)
    pos = straight_rail_trajectory(params)
    targets = default_target_grid(center_range=100.0, spacing=10.0, n_side=3)
    data = simulate_point_targets(pos, targets, params)
    assert data.dtype == torch.complex64
    assert data.shape[0] == pos.shape[0]
    expected_fft_len = int(round(params.nsamples * params.oversample))
    assert data.shape[1] == expected_fft_len


def test_simulate_point_targets_range_bin_increases_with_distance():
    """A more distant target must range-compress to a larger sample index."""
    pytest.importorskip("torchbp")
    from sar_sim.point_targets import simulate_point_targets

    params = RadarParams(rail_length=0.1)
    pos = straight_rail_trajectory(params)
    near = torch.tensor([[50.0, 0.0, 0.0]])
    far = torch.tensor([[150.0, 0.0, 0.0]])
    data_near = simulate_point_targets(pos, near, params)
    data_far = simulate_point_targets(pos, far, params)
    bin_near = torch.argmax(data_near[0].abs())
    bin_far = torch.argmax(data_far[0].abs())
    assert bin_far > bin_near


def test_linear_drift_reaches_magnitude():
    pos = torch.zeros(10, 3)
    pos_err, err = linear_drift(pos, magnitude=0.2, axis=0)
    assert torch.allclose(err[0], torch.zeros(3))
    assert math.isclose(float(err[-1, 0]), 0.2, rel_tol=1e-5)
    assert torch.allclose(pos_err, pos + err)


def test_sinusoidal_wobble_amplitude_and_axis_isolation():
    pos = torch.zeros(200, 3)
    amp = 0.02
    pos_err, err = sinusoidal_wobble(pos, amplitude=amp, cycles=5.0, axis=0)
    assert float(err[:, 0].abs().max()) <= amp + 1e-6
    assert float(err[:, 0].abs().max()) > 0.9 * amp
    assert torch.allclose(err[:, 1:], torch.zeros(200, 2))
    assert torch.allclose(pos_err, pos + err)


def test_random_walk_starts_at_zero_and_accumulates():
    torch.manual_seed(0)
    pos = torch.zeros(500, 3)
    pos_err, err = random_walk(pos, step_std=0.01, axis=0)
    assert float(err[0, 0]) == 0.0
    assert float(err[:, 0].std()) > 0.0
    assert torch.allclose(pos_err, pos + err)
    assert torch.allclose(err[:, 1:], torch.zeros(500, 2))
