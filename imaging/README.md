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

### PolarGrid-olion rakenne

`torchbp/grid.py:25` (`class PolarGrid(Grid)`):

```python
PolarGrid(
    r_range: Tuple[float, float],       # (r0, r1) metreinä, r1 > r0
    theta_range: Tuple[float, float],   # (theta0, theta1) = sin(atsimuuttikulma), oltava [-1, 1]
    nr: int,                             # range-binien lukumäärä
    ntheta: int,                         # atsimuutti-binien lukumäärä
)
```

- **Kentät:** vain `r_range`/`theta_range`/`nr`/`ntheta` (tallennettu sellaisenaan,
  `dr`/`dtheta` laskettu ja cachettu: `dr=(r1-r0)/nr`, `dtheta=(theta1-theta0)/ntheta`).
  **Ei origo-siirtymäkenttää** `PolarGrid`-oliossa itsessään — origo hoidetaan
  `pos`-tensorin kautta (ks. alla).
- **Yksiköt:** `r_range` metreinä. `theta_range` on **sin(kulma)**, ei radiaaneja
  eikä asteita — `-1..1` vastaa 180°:n näkymää (docstring: `"theta represents sin
  of angle (-1, 1 for 180 degree view)"`).
- **`d0`-parametri** `backprojection_polar_2d`:ssä: docstringin mukaan "Zero range
  correction". Lähdekoodissa (`torchbp/csrc/cpu/backproj.cpp:154`,
  `sx = delta_r * (d + d0)`) `d0` on metrimääräinen vakiokorjaus joka **lisätään
  geometrisesti laskettuun etäisyyteen** `d` ennen range-bin-indeksiksi
  muuntamista — eli kiinteä kalibrointitermi (esim. kaapeliviive), ei origon
  siirto grid-koordinaatistossa.
