# imaging/ — SAR-kuvanmuodostuksen ja autofokuksen validointi (torchbp)

| | |
|---|---|
| **Projekti** | SDR |
| **Tyyppi** | Toteutuksen README (asennus, ajo, hyväksymiskriteerit) |
| **Päivitetty** | 2026-07-15 |
| **Liittyy** | [`10_START_sdr_rail-SAR.md`](../docs/10_START_sdr_rail-SAR.md) vaihe 0, [`30_laskentakone_pystytys.md`](../docs/30_laskentakone_pystytys.md), [`tehtavat/2026-07-11_vaihe0_imaging_runko.md`](../docs/tehtavat/2026-07-11_vaihe0_imaging_runko.md) |

Tämä hakemisto validoi torchbp-kirjaston kuvanmuodostus- ja autofokusketjun
simuloidulla datalla ennen kuin mitään mittausdataa on kerätty (projektin
vaihe 0, ks. `10_START_sdr_rail-SAR.md`).

Tehtävänannon mukaisesti työ etenee vaiheittain: **vaihe A** (torchbp:n
lähdekoodin inventointi, tämä osio) on tehty kokonaan ennen kuin
`sar_sim/`-, `scripts/`- tai `tests/`-koodia on kirjoitettu. Vaiheet B
(runko: simulaattori + skriptit + testit) ja C (asennusohjeet, ajojärjestys,
"known good" -osio) täydentävät tätä README:tä myöhemmin.

## torchbp API -muistiinpanot

