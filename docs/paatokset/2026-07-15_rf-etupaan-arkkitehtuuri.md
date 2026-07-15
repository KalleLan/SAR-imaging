# Päätös: RF-etupään komponenttiarkkitehtuuri (chirp-PLL, PA, RX-suojaus, polarisaatio)

> **Scope laajennettu 2026-07-15:** kirjoitushetkellä tämä oli "RF-etupää-lisäkortti" SDR-devboardin päälle. `2026-07-15_dedikoitu-tutkakortti.md` kumosi SDR-kortin käytön — tässä tehdyt komponenttihavainnot (chirp-PLL, PA, RX-suojaus, polarisaatio) ovat silti edelleen voimassa lähtökohtana koko tutkakortille, ei enää vain lisäkortille.

| | |
|---|---|
| **Tyyppi** | Päätösmuistio |
| **Päätetty** | 2026-07-15 |
| **Liittyy** | `2026-07-15_dedikoitu-tutkakortti.md` (oma tutkakortti), `2026-07-15_sdr-kortti-ad9361.md` (kumottu), `10_START_sdr_rail-SAR.md` (Vaihe 1 — Rautaminimi) |

---

## Päätös

1. **Chirp-PLL/VCO: ADF4159 (Analog Devices) + HMC431LP4E (Analog Devices/Hittite VCO)** suositellaan ensisijaisena chirp-lähteenä TX-polulle ja AD9361:n ulkoiselle LO-tulolle. **LMX2491 (Texas Instruments) + HMC431LP4E** on teknisesti yhtä pätevä varavaihtoehto, jolla on julkaistu SAR-precedentti.
2. **PA: Skyworks SE5004L** (5,15–5,85 GHz WLAN-tehovahvistin) suositellaan TX-polun lisävahvistukseksi. Se kattaa vaaditun ~24 dB budjetin mutta jää n. 4 dB tavoitetehon (+30 dBm) alle — hyväksytään alkuvaiheen kompromissiksi, ei lukita lopulliseksi.
3. **RX-suojaus: Skyworks SKY16603-632LF** (kaksois-PIN-diodi-limiter) sijoitetaan RX-SMA-tulon ja AD9361:n väliin. Erillistä sirkulaattoria/TR-kytkintä ei tarvita, koska arkkitehtuuri käyttää jo erillisiä TX- ja RX-antenneja.
4. **TX/RX-antennieristys** rakennetaan Forsténin oman ratkaisun mukaisesti kaksitasoisena: fyysinen erotus/eristysseinä + polarisaatiodiversiteetti antennitasolla, varmistettuna elektronisella marginaalilla (limiteri + mahdollinen säädettävä vaimennin PA:n edessä). Tarkka geometria jää mitattavaksi, ei ratkaista pelkällä komponenttivalinnalla.
5. **Polarisaatioarkkitegia: "2 chirpiä, simultaani dual-RX"** — ei RF-kytkimiä, ei täysin simultaania 1-chirp-ratkaisua. Chirp 1 TX1A:lta (H) → RX1A+RX2A digitoivat samanaikaisesti (HH+HV); chirp 2 TX2A:lta (V) → RX1A+RX2A digitoivat samanaikaisesti (VH+VV). Kaikki neljä HH/HV/VH/VV-kombinaatiota saadaan kahdesta chirpistä yhden sijaan, ilman RF-kytkimiä.
6. **Kaikki neljä suositeltua osaa (ADF4159, HMC431LP4E, SE5004L, SKY16603-632LF) ovat tavanomaisia kaupallisia telekom-/WLAN-komponentteja**, jotka löytyvät avoimesti Digikey/Mouser-jakelijasivuilta ilman ITAR/EAR-lippuja — matala export-riski verrattuna GaN-radar-PA-luokkaan.

## Taajuuskonfliktin ratkaisu

**Lähtökohta** (`../tehtavat/2026-07-15_rf-etupaan-taajuuskonflikti.md`): AD9361 Reference Manual (UG-570), "External LO" -osio, vahvistaa että EXT_LO-signaalin dokumentoitu tukialue on **140 MHz–8 GHz, kattaen RF-tune-taajuuden 70 MHz–4 GHz** — ei koko sisäisen synteesin 70 MHz–6 GHz -aluetta. Pohjantähden ~5,77 GHz -tavoite (EXT_LO ~11,3–11,9 GHz) on tämän dokumentoidun rajan ulkopuolella. Selvitettiin neljä kohtaa ennen skeema-/tilaustyötä.

