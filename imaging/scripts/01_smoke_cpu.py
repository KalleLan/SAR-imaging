#!/usr/bin/env python3
"""torchbp-asennuksen savutesti: importti + pieni CPU-backprojection.

Tarkoitus: nopea "asennus kunnossa" -tarkistus joka toimii myos Macilla
(ei CUDAa), koska torchbp.ops.backprojection_polar_2d:lla on CPU-kerneli
(ks. imaging/README.md, osio "torchbp API -muistiinpanot").
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    try:
        import torch
        import torchbp
    except ImportError as e:
        print(f"FAIL: torch/torchbp ei importoidu: {e}")
        print("Katso imaging/README.md, osio Asennus.")
        sys.exit(1)

    from sar_sim.geometry import RadarParams, straight_rail_trajectory
    from sar_sim.point_targets import (
        default_target_grid,
        simulate_point_targets,
        target_polar_coords,
    )
    from torchbp.util import make_polar_grid

    params = RadarParams(rail_length=1.0)  # lyhyt rata, nopea savutesti
    pos = straight_rail_trajectory(params)
    targets = default_target_grid(center_range=100.0, spacing=10.0, n_side=1)

    data = simulate_point_targets(pos, targets, params)

    r, theta = target_polar_coords(targets)
    margin_r, margin_theta = 10.0, 0.3
    grid = make_polar_grid(
        float(r.min()) - margin_r,
        float(r.max()) + margin_r,
        64,
        64,
        theta_limit=float(theta.abs().max()) + margin_theta,
    )

    img = torchbp.ops.backprojection_polar_2d(data, grid, params.fc, params.r_res, pos)
    peak = float(img.abs().max())
    ok = torch.isfinite(img).all() and peak > 0

    print(f"torch {torch.__version__}, CUDA saatavilla: {torch.cuda.is_available()}")
    print(f"backprojection_polar_2d (CPU): kuvan muoto {tuple(img.shape)}, "
          f"dtype {img.dtype}, huippuarvo {peak:.3e}")
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
