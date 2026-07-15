# Päätös: dedikoitu oma tutkakortti korvaa Zynq+AD9361-SDR-kortin

| | |
|---|---|
| **Tyyppi** | Päätösmuistio (kumoaa aiemman päätöksen) |
| **Päätetty** | 2026-07-15 |
| **Liittyy** | `10_START_sdr_rail-SAR.md` (Vaihe 1), `paatokset/2026-07-15_sdr-kortti-ad9361.md` (kumottu), `paatokset/2026-07-15_rf-etupaan-arkkitehtuuri.md` (scope muuttuu) |

---

## Päätös

1. **`paatokset/2026-07-15_sdr-kortti-ad9361.md` kumotaan.** Olemassa oleva Z7020+AD9361-SDR-kortti (7020-SDR, PlutoSDR-klooni) **ei** ole tämän tutkan rauta. Kortti siirtyy muihin SDR-käyttötarkoituksiin.
2. **Rakennetaan dedikoitu, kompakti oma tutkakortti** — Zynq (tai vastaava FPGA+ARM-SoC) ja Forsténin `fmcw3`-tyylinen diskreetti dechirp-RF-ketju samalla, tähän tehtävään suunnitellulla piirilevyllä. Ei yleiskäyttöisen devboardin ja päälle liimattujen lisäkorttien yhdistelmä.
3. **`paatokset/2026-07-15_rf-etupaan-arkkitehtuuri.md`:n scope laajenee** "RF-etupää-lisäkortista" koko tutkan omaksi kortiksi. Siinä tehdyt komponenttihavainnot (chirp-PLL, PA, RX-suojaus, polarisaatioarkkitehtuuri) pysyvät voimassa lähtökohtana, koska ne perustuivat jo osin samaan Forstén-referenssiin.
4. **Rakennetaan silti nyt, vaikka ei lennä vielä.** Kiskovaihe (vaihe 0–2) ja sisätilamittaukset (vaihe 3, olohuone) käyttävät samaa korttia kuin lopullinen drone-versio — ei väliaikaista devboard-ratkaisua.

## Perustelut

- **Kompaktius ja paino ovat suunnittelurajoite alusta asti, ei myöhempi optimointi.** Pohjantähti asettaa koko järjestelmälle alle 1 kg -budjetin akku mukaan lukien. Yleiskäyttöisen SDR-kortin käyttö "vain Zynq-osalta" olisi tarkoittanut koko kortin muodon, liittimien ja käyttämättömän AD9361-piirin kuljettamista turhana painona ja tilana — ei toimi lopullisessa alustassa.
- **Riski on nyt pienempi kuin alun perin, koska Forsténin todistettu referenssi on olemassa.** `fmcw3`-skeemat (ADF4158+HMC431LP4, ADL5802-dechirp-mikseri, SKY65404-LNA, LTC229x-ADC) ovat julkiset ja SAR-todistetut kolmessa sukupolvessa. Kahden riippumattoman muun lähteen (MIT Coffee Can Radar, Merlo & Nanzer arXiv:2110.14114) sama arkkitehtuurivalinta samalla taajuusalueella vahvistaa ettei tämä ole Forsténin oikotie vaan toistuva insinöörikäytäntö. Oma kortti ei siis ole enää "suunnittele tyhjästä" -riski, vaan tunnetun topologian sovitus.
- **AD9361-reitti olisi joka tapauksessa vaatinut ratkaisemattoman taajuuskonfliktin** (ulkoinen LO dokumentoitu vain 70 MHz–4 GHz:iin, tavoite 5,77 GHz) tai arkkitehtuurin osittaisen hylkäämisen (vain Zynq-osa käyttöön). Kun joka tapauksessa jouduttaisiin suunnittelemaan oma RF-ketju AD9361:n ohi, ei ole järkeä pitää AD9361:tä mukana ollenkaan.
- **"Ei osia yhteen liimattuna" -periaate koskee myös testausjärjestystä:** sama kortti todistetaan ensin sisätiloissa (vaihe 3) ja kiskolla/turntablella ennen ilmaan siirtoa — rauta ei muutu vaiheiden välillä, vain testiympäristö.

## Uusi välivaihe: liikkuva alusta ennen lentoa

Kiskon/turntablen (täysin tunnettu rata) ja dronen (autofokus pakollinen, tuuli, epäsuora rata) välissä on hyödyllinen aukko: **auton katolle kiinnitetty testi, ajettuna sivusuunnassa kohteeseen nähden.** Nopeus pidetään vakiona (esim. vakionopeudensäädin), korkeus vaihtelee vain jousituksen verran (muutama senttimetri, ei kymmeniä). Tämä antaa:

- Jatkuvan, ei-pysähtyvän liikkeen (toisin kuin step-stop-kisko) — testaa oikean PRF-pohjaisen jatkuvan hankinnan ensimmäistä kertaa.
- Paljon pienemmän ja paremmin ennustettavan virhemallin kuin drone (ei tuulta, ei kallistusta, nopeus tasainen) — hyvä välitaso autofokuksen stressitestaukseen ennen oikeaa lentodataa.

Tätä ei ole vielä spesifioitu (nopeuden mittaustapa, kiinnitys, turvallisuus) — kirjataan avoimeksi ideaksi `10_START_sdr_rail-SAR.md`:hen, tarkennetaan kun vaihe 3 on todistettu.

## Hylätyt vaihtoehdot

- **Zynq+AD9361-kortin osittainen uusiokäyttö** (vain FPGA/ARM, oma RF-ketju erillisenä ADC:llä) — hylätty: ei kompakti, kaksi erillistä korttia liimattuna yhteen ei ole se lopullinen integraatio jota drone-alusta vaatii.
- **AD9361:n käyttö ulkoisella LO:lla dokumentoidun 4 GHz -rajan yli, empiirisesti testaten** — hylätty: vaikka voisi teknisesti toimia, rakentaisi koko arkkitehtuurin epävarmalle, dokumentoimattomalle pohjalle kun todistettu vaihtoehto on olemassa.

## Muutosloki

- **2026-07-15** — Ensimmäinen versio. Kumoaa `2026-07-15_sdr-kortti-ad9361.md`.