**1) Empiirinen näyttö EXT_LO:sta yli 4 GHz RF (yli 8 GHz LO) — ei löytynyt.**
- Haut EngineerZonesta, AD9361-datasheet-lähteistä ja GitHub-koodihauista (`analogdevicesinc/linux`, `analogdevicesinc/libad9361-iio`) toistavat vain saman 70 MHz–4 GHz / 8 GHz-LO-rajan. Ei yhtään foorumiraporttia, GitHub-issueta tai julkaisua, jossa EXT_LO:ta olisi ajettu yli 8 GHz:n.
- ADI:n oma virallinen ext-LO-referenssidesign löytyi: `analogdevicesinc/linux` → `arch/arm64/boot/dts/xilinx/zynqmp-zcu102-rev10-ad9361-fmcomms5-ext-lo-adf5355.dts` (FMCOMMS5, ADF5355 ulkoisena LO:na, `adi,power-up-frequency = 4800000000` → 4,8 GHz LO → 2,4 GHz RF). ADI:n oma esimerkki pysyy siis itsekin reilusti dokumentoidun rajan **sisällä** — ei vasta- eikä puoltoevidenssiä yli 4 GHz:n käytölle.
- Yksi harhaanjohtava osuma tarkistettu ja hylätty: EngineerZone-ketju "Can't set AD9361 LO Freq above 4.29Ghz" (`ez.analog.com/linux-software-drivers/f/q-a/111617`) ei liity RF-karakterisointiin — kyse on PowerPC/big-endian-alustan ohjelmistobugista (`round_rate`-kutsu clk-ajurissa), ei taajuusrajasta.
- Kaksi ketjua jäi sisällöltään vahvistamatta teknisen esteen takia (WebFetch-aikakatkaisu): `ez.analog.com/rf/wide-band-rf-transceivers/design-support/f/q-a/533783/ad9361-external-lo-configuration` ja `.../f/q-a/113021/internal-lo-of-ad9361`. **Avoin kohta, ei täytetty arvauksella.**
- **Johtopäätös:** rajan ylitys on karakterisoimaton riski — ei todistettu toimivaksi eikä todistettu rikkoutuvaksi. Ei riittävä peruste tilata komponentteja tälle oletukselle.

**2) SFCW-vaihtoehto — toimisi Vaihe 1:ssä (kisko), epäonnistuisi drone-vaiheessa.**
- `10_START_sdr_rail-SAR.md` Vaihe 2 ("Kiskomekaniikka"): kiskovaihe on **step-stop-measure** — tutka pysähtyy joka mittauspisteessä. Tässä vaiheessa ei ole reaaliaikaista PRF/nopeus-sidontaa, joten SFCW:n askelmäärä × lukitusaika ei riko mitään ajallista rajoitetta kiskolla, vaikka täysi pyyhkäisy kestäisi kymmeniä millisekunteja.
- `00_POHJANTAHTI...` antaa drone-vaiheen luvut ("PRF ↔ lentonopeus", "Look-angle/varjot"): ~2 km kantama-esimerkki, 10 m/s → λ/4-näyteväli vaatii PRF ≥ 800 Hz/pol, ×4 pol → 3,2 kHz → per-chirp-budjetti ~280–312 µs.
- Oma laskelma (ei ulkoinen lähde): yksiselitteinen kantama Ru = c/(2Δf) ≥ 2 km → Δf ≤ 75 kHz. Askelmäärä N = B/Δf = 300 MHz / 75 kHz ≈ 4000 (500 MHz kaistalla ~6700). AD9361:n lukitusaika (hakutuloksista koottu, ei suoraan datasheet-PDF:stä varmistettu — keskisuuri luotettavuus): parhaimmillaan ~20 µs, tyypillisesti ~250 µs, VCO-kalibrointi mukana ~500 µs, fast-lock-taulukoilla jopa 1000 hyppyä/s (~1 ms/hyppy). Täysi N-askeleen pyyhkäisy: 4000×20 µs = 80 ms parhaassakin tapauksessa, tyypillisesti ~1 s — vs. ~280–312 µs budjetti.
- **SFCW on n. 250–3500× liian hidas** kattamaan tarvittavan yksiselitteisen kantaman + kaistan drone-vaiheen näyteväli-budjetissa, myös optimistisimmalla lukitusaika-arviolla. Koska sama RF-kortti on tarkoitus siirtyä kiskolta droneen muuttumattomana (pohjantähti, "Mikä tästä siirtyy ilmaan"), arkkitehtuurin pitää toimia molemmissa vaiheissa — SFCW läpäisisi Vaihe 1:n mutta olisi arkkitehtuurivelkaa joka räjähtäisi käsiin drone-siirrossa.

**3) Forstén — tärkein löydös: hän ei käytä AD9361:tä (tai vastaavaa integroitua transceiveria) chirp-/LO-polulla lainkaan.**
- Luettu uudelleen hforsten.com/homemade-polarimetric-synthetic-aperture-radar-drone.html juuri tästä kulmasta. Hänen arkkitehtuurinsa on täysin diskreetti: PLL generoi pyyhkäisyn → vaihdeltava vaimennin → PA → antenni. RX-puolella lainaus: *"Part of the transmitted signal is coupled to the receiver mixer, where it's mixed together with the received reflected signal"* — osa TX-signaalista kytketään suoraan erilliseen, diskreettiin RX-mikseriin LO:ksi (self-mixing dechirp-on-receive), mikseri ilman image rejectionia, tuottaen matalataajuisen beat-signaalin joka vahvistetaan ja digitoidaan ADC:llä (50 MHz näytteistys). Zynq 7020 toimii hänellä puhtaasti digitaalisena prosessointipiirinä (FPGA+ARM, USB3-silta FT600:lla PC-yhteyteen) — **ei RF-transceiverina**. Ei mainintaa AD9361:stä, PlutoSDR:stä eikä muusta integroidusta RF-transceiveristä missään kohtaa TX/RX-RF-ketjua.
- **Tämä väistää koko EXT_LO-rajakysymyksen kokonaan** — mikään komponentti hänen ketjussaan ei koskaan tarvitse minkään integroidun transceiverin dokumentoitua LO-tukea. Chirp-PLL:n LO menee suoraan diskreettiin mikseriin, ei transceiverin RF-tuloon.

