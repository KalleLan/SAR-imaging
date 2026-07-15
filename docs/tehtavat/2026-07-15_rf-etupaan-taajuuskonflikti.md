# RF-etupään taajuuskonflikti — jatkoselvitys ennen skeematyötä

| | |
|---|---|
| **Projekti** | SDR |
| **Tyyppi** | Tehtävänanto (Claude Code, Zed) — jatkoselvitys, ei vielä toteutusta |
| **Päivitetty** | 2026-07-15 |
| **Liittyy** | [`../paatokset/2026-07-15_rf-etupaan-arkkitehtuuri.md`](../paatokset/2026-07-15_rf-etupaan-arkkitehtuuri.md), [`../paatokset/2026-07-15_sdr-kortti-ad9361.md`](../paatokset/2026-07-15_sdr-kortti-ad9361.md), [`../10_START_sdr_rail-SAR.md`](../10_START_sdr_rail-SAR.md) |

---

## Konteksti

`2026-07-15_rf-etupaan-arkkitehtuuri.md` valitsi ulkoisen chirp-PLL:n (ADF4159 + HMC431LP4E) syötettynä AD9361:n `RX_EXT_LO_IN`/`TX_EXT_LO_IN`-pinneihin, koska AD9361:n sisäinen synteesi ei tue 300–500 MHz jatkuvaa pyyhkäisyä (kanavakaista max 56 MHz). Selvityksessä jäi avoimeksi, vaatiiko ulkoinen LO 2× taajuuden.

Tämä tarkistettiin nyt suoraan primaarilähteestä, **AD9361 Reference Manual (UG-570)**, "External LO" -osiosta:

> "Unlike the internal synthesizers that always operate from 6 GHz to 12 GHz no matter the RF tune frequency, the frequency applied when an External LO is used is 2× the desired RF LO frequency. The range of the EXT LO signal is from 140 MHz to 8 GHz, **covering the RF tune frequency range of 70 MHz to 4 GHz**."

Kaksi löydöstä:
1. **2× vahvistui** (kuten epäiltiin).
2. **Uusi, vakavampi löydös:** ulkoisen LO:n dokumentoitu tukialue on rajattu **70 MHz–4 GHz RF-taajuuteen** — ei kata koko sisäisen synteesin 70 MHz–6 GHz -aluetta. Pohjantähden ~5,77 GHz -tavoite on tämän dokumentoidun rajan **ulkopuolella**. Koko nykyinen RF-etupään arkkitehtuuri (ulkoinen LO-injektio) nojaa ominaisuuteen jota ei ole spesifioitu toimimaan valitulla taajuudella.

Sivulöydös samasta osiosta, hyödyllinen jakoverkon mitoitukseen jos ulkoista LO:ta silti käytetään: EXT_LO-signaalin tehotaso AD9361:n pinnissä tulee olla −3 dBm ≤ Pin ≤ +3 dBm, maksimi +6 dBm.

## Tehtävä

Selvitä, ennen mitään skeema- tai komponenttitilaustyötä, **pitääkö arkkitehtuuri vaihtaa stepped-frequency CW:hen (SFCW)** vai voiko ulkoista LO-injektiota käyttää 5,77 GHz:llä siitä huolimatta että se on dokumentoidun alueen ulkopuolella. Tuota selkeä suositus perusteluineen — ei vielä toteutusta.

Selvitä seuraavat, kukin lähteisiin viitaten (ei arvauksia):

1. **Empiirinen näyttö EXT_LO:n toiminnasta yli 4 GHz:n.** Etsi foorumeilta (EngineerZone/Analog Devices, GitHub-issuet analogdevicesinc/linux tai libiio/libad9361-iio -repoissa), akateemisista julkaisuista tai muista projekteista raportteja jossa AD9361:n ulkoista LO:ta on ajettu yli 8 GHz:n (eli yli 4 GHz RF-taajuudella). Datasheet-raja voi olla karakterisointiraja, ei ehdoton fyysinen raja — mutta tätä ei saa olettaa ilman näyttöä.

