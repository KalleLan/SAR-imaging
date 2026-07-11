# Pohjantähti — Lentävä polarimetrinen SAR-tutka

| | |
|---|---|
| **Tyyppi** | Pohjantähti (jaettu visio- ja referenssidokumentti) |
| **Tallennetaan** | Tämä repo (`docs/00_…`) — yksi master-kopio, molemmat projektit viittaavat tänne |
| **Status** | Elävä master-dokumentti |
| **Päivitetty** | 2026-07-11 |
| **Liittyvät docit** | [`10_START_sdr_rail-SAR.md`](10_START_sdr_rail-SAR.md), [`20_START_drone_SAR-integraatio.md`](20_START_drone_SAR-integraatio.md) |

---

## Tarkoitus

Tämä on molempien projektien jaettu pohjantähti: yksi paikka, joka kertoo *mitä* lopulta rakennetaan ja *miksi* keskeiset valinnat on tehty. SDR- ja drone-projektit tekevät omaa työtään, mutta molemmat tähtäävät tähän samaan lopputulokseen ja jakavat tässä kuvatut rajapinnat. Jos jokin arkkitehtuurivalinta muuttuu, se muuttuu **tässä** ja molemmat projektit lukevat sen samasta lähteestä.

## Lopputavoite

Ilmasta kuvantava polarimetrinen FMCW-SAR-tutka pienessä FPV-dronessa. Harrastajabudjetti, luokkaa 800 € (drone + kaksi tutkakorttia), kuvantaa vähintään ~1,5 km etäisyydelle, koko järjestelmä alle 1 kg akku mukaan lukien, neljä polarisaatiota (HH/HV/VH/VV). Positio ei-RTK-GPS + IMU, ja kuvan tarkennus hoidetaan autofokuksella eikä RTK:lla.

## Referenssijärjestelmä

Henrik Forsténin toteutus on suora pohjantähti — suomalainen, samat olosuhteet (lumi, metsä, Traficomin 120 m korkeusraja), julkinen ja täydellinen ketju RF:stä kuvanmuodostukseen.