**3a) Jatkoselvitys 2026-07-15 — Forsténin todellinen kytkentä (fmcw3-repo), konkreettiset osanumerot.**
Forsténilla on julkinen GitHub-käyttäjä `Ttl` (sama kuin `torchbp`), ja sieltä löytyy kolme sukupolvea täysiä KiCad-skeemoja:
- `github.com/Ttl/fmcw` — ensimmäinen versio (Kinetis KL26Z).
- `github.com/Ttl/fmcw2` — toinen versio (LPC4320, firmware pohjautuu HackRF:ään, kuvanmuodostus RITSAR- ja Charvat-pohjainen).
- `github.com/Ttl/fmcw3` — **"Two RX-channel 6 GHz FMCW radar design files"** (309 tähteä). Blogipostaus: hforsten.com/third-version-of-homemade-6-ghz-fmcw-radar.html. README:ssä on suoraan SAR-kuvanmuodostusputki (`backprojection_tf.py`, `omegak_tf.py`) ja esimerkkidataa (`parking_lot_sar.log`) — **tämä on se laitteisto jolla hän todisti SAR-kuvanmuodostuksen ennen drone-versiota**, ja se on 6 GHz kaksikanavainen, samaa taajuusaluetta kuin oma projektimme.

`fmcw3`-repon `hardware/`-kansiosta löytyy erilliset KiCad-skeemat (`tx.sch`, `rx.sch`, `mixer.sch`, `if.sch`, `adc.sch`, `fpga.sch`). Ladattiin ja luettiin suoraan tekstinä (KiCad legacy-formaatti on tekstipohjainen), joten seuraavat osanumerot ovat verrattavissa alkuperäiseen lähdekoodiin, ei blogitekstin parafraasia:

| Lohko | Osa | Rooli (verkkonimien/topologian perusteella) |
|---|---|---|
| TX (`tx.sch`) | **ADF4158** | Chirp-PLL + ramp-generaattori — ADF4159:n suora edeltäjä, sama tuoteperhe jonka valitsimme jo omaan arkkitehtuuriimme |
| TX | **HMC431LP4** | VCO — **täsmälleen sama piiri kuin oma valintamme** (HMC431LP4E) |
| TX | MGA-25203 | Yleiskäyttöinen vahvistin/puskuri VCO:n jälkeen |
| TX | PAT1220 (×2) | Vaimennin/ALC-piiri (TLV172DCK-op-ampin viereisyys viittaa tehon takaisinkytkentäsilmukkaan) — rooli päätelty topologiasta, ei erikseen datasheet-tasolla varmistettu |
| TX | BRANCHLINE-kytkin (Z1) | Haaroittaa osan TX-signaalista ennen antennia. Verkkonimi `TX_COUPLED` on skeeman ainoa TX-lohkon ulostulo mixer-lohkoon — **tämä on kirjaimellisesti "coupled TX signal as LO" -kytkentä**, sama jota blogiteksti kuvasi sanallisesti |
| RX (`rx.sch`) | SKY65404 | LNA |
| RX | TRF37A75 | RX-vahvistinlohko |
| Mixer (`mixer.sch`) | **ADL5802** | Diskreetti aktiivimikseri (ADI, 5,4–6,4 GHz) — tulot `LO_IN` (= `TX_COUPLED`) ja `RF1`/`RF2` (RX-ketjuista), ulostulot `IF1±`/`IF2±`. Koko skeemalohko instantioitu **kahdesti** hierarkiassa — yksi ADL5802 per RX-kanava |
| Mixer | 5400BL15B050E (×2/kanava) | Suunnattu kytkin/jakaja LO- ja RF-signaalien yhdistämiseen mikserin tuloon |
| IF (`if.sch`) | ADA4940-2 (×2) | Differentiaalinen IF-vahvistin/ADC-ajuri, kaksikanavainen |
| ADC (`adc.sch`) | LTC229x-perhe (blogissa nimetty LTC2292, 40 MHz näytteistys, SNR 71,3 dB) | Digitoi IF-signaalin — **ei AD9361:n eikä minkään integroidun transceiverin kautta** |

Tämä vahvistaa suoraan lähdekoodista (ei vain blogitekstistä) sen minkä blogi kuvasi sanallisesti: ADF4158+HMC431 (sama VCO kuin oma valintamme) generoi pyyhkäisyn, pieni osa siitä haarotetaan suunnatulla kytkimellä `TX_COUPLED`-signaaliksi, joka syötetään suoraan ADL5802-mikserin LO-tuloon yhdessä RX-LNA-ketjun kanssa — koko dechirp tapahtuu tässä diskreetissä mikserissä, ja tulos digitoidaan yleiskäyttöisellä ADC:llä. AD9361-tyyppistä siruakaan ei ole missään näissä kolmessa sukupolvessa (fmcw/fmcw2/fmcw3).

**3b) Muut vastaavat SAR-/tutkaprojektit, joissa sama arkkitehtuuri on dokumentoitu:**

