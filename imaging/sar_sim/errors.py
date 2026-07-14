"""Position-error injection for autofocus stress testing.

Each function takes an ideal trajectory and returns (pos_with_error, error),
where error is the [nsweeps, 3] truth vector (pos_with_error - pos), so
callers can compare an autofocus-solved trajectory against the injected
ground truth.
"""

from typing import Tuple

import torch


def linear_drift(
    pos: torch.Tensor, magnitude: float, axis: int = 0
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Linear ramp from 0 to `magnitude` meters along `axis` over the track."""
    n = pos.shape[0]
    ramp = torch.linspace(0.0, magnitude, n, dtype=pos.dtype)
    err = torch.zeros_like(pos)
    err[:, axis] = ramp
    return pos + err, err


def sinusoidal_wobble(
    pos: torch.Tensor, amplitude: float, cycles: float = 3.0, axis: int = 0
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Sinusoidal wobble along `axis`, `amplitude` meters, `cycles` periods
    over the track. Amplitude is in meters; callers typically derive it from
    the radar wavelength (reference range ~0.1-1 lambda)."""
    n = pos.shape[0]
    phase = 2 * torch.pi * cycles * torch.arange(n, dtype=pos.dtype) / (n - 1)
    err = torch.zeros_like(pos)
    err[:, axis] = amplitude * torch.sin(phase)
    return pos + err, err


def random_walk(
    pos: torch.Tensor,
    step_std: float,
    axis: int = 0,
    generator: torch.Generator = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Cumulative random-walk error along `axis`, zero at the first sweep,
    Gaussian steps with standard deviation `step_std` meters."""
    n = pos.shape[0]
    steps = torch.randn(n, generator=generator, dtype=pos.dtype) * step_std
    walk = torch.cumsum(steps, dim=0)
    walk = walk - walk[0]
    err = torch.zeros_like(pos)
    err[:, axis] = walk
    return pos + err, err
