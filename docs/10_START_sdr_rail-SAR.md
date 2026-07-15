# SDR-projekti — START: Rail-SAR (olohuoneesta pihalle)

| | |
|---|---|
| **Projekti** | SDR |
| **Tyyppi** | Start-dokumentti (käynnistää SAR-tutkan rakennuksen) |
| **Status** | Aktiivinen — aloitusvaihe |
| **Päivitetty** | 2026-07-11 |
| **Pohjantähti** | [`00_POHJANTAHTI_lentava-SAR.md`](00_POHJANTAHTI_lentava-SAR.md) |
| **Seuraava** | [`20_START_drone_SAR-integraatio.md`](20_START_drone_SAR-integraatio.md) (aktivoituu kun tämä on todistettu) |

---

## Tavoite

Todistaa **koko kuvanmuodostusketju kiskolla**, ympäristössä jossa rata tunnetaan täydellisesti. Näin liikekompensaatio-ongelma eristetään kokonaan pois muuttujista, ja kun kuva on epätarkka, vika on koodissa tai raudassa — ei radassa. Tämä on projektin known-good-referenssi: kun ketju toimii kiskolla, se voidaan siirtää droneen tietäen että ainoa jäljellä oleva vaikea asia on autofokus.

Tämä on "halvin kokeilu ensin" puhtaimmillaan — ja tässä halvin kokeilu on myös opettavaisin, koska se eristää yhden vaikeuden kerrallaan.

## Vaihe 0 — Ohjelmistoketju ensin (ennen kuin mitään juotetaan)

Halvin ja tärkein askel. Aja kuvanmuodostus + autofokus **simuloidulla tai valmiilla datalla** ennen kuin tutkakorttia edes tilataan.

- Kloonaa `torchbp` (https://github.com/Ttl/torchbp) ja saa se pyörimään.
- Ratkaise laskenta-alusta: MPS Macilla vs. vuokra-GPU vs. Hacklabin NVIDIA-kone (ks. pohjantähti). Tämä on pakko ratkaista nyt, ei myöhemmin.
- Syötä simuloitua tai Forsténin tyyppistä dataa ja varmista että backprojection tuottaa kuvan ja autofokus tarkentaa sen.

**Onnistumiskriteeri:** näet tarkennetun kuvan datasta jota et itse kerännyt. Ketju on validoitu ohjelmiston osalta.

## Vaihe 1 — Rautaminimi (FMCW-tutka)

**Päivitetty 2026-07-15, ks. `paatokset/2026-07-15_sdr-kortti-ad9361.md`:** reitit A ja B eivät enää ole kaksi erillistä polkua — olemassa oleva Z7020+AD9361-SDR-kortti kattaa digitaalisen selkärangan molemmille, ja reitti B kutistuu RF-etupää-lisäkortiksi (chirp-PLL, PA, RX-suojaus, polarisaatiokytkentä) joka liittyy tähän korttiin. Perustelut ja avoimet suunnittelukohdat päätösmuistiossa.

- **A) Nopea validointi:** SDR-kortti sellaisenaan (natiivi AD9361-teho) riittää mittaus→data→kuva-ketjun todistamiseen ennen RF-etupään valmistumista.
- **B) Oma RF-etupää (pohjantähden mukainen):** ~6 GHz, kaista 300–500 MHz, ulkoinen chirp-PLL syötettynä AD9361:n `RX_EXT_LO_IN`/`TX_EXT_LO_IN`-pinneihin, PA n. 24 dB lisävahvistuksella +30 dBm-tavoitteeseen (kortin natiivi TX ~6,5 dBm ei riitä yksin), RX-suojaus, direct-conversion (AD9361:n natiivi ominaisuus).

**Huomioitavat sudenkuopat (Forsténin oppeja):**
- TX-RX-vuoto: >50 dB eristys TX/RX-antennien välillä, muuten vastaanotin kyllästyy.
- Zynqin hitaat massamuisti-interfacet (SD 25 MB/s) — ADC:n datavirta voi ylittää ne; ZipCPU:n `sdspi`-core auttaa.
- I/O-jännitteet (Forsténin SD-kortti-moka: 1,8 V vs 3,3 V) — tarkista footprintit.

**Onnistumiskriteeri:** tutka tuottaa range-compressed dataa jossa erottuu tunnettu kohde tunnetulla etäisyydellä.

## Vaihe 2 — Kiskomekaniikka

Tunnettu, toistettava rata ilman antureita. Tämä on Hacklab-työtä (lineaarijohde, askelmoottori, 3D-printatut kiinnikkeet).

- **Step-stop-measure -rytmi:** liikuta tutka pysähdyspisteeseen, mittaa, siirry seuraavaan. Ei Doppler-smearia, rata tunnetaan mikrometreillä.
- Vaihtoehto lyhyelle kantamalle: **turntable-ISAR** — pidä tutka paikallaan ja pyöritä kohdetta. Yksinkertaisempi mekaniikka sisätiloissa.

