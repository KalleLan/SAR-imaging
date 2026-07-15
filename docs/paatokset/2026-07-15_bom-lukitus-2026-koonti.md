# Päätös: BOM-lukitus 2026-koontiin (Forstén fmcw3 -osalista + Zynq-SoC)

| | |
|---|---|
| **Tyyppi** | Päätösmuistio |
| **Päätetty** | 2026-07-15 |
| **Liittyy** | `2026-07-15_dedikoitu-tutkakortti.md` (oma tutkakortti), `2026-07-15_rf-etupaan-arkkitehtuuri.md` (RF-arkkitehtuuri, komponenttihavainnot kohdassa 3a), `../10_START_sdr_rail-SAR.md` (Vaihe 1 — Rautaminimi) |

---

## Päätös

RF-etupään arkkitehtuuripäätöksessä (`2026-07-15_rf-etupaan-arkkitehtuuri.md`) valitut osat (ADF4159/HMC431LP4E, SE5004L, SKY16603-632LF) valittiin vielä AD9361-oletuksella. Tässä muistiossa jokainen Forsténin `fmcw3`-BOM:in osa (skeemoista poimitut tarkat osanumerot, ks. edellisen päätöksen kohta 3a) sekä nuo kolme aiemmin valittua osaa on tarkistettu erikseen: onko yhä valmistuksessa 2026, tarvitseeko korvaajan, ja mikä on export-control-riski. Lisäksi lukitaan Zynq-luokan SoC omalle kortille.

### Lopullinen BOM — tila 2026-07-15

| Lohko | Osa | Valmistaja | Status 2026 | Toimenpide |
|---|---|---|---|---|
| Chirp-PLL | **ADF4159** | Analog Devices | Active, EAR99 | **Säilyy.** Vahvistettu parempi valinta kuin ADF4158 (fast-ramp-moottori) — ADF4158 säilyy varana, myös Active |
| VCO | **HMC431LP4E** | Analog Devices | Active | Säilyy |
| TX-puskuri (VCO jälkeen) | ~~MGA-25203~~ | Broadcom | **Obsolete** | **Korvattava.** Ei vahvistettua pin-yhteensopivaa korvaajaa löytynyt tässä haussa — avoin kohta, ks. alla |
| TX-vaimennin/ALC | **PAT1220** (×2) | Susumu | Active | Säilyy |
| ALC-op-ampi | **TLV172DCK** | Texas Instruments | Active | Säilyy |
| TX-haaroitus | Branchline-kytkin (Z1) | — | PCB-mikroliuskarakenne, ei ostettava osa | Ei BOM-riviä, suunnitellaan/simuloidaan skeemavaiheessa |
| TX-tehovahvistin | **SE5004L** | Skyworks | Active | **Säilyy, rooli täsmennetty:** erillinen PA-aste mikserin/haaroituksen jälkeisessä TX-polussa (pohjantähden +30 dBm-tavoite), ei osa Forsténin matalatehoisesta LO-/puskuriketjusta |
| RX LNA | ~~SKY65404~~ | Skyworks | **Discontinued** (viallinen PCN 2025-03-20) | **Korvattava.** Ei vahvistettua korvaajaa löytynyt tässä haussa — avoin kohta, ks. alla |
| RX-vahvistin | **TRF37A75** | Texas Instruments | Active | Säilyy |
| Mikseri | **ADL5802** (×2, 1/RX-kanava) | Analog Devices | Active | Säilyy |
| Mikserin LO/RF-yhdistin | **5400BL15B050E** (×2/kanava) | **Johanson Technology** (ei Anaren, korjattu) | Active, ~7000+ kpl varastossa | Säilyy — tarkennus: keraaminen balun (180° vaihekäännin), ei suunnattu kytkin |
| IF-vahvistin | **ADA4940-2** (×2) | Analog Devices | Active | Säilyy |
| ADC | **LTC2292** (LTC229x-perhe) | Analog Devices (ent. Linear Tech) | Active, koko perhe yhä ADI:n katalogissa | Säilyy |
| RX-suojaus | **SKY16603-632LF** | Skyworks | Ristiriitainen tila (jakelijat: active; Skyworksin oma sivu viittaa lopetukseen) | **Rooli kyseenalaistettu, ei pakollinen.** Ks. alla |
| Zynq-luokan SoC | **XC7Z020** (`-1CLG400C` tai `-2CLG400I`) | AMD/Xilinx | Active, elinkaari taattu 2035:een | **Uusi valinta.** Korvaa AD9361-kortin Z7020-riippuvuuden omalla, samaan piiriin perustuvalla valinnalla |

## Perustelut

### Chirp-PLL, VCO, ALC-ketju
ADF4159 pysyy ensisijaisena valintana: sekä ADF4158 että ADF4159 ovat 2026 aktiivisia ja EAR99-luokassa, mutta ADF4159:n fast-ramp-moottori on suoraan relevantti FMCW-pyyhkäisyn retrace-ajan minimointiin — sama peruste kuin alkuperäisessä RF-etupäätöksessä. HMC431LP4E, PAT1220 ja TLV172DCK ovat kaikki aktiivisia, avoimesti Digikey/Mouser-jakelussa ilman ITAR-merkintöjä.

