# Vaihe 0 — Claude Code -tehtävänanto: imaging/-runko

| | |
|---|---|
| **Projekti** | SDR |
| **Tyyppi** | Tehtävänanto (Claude Code, Zed) + imaging/-hakemiston suunnitelma |
| **Päivitetty** | 2026-07-11 |
| **Liittyy** | [`10_START_sdr_rail-SAR.md`](../10_START_sdr_rail-SAR.md) vaihe 0, [`30_laskentakone_pystytys.md`](../30_laskentakone_pystytys.md) |

---

## imaging/-hakemiston runko (suunnitelma)

```
imaging/
├── README.md                  # asennus, ajo, hyväksymiskriteerit
├── requirements.txt           # torch (cu126-huomautus), numpy, scipy, matplotlib
├── requirements-lock.txt      # pip freeze validoidusta ympäristöstä (syntyy myöhemmin)
├── sar_sim/
│   ├── __init__.py
│   ├── geometry.py            # rata: suora lineaarinen rata, λ/4-näytteistys
│   ├── point_targets.py       # FMCW-raakadatan simulointi pistemaaleista
│   └── errors.py              # positiovirheen injektointi rataan (sini/lineaarinen/satunnaiskävely)
├── scripts/
│   ├── 01_smoke_cpu.py        # torchbp importtaantuu, pieni bp CPU:lla (toimii Macilla)
│   ├── 02_backprojection.py   # GPU-bp simuloidulla datalla → PNG + metriikat
│   └── 03_autofocus.py        # virheellinen rata → minimi-entropia-autofokus → vertailu-PNG:t
├── results/                   # .gitignore: PNG:t ja välidata eivät mene gitiin
└── tests/
    └── test_sim.py            # simulaattorin yksikkötestit (ei GPU:ta)
```

Suunnitteluperiaatteet:
- **Simulaattori on oma moduulinsa**, ei torchbp:n kylkeen kirjoitettu — sama simulaattori palvelee myöhemmin autofokuksen stressitestausta (START-dokumentin "autofokus voidaan testata simuloidulla epätarkkuudella jo nyt").
- **Skriptit numeroitu ajojärjestykseen** ja jokainen tulostaa lopuksi selkeän PASS/FAIL-rivin onnistumiskriteeriään vasten.
- **CPU-savutesti erikseen**, koska torchbp:n CPU-operaatiot mahdollistavat ketjun osittaisen validoinnin Macilla ennen kuin GPU-kone on pystyssä.
- Parametrit (taajuus 6 GHz, kaista 300 MHz, λ/4-näyteväli) otetaan pohjantähden referenssiarvoista yhteen `params`-rakenteeseen, ei ripoteltuna koodiin.

---

## Tehtävänanto Claude Codelle (kopioi tästä alaspäin)

Toteuta SAR-imaging-repoon `imaging/`-hakemisto, joka validoi torchbp-kirjaston kuvanmuodostus- ja autofokusketjun simuloidulla datalla. Tämä on projektin vaihe 0 (ks. `docs/10_START_sdr_rail-SAR.md`); onnistumiskriteeri on tarkennettu SAR-kuva datasta jota emme itse keränneet.

### Konteksti ja reunaehdot

- Kohdeympäristö: headless Ubuntu 24.04, GTX 1070 (Pascal, sm_61), CUDA toolkit 12.6, PyTorch cu126-wheel. Kehitys tapahtuu Macilla (Apple Silicon, ei CUDAa) — siksi kaiken pitää degradoitua siististi: GPU-skriptit tarkistavat `torch.cuda.is_available()` ja antavat selkeän virheilmoituksen CPU-koneella sen sijaan että kaatuvat stack traceen.
- torchbp asennetaan erikseen ohjeella: ensin torch, sitten `pip install --no-build-isolation -e .` torchbp-kloonissa. Älä lisää torchbp:tä requirements.txt:hen pip-riippuvuutena — kirjaa se README:hen manuaalisena vaiheena.
- Referenssiskenaario on Forsténin autofokus-blogin synteettinen esimerkki: 9 pistemaalia ruudukossa, tutka 20 m korkeudella, suora rata Y-akselia pitkin, näyteväli λ/4 (12,5 mm @ 6 GHz).

### Vaihe A — inventoi torchbp ennen koodin kirjoittamista

Kloonaa https://github.com/Ttl/torchbp (jos ei jo kloonattu) ja selvitä lukemalla lähdekoodia, ÄLÄ arvaamalla:

