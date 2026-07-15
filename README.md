# SAR-imaging — Lentävä polarimetrinen SAR-tutka

> Ilmasta kuvantava polarimetrinen FMCW-SAR-tutka pienessä FPV-dronessa.
> Harrastajabudjetti (~800 €), kantama ≥ 1,5 km, paino < 1 kg, neljä polarisaatiota (HH/HV/VH/VV).

| | |
|---|---|
| **Status** | Aktiivinen — Vaihe 0 (ohjelmistoketju) todistettu CPU:lla, odottaa GPU-konetta lopulliseen validointiin. Vaihe 1 (rautaminimi): dedikoitu oma tutkakortti päätetty, RF-arkkitehtuuri lukittu, komponenttivalinta käynnissä. |
| **Pohjantähti** | [`docs/00_POHJANTAHTI_lentava-SAR.md`](docs/00_POHJANTAHTI_lentava-SAR.md) |
| **Päivitetty** | 2026-07-15 |

---

## Tavoite

Rakennetaan Henrik Forsténin toteutuksen viitoittama drone-SAR-järjestelmä kahdessa vaiheessa:

1. **Rail-SAR (SDR-projekti)** — koko kuvanmuodostusketju todistetaan kiskolla, jossa rata tunnetaan täydellisesti. Liikekompensaatio eristetään pois muuttujista.
2. **Ilmaan siirto (drone-projekti)** — todistettu ketju (RF-kortti, antennit, firmware, kuvanmuodostus) siirretään lentävälle alustalle. Ainoa uusi vaikea asia on liikekompensaatio: ei-RTK-GPS + IMU + autofokus.