1. **Gregory Charvat, MIT "Build a Small Radar System" (OpenCourseWare) / "Coffee Can Radar" / kirja *Small and Short-Range Radar Systems*.** Akateeminen, avoin, hyvin dokumentoitu 2,4 GHz FMCW-tutka jolla tehdään mm. turntable-SAR-kuvantaminen kurssilla. Arkkitehtuuri: diskreetti PLL/VCO + Mini-Circuits-konnektorisoidut RF-lohkot, mikseri yhdistää TX-referenssin ja RX-kaiun suoraan (direct conversion), ei mitään integroitua RF-transceiveria. Tämä on ala- taajuudeltaan matalampi (2,4 GHz vs. 5,77 GHz) mutta arkkitehtuuriltaan sama perhe, ja on todennäköisesti alan tunnetuin avoin SAR-opetusreferenssi tälle topologialle. Lähde: sites.google.com/view/glcharvat/radar, glcharvat.com/tincan.
2. **Merlo & Nanzer, "A C-Band Fully Polarimetric Automotive Synthetic Aperture Radar" (arXiv:2110.14114)** — jo ennestään viitattu tässä muistiossa PLL-valinnan precedenttinä (LMX2491+HMC431-pari). Uusi löydös: paperin oma teksti kuvaa arkkitehtuurin nimenomaan **"direct-downconversion"**-tyyppiseksi, yksi lähetin + neljä vastaanotinta, IF-signaalit digitoitu **erillisellä yleiskäyttöisellä DAQ:lla** (Measurement Computing USB-1608-FS-Plus, 100 kSps/kanava) — ei minkään integroidun transceiverin kautta. Toimii samalla taajuusalueella kuin oma projektimme (5,725–6,0 GHz). Lähde: arxiv.org/abs/2110.14114.
3. **ckflight/FMCW_RADAR (GitHub)** — riippumaton (ei Forsténin) avoin FMCW-tutkaprojekti, 5,5–6,1 GHz, ADF4158-PLL, suunnattu kytkin haarottaa TX-chirpin näytteen diskreettiin mikseriin (LNA+gain block+mixer-ketju), STM32F4 digitoi IF:n. **Ei ole SAR-projekti** (pelkkä etäisyysmittaus, ~250 m kantama) — mainitaan koska se vahvistaa saman arkkitehtuurikuvion (PLL+coupler+diskreetti mikseri, ei transceiveria) esiintyvän myös täysin Forsténista riippumattomissa projekteissa samalla taajuusalueella.

**Johtopäätös (3a+3b):** kolme riippumatonta lähdettä (Forstén/hforsten×3 sukupolvea, MIT/Charvat-akateeminen kurssireferenssi, Merlo & Nanzer -vertaisarvioitu julkaisu) — kaikki 5–6 GHz-luokan FMCW/SAR-projekteja — käyttävät samaa perusarkkitehtuuria: diskreetti PLL+VCO-chirp, suunnatulla kytkimellä haarotettu TX-näyte diskreetin mikserin LO:ksi, yleiskäyttöinen ADC/DAQ digitointiin. **Ei yhtään löydettyä esimerkkiä**, jossa tämän taajuusalueen FMCW-SAR käyttäisi AD9361- tai PlutoSDR-tyyppistä integroitua transceiveria EXT_LO-tulon kautta. Tämä ei ole pelkkä yksittäisen harrastajan oikotie, vaan toistuva, riippumattomasti valittu insinöörikäytäntö juuri tälle taajuusalueelle ja sovellukselle — vahvistaa merkittävästi kohdan "Suositus" kohtaa 3.

**4) Taajuuden laskeminen ≤4 GHz — kirjattu vaihtoehtona, ei ratkaistu tässä.**
Jos kohdan 3 mukainen arkkitehtuurimuutos osoittautuu epäkäytännölliseksi, taajuuden laskeminen ≤4 GHz pitäisi nykyisen EXT_LO-arkkitehtuurin dokumentoidun tuen sisällä sellaisenaan. Isompi päätös (muuttaa pohjantähden ~6 GHz -valinnan perustetta: kuluttajakomponenttien saatavuus) — rajattu tämän tehtävän ulkopuolelle, kirjattu vain vaihtoehtona kuten tehtävänanto edellytti.

### Suositus

1. **Hylätään** "jatka ulkoisella LO:lla dokumentoidun rajan yli" ilman lisätodisteita — ei empiiristä näyttöä, karakterisoimaton riski juuri ennen tilaustyötä.
2. **Hylätään** SFCW suorana korvaajana nykyiselle EXT_LO-arkkitehtuurille — toimisi kiskolla, epäonnistuisi räikeästi drone-vaiheessa, eikä sama kortti silloin siirtyisi muuttumattomana kuten pohjantähti edellyttää.
3. **Suositellaan Forstén-tyylistä diskreettiä dechirp-mikseriä ensisijaiseksi jatkopoluksi** (komponenttivalinta/skeema on silti oma, erillinen päätöksensä — ei lyödä lukkoon tässä): AD9361 jätetään pois chirp-/dechirp-polulta — ADF4159+HMC431-chirp haarotetaan suunnatulla kytkimellä suoraan diskreetin RX-mikserin (Forsténin tapauksessa ADL5802) LO:na, ja tuloksena syntyvä matala beat-signaali joko (a) digitoidaan erillisellä ADC:llä suoraan Zynqin fabricille, tai (b) syötetään AD9361:n RX-porttiin käyttäen AD9361:n **omaa kiinteää sisäistä LO:ta** (ei pyyhkäisyä, ei EXT_LO:ta — pysyy reilusti dokumentoidun 70 MHz–6 GHz alueen sisällä) toisena, matalataajuisena digitointivaiheena. Kumpikin reitti poistaisi taajuuskahdentimen tarpeen ja koko EXT_LO->4 GHz -riskin kokonaan. **Uutta 2026-07-15:** tämä ei ole enää pelkkä konsepti — kolme riippumatonta 5–6 GHz-luokan FMCW/SAR-lähdettä (Forsténin kolme sukupolvea GitHub-skeemoineen, MIT/Charvat-akateeminen referenssi, Merlo & Nanzer -vertaisarvioitu julkaisu) käyttävät kaikki tätä samaa arkkitehtuuria, ja Forsténin `fmcw3`-repo antaa konkreettisen, jo toimivaksi todistetun osalistan (ks. kohta 3a) jolla aloittaa jatkoselvitys/BOM.
4. **Taajuuden laskeminen ≤4 GHz** säilyy varavaihtoehtona, ei päätetä nyt.