**Onnistumiskriteeri:** rata (tai kiertokulma) on toistettava ja tunnettu ilman erillistä paikannusta.

## Vaihe 3 — Ensimmäinen kohde: olohuone

Ensimmäinen oikea kuva sisätiloissa, lyhyellä kantamalla, täysin hallituissa oloissa.

**Miksi olohuone ensin:**
- Ei säätä, ei tuulta, ei GPS:ää — mikään ilmavaiheen vaikeus ei ole vielä läsnä.
- Kohteet ovat tunnettuja: voit asettaa kulmaheijastimia tai tuttuja esineitä ja verrata kuvaa siihen mitä *tiedät* olevan siellä.
- Nopea iterointisykli: mittaa, prosessoi, korjaa, toista — samassa huoneessa minuuteissa.
- Lyhyt kantama pitää IF-taajuudet matalina ja datamäärän pienenä.

**Käytännössä:** rail- tai turntable-skannaus huoneesta, muutama kulmaheijastin referenssikohteiksi, kuvanmuodostus vaiheen 0 ketjulla. Odota karkeaa kuvaa (0,3–0,5 m resoluutiolla huoneessa on vain kourallinen resoluutiosoluja) — tavoite ei ole kaunis kuva vaan *oikea* kuva: heijastimet näkyvät siellä missä ne oikeasti ovat.

**Onnistumiskriteeri:** tunnetut kohteet erottuvat kuvassa oikeilla paikoillaan. Ketju toimii päästä päähän omalla raudalla ja omalla datalla.

## Vaihe 4 — Siirto pihalle

Isompi, ulkoinen kohde — edelleen kisko tai turntable, ei vielä lentoa.

- Suurempi skene, pidempi kantama, luonnollisia kohteita (rakennuksen seinä, aita, puut, auto).
- Testaa dynamiikka-aluetta, kantamaa ja polarimetriaa oikeilla materiaaleilla (metsä vs. sileä pinta → HV/VH-ero).
- Edelleen tunnettu rata → ei tarvita autofokusta. Jos kuva on tarkka ilman autofokusta, ketju on kunnossa ja voit rajata drone-vaiheen ongelman puhtaasti liikekompensaatioon.

**Onnistumiskriteeri:** tunnistettava ulkokuva pihalta, polarimetriset erot näkyvissä. Tämän jälkeen aktivoituu [`20_START_drone_SAR-integraatio.md`](20_START_drone_SAR-integraatio.md).

## Mikä tästä siirtyy ilmaan — ja mikä ei

**Siirtyy drone-projektiin:** RF-kortti, antennit, Zynq/firmware, kuvanmuodostuskoodi, tutkan mikro-ohjaimen ohjelmisto, kaikki opittu RF- ja kuvanmuodostustieto.

**Ei siirry:** kisko, step-stop-mittaustapa, turntable. Ilmassa rata on jatkuva ja tuntematon — sen tilalle tulee ArduPilot-positiodata + autofokus.

**Jää viimeisteltäväksi vasta ilmassa:** autofokus. Se voidaan testata simuloidulla epätarkkuudella jo nyt, mutta lopullinen viritys vaatii oikeaa lentodataa oikealla tuuliheilunnalla.

## Työkaluketju

- **KiCad** — tutkakortti (6 kerrosta, ks. Forsténin schematic referenssinä).
- **Vivado + Tcl-pohjainen projektitallennus GitLabissa** — Zynq-firmware, CI/CD (sama käytäntö kuin Geckokapula-työssä).
- **`torchbp`** — kuvanmuodostus + autofokus.
- **GitLab-repo** — koodi + tämä doc + pohjantähti markdownina koodin vieressä.

## Avoimet kysymykset

- Laskenta-alusta lopullisesti (MPS vs. pilvi vs. Hacklab-NVIDIA)?
- ~~Oma kortti heti vai evalboard-välivaihe (reitti A vs B)?~~ — ratkaistu 2026-07-15, ks. `paatokset/2026-07-15_sdr-kortti-ad9361.md`.
- RF-etupään komponenttivalinnat (chirp-PLL, PA) — avoinna, ks. sama päätösmuistio.
- Kiskon pituus ja askelväli ensimmäistä olohuonemittausta varten?

## Muutosloki

- **2026-07-11** — Ensimmäinen versio. Vaiheistus 0→4 (ohjelmisto → rauta → kisko → olohuone → piha) kirjattu. Laskenta-alusta merkitty avoimeksi kysymykseksi ratkaistavaksi vaiheessa 0.
- **2026-07-11** — Siirretty GitHub-repoon `KalleLan/SAR-imaging` (`docs/`). Tiedostonimiin lisätty järjestysprefiksit (00/10/20), ristiviittaukset muutettu suhteellisiksi linkeiksi.
- **2026-07-15** — Vaihe 1 päivitetty: olemassa oleva Z7020-AD9361-SDR-kortti kattaa digitaalisen selkärangan, reitti B kutistuu RF-etupää-lisäkortiksi. Ks. `paatokset/2026-07-15_sdr-kortti-ad9361.md`.
