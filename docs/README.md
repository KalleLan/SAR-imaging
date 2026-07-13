# docs/ — dokumentaation rakenne ja käytännöt

| | |
|---|---|
| **Tyyppi** | Rakennekuvaus (lue tämä ennen uuden dokumentin luontia) |
| **Päivitetty** | 2026-07-13 |

---

## Periaate

Dokumentit jakautuvat kahteen luokkaan:

1. **Numeroitu lukupolku** — pieni ydinjoukko, joka luetaan järjestyksessä kun projektiin tullaan sisään. Kaksinumeroinen etuliite kymmenvälein (00, 10, 20, ...), jotta väliin voi lisätä (05, 15, ...) ilman uudelleennimeämistä. Pidetään korkeintaan ~5–6 dokumentissa.
2. **Aihekansiot** — kaikki muu: tehtävänannot, päätösmuistiot, mittauspöytäkirjat. Näillä ei ole lukujärjestystä vaan ne ovat hakemistoa. Tiedostonimi alkaa päivämäärällä `YYYY-MM-DD_aihe.md`, jolloin aakkosjärjestys = aikajärjestys ilman juoksevan numeron ylläpitoa.

## Rakenne

```
docs/
├── README.md                          # tämä tiedosto
├── 00_POHJANTAHTI_lentava-SAR.md      # visio ja jaetut rajapinnat (master)
├── 10_START_sdr_rail-SAR.md           # SDR-projektin vaiheistus (rail-SAR)
├── 20_START_drone_SAR-integraatio.md  # drone-projektin vaiheistus
├── 30_laskentakone_pystytys.md        # laskentakoneen rauta, pystytys, versiolukitus
├── tehtavat/                          # Claude Code -tehtävänannot
│   └── 2026-07-11_vaihe0_imaging_runko.md
├── paatokset/                         # päätösmuistiot: mitä, miksi, mitkä vaihtoehdot hylättiin
│   └── 2026-07-13_gpu-valinta.md
└── mittaukset/                        # mittauspöytäkirjat (syntyy vaiheesta 1 alkaen)
```

## Säännöt uudelle dokumentille

- **Kuuluuko lukupolkuun?** Vain jos projektiin sisään tuleva lukija tarvitsee sen ymmärtääkseen kokonaisuuden. Jos epäröit, se ei kuulu → aihekansioon.
- **Päätös tehty?** Kirjaa se `paatokset/`-kansioon omana muistiona (mitä päätettiin, miksi, hylätyt vaihtoehdot, kirjauspäivä). Elävät dokumentit *viittaavat* päätösmuistioihin, eivät toista niiden sisältöä — näin päätöksen perustelu löytyy yhdestä paikasta eikä eriydy.
- **Tehtävänanto Claude Codelle?** → `tehtavat/`, päivämäärällä. Tehtävänanto on kertakäyttöinen tilannekuva; jos suunnitelma muuttuu toteutuksessa, todellisuus kirjataan toteutuksen omaan README:hen (esim. `imaging/README.md`), ei tehtävänantoa muokkaamalla.
- **Jokaisessa dokumentissa:** alkuun metataulukko (tyyppi, status, päivitetty, liittyvät docit) ja loppuun muutosloki. Sama käytäntö kuin start-dokumenteissa.

## Muutosloki

- **2026-07-13** — Ensimmäinen versio. Kaksitasoinen rakenne (numeroitu lukupolku + päivämäärälliset aihekansiot) otettu käyttöön ennen dokumenttimäärän kasvua.