## Perustelut

### 1) Chirp-PLL/VCO

| Osa | Tyyppi | Kaista / teho | Ramp/chirp-tuki | Hinta-arvio (1 kpl) | Saatavuus |
|---|---|---|---|---|---|
| ADF4159 + HMC431LP4E | PLL (max 13 GHz syöttö) + erillinen VCO | HMC431: 5,5–6,1 GHz, +2 dBm ulos | Omistettu "fast/slow ramp" -moottori, 25-bit modulus, ADIsimPLL-tuki | ADF4159 ~15–20 €, HMC431 ~10–15 € | Digikey/Mouser-kanavatuote |
| LMX2491 + HMC431LP4E | PLL (max 6,4 GHz syöttö) + sama VCO | sama HMC431 | 8-segmenttinen piecewise-lineaarinen FM, FSK/PSK-tuki | LMX2491 ~15–20 € | Digikey/Mouser. **Precedentti:** "A C-Band Fully Polarimetric Automotive Synthetic Aperture Radar" (arXiv:2110.14114) käyttää täsmälleen tätä paria |
| ADF5355 | Integroitu PLL+VCO | 54 MHz–13,6 GHz; RFOutA ~3,4–6,8 GHz perustaajuus, RFOutB kahdennettu (esim. −16 dBm @ 8,57 GHz) | Ei varmistettua radar-spesifistä ramp-moottoria — yleiskäyttöinen wideband-syntetisaattori | ~25–30 € | Digikey/Mouser |

ADF4159 valitaan ensisijaiseksi, koska se on tarkoitushaettu FMCW-chirp-piiri: fast-ramp-moottori minimoi retrace-ajan, mikä maksimoi käytettävissä olevan kaistan per pyyhkäisy — suoraan relevanttia etäisyysresoluutiolle (pohjantähti: 300–500 MHz kaista → 0,3–0,5 m resoluutio, riippuu pyyhkäisyn lineaarisuudesta). Sillä on myös laaja ADI-referenssidokumentaatio ja ADIsimPLL-simulointituki. LMX2491+HMC431 säilytetään varavaihtoehtona, koska sillä on julkaistu, täsmälleen samalla taajuusalueella toimiva SAR-precedentti.

HMC431LP4E:n taajuusalue (5,5–6,1 GHz) on suoraan RF-kaistalla, ei kahdennettuna — se ratkaisee TX-syötön suoraan, mutta **AD9361:n ulkoinen LO-tulo vaatii 2× RF-taajuuden**, joten jakoverkkoon tarvitaan taajuuskahdennin (ks. Avoimet kohdat).

**Uusi löydös, korjaa SDR-korttipäätöksen implisiittisen oletuksen:** AD9361:n `RX_EXT_LO_IN`/`TX_EXT_LO_IN`-pinneihin syötettävän ulkoisen LO:n on oltava taajuudeltaan **2× haluttu RF-taajuus**, tehotasolla −3…+3 dBm (50 Ω). Lähde: AD9361-datasheet ja EngineerZone-foorumikeskustelut ("AD9361 and External LO Input Reference", "FMCOMMS5 External LO Input Level"), tuettuna arkkitehtuurin sisäisellä logiikalla — AD9361:n sisäinen synteesi-VCO toimii aina 6–12 GHz riippumatta viritystaajuudesta ja jakautuu ÷2:lla RF-taajuudelle; ulkoinen LO syötetään samaan pisteeseen ennen jakajaa. Tätä ei saatu vahvistettua suoraan datasheet-PDF:n tekstinä toistuvien fetch-timeoutien takia analog.com:iin — **merkitty avoimeksi kohdaksi, varmistettava AD9361 Reference Manual (UG-570) -lähteestä ennen skeemaa**, koska se määrää koko taajuussuunnitelman: 5,77 GHz ± 250 MHz keskitaajuudella ulkoisen LO:n pitää pyyhkäistä ~11,04–11,54 GHz (500 MHz kaista) tai ~11,3–11,9 GHz (300 MHz).

### 2) PA

