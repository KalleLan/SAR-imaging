# Vaihe 0 jatko — Claude Code -tehtävänanto: DEM-backprojection ja squint-tuki torchbp:ssä

| | |
|---|---|
| **Projekti** | SDR |
| **Tyyppi** | Tehtävänanto (Claude Code) — torchbp-inventaario, jatkoa vaihe A:lle |
| **Päivitetty** | 2026-07-15 |
| **Liittyy** | [`imaging/README.md`](../../imaging/README.md) ("torchbp API -muistiinpanot"), [`00_POHJANTAHTI_lentava-SAR.md`](../00_POHJANTAHTI_lentava-SAR.md), [`10_START_sdr_rail-SAR.md`](../10_START_sdr_rail-SAR.md) vaihe 0, [`2026-07-11_vaihe0_imaging_runko.md`](2026-07-11_vaihe0_imaging_runko.md) (edellinen inventaario, sama torchbp-klooni/commit) |

---

## Tausta

Bekar, Antoniou & Baker, "Low-Cost, High-Resolution, Drone-Borne SAR Imaging"
(IEEE TGRS 2021) käytiin läpi vertailukohtana omalle projektille. Kaksi
löydöstä sieltä koskevat suoraan `torchbp`:n ominaisuuksia joita ei ole vielä
tutkittu:

1. **Kohteen korkeus vaikuttaa vaiheeseen.** Bekarin paperin keskeinen tulos
   (heidän Fig. 2c, kappale IV) on että jo muutaman metrin korkeusero
   kohteiden välillä riittää sotkemaan fokusoinnin, koska heidän algoritminsa
   olettaa tasomaisen maan. Paperin oma johtopäätös: seuraava askel on
   "height-dependent target focusing using digital elevation models". Oman
   `imaging/README.md`:n torchbp-inventaario (vaihe A) mainitsi ohimennen että
   `docs/source/examples/`-kansiossa on `dem_backprojection`-notebook, mutta
   sen sisältöä ei avattu. Tämä on suoraan relevantti oman projektin
   polarimetria-tavoitteelle (metsä/kasvillisuus vs. sileä maa on juuri
   korkeusvaihtelevaa maastoa).
2. **Squint (ei-broadside-kuvantaminen).** Oma suunnitelma (`20_START`)
   kääntää antennin ROI:hin lennon aikana (ArduPilot ROI-spotlight-patch
   #28486), mikä tuottaa squintatun geometrian. Bekarin viitteet [10] (Hu et
   al., range-azimuth-kytkentä + squint-minimointi + squintattu PGA/MEA) ja
   [20] (wavenumber-domain-autofokus squintatulle SAR:lle) käsittelevät tätä
   ongelmaa erikseen omana asianaan — se ei ole itsestäänselvä laajennus
   broadside-menetelmistä.

Molemmat ovat torchbp:n lähdekoodin lukemista, eivät riipu GPU-koneesta tai
raudasta — sama laji työtä kuin jo tehty vaihe A -inventaario. Ei tarvitse
odottaa rautareitin A/B-päätöstä (`10_START` vaihe 1): tämä työ on siitä
riippumaton ja voidaan tehdä rinnakkain.

---

## Tehtävänanto Claude Codelle (kopioi tästä alaspäin)

Jatka `imaging/README.md`:n "torchbp API -muistiinpanot" -osiota kahdella
uudella aliluvulla. Sama periaate kuin vaihe A:ssa: lue lähdekoodista, älä
arvaa. Käytä samaa torchbp-kloonia/commitia kuin edellisessä inventaariossa
(`cf59c15fae5058382ff4e27b38e7a306c36b5a7f`), ellei origin/master ole
edennyt — jos on, kirjaa uusi commit-hash.

### Osa 1 — DEM-backprojection