Lähde: [github.com/Ttl/torchbp](https://github.com/Ttl/torchbp), luettu
lähdekoodista (ei arvattu) commitista `cf59c15fae5058382ff4e27b38e7a306c36b5a7f`.

### examples/-hakemisto

torchbp:n `examples/`-hakemistossa **ei ole valmista pistemaalisimulaatiota**.
Kaikki kolme skriptiä käsittelevät oikeaa, ladattua mittausdataa
(`sar.safetensors`, ladataan Henrik Forsténin blogista), eivät synteettistä
esimerkkiä:

- `examples/sar_process_safetensor.py` — lataa datan, range-compressaa
  (`torch.fft.rfft` + residual-video-phase-korjaus), ajaa
  `torchbp.autofocus.bp_polar_grad_minimum_entropy(...)` (minimi-entropia-
  autofokus) ja lopuksi `torchbp.ops.backprojection_polar_2d(...)`.
  Pakottaa `dev = torch.device("cuda")` — käytännössä CUDA-only, koska
  minimi-entropia-autofokus käyttää CUDA-only-entropiakerneliä (ks. alla).
- `examples/sar_process_safetensor_gpga.py` — sama data/range-compression,
  mutta käyttää `torchbp.autofocus.gpga_tde(...)` (vaihtoehtoinen
  phase-gradient-autofokus) ja valitsee laitteen ehdollisesti
  (`"cuda" if torch.cuda.is_available() else "cpu"`).
- `examples/sar_polar_to_cart.py` — projisoi valmiin polaarikuvan
  karteesiseksi näyttöä varten (`torchbp.ops.polar_to_cart`).

Näitä ei voi käyttää suoraan pohjana pistemaalisimulaattorille, mutta niiden
data-flow (range-compress → autofokus → backprojection → polar-to-cart)
toimii mallina omille `scripts/02_backprojection.py`- ja
`03_autofocus.py`-tiedostoille. `docs/source/examples/` sisältää lisäksi
per-algoritmi-Jupyter-notebookit (afbp, backprojection, cfbp, ffbp, gpga,
pga, dem_backprojection, ym.) — näiden sisältöä ei ole tässä vaiheessa
avattu tarkemmin, koska tehtävänanto rajasi tarkastelun `examples/`-kansioon.

### Julkinen API

**Backprojection polaarigridille** — `torchbp.ops.backprojection_polar_2d`:

```python
def backprojection_polar_2d(
    data: Tensor,          # RANGE-COMPRESSED data, [nsweeps, samples] tai
                            # [nbatch, nsweeps, samples], complex64
    grid: "PolarGrid | dict",   # PolarGrid(r_range, theta_range, nr, ntheta)
    fc: float,              # kantoaaltotaajuus, Hz
    r_res: float,           # range-bin-resoluutio metreinä
    pos: Tensor,            # [nsweeps, 3] tai [nbatch, nsweeps, 3], float32 XYZ
    d0: float = 0.0,
    dealias: bool = False,
    att: Tensor | None = None,   # [nsweeps,3] roll/pitch/yaw (vain antennikuvion kanssa)
    g: Tensor | None = None,     # sqrt(kaksisuuntainen antennivahvistus)
    g_extent: list | None = None,
    normalize: bool = True,
    dem: Tensor | None = None,
) -> Tensor   # complex64 pseudo-polaarikuva
```

Tärkeä huomio: `data` on **range-compressed**, ei raaka FMCW-aikatason data.
Gradientti tuettu `data`:n ja `pos`:n suhteen (ei `dem`-tapauksessa).
Toimii CPU:lla (ks. CPU/CUDA-taulukko alla). Karteesinen vastine on
`torchbp.ops.backprojection_cart_2d(data, grid: CartesianGrid|dict, fc, r_res,
pos, d0=0.0, beamwidth=pi, ...)`. Nopeammat tekijöityt variantit:
`torchbp.ops.ffbp`, `afbp`, `cfbp`/`cfbp_adaptive` (dispatchaavat sisäisesti
samoihin ytimiin).

Trajektori/positio annetaan aina tavallisena `torch.Tensor`-oliona,
muoto `[nsweeps, 3]` (float32, metriä) — ei erillistä "platform"-luokkaa.
Grid annetaan erillisenä `PolarGrid`/`CartesianGrid`-oliona
(`torchbp/grid.py`) tai vastaavana dict-rakenteena.

**Minimi-entropia-autofokus** — `torchbp.autofocus`:

```python
def bp_polar_grad_minimum_entropy(...)   # = minimum_entropy_grad_autofocus(backprojection_polar_2d, ...)
def bp_cart_grad_minimum_entropy(...)    # = minimum_entropy_grad_autofocus(backprojection_cart_2d, ...)

def minimum_entropy_grad_autofocus(
    f, data, data_time, pos, fc, r_res, grid, wa,
    max_steps=100, lr_max=10000, d0=0, pos_reg=1, ...,
) -> tuple[Tensor, Tensor, Tensor, int]   # (sar_img, origin, pos, step)
```

Optimoi **per-sweep nopeutta** (`vopt`, autodiff), integroi position
kumulatiivisesti, muodostaa kuvan joka iteraatiolla uudestaan ja minimoi
`torchbp.ops.entropy(sar_img) + pos_reg * mean((pos - pos_orig)^2)`
manuaalisella SGD-askeleella. Palauttaa korjatun kuvan, originin, korjatun
position ja käytettyjen askelten määrän.

**Kriittinen rajoitus:** `torchbp.ops.entropy`-kerneli on **CUDA-only** — ei
CPU-toteutusta (`csrc/cuda/entropy.cu`, ei vastaavaa `csrc/cpu/`-rekisteröintiä;
`tests/test_entropy.py` ohittaa CPU-testin eksplisiittisesti kommentilla
"CPU implementation not available"). **Tämä tarkoittaa, ettei minimi-
entropia-autofokus toimi CPU:lla sellaisenaan** — se vaatii CUDA:n. CPU-
yhteensopiva entropia-metriikka on olemassa (`torchbp.util.entropy(x)`,
tavallinen autograd, ei custom-kerneliä), mutta sitä käytetään
esimerkkiskripteissä vain raportointiin, ei itse autofokuksen sisällä.

Vaihtoehtoinen algoritmiperhe on **generalized phase-gradient autofocus**:
`torchbp.autofocus.gpga(...)` (palauttaa vaihekorjauksen) ja
`torchbp.autofocus.gpga_tde(...)` (palauttaa 3D-positiokorjauksen). Nämä
toimivat CPU:lla (linear-interp-ydin), mutta eivät ole minimi-entropia-
menetelmä eivätkä siis suoraan vastaa tehtävänannon "minimi-entropia-
autofokus" -vaatimusta.

**Pistemaalidatan generointi on valmiina torchbp:ssä** —
`torchbp.util.generate_fmcw_data`:

```python
def generate_fmcw_data(
    target_pos: Tensor,     # [ntargets, 3] XYZ
    target_rcs: Tensor,     # [ntargets, 1] kompleksinen heijastavuus
    pos: Tensor,             # [nsweeps, 3] tutkan positiot
    fc: float, bw: float, tsweep: float, fs: float, d0: float = 0,
    g: Tensor | None = None, g_extent: list | None = None, att: Tensor = None,
    rvp: bool = True, vel: Tensor | None = None,
) -> Tensor   # [nsweeps, nsamples] complex64, RAAKA (ei range-compressed) FMCW-beat-signaali
```

Puhdasta PyTorchia, ei `torch.ops.torchbp.*`-kutsuja → laiteriippumaton,
toimii myös CPU:lla ja siis Macilla. **`sar_sim/point_targets.py` tulee
wrapata tämä funktio** (ohut wrapperi) sen sijaan että fysiikka kirjoitetaan
itse — tämä on suora vastaus tehtävänannon vaiheen A kohtaan 4.

### Tärkeä poikkeama alkuperäiseen suunnitelmaan

`backprojection_polar_2d` odottaa **range-compressed** dataa, mutta
`generate_fmcw_data` tuottaa **raakaa** FMCW-signaalia. Tämä tarkoittaa,
että `point_targets.py`:n (tai `scripts/02_backprojection.py`:n) täytyy
tehdä range-compression (`torch.fft.rfft` + RVP-korjaus, kuten
`examples/sar_process_safetensor.py` tekee) ennen datan syöttämistä
backprojektioon. Tämä lisätään vaiheen B suunnitelmaan eksplisiittisesti,
koska alkuperäinen tehtävänanto ei erikseen maininnut tätä välivaihetta.

### CPU vs. CUDA -tuki (varmistettu csrc/-rekisteröinneistä, ei oletettu)

torchbp on C++/CUDA-PyTorch-laajennus (`torchbp._C`), ei puhdas
Python-paketti. CPU-ytimet (`csrc/cpu/*.cpp`) käännetään **aina**, CUDA-ytimet
(`csrc/cuda/*.cu`) vain jos CUDA on saatavilla käännösaikana.

**Toimii CPU:lla:**
`backprojection_polar_2d` (+grad), `backprojection_cart_2d` (+grad),
`generate_fmcw_data`, `projection_cart_2d` / `projection_cart_2d_nufft`
(eteenpäin-simulaattori kuvasta dataksi), `ffbp`/`afbp`/`cfbp`,
`gpga`/`gpga_tde` (linear-interp-ydin), `polar_to_cart`/`cart_to_polar`
(linear-interp), `coherence_2d`, `resample_2d_*`, `polar_range_dealias`.

**Vain CUDA:**
`torchbp.ops.entropy` (→ **minimi-entropia-autofokus vaatii CUDA:n**),
`cfar_2d`, `subpixel_correlation` (interferometrinen koregistrointi),
`backprojection_polar_2d_lanczos`/`_knab` (Lanczos/Knab-interpolointi-
variantit), `gpga_backprojection_2d_lanczos`.

torchbp:n oma `Readme.md` sanoo: *"Only Nvidia GPUs are supported.
Currently, only some of the operations are supported on CPU."* — tämä
vahvistuu lähdekoodista. `docs/source/index.rst`:n vanhempi väite ("GPU and
CPU support") on osittain vanhentunut/harhaanjohtava; yllä oleva jako on
todellinen tilanne.

**Ei löydetty:** mitään mainintaa Pascal/sm_61-arkkitehtuurivaatimuksesta
torchbp:n lähdekoodista (ei `-arch`/`-gencode`-käännöslippuja, ei
"sm_"/"Pascal"-tekstiä missään). Tätä ei siis voida vahvistaa torchbp:n
lähteestä käsin — CUDA toolkit 12.6 -yhteensopivuus GTX 1070:n (sm_61)
kanssa pitää tarkistaa erikseen GPU-koneella asennusvaiheessa, ks.
`docs/30_laskentakone_pystytys.md`. torchbp:n oma testisuite (CI)
rakentaa myös CPU-only-torchia vasten, joten CPU-only-build on projektin
itsensä tukema/testaama konfiguraatio.

### Asennus

```bash
pip install torch   # cu126-wheel GPU-koneella, ks. docs/30_laskentakone_pystytys.md
git clone https://github.com/Ttl/torchbp.git
cd torchbp
pip install --no-build-isolation -e .
```

`--no-build-isolation` on pakollinen, koska laajennus linkittää
non-ABI-stabiileja libtorch-symboleita ja täytyy kääntää tarkalleen
käytössä olevaa torch-versiota vasten. torchbp:tä **ei** lisätä
`requirements.txt`:hen pip-riippuvuutena — se asennetaan manuaalisesti
yllä kuvatulla tavalla.

### Vaikutus scripts/01_smoke_cpu.py:n suunnitteluun

CPU-savutesti voi: importata torchbp:n, generoida datan
`torchbp.util.generate_fmcw_data`:lla, range-compressata se ja ajaa
`torchbp.ops.backprojection_polar_2d`:n CPU:lla saaden `complex64`-kuvan.
Se **ei voi** ajaa minimi-entropia-autofokusta CPU:lla, koska
`torchbp.ops.entropy` vaatii CUDA:n — `scripts/03_autofocus.py`:n täytyy
tunnistaa tämä ja epäonnistua siististi selkeällä viestillä ennen
autofokus-kutsua, jos CUDA ei ole saatavilla (samaan tapaan kuin
`torch.cuda.is_available()`-tarkistus muissakin GPU-skripteissä).

## Seuraavat vaiheet

Vaihe B (hakemistorunko: `sar_sim/`, `scripts/`, `tests/`) ja vaihe C
(asennus-/ajojärjestys, PASS-kriteerit, "known good" -osio) suunnitellaan
ja toteutetaan erikseen tämän jälkeen.

## Muutosloki

- **2026-07-15** — Vaihe A: torchbp:n lähdekoodi inventoitu (commit
  `cf59c15fae5058382ff4e27b38e7a306c36b5a7f`), löydökset kirjattu tähän
  ennen toteutuskoodin kirjoittamista.
