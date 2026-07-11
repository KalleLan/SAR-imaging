# Drone-projekti — START: SAR-integraatio (maasta ilmaan)

| | |
|---|---|
| **Projekti** | Drone |
| **Tyyppi** | Start-dokumentti (ilmaan-siirtovaihe) |
| **Status** | Odottaa esiehtoja — ei vielä aktiivinen |
| **Päivitetty** | 2026-07-11 |
| **Pohjantähti** | [`00_POHJANTAHTI_lentava-SAR.md`](00_POHJANTAHTI_lentava-SAR.md) |
| **Edeltäjä** | [`10_START_sdr_rail-SAR.md`](10_START_sdr_rail-SAR.md) (tämä aktivoituu kun SDR-ketju on todistettu) |

---

## Milloin tämä aktivoituu

Tämä dokumentti käynnistää työn vasta kun SDR-projektin kuvanmuodostusketju on todistettu kiskolla (viimeistään [`10_START_sdr_rail-SAR.md`](10_START_sdr_rail-SAR.md) vaihe 4, kuva pihalta). Ennen sitä drone-puolella tehdään valmistelevaa työtä (alla), mutta itse SAR-integraatioon ei kannata mennä ennen kuin ketju on kunnossa maassa.

**Esiehdot ennen integraatiota:**
- Kuvanmuodostus + autofokus toimivat todistetusti (SDR vaihe 0).
- Tutkakortti tuottaa oikeaa dataa oikealla raudalla (SDR vaihe 3–4).
- Laskenta-alusta kuvanmuodostukselle ratkaistu.

## Iso kuva: paljon tulee ennen SAR:ia

SAR on tämän projektin lopullinen hyötykuorma, mutta drone-puolelle tulee runsaasti muuta ennen kuin järjestelmä nostetaan taivaalle. Nämä kannattaa tehdä ja luotettavaksi todeta **ilman tutkaa** — halvemmalla ja pienemmällä riskillä — jotta integraatiovaiheessa vain yksi asia on uutta kerrallaan.

### Lentoalusta (perusta)
- 7" ArduPilot-kopteri joka nostaa ~1 kg hyötykuormaa (Forsténin luokka).
- Lentokontrolleri mieluiten 2 MB flashilla (ArduPilot on iso; 1 MB on ahdas).
- Viritetty, luotettava, toistettavasti lennettävä **ennen** kuin mitään hyötykuormaa lisätään.

### Autonomia ja linkit
- GPS + kompassi (kaukana akkukaapeleista magneettihäiriön takia) + IMU-fuusio toimii.
- ELRS-ohjauslinkki. **MAVLink ELRS:n yli** → yksi radio hoitaa sekä ohjauksen että telemetrian (ei tarvita kahta radiota).
- Maa-asema (Mission Planner) telemetriaan ja mission ohjelmointiin.
- Autonominen waypoint-lento hallussa ja luotettava.

### ROI / spotlight
- **ArduPilot ROI-spotlight-patch (PR #28486)** käännettynä omaan firmwareen. Oletuksena drone kääntää *nokan* ROI:hin; patch kääntää *antennin* ROI:hin, mikä on spotlight-kuvantamisen edellytys.
- Missioon `digicam configure` -komento tutkan laukaisuun (tutka kuuntelee tätä).

### Mekaniikka ja integrointi (Hacklab)
- 3D-printattu kiinnike joka pitää tutkakortin rungon alla.
- Laskeutumisjalat (hiilikuituputki + TPU-päädyt) niin ettei drone laskeudu tutkan päälle.
- Virransyöttö suoraan akusta (XT60-splitteri FC + tutka); tutka sietää 12–30 V.
- Painobudjetti < 1 kg akku mukaan lukien — seuraa tarkasti.
- Sääsuojaus kortille (Forsténilla jäi tekemättä — tee paremmin).
- Antennilevyn kulma säädettävissä (look-angle).

## Rajapinnat SDR-projektiin

Nämä ovat pohjantähden jaettuja rajapintoja; drone-puolen vastuu niistä:

- **Positiodata ulos:** ArduPilot syöttää fuusioidun paikka-arvion tutkalle sarjaportin yli. Tutka ei tarvitse omaa GPS/IMU:a — se käyttää lentokoneen estimaattia.
- **Laukaisu:** missio antaa `digicam configure` oikeassa kohdassa rataa.
- **ROI-osoitus:** patch #28486 kääntää antennin.
- **PRF ↔ lentonopeus:** valittu lentonopeus (esim. 5–10 m/s) sanelee tutkan sweep-parametrit. Sovi tämä SDR-puolen kanssa ennen mittauslentoa — älä lennä nopeutta johon tutkan PRF ei riitä.

## Integraatiovaiheen työjärjestys

1. Lennätä alusta luotettavaksi ilman hyötykuormaa.
2. Lisää tutkan **massa-attrappi** (oikea paino, ei elektroniikkaa) ja varmista lento-ominaisuudet + painopiste kiinnikkeineen ja laskeutumisjalkoineen.
3. Kytke oikea tutka virtaan ja positiodataan maassa; varmista laukaisu ja datankeruu ilman lentoa.
4. Ensimmäinen mittauslento suoralla radalla, ROI kaukana, matala nopeus.
5. Prosessoi maassa; jos kuva sumea → autofokuksen viritys oikealla lentodatalla.
6. Vasta sitten monimutkaisemmat radat (oktagoni / VideoSAR).

## Regulaatio

- Traficom / EU open category, näköyhteys (VLOS).
- Ilman erityislupia max **120 m** korkeus — sama raja jota Forsténkin käyttää; vaikuttaa suoraan kuvantamisgeometriaan ja varjoihin (ks. pohjantähti).
- Tarkista lennätysalueen rajoitukset ennen jokaista mittauslentoa.

## Riskit ja avoimet kysymykset

- Painopiste: tutka + antennit rungon alla siirtää CG:tä — akun sijainti tasapainottaa.
- Tuuli: kevyt drone heiluu → juuri se mikä tekee autofokuksesta pakollisen. Valitse tyyni sää ensimmäisiin lentoihin.
- Akku vs. lentoaika vs. baseline-pituus: pidempi rata = parempi poikittaisresoluutio, mutta rajana näköyhteys ja akku.
- Avoin: 7" kopteri vs. isompi alusta vs. myöhempi VTOL-siipi pidempään loiteriin? (Aiempi keskustelu VTOL:sta koskee tähystäjä-gimbal-käyttöä; SAR:lle Forsténin 7" riittää aloitukseen.)

## Muutosloki

- **2026-07-11** — Ensimmäinen versio. Esiehdot, "paljon tulee ennen SAR:ia" -valmistelulista, rajapinnat SDR:ään ja integraation työjärjestys kirjattu.
- **2026-07-11** — Siirretty GitHub-repoon `KalleLan/SAR-imaging` (`docs/`). Tiedostonimiin lisätty järjestysprefiksit (00/10/20), ristiviittaukset muutettu suhteellisiksi linkeiksi.