**Kandidaatti:** Skyworks SE5004L — 5,15–5,85 GHz WLAN-tehovahvistin, Psat 26 dBm, P1dB 30 dBm min / 34 dBm tyyp. (moduloimattomana), gain 30 dB min / 32 dB tyyp., sisäänrakennettu tehodetektori. Hinta-arvio ~20–30 €/kpl pienissä erissä. Täysin kaupallinen WLAN-router-komponentti.

- **Vahvistuskuilu tavoitteeseen:** +30 dBm-tavoitteeseen on n. 4 dB vajetta SE5004L:n 26 dBm Psat-pisteestä. AD9361:n natiivi 6,5 dBm + SE5004L:n 32 dB gain riittää selvästi vaadittuun ~24 dB budjettiin (jopa ylimäärin) — PA:ta ei tarvitse ajaa täydessä kompressiossa, mikä auttaa lineaarisuutta.
- **Lineaarisuus:** P1dB 30 dBm jää selvästi Psat-pisteen (26 dBm) yläpuolelle → hyvä marginaali, kompressio ei rajoita pyyhkäisyn lineaarisuutta merkittävästi normaalikäytössä. Tämä on FMCW:lle oleellisempaa kuin pelkkä huipputeho, koska epälineaarisuus turmelee pyyhkäisyn.
- **Lämmönhallinta — avoin kohta:** SE5004L on karakterisoitu WLAN-pakettiliikenteelle (purskeinen duty cycle), ei jatkuvalle chirp-pyyhkäisylle. Pohjantähden oma PRF↔lentonopeus-laskelma (PRF 800 Hz–3,2 kHz, pyyhkäisy max ~280 µs) antaa duty cyclen joka voi lähestyä ~100 % lennon aikana — jatkuvan käytön tehonhäviö pitää tarkistaa datasheetin thermal derating -käyristä ennen tilausta.

**Hylätty riskin takia:** GaN-luokan radartehovahvistimet (Qorvo TGA-sarja, Wolfspeed CMPA-sarja, RFHIC:n GaN-moduulit) — teknisesti parempi teho/lineaarisuus, mutta markkinoitu eksplisiittisesti tutka-/puolustussovelluksiin. Sama end-use-riskikategoria josta Forsténin RF-kytkintilaus peruttiin jälkikäteen (pohjantähti, "Komponenttien end-use-rajoitukset").

### 3) RX-suojaus

**Kandidaatti:** Skyworks SKY16603-632LF — integroitu kaksois-PIN-diodi-limiter, 0,6–6,0 GHz, matala rajoituskynnys, matala lisävaimennus, DFN-kotelo, täysin passiivinen (ei ohjauslogiikkaa). Hinta-arvio ~20–25 €/kpl. Sijoitetaan RX-SMA-tulon ja AD9361:n RF-tulon väliin, mitoitettuna niin että kynnysteho jää selvästi alle AD9361:n absoluuttisen maksimin 2,5 dBm (peak, SDR-korttipäätöksestä). Tarvittaessa lisätään kiinteä vaimennuspatja lisämarginaaliksi.

Sirkulaattoria tai TR-kytkintä ei tarvita: arkkitehtuuri käyttää jo erillisiä TX- ja RX-antenneja (kortin 4 SMA-porttia + pohjantähden vaatimus "erilliset TX/RX-antennit"), joten yhteistä antenniporttia jakavaa komponenttia ei ole. Limiteri riittää sekä TX-vuodon että vikatilanteiden (esim. irronnut antenni → heijastus) varalle.

### 4) TX/RX-eristys antennitasolla

Pohjantähti vaatii >50 dB eristyksen. Tämä on ensisijaisesti mekaaninen/antennisuunnitteluongelma, ei komponenttihankintaongelma — ei ratkaistavissa pelkällä datasheet-tutkimuksella, vaan vaatii EM-simulaation tai VNA-mittauksen kun antennit on rakennettu.

Forsténin oma polarimetrinen drone-SAR (sama >50 dB vaatimus, hforsten.com) käyttää kaksitasoista strategiaa: (a) fyysinen erotusseinä TX/RX-antennien välillä (~0,25×0,5 aallonpituutta), (b) säädettävä vaimennin PA:n edessä joka pudottaa TX-tehoa lähellä vastaanotinta. Suositellaan saman strategian replikointia, täydennettynä polarisaatiodiversiteetillä: TX-H/RX-H ja TX-V/RX-V erillisillä apertuureilla ristipolarisaatio vähentää ristikytkentää edelleen. Tarkka geometria/etäisyys jää avoimeksi kohdaksi, ratkaistavaksi RF-mock-upilla ennen mekaniikan lyömistä lukkoon.

### 5) Polarisaatioarkkitehtuuri

Kortin 2×2 MIMO (TX1A/TX2A, RX1A/RX2A) mahdollistaa osittain simultaanisen H/V-ajon, mutta ei täysin ilmaiseksi yhdellä pyyhkäisyllä: koska ulkoinen chirp-PLL syöttää sekä TX1A:ta että TX2A:ta saman `TX_EXT_LO_IN`-pinnin kautta, molemmat lähettäisivät identtisen chirp-signaalin. Jos molemmat lähettäisivät samanaikaisesti, RX-puolella ei voisi erottaa H- ja V-illuminaation vaikutusta samasta chirp-ikkunasta (klassinen simultaani-polarimetrian ongelma) — erottelu vaatisi ortogonaaliset aaltomuodot TX1/TX2:lle (esim. kaksi riippumatonta chirp-lähdettä tai ylös/alaspäin-chirp-temppu).