- **`pos`-koordinaattikonventio:** pikselin sijainti grid-koordinaatistossa on
  `x = r*sqrt(1-theta²)`, `y = r*theta`, `z = 0` (maanpinta-taso, ellei `dem`
  annettu) — ks. `torchbp/csrc/cpu/backproj.cpp:82-83` ja koodikommentti rivillä
  ~139: *"equals the Cartesian distance to (x, y, 0)... for a straight track on
  the y axis"*. Etäisyys tutkaan lasketaan `d² = (x-pos_x)² + (y-pos_y)² +
  pos_z²` (rivit 137-149), eli **`pos_z` on tutkan korkeus maanpinta-tasosta
  (z=0)** — **z-akseli on "ylös"**, `x` on poikittaissuunta (ground-range) ja
  `y` on kanoninen suora-rata-suunta (koodin oma kommentti olettaa radan
  olevan y-akselilla, mikä täsmää tehtävänannon "suora rata Y-akselia pitkin"
  -skenaarioon). Origon sijainti suhteessa rataan **ei ole kiinteä** —
  `minimum_entropy_grad_autofocus` (`torchbp/autofocus.py:2685-2687`) keskittää
  radan ennen kuvanmuodostusta: `origin = mean(pos, axis=0)`, `origin[:,2] = 0`,
  `pos_centered = pos - origin` — eli grid-origo (0,0,0) asetetaan radan
  x/y-keskiarvoon maanpinnalla, ja rata itse on tästä keskipisteestä siirtynyt
  `pos_centered`-arvon verran. Oman simulaattorin kannattaa noudattaa samaa
  konventiota (rata keskitetty origon ympärille, korkeus z-akselilla).

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

### DEM-backprojection

Lähde: `docs/source/examples/dem_backprojection.ipynb` (luettu kokonaan,
sama torchbp-klooni/commit kuin vaihe A), `torchbp/ops/backproj.py`,
`torchbp/csrc/cpu/backproj.cpp`, `torchbp/autofocus.py`.

**Notebookin sisältö:** rakentaa synteettisen 15 m korkean mäen ("smooth
hill") ja 5x5-ruudukon pistemaaleja mäen pinnalla, näyttää että ilman
`dem`-argumenttia korkeat kohteet siirtyvät kuvassa kohti tutkaa
(layover-tyyppinen virhe, "flat-earth image ... warped"), ja että `dem`:n
kanssa `ffbp`/`backprojection_polar_2d` fokusoivat kaikki 25 kohdetta
oikeisiin koordinaatteihin. Vertaa myös suoraa `backprojection_polar_2d`:tä
ja `ffbp`:tä samalla `dem`:llä keskenään (pieni jäännösvirhe, `relerr`).
Notebookin lopussa mainitaan lyhyesti että myös `gpga`/`gpga_tde`
hyväksyvät `dem`-argumentin. **Notebookissa ei ole esimerkkiä minimi-
entropia-autofokuksen ja DEM:n yhdistämisestä** — ainoastaan suora
kuvanmuodostus DEM:n kanssa, ei autofokusta lainkaan.

**`dem`-tensorin muoto ja koordinaatisto** (`torchbp/ops/backproj.py:1090-
1096`, notebookin markdown-solu): `[dem_nr, dem_ntheta]`, `float32`.
Kattaa saman r/theta-alueen kuin kuvan grid, voi olla karkeampi kuin
kuvagrid — arvot bilineaarisesti interpoloidaan per pikseli. Arvot ovat
pikselin z-koordinaatteja **samassa koordinaatistossa kuin `pos`** (sama
z="ylös"-konventio joka on jo dokumentoitu yllä "PolarGrid-olion rakenne"
-osiossa). DEM-näyte `[i, j]` vastaa solun alkukoordinaattia
`r = r0 + i*(r1-r0)/dem_nr`, `theta = t0 + j*(t1-t0)/dem_ntheta` (ei
solun keskipistettä). `torchbp.util.dem_to_polar` (`torchbp/util.py:820-
886`) resamplaa karteesisen DEM:n (esim. GeoTIFF-pohjaisen) tälle
polaarigridille `F.grid_sample`-bilineaarilla.

**Geometria ei ole approksimaatio** (`torchbp/csrc/cpu/backproj.cpp:130-
152`): DEM-tapauksessa pikselin etäisyys tutkaan lasketaan
`d² = r²+|pos|² + z² - 2*(x*pos_x + y*pos_y + z*pos_z)` — täsmälleen sama
kaava kuin flat-earth-tapaus (`d² = r²+|pos|² - 2*(x*pos_x + y*pos_y)`)
täydennettynä z-termeillä, ei kevennetty/linearisoitu malli.

**Gradientti/autofokus-rajoitus vahvistuu täsmälleen** README:hen jo
kirjatun huomion mukaisesti: `torchbp/ops/backproj.py:1799-1804`
(`_backward_polar_2d`) sisältää eksplisiittisen
`if ctx.saved[25] is not None: raise ValueError("gradient with dem not
supported")` — tämä on tarkoituksellinen `raise`, ei vain
dokumentoimaton puute. `minimum_entropy_grad_autofocus`-funktiolla
(`torchbp/autofocus.py:2551-2736`) **ei ole edes `dem`-parametria
signatuurissa**: se kutsuu kuvanmuodostusfunktiota aina ilman `dem`:ää
(rivi 2689: `f(data, grid, fc, r_res, pos_centered, d0,
data_fmod=data_fmod)`).

**`gpga`/`gpga_tde` sen sijaan tukevat `dem`:ää suoraan**, koska ne eivät
käytä backprop-gradienttia vaan phase-gradient-estimointia:
`torchbp/autofocus.py:708-717` (docstring) sanoo eksplisiittisesti *"Used
both for the image formation and for the autofocus target positions"*,
toteutus `torchbp/autofocus.py:738-741,765-767`. Rajoitus: vain
polaarigridi + algoritmi `"bp"` tai `"ffbp"` (`autofocus.py:714`).

**Työjärjestys — ei yhtä virallista kaavaa, kaksi erillistä polkua:**
1. Minimi-entropia-gradienttiautofokus ei voi käyttää `dem`:ää lainkaan.
   Jos tätä menetelmää halutaan yhdistää DEM:ään, ainoa mahdollinen
   järjestys on tehtävänannon olettama "autofokusoi ensin tasomaisella
   oletuksella (`dem=None`) → aja lopullinen kuvanmuodostus korjatulla
   `pos`:lla ja oikealla `dem`:llä" — **mutta tätä ei dokumentoida eikä
   demonstroida torchbp:n lähdekoodissa tai notebookeissa missään**, se
   on oma päätelmämme rajoituksesta, ei löydetty resepti.
2. `gpga`/`gpga_tde` tukevat `dem`:ää suoraan yhdessä ajossa, ei
   kaksivaiheista järjestystä tarvita. Näistä juuri `gpga`-perhe toimii
   CPU:lla (jo dokumentoitu alla "CPU vs. CUDA -tuki" -osiossa), kun taas
   minimi-entropia vaatii CUDA:n. Käytännön seuraus: jos DEM-autofokus
   halutaan CPU:lla (Macilla), `gpga`/`gpga_tde` on ainoa toimiva reitti.

**Käytännön arvio validointitarpeesta:** `torchbp.util.generate_fmcw_data`
(jo dokumentoitu yllä) ottaa 3D-`target_pos`:n suoraan — korkeusvaihtelun
lisääminen omaan simulaattoriin ei vaadi mitään muutoksia itse
torchbp-kutsuun, tarvitsee vain kohteille nollasta poikkeavan z:n (sama
malli kuin notebookin `terrain()`-funktio ja Bekarin kappale IV:n koestus,
jossa osa kohteista on korotettu). Oikeaa avointa korkeusdata-aineistoa ei
tarvita validoinnin ensimmäiseen vaiheeseen — synteettinen korkeuskartta
(notebookin `terrain()`-tyylinen Gaussin-mäki) riittää todentamaan että
DEM korjaa defokusoinnin omassa simulaattorissa. Ehdotettu pienin seuraava
askel (ei toteuteta tässä tehtävässä): lisää `sar_sim/point_targets.py`:hen
valinnainen z-korkeus per kohde ja testi, joka toistaa notebookin
flat-vs-DEM-vertailun `sar_sim`:n omalla data-flow'lla — kirjataan
"Seuraavat vaiheet" -osioon.

**Suositus:** Ei blokkaa mitään nyt. Oikea maastodata tarvitaan vasta kun
mittausdataa on olemassa; validointi omassa simulaattorissa synteettisellä
DEM:llä on halpa tehdä milloin tahansa vaiheen B jälkeen, mutta ei ole
kriittinen polku tälle hetkelle.

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

**Vahvistettu: Mac-build toimii ilman CUDAa, ei enää avoin kysymys.**
`setup.py:39-44` (`get_extensions()`):

```python
use_cuda = os.getenv("USE_CUDA", "1") == "1"
use_cuda = use_cuda and torch.cuda.is_available() and CUDA_HOME is not None
extension = CUDAExtension if use_cuda else CppExtension
```

Kun `torch.cuda.is_available()` on `False` (Macilla aina, ei NVIDIA-GPU:ta) tai
`CUDA_HOME` puuttuu, `use_cuda` on `False` ja käännin valitsee `CppExtension`:in,
joka kääntää vain `csrc/*.cpp` + `csrc/cpu/*.cpp` -lähteet (`setup.py:85-93`);
`csrc/cuda/*.cu` jätetään kokonaan pois käännöksestä. Eli
`pip install --no-build-isolation -e .` **toimii sellaisenaan Macilla** —
build putoaa automaattisesti CPU-only-polulle ilman erillistä lippua tai
ympäristömuuttujaa. Tämä on nyt todettu suoraan lähdekoodista, ei enää
avoin kysymys.

### Käytännön Mac-toolchain-resepti (todettu kokeilemalla, vaihe B)

Tämä osio on täsmällinen toistettava resepti, ei vain kuvaus — tarkoitus on
ettei tätä tarvitse löytää uudestaan. Kolme perättäistä yritystä ja mitä
kussakin tapahtui, sitten toimiva resepti täsmäversioin.

**Yritys 1 — Applen oma Xcode Command Line Tools -clang (oletus, ei mitään
erikoisasetuksia):** `pip install --no-build-isolation -e .` epäonnistuu
käännösvaiheeseen, virhe toistuu jokaiselle `csrc/cpu/*.cpp`-tiedostolle:
```
clang++: error: unsupported option '-fopenmp'
```
Syy: `setup.py`:n `extra_compile_args`/`extra_link_args` sisältävät
kovakoodatun `-fopenmp`-lipun (`csrc/cpu/*.cpp` käännetään aina
OpenMP:llä), eikä Applen clang-kääre tue sitä ilman
`-Xpreprocessor -fopenmp -lomp`-erikoiskäsittelyä, jota `setup.py` ei tee.

**Yritys 2 — Homebrew'n GCC (`brew install gcc`, `CC=gcc-16 CXX=g++-16`)
Xcoden mukana tulevalla system-Pythonilla (`/usr/bin/python3`,
universal2-binääri):** käännös epäonnistuu heti:
```
g++-16: warning: this compiler does not support x86 ('-arch' option ignored)
g++-16: error: unrecognized command-line option '-iwithsysroot/System/Library/Frameworks/System.framework/PrivateHeaders'
```
Syy: CPython:n oma sysconfig-käännöskokoonpano sisältää Apple-clang-
spesifiset liput (`-arch arm64 -arch x86_64` universal2-buildia varten,
`-iwithsysroot...`), joita GCC ei tunne.

**Yritys 3 — Homebrew'n GCC + Homebrew'n `python@3.12`** (ei
Apple-clang-spesifisiä sysconfig-lippuja): käännös **onnistuu**, mutta
`import torchbp` kaatuu ajonaikaisesti:
```
ImportError: dlopen(.../torchbp/_C.abi3.so, 0x0002): symbol not found in flat namespace
'__ZN2at4_ops10empty_like4callERKNS_6TensorESt8optionalIN3c1010ScalarTypeEES5_INS6_6LayoutEES5_INS6_6DeviceEES5_IbES5_INS6_12MemoryFormatEE'
```
Syy: Homebrew'n GCC linkkaa libstdc++:aa vasten, virallinen pip-torch-wheel
on käännetty clangilla/libc++:lla — ABI ei täsmää. `torch.utils.cpp_extension`
tulostaa tästä itse käännösvaiheessa varoituksen ("Your compiler (g++-16) is
not compatible with the compiler Pytorch was built with... which is
clang++ on darwin"), mutta build ei silti kaadu — vasta `import` paljastaa
ongelman.

**Toimiva resepti — Homebrew'n LLVM-clang + Homebrew'n `python@3.12`.**
Täsmäversiot joilla tämä on vahvistettu tällä koneella (`arm64`,
macOS/Darwin 25.5.0):

| Työkalu | Versio | Tarkistuskomento |
|---|---|---|
| `llvm` (Homebrew) | 22.1.8 | `brew list --versions llvm` |
| `python@3.12` (Homebrew) | 3.12.13_4 (Python 3.12.13) | `brew list --versions python@3.12` |
| `gcc` (Homebrew, jäi lopulta tarpeettomaksi) | 16.1.0 | `brew list --versions gcc` |
| torch (pip, tässä ympäristössä) | 2.13.0 | `pip show torch` |

Asennus- ja käännöskomennot:
```bash
brew install llvm python@3.12
# (brew install libomp EI ole tarpeen erikseen: llvm-formula sisältää oman
#  libomp.dylib:nsa ja omp.h:nsa, ks. alla.)

/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools   # setuptools >= 64 (PEP 660 editable-tuki)
pip install torch numpy scipy matplotlib pytest expecttest

cd <torchbp-klooni>
export CC=/opt/homebrew/opt/llvm/bin/clang
export CXX=/opt/homebrew/opt/llvm/bin/clang++
export LDFLAGS="-L/opt/homebrew/opt/llvm/lib -Wl,-rpath,/opt/homebrew/opt/llvm/lib"
export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"
pip install --no-build-isolation -e .
```

Jos `CC`/`CXX` jätetään asettamatta tässä vaiheessa, pip käyttää
oletuskääntäjää (`/usr/bin/clang++`, Yritys 1:n virhe) tai mitä tahansa
ympäristön `CC`/`CXX` sattuu osoittamaan (esim. jäänyt Homebrew-GCC,
Yritys 3:n virhe) — build ei tunnista automaattisesti oikeaa kääntäjää.

**Ajonaikainen OpenMP-ristiriita (uusi löydös, ei pelkkä käännösongelma):**
kun torchbp on käännetty edellä kuvatulla tavalla, pelkkä `import torchbp`
toimii sellaisenaan, mutta minkä tahansa `torchbp.ops.*`-funktion
kutsuminen (esim. `backprojection_polar_2d`) kaatuu tai varoittaa:
```
OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized.
OMP: Hint This means that multiple copies of the OpenMP runtime have been linked into the program...
```
Syy (varmistettu `otool -L`:lla): `torch/lib/libtorch_cpu.dylib` linkkaa
oman pip-torch-wheelin mukana tulevan `@rpath/libomp.dylib`:n (tiedosto
`<venv>/lib/python3.12/site-packages/torch/lib/libomp.dylib`), kun taas
torchbp:n `_C.abi3.so` linkkaa Homebrew'n `libomp.dylib`:n absoluuttisella
polulla `/opt/homebrew/opt/llvm/lib/libomp.dylib` — sama prosessi lataa
kaksi eri OpenMP-runtime-kopiota. **Korjaus: aseta `DYLD_LIBRARY_PATH`
ajettaessa** (ei riitä pelkkä `LDFLAGS` käännösvaiheessa) niin että torchin
oma `@rpath`-haku ohjautuu samaan Homebrew-kopioon jonka torchbp jo
käyttää:
```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/llvm/lib:$DYLD_LIBRARY_PATH"
```
Tämän jälkeen vain yksi `libomp.dylib`-kopio ladataan prosessiin eikä
ristiriitaa synny. (Virheviestin ehdottama `KMP_DUPLICATE_LIB_OK=TRUE` on
sen omien sanojen mukaan "unsafe, unsupported, undocumented workaround" —
ei suositella, koska se voi hiljaisesti tuottaa vääriä tuloksia; oikea
korjaus on yksi jaettu runtime, ei kahden olemassaolon salliminen.)

Tällä täydellisellä reseptillä (kääntäjä + `DYLD_LIBRARY_PATH`)
`torchbp.ops.backprojection_polar_2d` CPU:lla toimii vahvistetusti tällä
Macilla — ks. `imaging/scripts/01_smoke_cpu.py` ja `02_backprojection.py`
tulokset (molemmat PASS).

Tämä on ympäristökohtainen käytännön löydös, ei osa torchbp:n virallista
dokumentaatiota — GPU-koneella (CUDA, Ubuntu) tätä täsmällistä
kääntäjäongelmaa ei odoteta, koska siellä käytetään `CUDAExtension`-polkua
eikä Applen/Homebrew'n kääntäjäkirjoa ole. Sen sijaan Ubuntu-koneella on
oma, rakenteeltaan analoginen riski (system-GCC:n ABI-yhteensopivuus
cu126-wheelin kanssa) — ks. `docs/30_laskentakone_pystytys.md`, osio
"Tunnetut sudenkuopat".

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

### Torch-versiolukko

`pyproject.toml` (koko tiedosto on vain kommentti + `[build-system]`-lohko)
sanoo eksplisiittisesti: *"torch is intentionally NOT listed here"* —
torchia ei listata build-riippuvuutena juuri siksi ettei PEP 517
build-isolation vetäisi sisään eri (uudempaa) torchia. `setup.py`:n
`install_requires = ["torch", "numpy", "scipy"]` (rivi ~118) **ei pinnaa
torch-versiota millään tavalla** — ei min-, max- eikä täsmäversiovaatimusta.

Ainoa versioon reagoiva koodihaara on `setup.py:33`:
`py_limited_api = Version(torch.__version__) >= Version("2.6.0")`, joka
valitsee abi3-yhteensopivan käännöksen (`_C.abi3.so`) torch ≥ 2.6:lle vs.
Python-versiokohtaisen nimen vanhemmille — tämä ei estä vanhempien
torch-versioiden käyttöä, vain muuttaa käännetyn `.so`-tiedoston nimeämistä.

**CUDA-versio:** `Readme.md:15` sanoo vain *"Tested with CUDA version
12.9."* — tämä on kehittäjän ilmoittama testattu versio, ei pakotettu
minimi- tai maksimivaatimus (ei versiotarkistusta koodissa). Ainoa CI-työ
(`.github/workflows/docs.yml:35`) asentaa `torch`:n indeksistä
`https://download.pytorch.org/whl/cpu` (versio lukitsematon, CI:n
ajohetken uusin), eikä aja mitään CUDA-testejä.

**Ristiriita/epävarmuus tehtävänannon ympäristölukkoon nähden:**
`docs/30_laskentakone_pystytys.md` lukitsee CUDA toolkit **12.6** ja
PyTorch cu126-wheelin (Pascal/sm_61-yhteensopivuuden vuoksi), kun taas
torchbp on kehittäjän mukaan testattu CUDA **12.9**:llä. Koska torchbp:n
lähdekoodi ei aseta mitään versiorajaa, tämä ei ole varmuudella este —
mutta yhteensopivuutta CUDA 12.6:n kanssa **ei voida vahvistaa
torchbp:n lähdekoodista**, ja se pitää todeta käytännössä GPU-koneen
build-vaiheessa (`pytest tests/` ajon jälkeen, ks.
`docs/30_laskentakone_pystytys.md`). Jos build tai testit epäonnistuvat
CUDA 12.6:lla, tämä on ensimmäinen epäilty syy.

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

Vaihe B (hakemistorunko: `sar_sim/`, `scripts/`, `tests/`) on toteutettu ja
testattu tällä Macilla CPU:lla (ks. Muutosloki). Vaihe C — asennus-/
ajojärjestyksen viimeistely tähän README:hen, tarkemmat PASS-kriteerit ja
"known good" -osio kun ketju on ajettu GPU-koneella (mukaan lukien
`03_autofocus.py`:n minimi-entropia-autofokus-osa, joka vaatii CUDA:n) —
suunnitellaan ja toteutetaan erikseen tämän jälkeen.

## Muutosloki

- **2026-07-15** — DEM-backprojection-inventaario lisätty (jatko-osa vaihe
  A:lle, `docs/tehtavat/2026-07-15_dem-squint-inventaario.md` osa 1): `dem`-
  tensorin muoto/koordinaatisto, `docs/source/examples/
  dem_backprojection.ipynb`:n sisältö, vahvistus että backprop-gradientti
  `dem`:n läpi ei ole tuettu (`backproj.py:1799-1804`,
  `minimum_entropy_grad_autofocus`:lla ei edes `dem`-parametria), ja että
  `gpga`/`gpga_tde` tukevat `dem`:ää suoraan sekä kuvanmuodostukseen että
  autofokuksen kohteiden sijaintiin. Sama klooni/commit
  `cf59c15fae5058382ff4e27b38e7a306c36b5a7f`.
- **2026-07-15** — Käytännön Mac-toolchain-resepti täsmennetty täydellä
  toistettavuudella: täsmäversiot (Homebrew `llvm` 22.1.8, `python@3.12`
  3.12.13_4), asennus-/käännöskomennot, kolmen epäonnistuneen yrityksen
  tarkat virheviestit (Apple clang `-fopenmp`, Homebrew GCC + system-Python
  sysconfig-liput, Homebrew GCC + Homebrew Python ABI-symbolivirhe), ja
  uusi löydös: ajonaikainen OpenMP-runtime-ristiriita
  (`OMP: Error #15 ... already initialized`, koska pip-torch-wheel ja
  torchbp linkkaavat kaksi eri `libomp.dylib`-kopiota) korjattuna
  `DYLD_LIBRARY_PATH`:lla. Ks. myös `docs/30_laskentakone_pystytys.md`,
  joka nyt kirjaa saman riskiluokan (kääntäjän ABI-yhteensopivuus) avoimeksi
  tarkistuskohdaksi GPU-koneen `torchbp`-käännösvaiheelle.
- **2026-07-15** — Vaihe B: `sar_sim/` (`geometry.py`, `point_targets.py`,
  `errors.py`), `scripts/01_smoke_cpu.py`, `02_backprojection.py`,
  `03_autofocus.py` ja `tests/test_sim.py` toteutettu. Range-compression-
  resepti (`torch.fft.ifft`, `rvp=False`, Hamming-ikkuna, FFT-oversample)
  kopioitu torchbp:n omasta testisuiteesta
  (`tests/test_ffbp.py::TestFfbpDem._terrain_scene`), ei keksitty itse.
  Koko ketju (pytest + kaikki kolme skriptiä) ajettu ja vahvistettu tällä
  Macilla CPU:lla: `02_backprojection.py` PASS (9/9 maalia ≤ 1 solu),
  `03_autofocus.py` SKIP CUDA:n puuttuessa (ei kaadu). torchbp käännettiin
  paikallisesti testausta varten Homebrew'n LLVM-clangilla + Homebrew'n
  `python@3.12`:lla — Applen oma clang ja Homebrew'n GCC eivät toimineet,
  ks. "Käytännön Mac-toolchain-resepti" edellä.
- **2026-07-15** — Vaihe A täydennys: PolarGrid-olion tarkka rakenne
  (kentät, yksiköt, `d0`:n ja `pos`:n koordinaattikonventio), torch-
  versiolukon tarkistus (ei pinnattu versio; CUDA 12.9 testattu vs.
  ympäristölukon CUDA 12.6 — vahvistamaton yhteensopivuus) ja
  Mac-buildin CUDA-fallback vahvistettu `setup.py`:stä (ei enää avoin
  kysymys). Sama klooni/commit `cf59c15fae5058382ff4e27b38e7a306c36b5a7f`
  (ei uudempaa commitia origin/master:issa).
- **2026-07-15** — Vaihe A: torchbp:n lähdekoodi inventoitu (commit
  `cf59c15fae5058382ff4e27b38e7a306c36b5a7f`), löydökset kirjattu tähän
  ennen toteutuskoodin kirjoittamista.
