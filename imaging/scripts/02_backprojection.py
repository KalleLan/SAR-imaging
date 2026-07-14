#!/usr/bin/env python3
"""Backprojection ideaaliradalla: 9 pistemaalia, tarkista paikat.

PASS-kriteeri (docs/tehtavat/2026-07-11_vaihe0_imaging_runko.md, vaihe B):
kunkin 9 maalin paikallinen maksimi <= 1 resoluutiosolun paassa tunnetusta
sijainnista. Tallentaa results/bp_ideal.png.

Ajetaan CUDA:lla jos saatavilla, muuten CPU:lla (backprojection_polar_2d:lla
on CPU-kerneli, ks. imaging/README.md).
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sar_sim.geometry import RadarParams, straight_rail_trajectory
from sar_sim.point_targets import (
    default_target_grid,
    simulate_point_targets,
    target_polar_coords,
)

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def find_peak(img_abs: torch.Tensor, ir: int, itheta: int, window: int = 6):
    nr, ntheta = img_abs.shape
    r0, r1 = max(0, ir - window), min(nr, ir + window + 1)
    t0, t1 = max(0, itheta - window), min(ntheta, itheta + window + 1)
    patch = img_abs[r0:r1, t0:t1]
    local = torch.argmax(patch)
    pr = int(local // patch.shape[1]) + r0
    pt = int(local % patch.shape[1]) + t0
    return pr, pt, float(patch.max())


def main() -> None:
    import torchbp
    from torchbp.util import make_polar_grid

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Laite: {device}")

    params = RadarParams()
    pos = straight_rail_trajectory(params).to(device)
    targets = default_target_grid(center_range=100.0, spacing=10.0, n_side=3).to(device)
    r_t, theta_t = target_polar_coords(targets)

    margin_r, margin_theta = 15.0, 0.1
    grid = make_polar_grid(
        float(r_t.min()) - margin_r,
        float(r_t.max()) + margin_r,
        512,
        512,
        theta_limit=float(theta_t.abs().max()) + margin_theta,
    )

    data = simulate_point_targets(pos, targets, params)
    img = torchbp.ops.backprojection_polar_2d(data, grid, params.fc, params.r_res, pos)
    if img.dim() == 3:
        img = img[0]
    img_abs = img.abs().cpu()

    dr = (grid.r1 - grid.r0) / grid.nr
    dtheta = (grid.theta1 - grid.theta0) / grid.ntheta

    r_t_cpu = r_t.cpu()
    theta_t_cpu = theta_t.cpu()

    print(f"{'maali':>5} {'r odotettu':>11} {'theta odotettu':>15} "
          f"{'r mitattu':>10} {'theta mitattu':>14} {'solu-etaisyys':>13} {'huippu':>10}")
    max_cells = 0.0
    for i in range(targets.shape[0]):
        ir = int(round((float(r_t_cpu[i]) - grid.r0) / dr))
        it = int(round((float(theta_t_cpu[i]) - grid.theta0) / dtheta))
        pr, pt, peak = find_peak(img_abs, ir, it)
        cell_dist = float(np.hypot(pr - ir, pt - it))
        max_cells = max(max_cells, cell_dist)
        r_meas = grid.r0 + pr * dr
        theta_meas = grid.theta0 + pt * dtheta
        print(f"{i:5d} {float(r_t_cpu[i]):11.2f} {float(theta_t_cpu[i]):15.4f} "
              f"{r_meas:10.2f} {theta_meas:14.4f} {cell_dist:13.2f} {peak:10.3e}")

    RESULTS_DIR.mkdir(exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.imshow(
            img_abs.numpy().T, origin="lower", aspect="auto",
            extent=[grid.r0, grid.r1, grid.theta0, grid.theta1], cmap="viridis",
        )
        ax.set_xlabel("r (m)")
        ax.set_ylabel("theta (sin kulma)")
        ax.set_title("Backprojection, ideaalirata")
        fig.tight_layout()
        fig.savefig(RESULTS_DIR / "bp_ideal.png", dpi=150)
        plt.close(fig)
        print(f"Tallennettu: {RESULTS_DIR / 'bp_ideal.png'}")
    except ImportError:
        print("Huom: matplotlib puuttuu, PNG:tä ei tallennettu.")

    ok = max_cells <= 1.0
    print(f"Suurin poikkeama: {max_cells:.2f} solua (raja 1.0)")
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
