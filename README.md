# SAR-imaging — Lentävä polarimetrinen SAR-tutka

> Ilmasta kuvantava polarimetrinen FMCW-SAR-tutka pienessä FPV-dronessa.
> Harrastajabudjetti (~800 €), kantama ≥ 1,5 km, paino < 1 kg, neljä polarisaatiota (HH/HV/VH/VV).

| | |
|---|---|
| **Status** | Aktiivinen — Rail-SAR-aloitusvaihe (SDR, vaihe 0) |
| **Pohjantähti** | [`docs/00_POHJANTAHTI_lentava-SAR.md`](docs/00_POHJANTAHTI_lentava-SAR.md) |
| **Päivitetty** | 2026-07-11 |

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
| Prosessori | Zynq 7020 (FPGA + 2× ARM) |
| Polarisaatiot | HH / HV / VH / VV |
| Positio | GPS (~1 m) + IMU-fuusio + autofokus |
| Lentoalusta | 7" ArduPilot-kopteri, hyötykuorma ~1 kg |

## Dokumentaatio

Dokumentit luetaan tässä järjestyksessä:

| # | Dokumentti | Rooli |
|---|---|---|
| 00 | [Pohjantähti — Lentävä polarimetrinen SAR](docs/00_POHJANTAHTI_lentava-SAR.md) | Jaettu visio: mitä rakennetaan ja miksi. Arkkitehtuurimuutokset kirjataan **vain tänne**. |
| 10 | [START: Rail-SAR](docs/10_START_sdr_rail-SAR.md) | **Aktiivinen.** SDR-projektin käynnistys: ohjelmisto → rauta → kisko → olohuone → piha. |
| 20 | [START: Drone-SAR-integraatio](docs/20_START_drone_SAR-integraatio.md) | Odottaa esiehtoja. Aktivoituu kun ketju on todistettu kiskolla. |

## Vaiheistus ja tila

```
SDR-projekti (Rail-SAR)                          Drone-projekti
──────────────────────────                       ──────────────────────────
[ ] 0. Ohjelmistoketju (torchbp + laskenta-alusta)   valmisteleva työ ilman tutkaa:
[ ] 1. Rautaminimi (FMCW-tutka)                      [ ] alusta viritetty & luotettava
[ ] 2. Kiskomekaniikka                               [ ] MAVLink ELRS:n yli
[ ] 3. Ensimmäinen kuva: olohuone                    [ ] ROI-spotlight-patch (#28486)
[ ] 4. Siirto pihalle ───────── aktivoi ──────────►  [ ] SAR-integraatio (START 20)
```

## Referenssit

- **Forsténin blogi (ensisijainen referenssi):** https://hforsten.com/homemade-polarimetric-synthetic-aperture-radar-drone.html
- **Jatko-osa — autofokus ja kalibrointi (10/2025):** https://hforsten.com/synthetic-aperture-radar-autofocus-and-calibration.html
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
│   └── 20_START_drone_SAR-integraatio.md
├── imaging/                 (tuleva: torchbp-kokeilut, vaihe 0)
├── hw/                      (tuleva: KiCad-kortti, vaihe 1)
├── fw/                      (tuleva: Zynq-firmware, vaihe 1)
└── rail/                    (tuleva: kiskomekaniikka, vaihe 2)
```

Hakemistot `imaging/`, `hw/`, `fw/` ja `rail/` luodaan kun vastaava vaihe alkaa — tyhjät hakemistot eivät versioidu Gitissä.