**Suositeltu arkkitehtuuri — "2 chirpiä, simultaani dual-RX":**
1. Chirp 1: vain TX1A (H) lähettää → RX1A ja RX2A digitoivat samanaikaisesti → HH ja HV saadaan yhdestä chirpistä.
2. Chirp 2: vain TX2A (V) lähettää → RX1A ja RX2A digitoivat samanaikaisesti → VH ja VV saadaan toisesta chirpistä.

Tulos: 2 chirpiä per mittauspaikka, ei 4 — molemmat RX-kanavat ovat aidosti rinnakkaisia (kortin natiivi 2×2 MIMO), joten puolet kombinaatioista saadaan ilmaiseksi jokaisesta chirpistä ilman RF-kytkimiä ja ilman ortogonaalisten aaltomuotojen monimutkaisuutta.

**Vertailu:**
- *Perinteinen kytkinpohjainen* (1 TX-antenni, RF-kytkin H/V:n välillä, 1 RX-antenni): 4 chirpiä/paikka, yksinkertaisin RF mutta täysi 4× PRF-sakko — täsmälleen se skenaario jota pohjantähden oma PRF-laskelma ("×4 polarisaatiota → 3,2 kHz → sweep max ~280 µs") käsitteli pahimpana tapauksena.
- *Suositeltu (2 chirpiä, dual-RX):* 2× PRF-sakko 4×:n sijaan, ei RF-kytkimiä, käyttää korttia sellaisenaan.
- *Täysin simultaani* (1 chirpi, ortogonaaliset TX1/TX2-aaltomuodot): paras teoreettinen PRF (1× sakko), mutta vaatisi kaksi riippumatonta chirp-lähdettä tai ylös/alaspäin-chirp-kikan — merkittävästi monimutkaisempi RF-ketju.

2-chirp-dual-RX-skeema valitaan, koska se antaa merkittävän (2×) PRF-hyödyn ilman RF-kytkimiä ja ilman chirp-ketjun kahdentamista, käyttäen korttia sellaisenaan.

### 6) Export-control-tarkistus

Kaikki suositellut osat (ADF4159, HMC431LP4E, SE5004L, SKY16603-632LF) löytyvät avoimesti Digikey/Mouser-jakelijasivuilta ilman lupavelvollisuus- tai ITAR-merkintöjä — tavanomaisia telekom-/WLAN-infrastruktuurikomponentteja, ei tutka-/puolustusmarkkinoinnilla myytyjä osia. Tämä on jakelijasivutason seulonta, ei juridinen export-control-päätös — tilaushetkellä kannattaa tarkistaa jakelijan compliance-liput uudelleen. GaN-luokan radar-PA:t hylättiin erikseen tämän riskin takia (ks. kohta 2).

## Avoimet kohdat

1. ~~AD9361:n ulkoisen LO:n 2× RF -vaatimus: vahvistettava ensisijaislähteestä (AD9361 Reference Manual, UG-570) ennen skeemaa.~~ — **Ratkaistu ja ylitetty 2026-07-15** (ks. "Taajuuskonfliktin ratkaisu"): 2× vahvistui, mutta löytyi vakavampi ongelma — EXT_LO on dokumentoitu vain 70 MHz–4 GHz RF:lle, pohjantähden 5,77 GHz on rajan ulkopuolella. Ei ratkaistu lopullisesti, ks. avoin kohta 7.
2. Taajuuskahdentimen (HMC431:n RF-kaistalta AD9361:n LO-kaistalle) tarkka IC-valinta ja tehobudjetti — ADIsimRF-tason budjettilaskenta puuttuu. **Huom:** tarpeeton, jos kohdan 7 Forstén-tyylinen diskreetti dechirp-mikseri osoittautuu toteutuskelpoiseksi (ei silloin tarvita EXT_LO:ta eikä taajuuskahdenninta lainkaan).
3. PA:n jatkuvan käytön (~100 % duty cycle) lämpöbudjetti — SE5004L on karakterisoitu purskekäytölle, ei jatkuvalle chirpille.
4. TX/RX-antennieristyksen tarkka geometria/etäisyys — vaatii EM-simulaation tai VNA-mittauksen, ei ratkaistavissa pelkällä komponenttivalinnalla.
5. SDR-korttipäätöksen (`2026-07-15_sdr-kortti-ad9361.md`) kirjaus ulkoisesta LO-injektiosta ei erittele 2× RF -vaatimusta — harkittava lyhyttä täsmennysviittausta sinne kun kohta 1 on vahvistettu ensisijaislähteestä, CLAUDE.md:n periaatteen mukaisesti ("arkkitehtuurimuutokset kirjataan vain pohjantähteen, ei hajalleen" — tämä on tarkennus komponenttivalintaan, ei arkkitehtuurimuutos, joten pysyy tässä muistiossa, mutta ristiviittaus kannattaa lisätä).
6. Jakoverkon (splitter/coupler + puskurivahvistin) tarkka mitoitus HMC431:n +2 dBm ulostulosta sekä TX-polulle että kahdennetulle LO-polulle. **Huom:** tarpeeton samalla ehdolla kuin kohta 2.
7. Forstén-tyylisen diskreetin dechirp-mikserin toteutettavuus tälle kortille (Z7020+AD9361) — chirp-PLL suoraan diskreetin RX-mikserin LO:na AD9361:n EXT_LO:n sijaan, beat-signaali digitoitava joko erillisellä ADC:llä tai AD9361:n RX-porttiin sen omalla kiinteällä sisäisellä LO:lla. Muuttaisi RF-etupään arkkitehtuurin perusteita (kohdat 1, 2, 6 tarpeettomiksi) jos toteutuskelpoinen. **Päivitetty 2026-07-15 (ks. "Taajuuskonfliktin ratkaisu" kohta 3a):** Forsténin `fmcw3`-GitHub-repo antaa konkreettisen, todistetusti toimivan osalistan tälle polulle (ADF4158/HMC431LP4-chirp → suunnattu kytkin → ADL5802-mikseri → ADA4940-2-IF-vahvistin → LTC229x-ADC), ja kaksi riippumatonta muuta 5–6 GHz SAR-lähdettä (Charvat/MIT, Merlo & Nanzer arXiv:2110.14114) vahvistavat saman arkkitehtuurin. Jäljellä ratkaistavaa: (a) sopiiko beat-signaalin taajuusalue AD9361:n 70 MHz minimirajaan ilman lisäsekoitusta vai tarvitaanko erillinen ADC, (b) tarkka BOM/kytkentäbudjetti omalle kantamalle/kaistalle — oma jatkoselvitys/päätös, komponentti-/skeemavalintaa ei ole vielä lukittu.