- **Blogi (ensisijainen referenssi):** https://hforsten.com/homemade-polarimetric-synthetic-aperture-radar-drone.html
- **Jatko-osa (parempi kuvankäsittely, 10/2025):** https://hforsten.com/synthetic-aperture-radar-autofocus-and-calibration.html
- **`torchbp` — kuvanmuodostus + autofokus (GPU, MIT-lisenssi):** https://github.com/Ttl/torchbp
- **ArduPilot ROI-spotlight-patch (PR #28486):** kääntää antennin ROI:hin nokan sijaan

Keskeiset referenssiparametrit (lähtökohta, ei kiveen hakattu):
- RF ~6 GHz (λ ≈ 5,2 cm) — valittu koska halpoja kuluttaja-RF-komponentteja saatavilla
- FMCW, suora konversio (ei image rejectionia)
- Kaista 300–500 MHz → etäisyysresoluutio 0,5–0,3 m
- ADC 50 MHz näytteistys
- TX-teho +30 dBm, antennivahvistus ~10 dBi, vastaanottimen NF ~6 dB
- FPGA Zynq 7020 (FPGA + kaksi ARM-ydintä samassa)
- Kuvanmuodostus: backprojection GPU:lla, tarkennus minimi-entropia-autofokuksella

## Keskeiset suunnitteluvalinnat ja perustelut

**FMCW, ei pulssitutka.** Lähettää ja vastaanottaa yhtä aikaa → parempi SNR hitaalla, lyhyen kantaman alustalla. Sallii ison RF-kaistan ilman nopeaa ADC:tä. Vaatii erilliset TX/RX-antennit ja niiden välisen eristyksen (>50 dB, muuten vuoto kyllästää vastaanottimen).

**~6 GHz.** Halvin taajuus jossa on runsaasti kuluttajakomponentteja. **Kääntöpuoli — kirjattu tietoisena rajoituksena alla:** ei mene läpi lehtien.

**Polarimetrinen (HH/HV/VH/VV).** Antaa materiaalin erottelun: metsä/kasvillisuus heijastaa ristipolarisaatiota (HV/VH) enemmän kuin sileä maa tai tie. Tämä **ei** ole lehtiläpäisy — se on pintamateriaalin tunnistusta.

**Autofokus, ei RTK-GPS.** RTK on iso ja kallis eikä mahdu tähän droneen. Ratkaisu: tavallinen GPS (~1 m virhe) + IMU-fuusio positioon, ja radiodatasta ratkaistu autofokus korjaa jäännösvirheen. Käytetään gradienttipohjaista minimi-entropia-autofokusta (backpropagation); klassinen PGA ei toimi hyvin leveän keilan ja pitkän baselinen takia.

**ArduPilot, ei Betaflight.** Betaflight ei osaa autonomista lentoa eikä mount/ROI-ohjausta. ArduPilotin IMU/GPS-sensorifuusio parantaa positiota, se syöttää position tutkalle sarjaväylän yli, ja ROI-patchilla saadaan spotlight-moodi.

## Fysiikan reunaehdot (muistilista)

- **Etäisyysresoluutio** = c / (2·B). 300 MHz → 0,5 m, 150 MHz → 1 m.
- **Poikittaisresoluutio** syntyy synteettisestä aukosta. Stripmap-raja on L/2 (antennin pituus); spotlight-moodissa (antenni seuraa kohdetta) rajana on lennetyn radan pituus, ei keilan leveys. Dronella suurin rajoite on käytännössä radan maksimipituus (näköyhteys).
- **Liikekompensaatio on koko projektin kova ydin.** Antennin vaihekeskiön paikka pitää tuntea aallonpituuden murto-osalla; 6 GHz:llä puhutaan senteistä/millimetreistä. Kiskolla tämä ratkeaa mekaanisesti (tunnettu rata), ilmassa autofokuksella.
- **PRF ↔ lentonopeus.** Vältettävä aliasointi vaatii ~λ/4 näytevälin. 6 GHz:llä λ/4 = 12,5 mm; 10 m/s → PRF ≥ 800 Hz; ×4 polarisaatiota → 3,2 kHz → sweep max ~280 µs (PLL-lukitus huomioiden). **Tämä on rajapinta:** "radion" sweep-parametri määräytyy "dronen" lentonopeudesta.
- **Look-angle / varjot.** 120 m korkeudella 2 km päässä grazing-kulma on vain ~3,4° → pitkät varjot, matala takaisinheijastus. Käytännön kuvantamisgeometria on kompromissi.

## Tärkeä rajaus: lehtiläpäisy

Tämä järjestelmä **ei näe latvuston läpi.** 6 GHz (C-bändi) siroaa lehvästöstä; metsä heijastaa voimakkaasti ja heittää tutkavarjoja. Aito lehtiläpäisy (FOPEN) vaatii matalaa taajuutta (P-/UHF-bändi), josta seuraa fyysisesti iso antenni — täysin eri, tutkimusluokan projekti.

**Päätös:** rakennetaan ensin tämä 6 GHz -luokan järjestelmä (opettaa koko ketjun, on toteutettavissa). FOPEN on erillinen myöhempi harkinta, ei tämän projektin tavoite.

## Vaiheistus (halvin kokeilu ensin)

1. **Rail-SAR — SDR-projekti.** Todista koko kuvanmuodostusketju kiskolla, missä rata tunnetaan täydellisesti. Eristää liikekompensaation pois muuttujista. → [`10_START_sdr_rail-SAR.md`](10_START_sdr_rail-SAR.md)
2. **Ilmaan siirto — drone-projekti.** Kun ketju toimii kiskolla, siirretään RF-kortti + antennit + firmware + kuvanmuodostus lentävälle alustalle. Ainoa uusi vaikea asia on liikekompensaatio (autofokus + ArduPilot-positiodata). → [`20_START_drone_SAR-integraatio.md`](20_START_drone_SAR-integraatio.md)

Huom: myös Forstén teki maassa SAR-kuvantamiskokeita ennen lentoa. Kisko ei ole kiertotie ilmaan — se on nopein reitti, koska jokainen dronessa kohdattu ongelma on helpompi kun kuvanmuodostus on jo todistettu.

## Domain-jako ja jaetut rajapinnat

**SDR-projektille kuuluu:** RF-arkkitehtuuri (PLL/DDS, PA, LNA, mikserit, polarisaatiokytkimet), antennit, Zynq/FPGA + firmware, ADC-ketju, kuvanmuodostus (backprojection) ja autofokus, tutkan mikro-ohjaimen ohjelmisto, kiskomekaniikka ja -mittaukset.

**Drone-projektille kuuluu:** lentoalusta ja sen viritys, ArduPilot-konfiguraatio, autonominen missio, ROI-spotlight-patch, mekaaninen kiinnike + laskeutumisjalat, virransyöttö, painobudjetti, sääsuojaus, regulaatio.

**Jaetut rajapinnat (nämä eivät kuulu puhtaasti kummallekaan — pidä synkassa):**
- **Positiodata:** ArduPilot → tutka, fuusioitu paikka-arvio sarjaväylän yli.
- **Laukaisu:** ArduPilotin `digicam configure` -komento käynnistää tutkamittauksen (tutkan mikro-ohjain kuuntelee tätä komentoa).
- **ROI/spotlight:** antenni osoitetaan ROI:hin (patch #28486).
- **PRF ↔ lentonopeus:** ks. fysiikan reunaehdot; tutkan sweep-parametri sidoksissa nopeuteen.
- **Autofokuksen olemassaolon syy:** dronen lentodynamiikka (tuuli, epäsuora rata). Autofokus-koodi asuu SDR-puolella, mutta sen viimeistely vaatii oikeaa lentodataa → ei valmis ennen drone-vaihetta.

> Nämä rajapinnat kannattaa pitää lyhyenä erillisenä `RAJAPINNAT.md`-dokumenttina repossa koodin vieressä, jos ne alkavat elää. Toistaiseksi ne asuvat tässä.

## Työkalu- ja laskentarealiteetti

`torchbp` on **CUDA**-pohjainen (Forstén ajoi RTX 3090 Ti:llä). 16 GB MacBookissa ei ole NVIDIA-GPU:ta. Vaihtoehdot kuvanmuodostukseen: (a) PyTorch Metal/MPS-backend — osa toimii, CUDA-kernelit eivät käänny suoraan; (b) vuokra-GPU pilvestä; (c) erillinen NVIDIA-kone Hacklabilla. Tämä on ketjun viimeinen lenkki — ilman toimivaa kuvanmuodostusta ei näe kuvaa, joten ratkaise se aikaisin (ks. SDR-start, vaihe 0).

## Komponenttien end-use-rajoitukset

Odota kitkaa: osa 6 GHz:n RF-komponenteista on end-use-valvonnan piirissä. Forsténilta peruttiin RF-kytkimen tilaus jälkikäteen, koska valmistaja ei myy sitä yksityishenkilöille (huoli puolustussovelluksista). Varaudu etsimään pin-yhteensopivia vaihtoehtoja tai vanhentuneita versioita.

## Muutosloki

- **2026-07-11** — Ensimmäinen versio. Lähde: Forstén-blogi + jatko-osa. Vaiheistus, domain-jako ja rajapinnat kirjattu.
- **2026-07-11** — Siirretty GitHub-repoon `KalleLan/SAR-imaging` (`docs/`). Tiedostonimiin lisätty järjestysprefiksit (00/10/20), ristiviittaukset muutettu suhteellisiksi linkeiksi.