### MGA-25203 — EOL, avoin korvaajakysymys
Broadcomin MGA-25203 (VCO:n jälkeinen puskurivahvistin Forsténin TX-ketjussa) on merkitty "Obsolete"/"Not Available" sekä Digikeyllä että Mouserilla. Broadcom ei ole julkaissut virallista cross-reference-korvaajaa. Yleiskäyttöisiä 5–6 GHz GaAs-gain-block-piirejä on markkinoilla (esim. Mini-Circuits, MACOM, Qorvo -valikoimat), mutta yhtä varmistettua pin-yhteensopivaa korvaajaa ei löytynyt tässä tutkimuksessa — ei täytetä arvauksella, kirjataan avoimeksi kohdaksi KiCad-vaiheelle.

### SKY65404 — discontinued, avoin korvaajakysymys
Skyworks julkaisi virallisen Product Discontinuance Notice -ilmoituksen SKY65404-sarjalle 2025-03-20 (syy: "low demand and end of business with filter supplier"). Jälleenmyyjävarastoja on vielä jäljellä (Digikey/Mouser/LCSC), mutta uutta valmistusta ei tule. Tarkkaa, vahvistettua korvaajaa ei löytynyt hakukyselyillä (jakelijasivut viittaavat "suggested replacement" -kenttään, mutta tarkkaa osanumeroa ei saatu varmistettua) — avoin kohta, ratkaistava ennen tilausta uudella hakukierroksella suoraan Skyworksin myyntikanavasta tai valitsemalla yleiskäyttöinen 5–6 GHz LNA muulta valmistajalta (esim. Qorvo, MACOM, Analog Devices/Hittite -valikoimista).

### 5400BL15B050E — valmistajakorjaus
Alkuperäinen RF-arkkitehtuuripäätös ei erikseen nimennyt tämän osan valmistajaa. Tarkistus osoitti sen olevan **Johanson Technology**, ei Anaren/Knowles kuten aiemmin oletettiin — kyseessä on keraaminen balun (4,9–5,9 GHz, 180°±10° vaihekäännin), ei suunnattu kytkin/jakaja. Rooli mikserin LO-tulon differentiaalisen ohjauksen tuottajana pysyy samana, vain valmistaja-/tyyppitieto tarkentuu. Aktiivinen, laajasti varastossa (~7000+ kpl Digikeyllä), ei export-merkintöjä.

### SKY16603-632LF — rooli kyseenalaistettu
Tämä valittiin alun perin AD9361-oletuksella suojaamaan integroidun transceiverin RX-tuloa. Forsténin oma julkaistu materiaali (blogi + `fmcw3`-repo) ei viittaa eksplisiittiseen PIN-diodilimiteriin RX-SMA:n ja LNA:n välissä — hänen ratkaisunsa nojaa ilmeisesti TX/RX-antennien fyysiseen erotteluun (bistaattinen konfiguraatio) ja ADC:n dynamiikka-alueen mitoitukseen AGC:n sijaan. Osan oma saatavuustilanne on lisäksi ristiriitainen (jakelijat: aktiivinen; Skyworksin oma sivu viittaa lopetukseen). **Päätös:** limiteriä ei lukita pakolliseksi tässä muistiossa. Se on halpa lisävarmuus vikatilanteita vastaan (esim. tahaton antennien lähentyminen testissä), joten säilytetään harkinnanvaraisena RX-suojauksena — jos päädytään pitämään, varavaihtoehtona diskreetti PIN-limiteridiodi (esim. Skyworks SMP1330-085LF) ulkoisella sovituspiirillä, koska integroitu SKY16603-632LF-moduuli ei ole yksiselitteisesti saatavilla.

### SE5004L — rooli täsmennetty
Forsténin oma TX-ketju (VCO → MGA-25203-puskuri/korvaaja → PAT1220-ALC-vaimennin → mikserin LO-haara) on matalatehoinen LO-polku, ei tuota pohjantähden +30 dBm-tavoitetta sellaisenaan. SE5004L säilyy, mutta sen rooli täsmennetään: se on **erillinen TX-tehovahvistin haaroituksen jälkeisessä, antenniin menevässä polussa** — ei osa Forsténin diskreettiä LO-/dechirp-ketjua. Aktiivinen, EAR99, ei muutosta saatavuuteen.