2. **SFCW-vaihtoehdon toteutettavuus tälle projektille.** Stepped-frequency CW pysyisi kokonaan AD9361:n dokumentoidulla 70 MHz–6 GHz sisäisen synteesin alueella (ei ulkoista LO:ta lainkaan) ja synteesoisi 300–500 MHz vastaavan kaistan diskreeteistä taajuusaskelista IFFT:llä. Selvitä: (a) tyypillinen askelmäärä ja lukitusaika per askel joka tarvittaisiin 300–500 MHz efektiiviselle kaistalle tässä etäisyysresoluutiossa, (b) onko tämä yhteensopiva pohjantähden PRF↔lentonopeus-rajapinnan kanssa (λ/4-näyteväli, ks. `00_POHJANTAHTI_lentava-SAR.md`) — SFCW on tyypillisesti hitaampi per "kuva" kuin jatkuva FMCW-pyyhkäisy, joten tarkista ettei tämä riko näyteväliä kiskovaiheessa, (c) tukeeko AD9361:n oma synteesin lukitusnopeus (`ad9361_set_rx_lo_freq`/`ad9361_set_tx_lo_freq` -kutsujen käytännön nopeus) ylipäätään SFCW:n vaatimaa askellusnopeutta.

3. **Tarkista mitä Forstén itse teki.** Pohjantähti nimeää hforsten.com:n ensisijaiseksi referenssiksi nimenomaan koska se on "täydellinen ketju RF:stä kuvanmuodostukseen". Lue hänen blogikirjoituksensa (ja mahdolliset schematic-kuvat) uudelleen tarkasti tällä kertaa juuri tästä näkökulmasta: käyttääkö hän AD9361/PlutoSDR-tyyppistä transceiveria ulkoisella LO:lla ylipäätään, vai onko hänen ratkaisunsa jokin muu (esim. erillinen mikseri + suoraan ADC, ei AD9361:n kautta ollenkaan)? Jos hänen arkkitehtuurinsa väistää tämän ongelman kokonaan eri reitillä, se on tärkein yksittäinen löydös tähän selvitykseen.

4. **Jos taajuuden laskeminen nousee esiin vaihtoehtona** (esim. ≤4 GHz, jolloin EXT_LO olisi dokumentoidusti tuettu) — älä tee tätä päätöstä itse, vain kirjaa se yhtenä vaihtoehtona perusteluineen. Pohjantähti valitsi ~6 GHz nimenomaan halpojen kuluttaja-RF-komponenttien takia; tämän muuttaminen on isompi päätös kuin tämän tehtävän scope.

## Tuotos

Päivitä `docs/paatokset/2026-07-15_rf-etupaan-arkkitehtuuri.md` uudella osiolla "Taajuuskonfliktin ratkaisu" (tai vastaava): mitä löytyi kustakin yllä olevasta kohdasta, lähteet, ja selkeä suositus kolmesta vaihtoehdosta (jatka ulkoisella LO:lla dokumentoidun rajan yli / vaihda SFCW:hen / harkitse taajuuden laskemista). Jos suositus muuttaa arkkitehtuuria, **älä vielä muokkaa komponenttivalintoja tai piirrä skeemaa** — se on oma, myöhempi tehtävänsä kun suunta on lukittu.

## Työtapa

- Lähteet aina näkyviin (URL, dokumentin nimi/versio, tai "ei löytynyt" jos ei löydy — älä täytä aukkoa arvauksella).
- Yksi committi tälle selvitykselle, kuvaava viesti.
- Jos selvitys jää kesken jostain kohdasta (esim. Forsténin blogista ei löydy riittävää yksityiskohtaa), kirjaa se eksplisiittisesti avoimeksi kohdaksi äläkä oleta parasta tapausta.

## Muutosloki

- **2026-07-15** — Ensimmäinen versio.