## Hylätyt vaihtoehdot

- **ADF5355/ADF5356 integroitu PLL+VCO ensisijaiseksi chirp-lähteeksi** — yksinkertaisempi (1 IC kahden sijaan), mutta ei varmistettua radar-spesifistä ramp-moottoria. Jää varavaihtoehdoksi jos ADF4159+HMC431-pari osoittautuu ongelmalliseksi.
- **GaN-radar-PA:t (Qorvo TGA-sarja, Wolfspeed CMPA-sarja, RFHIC:n GaN-moduulit)** — hylätty export-control-riskin takia, sama kategoria josta Forsténin RF-kytkintilaus peruttiin.
- **Sirkulaattori/TR-kytkin RX-suojaukseen** — tarpeeton, koska arkkitehtuuri käyttää jo erillisiä TX/RX-antenneja eikä yhteistä antenniporttia jaeta.
- **Täysin simultaani 1-chirp-polarimetria ortogonaalisilla aaltomuodoilla** — liian monimutkainen ensimmäiseksi versioksi (vaatisi chirp-ketjun kahdentamisen), mahdollinen myöhempi optimointi jos PRF-budjetti osoittautuu pullonkaulaksi suuremmilla lentonopeuksilla.
- **Perinteinen kytkinpohjainen polarisaatio (4× PRF-sakko)** — kortin natiivi 2×2 MIMO tekee siitä turhan hitaan vaihtoehdon kun 2-chirp-dual-RX-skeema on saatavilla samalla raudalla ilman RF-kytkimiä.

## Muutosloki

- **2026-07-15** — Ensimmäinen versio. Perustuu Forsténin blogiin (hforsten.com/homemade-polarimetric-synthetic-aperture-radar-drone.html), AD9361-datasheetiin ja EngineerZone-foorumikeskusteluihin, Skyworks/Analog Devices/TI-datasheeteihin, sekä yhteen akateemiseen C-kaista-polarimetria-SAR-viitteeseen (arXiv:2110.14114).
- **2026-07-15** — Lisätty osio "Taajuuskonfliktin ratkaisu" (`../tehtavat/2026-07-15_rf-etupaan-taajuuskonflikti.md`): EXT_LO:n toiminnasta yli 4 GHz RF:n ei löytynyt empiiristä näyttöä; SFCW hylätty, koska se toimisi kiskovaiheessa mutta olisi 250–3500× liian hidas drone-vaiheen λ/4-näyteväli-budjetissa; Forstén-arkkitehtuuri (ei AD9361:tä chirp-/LO-polulla lainkaan, täysin diskreetti dechirp-on-receive-mikseri) tunnistettu tärkeimmäksi löydökseksi ja suositeltu jatkoselvityksen kohteeksi. Komponenttivalintoja ei muutettu.
- **2026-07-15** — Jatkoselvitys Forsténin ratkaisusta: luettu suoraan hänen `Ttl/fmcw`/`fmcw2`/`fmcw3`-GitHub-repojensa KiCad-skeemat, saatu konkreettinen osalista (ADF4158+HMC431LP4-chirp → suunnattu kytkin → ADL5802-mikseri → ADA4940-2 → LTC229x-ADC, ei AD9361:tä missään). Lisäksi löydetty kaksi riippumatonta muuta 5–6 GHz FMCW/SAR-lähdettä samalla arkkitehtuurilla (MIT/Charvat "Coffee Can Radar" -kurssireferenssi, Merlo & Nanzer arXiv:2110.14114 -julkaisu) — vahvistaa diskreetin dechirp-mikserin olevan toistuva, riippumaton insinöörikäytäntö tälle taajuusalueelle, ei vain Forsténin oikotie. Ei komponentti-/skeemapäätöstä vielä tehty.
