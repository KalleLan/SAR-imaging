# Päätös: laskentakoneen GPU-linja

| | |
|---|---|
| **Tyyppi** | Päätösmuistio |
| **Päätetty** | 2026-07-13 |
| **Liittyy** | `30_laskentakone_pystytys.md` |

---

## Päätös

1. **Vaihe 0 ajetaan GTX 1070:llä** (8 GB, Pascal, cc 6.1), joka vapautuu pelikoneesta RTX 5070 -päivityksen myötä. Vara: GTX 970 (4 GB, cc 5.2).
2. **Kun kortti päivitetään, hankitaan käytetty RTX 3060 12GB** (Ampere, cc 8.6).

## Perustelut

**1070 ensin:** kortti on ilmainen (vapautuu joka tapauksessa) ja vaiheen 0 simulaatiokuorma mahtuu 8 GB:hen helposti. Pascal pakottaa versiolukkoon — ajuri 560 / CUDA toolkit 12.6 / PyTorch cu126-wheel — koska CUDA 13 pudotti Pascal-tuen ja PyTorch ≥ 2.8 pudotti sm_61:n cu128/cu129-wheeleistä. Lukko on hallittavissa (`apt-mark hold` + `pip freeze`), yksityiskohdat pystytysohjeessa.

**RTX 3060 12GB seuraavaksi:** ratkaiseva kriteeri on tukihorisontti. NVIDIA:n pudotusjärjestys: CUDA 13 vei Maxwell/Pascal/Voltan, seuraavana jonossa Turing (cc 7.5). Ampere on halvin arkkitehtuuri jolla on vuosia tukea jäljellä (datacenter-Ampere A100 pitää sen elossa PyTorch-ekosysteemissä). Lisäksi: 12 GB VRAM (+50 % vs 1070) osuu juuri SAR-kuorman pullonkaulaan, ~170 W TDP sopii jämäkoneen virtalähteelle, ja hinta Suomen käytetyillä markkinoilla n. 150–200 € (07/2026). Kortti palasi 07/2026 myös uustuotantoon (~330 $), mikä pitää käytettyjen hinnat vakaina ja saatavuuden hyvänä. Päivityksen yhteydessä Pascal-versiolukko puretaan ja siirrytään ajantasaiseen CUDA/torch-pinoon; torchbp käännetään uudelleen.

## Hylätyt vaihtoehdot

- **RTX 3060 Ti** — nopeampi, mutta 8 GB; SAR-kuormassa muisti > nopeus.
- **RTX 2060 12GB** — riittävä muisti, mutta Turing on seuraavana tuen pudotuslistalla.
- **RTX 4060 Ti 16GB** — selvästi kalliimpi, hyöty tähän vaiheeseen nähden pieni.
- **RTX 3080/3090** — hinta, virrankulutus ja jämäkoneen virtalähdevaatimukset.
- **Suora hyppy uuteen korttiin ilman 1070-välivaihetta** — hylätty: 1070 on ilmainen ja riittää vaiheen 0 validointiin; rahaa ei sidota ennen kuin ketju on todistettu.

## Muutosloki

- **2026-07-13** — Ensimmäinen versio.
