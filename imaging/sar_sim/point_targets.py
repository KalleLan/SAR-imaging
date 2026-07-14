"""Point-target scene and simulated raw/range-compressed FMCW data.

Wraps torchbp.util.generate_fmcw_data (raw FMCW beat signal, see
imaging/README.md "torchbp API -muistiinpanot") instead of re-deriving the
point-target physics. The range-compression recipe (ifft, rvp=False,
Hamming window, FFT oversampling) is copied from torchbp's own test suite
(tests/test_ffbp.py::TestFfbpDem._terrain_scene), which torchbp uses to
verify that backprojection recovers known point-target positions.
"""

from typing import Tuple

import torch

from .geometry import RadarParams


def default_target_grid(
    center_range: float = 100.0, spacing: float = 10.0, n_side: int = 3
) -> torch.Tensor:
    """N x N point-target grid on the ground plane (z=0).

    x (ground range) is centered on center_range, y (along-rail) is centered
    on 0, spacing meters between neighbors. Returns [n_side**2, 3] float32.
    """
    offsets = spacing * (torch.arange(n_side, dtype=torch.float32) - (n_side - 1) / 2)
    gx, gy = torch.meshgrid(offsets, offsets, indexing="ij")
    x = center_range + gx.reshape(-1)
    y = gy.reshape(-1)
    z = torch.zeros_like(x)
    return torch.stack([x, y, z], dim=-1)


def target_polar_coords(targets: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Convert ground-plane XYZ targets to the (r, theta=sin(angle)) polar
    grid convention backprojection_polar_2d expects (imaging/README.md)."""
    r = torch.linalg.norm(targets[:, :2], dim=-1)
    theta = targets[:, 1] / r
    return r, theta


def simulate_point_targets(
    pos: torch.Tensor,
    targets: torch.Tensor,
    params: RadarParams,
    target_rcs: torch.Tensor = None,
) -> torch.Tensor:
    """Simulate range-compressed FMCW data for point targets.

    Parameters
    ----------
    pos : Tensor
        [nsweeps, 3] platform positions (see geometry.straight_rail_trajectory).
    targets : Tensor
        [ntargets, 3] target XYZ positions.
    params : RadarParams
    target_rcs : Tensor or None
        [ntargets, 1] complex reflectivity. Defaults to unit reflectivity.

    Returns
    -------
    data : Tensor
        [nsweeps, nsamples*oversample] complex64 range-compressed data,
        suitable for torchbp.ops.backprojection_polar_2d (r_res=params.r_res).
    """
    import torchbp  # optional dependency, installed manually per imaging/README.md

    n_targets = targets.shape[0]
    if target_rcs is None:
        target_rcs = torch.ones((n_targets, 1), dtype=torch.complex64)

    raw = torchbp.util.generate_fmcw_data(
        targets, target_rcs, pos, params.fc, params.bw, params.tsweep, params.fs,
        rvp=False,
    )
    nsamples = raw.shape[-1]
    window = torch.hamming_window(nsamples, periodic=False, dtype=torch.float32)
    n_fft = int(round(nsamples * params.oversample))
    data = torch.fft.ifft(raw * window[None, :], dim=-1, n=n_fft)
    return data