### Zynq-luokan SoC — XC7Z020
AMD/Xilinx laajensi lokakuussa 2022 koko 7-sarjan (myös Zynq-7000) elinkaaren vähintään vuoteen 2035, kaikki nopeus-/lämpötilaluokat mukaan lukien — ei EOL-riskiä. Verrattiin XC7Z007S (23K logic cells, yksiytiminen), XC7Z010 (28K, kaksiytiminen, mutta 2026-07 hetkellä loppuunmyyty 52 vk toimitusajalla), XC7Z012S (55K, yksiytiminen mutta kalliimpi kuin Z7020 — dominoitu vaihtoehto) ja XC7Z020 (85K, kaksiytiminen, $131/kpl, 26 kpl varastossa). Verrattiin myös Zynq UltraScale+ CG-perhettä (esim. XCZU2CG, $307/kpl, hienojakoinen 0,5 mm BGA) — ylimitoitettu ja vaikeampi koota pienelle harrastajakortille, koska raskas kuvanmuodostus on joka tapauksessa siirretty ulkoiselle GPU:lle eikä UltraScale+:n R5-reaaliaikaydintarvetta ole.

**Valinta: XC7Z020**, sama piiri kuin Forsténin todistetussa `fmcw3`-korttissa. Perusteet: (1) suora referenssi pienentää bring-up-riskiä — pin-out ja ADC-rinnakkaisväylälogiikka on jo olemassa fmcw3:n fabric-lähteissä, (2) dual-core Cortex-A9 riittää housekeepingiin ja SPI-ohjaukseen ilman yksiytimistä pullonkaulaa, (3) 85K logic cells jättää marginaalia tulevalle fabric-esikäsittelylle, (4) CLG400-paketti (0,8 mm pitch) on kokoonpantavampi kuin UltraScale+:n hienojakoinen BGA, (5) saatavilla nyt (toisin kuin Z7010), (6) elinkaari taattu 2035:een, (7) ECCN 3A991.d (EAR, dual-use, ei ITAR/USML) — ei vientilupavaadetta Suomeen. Hintaero Z7007S:ään (~60 €) on pieni koko ~800 € järjestelmäbudjetissa, joten Z7020:n marginaali on perusteltu.

## Hylätyt vaihtoehdot

- **XC7Z010** — halvempi mutta 2026-07 hetkellä loppuunmyyty Digikeyllä (52 vk toimitusaika) — riski yksittäistilaukselle.
- **XC7Z012S** — kalliimpi kuin Z7020 mutta yksiytiminen ja pienempi fabric — dominoitu, ei perustetta valita.
- **Zynq UltraScale+ CG-perhe (esim. XCZU2CG)** — teknisesti kelpaava mutta ylimitoitettu tähän kevyeen käyttötapaukseen, 2,3–4× kalliimpi, vaikeammin koottava BGA.
- **Lattice ECP5 + erillinen MCU/SoM** — löytyi referenssi (FUSBee5, ECP5+FT600), halpa ja avoimen työkaluketjun tukema, mutta vaatii erillisen ARM-piirin housekeepingiin → lisää osamäärää ja rajapintoja pienellä dronekortilla verrattuna yhteen Zynq-piiriin. Ei suositella, ellei Zynq-saatavuus muutu myöhemmin ongelmaksi.

## Avoimet kohdat

1. **MGA-25203-korvaaja** — ei vahvistettua pin-yhteensopivaa osaa löytynyt. Ratkaistava oma jatkoselvitys (kandidaattiperheet: Mini-Circuits, MACOM tai Qorvo 5–6 GHz GaAs gain-block -sarjat) ennen skeemaa.
2. **SKY65404-korvaaja** — discontinued, jälleenmyyjävarastoja jäljellä mutta ei uutta valmistusta. Ratkaistava oma jatkoselvitys ennen tilausta.
3. **SKY16603-632LF:n lopullinen tarve/saatavuus** — rooli ei ole Forsténin arkkitehtuurissa pakollinen; jos päädytään pitämään RX-suojaus, vahvistettava suoraan Skyworksilta onko integroitu moduuli yhä tilattavissa vai tarvitaanko diskreetti PIN-limiteridiodivaihtoehto (esim. SMP1330-085LF).
4. **LTC229x-perheen tarkka ECCN-vahvistus** — ei löytynyt punaisia lippuja, mutta suositellaan varmistamaan ADI:n export-classification-työkalulla ennen lopullista tilausta.
5. Kaikki tässä "Active"-statuksella olevat osat kannattaa tarkistaa uudelleen tilaushetkellä — jakelijoiden varastotilanne ja lifecycle-statukset muuttuvat kuukausien kuluessa.

## Muutosloki

- **2026-07-15** — Ensimmäinen versio. Tarkistettu jokainen Forsténin `fmcw3`-BOM:in osa (RF-arkkitehtuuripäätöksen kohta 3a) sekä aiemmin AD9361-oletuksella valitut osat (SE5004L, SKY16603-632LF) 2026-saatavuuden, korvaajien ja export-controlin osalta. Kaksi osaa (MGA-25203, SKY65404) todettu EOL/discontinued ilman vahvistettua korvaajaa — jätetty avoimeksi, ei täytetty arvauksella. Zynq-luokan SoC lukittu (XC7Z020, sama piiri kuin Forsténin fmcw3:ssa).
