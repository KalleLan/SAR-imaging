#!/usr/bin/env python3
"""Virheellinen rata -> minimi-entropia-autofokus -> vertailu.

torchbp.autofocus.bp_polar_grad_minimum_entropy vaatii CUDA:n, koska sen
sisainen torchbp.ops.entropy-kerneli on CUDA-only (ks. imaging/README.md,
osio "torchbp API -muistiinpanot"). CPU-koneella (esim. Mac) skripti
muodostaa ideaali- ja virhekuvat (results/bp_error.png) mutta ohittaa
autofokuksen selkealla viestilla sen sijaan etta kaatuisi poikkeukseen.

PASS-kriteerit (docs/tehtavat/2026-07-11_vaihe0_imaging_runko.md, vaihe B),
tarkistetaan vain kun CUDA on saatavilla:
  1. autofokusoidun kuvan entropia lahella ideaalikuvan entropiaa
  2. maalien paikat palautuvat <= 1 solun tarkkuuteen
  3. ratkaistun positiovirheen RMS raportoidaan suhteessa injektoituun totuuteen
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sar_sim.errors import sinusoidal_wobble
from sar_sim.geometry import RadarParams, straight_rail_trajectory
from sar_sim.point_targets import (
    default_target_grid,
    simulate_point_targets,
    target_polar_coords,
)

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def _form_image(torchbp, data, grid, params, pos):
    img = torchbp.ops.backprojection_polar_2d(data, grid, params.fc, params.r_res, pos)
    return img[0] if img.dim() == 3 else img


def _peak_cell_offsets(img_abs, grid, r_t, theta_t, window=6):
    dr = (grid.r1 - grid.r0) / grid.nr
    dtheta = (grid.theta1 - grid.theta0) / grid.ntheta
    offsets = []
    for i in range(r_t.shape[0]):
        ir = int(round((float(r_t[i]) - grid.r0) / dr))
        it = int(round((float(theta_t[i]) - grid.theta0) / dtheta))
        r0b, r1b = max(0, ir - window), min(img_abs.shape[0], ir + window + 1)
        t0b, t1b = max(0, it - window), min(img_abs.shape[1], it + window + 1)
        patch = img_abs[r0b:r1b, t0b:t1b]
        local = torch.argmax(patch)
        pr = int(local // patch.shape[1]) + r0b
        pt = int(local % patch.shape[1]) + t0b
        offsets.append(float(np.hypot(pr - ir, pt - it)))
    return offsets


def _save_comparison(images, titles, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(images), figsize=(5 * len(images), 5))
    if len(images) == 1:
        axes = [axes]
    for ax, img, title in zip(axes, images, titles):
        ax.imshow(img.abs().detach().cpu().numpy().T, origin="lower", aspect="auto",
                   cmap="viridis")
        ax.set_title(title)
        ax.set_xlabel("r-solu")
        ax.set_ylabel("theta-solu")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Tallennettu: {path}")


def main() -> None:
    import torchbp
    from torchbp.util import entropy as util_entropy
    from torchbp.util import make_polar_grid

    RESULTS_DIR.mkdir(exist_ok=True)

    params = RadarParams()
    pos_true = straight_rail_trajectory(params)
    nsweeps = pos_true.shape[0]
    targets = default_target_grid(center_range=100.0, spacing=10.0, n_side=3)
    r_t, theta_t = target_polar_coords(targets)

    # Tehtavanannon oletusvali n. 0.1-1 lambda; 0.5 lambda on keskiväli.
    wobble_amplitude = 0.5 * params.wavelength
    pos_guess, truth_err = sinusoidal_wobble(pos_true, wobble_amplitude, cycles=3.0, axis=0)

    margin_r, margin_theta = 15.0, 0.1
    grid = make_polar_grid(
        float(r_t.min()) - margin_r,
        float(r_t.max()) + margin_r,
        512,
        512,
        theta_limit=float(theta_t.abs().max()) + margin_theta,
    )

    # Sama data seka ideaali- etta virhekuvassa: vain kasittelyssa kaytetty
    # (oletettu) rata muuttuu ideaalista (pos_true) virheelliseksi (pos_guess).
    data = simulate_point_targets(pos_true, targets, params)

    img_ideal = _form_image(torchbp, data, grid, params, pos_true)
    img_error = _form_image(torchbp, data, grid, params, pos_guess)

    entropy_ideal = float(util_entropy(img_ideal))
    entropy_error = float(util_entropy(img_error))
    print(f"Injektoitu virhe: sinimuotoinen heilunta, amplitudi {wobble_amplitude * 1e3:.2f} mm "
          f"({wobble_amplitude / params.wavelength:.2f} lambda)")
    print(f"Entropia ideaali: {entropy_ideal:.4f}")
    print(f"Entropia virhe:   {entropy_error:.4f}")

    _save_comparison(
        [img_ideal, img_error],
        ["Ideaali", f"Virhe ({wobble_amplitude * 1e3:.1f} mm sini)"],
        RESULTS_DIR / "bp_error.png",
    )

    if not torch.cuda.is_available():
        print("CUDA ei saatavilla: torchbp.ops.entropy (minimi-entropia-autofokus) "
              "vaatii CUDA:n, ks. imaging/README.md. Ohitetaan autofokus-vaihe.")
        print("SKIP (autofokus vaatii CUDA:n)")
        sys.exit(0)

    device = torch.device("cuda")
    data_gpu = data.to(device)
    pos_guess_gpu = pos_guess.to(device)
    data_time = torch.arange(nsweeps, dtype=torch.float32, device=device)
    wa = torch.ones(nsweeps, dtype=torch.float32, device=device)

    sar_img, _origin, pos_recovered, steps = torchbp.autofocus.bp_polar_grad_minimum_entropy(
        data_gpu, data_time, pos_guess_gpu, params.fc, params.r_res, grid, wa,
        max_steps=100, verbose=False,
    )

    entropy_auto = float(util_entropy(sar_img))
    print(f"Entropia korjattu: {entropy_auto:.4f} ({steps} askelta)")

    _save_comparison(
        [img_ideal, img_error, sar_img],
        ["Ideaali", "Virhe", "Autofokus"],
        RESULTS_DIR / "bp_autofocus.png",
    )

    pos_recovered_cpu = pos_recovered.cpu()
    rms_before = float(torch.sqrt(torch.mean((pos_guess - pos_true) ** 2)))
    rms_after = float(torch.sqrt(torch.mean((pos_recovered_cpu - pos_true) ** 2)))
    print(f"Positiovirheen RMS ennen autofokusta: {rms_before * 1e3:.2f} mm")
    print(f"Positiovirheen RMS autofokuksen jalkeen: {rms_after * 1e3:.2f} mm")

    offsets = _peak_cell_offsets(sar_img.abs().cpu(), grid, r_t.cpu(), theta_t.cpu())
    max_offset = max(offsets)
    print(f"Maalien suurin poikkeama autofokuksen jalkeen: {max_offset:.2f} solua")

    # Entropiaraja on alustava (5 %); tarkennettava kun ajettu oikealla
    # GPU-koneella, ks. imaging/README.md "known good" -osio.
    ok = entropy_auto <= entropy_ideal + 0.05 * abs(entropy_ideal) and max_offset <= 1.0
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