Positiotarkkuus hoidetaan **autofokuksella, ei RTK:lla**. Kuvanmuodostus on GPU-backprojection ([`torchbp`](https://github.com/Ttl/torchbp)) + minimi-entropia-autofokus.

**Tietoinen rajaus:** 6 GHz (C-bändi) **ei näe latvuston läpi**. Tämä on pintamateriaalin tunnistusta (polarimetria), ei FOPEN-järjestelmä.

## Avainparametrit (lähtökohta)

| Parametri | Arvo |
|---|---|
| Taajuus | ~6 GHz (λ ≈ 5,2 cm) |
| Aaltomuoto | FMCW, suora konversio |
| Kaista | 300–500 MHz → resoluutio 0,5–0,3 m |
| TX-teho | +30 dBm, antennivahvistus ~10 dBi |
| ADC | 50 MHz |
| Prosessori | Zynq-luokan SoC (FPGA + 2× ARM), oma dedikoitu kortti |
| RF-ketju | Diskreetti chirp-PLL + dechirp-mikseri (Forsténin `fmcw3`-arkkitehtuuri), ei integroitu transceiver-piiri |
| Polarisaatiot | HH / HV / VH / VV |
| Positio | GPS (~1 m) + IMU-fuusio + autofokus |
| Lentoalusta | 7" ArduPilot-kopteri, hyötykuorma ~1 kg |

## Dokumentaatio

Dokumentit luetaan tässä järjestyksessä:

| # | Dokumentti | Rooli |
|---|---|---|
| 00 | [Pohjantähti — Lentävä polarimetrinen SAR](docs/00_POHJANTAHTI_lentava-SAR.md) | Jaettu visio: mitä rakennetaan ja miksi. Arkkitehtuurimuutokset kirjataan **vain tänne**. |
| 10 | [START: Rail-SAR](docs/10_START_sdr_rail-SAR.md) | **Aktiivinen.** SDR-projektin käynnistys: ohjelmisto → rauta → kisko → olohuone → auto → piha. |
| 20 | [START: Drone-SAR-integraatio](docs/20_START_drone_SAR-integraatio.md) | Odottaa esiehtoja. Aktivoituu kun ketju on todistettu kiskolla. |
| 30 | [Laskentakone: pystytys](docs/30_laskentakone_pystytys.md) | GPU-koneen rauta, versiolukko (CUDA 12.6, GTX 1070), asennusohjeet. |

Yksittäiset arkkitehtuuripäätökset (mitä valittiin, miksi, mitkä vaihtoehdot hylättiin) ovat `docs/paatokset/`-kansiossa, Claude Code -tehtävänannot `docs/tehtavat/`-kansiossa — elävät dokumentit yllä viittaavat näihin, eivät toista niiden sisältöä.

## Vaiheistus ja tila

```
SDR-projekti (Rail-SAR)                              Drone-projekti
──────────────────────────                           ──────────────────────────
[~] 0. Ohjelmistoketju — CPU-ketju todistettu,           valmisteleva työ ilman tutkaa:
      GPU-validointi (autofokus) odottaa laskentakonetta [ ] alusta viritetty & luotettava
[~] 1. Rautaminimi — dedikoitu oma kortti päätetty,      [ ] MAVLink ELRS:n yli
      RF-arkkitehtuuri lukittu, komponenttivalinta käynnissä
[ ] 2. Kiskomekaniikka                                   [ ] ROI-spotlight-patch (#28486)
[ ] 3. Ensimmäinen kuva: olohuone
[ ] 3.5 Liikkuva alusta (auto)
[ ] 4. Siirto pihalle ───────── aktivoi ──────────►      [ ] SAR-integraatio (START 20)
```

## Referenssit

- **Forsténin blogi (ensisijainen referenssi):** https://hforsten.com/homemade-polarimetric-synthetic-aperture-radar-drone.html
- **Jatko-osa — autofokus ja kalibrointi (10/2025):** https://hforsten.com/synthetic-aperture-radar-autofocus-and-calibration.html
- **Forsténin RF-kortit (GitHub `Ttl`), konkreettinen skeemareferenssi rautaminimille:** `fmcw`/`fmcw2`/`fmcw3` — `fmcw3` on SAR-todistettu (ADF4158+HMC431LP4 chirp-PLL, ADL5802-dechirp-mikseri, SKY65404-LNA, LTC229x-ADC, ei integroitua transceiveria).
- **Kaksi riippumatonta muuta SAR-precedenttiä samalla diskreetillä arkkitehtuurilla:** MIT/Charvat "Coffee Can Radar" (2,4 GHz, avoin kurssireferenssi), Merlo & Nanzer, arXiv:2110.14114 (vertaisarvioitu, C-kaista 5,725–6,0 GHz).
- **torchbp — GPU-backprojection + autofokus (MIT):** https://github.com/Ttl/torchbp
- **ArduPilot ROI-spotlight-patch:** PR #28486

## Työkalut

- **KiCad** — tutkakortti (6 kerrosta)
- **Vivado** (Tcl-pohjainen projektitallennus) — Zynq-firmware
- **torchbp / PyTorch** — kuvanmuodostus ja autofokus
- Tämä repo — koodi + dokumentaatio samassa paikassa

## Repon rakenne

```
SAR-imaging/
├── README.md                ← tämä: tavoite, tila, kartta dokumentteihin
├── docs/
│   ├── 00_POHJANTAHTI_lentava-SAR.md
│   ├── 10_START_sdr_rail-SAR.md
│   ├── 20_START_drone_SAR-integraatio.md
│   ├── 30_laskentakone_pystytys.md
│   ├── paatokset/            (arkkitehtuuripäätökset: mitä, miksi, hylätyt vaihtoehdot)
│   └── tehtavat/              (Claude Code -tehtävänannot)
├── imaging/                  torchbp-kuvanmuodostus + autofokus, vaihe 0 — CPU-ketju
│   │                         todistettu (sar_sim/, scripts/01-03, tests/), GPU-validointi avoinna
│   ├── sar_sim/               simulaattori (geometry, point_targets, errors)
│   ├── scripts/                01_smoke_cpu / 02_backprojection / 03_autofocus
│   └── tests/
├── hw/                       (tuleva: KiCad-kortti, Forsténin fmcw3 -referenssillä, vaihe 1)
├── fw/                       (tuleva: Zynq-firmware, vaihe 1)
└── rail/                     (tuleva: kiskomekaniikka, vaihe 2)
```

Hakemistot `hw/`, `fw/` ja `rail/` luodaan kun vastaava vaihe alkaa — tyhjät hakemistot eivät versioidu Gitissä.