1. Mitä `examples/`-hakemistossa on — jos siellä on valmis pistemaalisimulaatio tai autofokus-esimerkki, **käytä sitä pohjana** oman keksimisen sijaan ja kirjaa mistä tiedostosta mikäkin on peräisin.
2. torchbp:n julkinen API: millä funktiolla ajetaan backprojection polaarigridille, mikä on odotettu raakadatan muoto (range-compressed vai raaka FMCW; tensorin dimensiot; dtype — todennäköisesti complex64), miten rata/positio annetaan, ja mikä funktio/luokka toteuttaa minimi-entropia-autofokuksen.
3. Mitkä operaatiot toimivat CPU:lla — tämän perusteella päätä mitä `01_smoke_cpu.py` voi oikeasti ajaa Macilla.
4. Onko `torchbp`-paketissa valmis simulaattori- tai util-moduuli datan generointiin. Jos on, käytä sitä `sar_sim`-moduulin sisältä (ohut wrapperi) sen sijaan että kirjoitat fysiikan itse.

Kirjoita inventaarion tulokset tiedostoon `imaging/README.md` osioon "torchbp API -muistiinpanot" ennen kuin jatkat.

### Vaihe B — toteuta runko

Toteuta yllä kuvattu hakemistorakenne. Tarkennukset:

**`sar_sim/point_targets.py`:** generoi simuloitu data 9 pistemaalille ruudukossa (esim. 3×3, 10 m välein, keskipiste ~100 m päässä radasta). Parametrit dataklassina: kantoaaltotaajuus 6.0 GHz, kaista 300 MHz, radan pituus (esim. 5 m → 400 näytettä λ/4-välein), tutkan korkeus 20 m. Jos torchbp tarjoaa datageneroinnin, wrappaa se; muuten toteuta yksinkertainen pistemaalivaste (etäisyysriippuva vaihe, ei tarvita RCS-fysiikkaa).

**`sar_sim/errors.py`:** funktio joka ottaa ideaaliradan ja palauttaa virheellisen: (a) lineaarinen driftti, (b) sinimuotoinen heilunta (amplitudi parametrina, oletus ~0.1 λ ... 1 λ), (c) satunnaiskävely. Palauttaa sekä virheellisen radan että totuusvirheen vertailua varten.

**`scripts/02_backprojection.py`:** simuloi data ideaaliradalla → aja torchbp:n backprojection → tallenna kuva `results/bp_ideal.png`. PASS-kriteeri: kuvan 9 kirkkainta paikallista maksimia osuvat ≤ 1 resoluutiosolun päähän maalien tunnetuista paikoista. Tulosta maalikohtainen taulukko (odotettu vs. mitattu paikka, huippuarvo).

**`scripts/03_autofocus.py`:** sama data mutta bp ajetaan **virheellisellä** radalla → tallenna sumea kuva `results/bp_error.png` → aja torchbp:n minimi-entropia-autofokus → tallenna `results/bp_autofocus.png`. PASS-kriteerit: (1) kuvan entropia autofokuksen jälkeen ≤ lähellä ideaalikuvan entropiaa, (2) maalien paikat palautuvat ≤ 1 solun tarkkuuteen, (3) tulosta ratkaistun positiovirheen RMS suhteessa injektoituun totuuteen. Tee kolmen kuvan rinnakkaisvertailu (ideaali / virhe / korjattu) yhteen PNG:hen.

**`scripts/01_smoke_cpu.py`:** importtaa torchbp, generoi minimaalinen data ja aja pienin CPU:lla tuettu operaatio (vaiheen A kohdan 3 perusteella). Tarkoitus: nopea "asennus kunnossa" -tarkistus joka toimii myös Macilla.

**`tests/test_sim.py`:** pytest-testit simulaattorille ilman GPU:ta: datan muoto ja dtype oikein, vaihe käyttäytyy etäisyyden funktiona odotetusti, virheinjektio palauttaa totuuden oikein.

### Vaihe C — dokumentoi

`imaging/README.md`: asennusjärjestys (viittaa `docs/30_laskentakone_pystytys.md`:ään ympäristön osalta), skriptien ajojärjestys ja kunkin PASS-kriteeri, torchbp API -muistiinpanot vaiheesta A, ja "known good" -osio johon kirjataan versiot ja ajopäivä kun ketju on ensimmäisen kerran mennyt läpi GPU-koneella.

### Työtapa

- Tee pieniä committeja loogisin välein (inventaario → sim → skriptit → testit → docs).
- Aja `pytest imaging/tests/` ja `scripts/01_smoke_cpu.py` Macilla ennen valmiiksi toteamista; GPU-skriptien osalta riittää tässä vaiheessa, että ne epäonnistuvat siististi selkeällä viestillä CUDA:n puuttuessa.
- Jos torchbp:n API poikkeaa oletuksista (esim. autofokus vaatii eri datamuodon), päivitä tämä suunnitelma todellisuuden mukaan ja kirjaa poikkeama README:hen — älä pakota suunnitelmaa väkisin.

## Muutosloki

- **2026-07-13** — Ristiviittaukset korjattu numeroituihin tiedostonimiin.
- **2026-07-11** — Ensimmäinen versio. imaging/-runko ja Claude Code -tehtävänanto (inventaario → toteutus → dokumentointi).