1. Etsi `docs/source/examples/`-kansiosta DEM-aiheinen notebook
   (`dem_backprojection` tms.) ja lue se rivi riviltä. Selvitä myös
   `torchbp/ops.py`:n ja `csrc/`:n `dem`-parametrin käsittely
   (`backprojection_polar_2d`:n signatuurissa on jo dokumentoitu
   `dem: Tensor | None = None` — tarkenna nyt mikä on tämän tensorin muoto,
   koordinaatisto (suhteessa jo dokumentoituun `pos`/origin-konventioon,
   ks. README:n "PolarGrid-olion rakenne" -osio) ja resoluutio-oletukset.
2. Vahvista/tarkenna jo README:hen kirjattu huomio: "Gradientti tuettu
   `data`:n ja `pos`:n suhteen (ei `dem`-tapauksessa)" — eli DEM-tapauksessa
   autofokus (`minimum_entropy_grad_autofocus`) ei ilmeisesti toimi suoraan
   backpropilla `dem`:n läpi. Selvitä lähdekoodista: onko tarkoitettu
   työjärjestys "autofokusoi ilman DEM:ää (tasomaisella oletuksella) → aja
   lopullinen kuvanmuodostus korjatulla `pos`:lla ja oikealla DEM:llä", vai
   onko jokin muu virallinen kaava? Onko notebookissa esimerkki tästä
   järjestyksestä?
3. Arvioi mitä DEM:n käyttö vaatisi meiltä käytännössä: tarvitaanko oikea
   maastomalli (esim. avoin korkeusdata-aineisto), vai riittäisikö
   validointiin (`sar_sim`) synteettinen/approksimoitu korkeuskartta samaan
   tapaan kuin Bekarin simulaatiossa (osa kohteista korotettuna, ks. paperin
   kappale IV) sen todentamiseksi että DEM-backprojection oikeasti korjaa
   korkeuseron aiheuttaman defokusoinnin meidän omassa simulaattorissamme.
   Ei tarvitse toteuttaa tätä koestusta vielä — riittää arvio ja ehdotus
   pienimmästä seuraavasta askeleesta.

### Osa 2 — Squint-tuki

1. Selvitä lähdekoodista tukeeko `backprojection_polar_2d`,
   `backprojection_cart_2d`, `gpga`/`gpga_tde` ja
   `minimum_entropy_grad_autofocus` squintattua (ei-broadside) geometriaa
   suoraan, vai onko taustaoletus stripmap/broadside. Kiinnitä huomiota
   erityisesti Doppler-keskipisteen (`fdc`/Doppler centroid) käsittelyyn —
   Bekarin paperissa (osa III.A) tämä on eksplisiittinen vaihe
   ("Doppler centroid correction") ennen autofokusta; onko vastaavaa
   torchbp:ssä, vai oletetaanko nollakeskipiste?
2. Jo dokumentoidut `att` (roll/pitch/yaw) ja `g`/`g_extent`
   (antennikuvio) -parametrit `backprojection_polar_2d`:ssä — tarkenna
   vaikuttavatko nämä vain antennivahvistuksen painotukseen (amplitudi)
   vai myös range/Doppler-geometrian laskentaan (vaihe). Jos vain
   amplitudiin, squintin *geometrinen* vaikutus (range-azimuth-kytkentä,
   ks. Bekarin viite [10]) ei ole hoidettu näillä parametreilla, ja se
   pitäisi huomioida erikseen ROI-spotlight-kuvantamisen suunnittelussa.
3. Johtopäätös: onko squintattu ROI-kuvantaminen käytettävissä torchbp:llä
   sellaisenaan, vai vaatiiko se lisätyötä (esim. oma Doppler-keskipisteen
   esiestimointi/-poisto ennen `torchbp`-kutsuja)? Tämä ei ole kiireellinen
   drone-integraation kannalta (ROI-patch tulee vasta myöhemmin), mutta
   halpa selvittää nyt kun vaihe A -inventaariokoodi on tuoreena.

### Tulostus

- Lisää molemmat löydökset `imaging/README.md`:n "torchbp API -muistiinpanot"
  -osioon omina alilukuinaan (samaan tyyliin kuin nykyiset "PolarGrid-olion
  rakenne" ja "CPU vs. CUDA -tuki" -alaluvut: lähdeviittaukset tiedosto- ja
  rivinumeroin, ei yleisluontoisia väitteitä).
- Lisää kummallekin lyhyt "Suositus"-kappale: blokkaako tämä jotain nyt, vai
  voiko odottaa myöhempään vaiheeseen (DEM: vasta kun oikeaa maastodataa
  tarvitaan; squint: vasta drone-integraatiossa ROI-patchin kanssa)?
- Päivitä README:n Muutosloki.

### Työtapa

- Pieniä committeja loogisin välein (DEM-inventaario → squint-inventaario →
  README-päivitys).
- Jos torchbp:n todellisuus poikkeaa tämän tehtävänannon oletuksista
  (esim. DEM-tuki on rakenteeltaan täysin toisenlainen), kirjaa poikkeama
  README:hen äläkä pakota tehtävänantoa väkisin — sama periaate kuin
  vaihe A:ssa.
- Ei koodimuutoksia `sar_sim`/`scripts`-hakemistoihin tässä tehtävässä —
  tämä on puhdas inventaariotehtävä, kuten vaihe A. Mahdolliset
  toteutusehdotukset (esim. korkeusvaihtelun lisääminen `sar_sim`:iin) vain
  kirjataan README:hen "Seuraavat vaiheet" -osioon.

## Muutosloki

- **2026-07-15** — Ensimmäinen versio. Tehtävänanto syntyi Bekar et al.
  (TGRS 2021) -paperin ja sen referenssien vertailusta omaan projektiin
  (Cowork-keskustelu 2026-07-15): kaksi konkreettista aukkoa tunnistettu
  (korkeusriippuvainen vaihevirhe / DEM-backprojection, ja squint-tuki
  ROI-spotlight-tilaa varten).
