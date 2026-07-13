# Laskentakone — pystytys ja versiolukitus (SDR vaihe 0)

| | |
|---|---|
| **Projekti** | SDR |
| **Tyyppi** | Pystytysohje (laskentakone kuvanmuodostukseen) |
| **Status** | Odottaa rautaa (GTX 1070 vapautuu RTX 5070 -päivityksessä) |
| **Päivitetty** | 2026-07-11 |
| **Liittyy** | [`10_START_sdr_rail-SAR.md`](10_START_sdr_rail-SAR.md) vaihe 0, [`00_POHJANTAHTI_lentava-SAR.md`](00_POHJANTAHTI_lentava-SAR.md) (laskentarealiteetti) |

---

## Kokoonpano ja päätökset

- **Kone:** jämäosista koottu dedikoitu headless-kone, Ubuntu Server LTS (24.04), käyttö SSH:lla Macista.
- **GPU:** GTX 1070 (8 GB, Pascal, compute capability 6.1). Vara: GTX 970 (4 GB, cc 5.2) — huom. cc 5.2 on Maxwell, sama CUDA 12.x -pino kelpaa, mutta 4 GB on ahdas isommille kuville.
- **Miksi CUDA 12.x eikä 13:** CUDA 13 pudotti Maxwell/Pascal-tuen kokonaan.
- **Miksi CUDA 12.6 eikä 12.8/12.9:** PyTorch poisti Maxwell/Pascal-arkkitehtuurit cu128/cu129-wheeleistä versiosta 2.8 alkaen; **cu126-wheelit ovat viimeinen linja jossa sm_61 on mukana** (tuettu väli 6.1–9.0). Toolkit ja wheel pidetään samassa minor-versiossa, jotta torchbp:n nvcc-käännös ja ajossa käytetty torch eivät eriydy.

## Lukittava kolmikko

| Kerros | Versio | Peruste |
|---|---|---|
| NVIDIA-ajuri | 560-sarja (tai uudempi 5xx) | CUDA 12.6 -yhteensopivuus |
| CUDA toolkit | **12.6** (nvcc torchbp:n käännökseen) | viimeinen "turvallinen" minor Pascal + torch-wheel -parille |
| PyTorch | **torch 2.7.x/2.8.x + cu126-wheel** | sm_61 mukana; ≥ 2.6 antaa abi3-buildin torchbp:lle |

> torchbp:n README sanoo "Tested with CUDA 12.9" — se koskee tekijän omaa RTX-rautaa. Pascalilla rajoittava tekijä on PyTorchin binäärituki, ei torchbp.

## Asennusjärjestys

### 1. Ubuntu Server 24.04 LTS

1. Asenna minimipaketilla, valitse asennuksessa **OpenSSH server**.
2. Anna koneelle kiinteä IP (reitittimen DHCP-varaus riittää) ja selkeä hostname, esim. `sar-gpu`.
3. `sudo apt update && sudo apt upgrade`, sitten peruspaketit:
   ```
   sudo apt install build-essential git python3-venv python3-dev
   ```
   (`build-essential` tuo GCC:n + OpenMP:n, jotka torchbp:n käännös vaatii.)

### 2. SSH Macilta

1. Macilla: `ssh-keygen -t ed25519` (jos avainta ei ole), sitten `ssh-copy-id kayttaja@sar-gpu`.
2. `~/.ssh/config` Maciin:
   ```
   Host sar-gpu
       HostName <ip>
       User <kayttaja>
   ```
3. Suositus pitkiin ajoihin: `tmux` koneelle (`sudo apt install tmux`), jotta kuvanmuodostusajo ei kuole SSH-katkoon.
4. Zed/Claude Code voi käyttää konetta remote-SSH:lla tai ajaa komennot `ssh sar-gpu '...'` -muodossa; kuvat voi kopioida takaisin `scp`:llä tai pitää repo synkassa gitin kautta.

### 3. NVIDIA-ajuri

```
sudo apt install nvidia-driver-560-server
sudo reboot
nvidia-smi   # GTX 1070 näkyy, ajuriversio 560.x
```
Jos 560-server ei ole jakelun paketeissa, käytä `ubuntu-drivers list` ja valitse uusin 5xx-server-ajuri. `nvidia-smi`:n oikeassa yläkulmassa näkyvä "CUDA Version" on ajurin *maksimi*, ei asennettu toolkit — älä hämäänny siitä.

### 4. CUDA toolkit 12.6

Asenna NVIDIA:n omasta apt-reposta **täsmäversiona** (jakelun `nvidia-cuda-toolkit` on väärä/liikkuva versio):

```
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cuda-toolkit-12-6
```

Polut käyttöön (`~/.bashrc`):
```
export PATH=/usr/local/cuda-12.6/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:$LD_LIBRARY_PATH
```

Tarkista: `nvcc --version` → release 12.6.

> Huom: `cuda-toolkit-12-6` asentaa vain toolkitin, ei ajuria — ajuri tuli vaiheessa 3. Älä asenna metapakettia `cuda`, joka vetäisi mukanaan uusimman ajurin ja voi rikkoa lukituksen.

### 5. Python-ympäristö + PyTorch cu126

```
python3 -m venv ~/venvs/sar
source ~/venvs/sar/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu126
```

Savutesti:
```
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0)); print(torch.cuda.get_arch_list())"
```
Hyväksymiskriteeri: `is_available() == True`, laite "GeForce GTX 1070", ja `sm_61` löytyy arkkitehtuurilistasta.

### 6. torchbp:n käännös

```
git clone https://github.com/Ttl/torchbp.git
cd torchbp
pip install --no-build-isolation -e .
pip install pytest expecttest
pytest tests/
```

- `--no-build-isolation` on **pakollinen**: laajennos linkittää ei-ABI-stabiileja libtorch-symboleita ja on käännettävä täsmälleen samaa torchia vasten jota ajetaan.
- Käännöksen alussa pitää lukea "Compiling with cuda support". Jos lukee "No cuda support", nvcc ei löytynyt polulta (vaihe 4) tai torch ei näe GPU:ta.
- Koodi käännetään `-march=native` — binääri on konekohtainen, ei siirrettävissä.
- **Jos torch päivittyy, torchbp on käännettävä uudestaan.** Tämä on tärkein syy lukitukseen.

### 7. Versiolukitus kun kolmikko on validoitu

apt-puoli:
```
sudo apt-mark hold nvidia-driver-560-server cuda-toolkit-12-6
```
(tarkista tarkat paketinimet `dpkg -l | grep -E 'nvidia-driver|cuda-toolkit'` ja holdaa myös ajurin alipaketit tarvittaessa; `apt-mark showhold` näyttää tilanteen). Varmista lisäksi ettei unattended-upgrades päivitä NVIDIA-paketteja.

pip-puoli — kirjaa toimiva ympäristö repoon:
```
pip freeze > imaging/requirements-lock.txt
```
ja kirjaa tämän dokumentin muutoslokiin validoitu kolmikko (ajuri x.y, nvcc 12.6.z, torch a.b.c+cu126).

## Tunnetut sudenkuopat

- **Secure Boot:** jos emolevyllä Secure Boot päällä, NVIDIA-moduulin allekirjoitus (MOK) kysytään asennuksessa — helpointa kytkeä Secure Boot pois BIOSista headless-koneessa.
- **Ajuri vs. toolkit -sekaannus:** `nvidia-smi` toimii ilman toolkitia; `nvcc` vaatii toolkitin. Molemmat pitää tarkistaa erikseen.
- **GTX 970 varakorttina:** cc 5.2 toimii samalla pinolla, mutta torchbp on käännettävä uudelleen kortin vaihdon jälkeen (arch tunnistetaan käännöshetkellä paikallisesta GPU:sta).
- **8 GB VRAM:** Forstén ajoi 3090 Ti:llä (24 GB). Vaiheen 0 simulaatiot mahtuvat 1070:een helposti; isommissa kuvissa pienennä gridiä tai pilko kuva — ffbp auttaa myös nopeudessa.

## Rautaspeksi (tavoite, ettei törmää seinään)

GPU on tässä työkuormassa ainoa kriittinen osa — muun raudan tehtävä on olla riittävä, ei muodostua pullonkaulaksi. Backprojection ja autofokus ajetaan GPU:lla.

| Osa | Tavoite | Minimi / huomiot |
|---|---|---|
| CPU | 4–6 ydintä, AVX2 | Intel 4. gen (Haswell) tai mikä tahansa Ryzen; `-march=native`-käännös ja torchin CPU-polut hyötyvät AVX2:sta. Ytimet nopeuttavat lähinnä torchbp:n käännöstä ja esikäsittelyä, eivät kuvanmuodostusta. |
| RAM | **32 GB** | Ehdoton minimi 16 GB. Tärkein "seinä": oikea mittausdata esikäsitellään host-muistissa ennen GPU-siirtoa. DDR3 vs DDR4 ei merkityksellistä — määrä on. |
| Levy | 500 GB – 1 TB **SSD** | SSD pakollinen OS-levynä. OS + venv + torchbp < 50 GB; loppu mittausdatalle. Binääridata ei mene gitiin (`.gitignore`) → järjestä varmuuskopio (rsync Macille / ulkoinen levy). |
| Virtalähde | **Laadukas 450–550 W**, 1× 8-pin PCIe | GTX 1070 150 W / RTX 3060 170 W; koko kone < 300 W. Pitkät GPU-ajot kuormittavat tunteja — vanha halpa virtalähde on koneen todennäköisin vikaantuja ja voi viedä GPU:n mukanaan. **Ainoa osa johon kannattaa laittaa rahaa, jos jämäkasasta puuttuu.** |
| Emolevy | PCIe 3.0 x16 | Riittää täysin myös 3060:lle — SAR-laskenta ei ole PCIe-kaistarajoitteista. |
| Verkko | Gigabitin ethernet (langallinen) | SSH + datansiirto. |

Headless-käytön BIOS-asetukset:
- **Boot without keyboard/display** — osa vanhoista emoista jää POST-virheeseen ilman näyttöä.
- **Restore power after AC loss** + Wake-on-LAN — kone henkiin sähkökatkon jälkeen ilman fyysistä käyntiä.

Jäähdytys: ei erikoisvaatimuksia, mutta kotelon läpiveto ratkaisee GPU:n lämpöthrottlauksen pitkissä ajoissa. Pölysuodatus/puhallus jos kone on lattiatasolla.

## Päivityssuositus: seuraava GPU (kirjattu 2026-07)

Vaihe 0 ajetaan GTX 1070:llä, mutta kun/jos kortti päivitetään, suositus on **käytetty RTX 3060 12GB**:

- **Arkkitehtuuri:** Ampere, compute capability 8.6 — täysi tuki CUDA 13:ssa ja kaikissa nykyisissä PyTorch-wheeleissä. Koko tämän dokumentin Pascal-versiolukko (ajuri 560 / CUDA 12.6 / cu126) raukeaa, ja voidaan ajaa ajantasaista pinoa.
- **Tukihorisontti:** NVIDIA pudotti CUDA 13:ssa Maxwellin, Pascalin ja Voltan; seuraavana jonossa on Turing (cc 7.5). Ampere on datacenter-käytön (A100 on cc 8.0) takia turvallisesti tuettu vielä vuosia — pisin jäljellä oleva tukiaika, jonka saa halvalla.
- **Muisti:** 12 GB GDDR6 > 1070:n 8 GB — suoraan lisää tilaa isommille kuvagrideille ja autofokuksen gradienteille.
- **Hinta:** Suomen käytetyillä markkinoilla (Tori/TechBBS) tyypillisesti n. 150–200 €; uutenakin korttia myydään taas ~330 $ hintaan, mikä pitää käytettyjen hinnat vakaina. Kortti on massatuote, joten saatavuus on hyvä.
- **Käytännön plussat:** ~170 W TDP kelpaa jämäkoneen virtalähteelle, eikä louhintahistoria ole SAR-laskennassa iso riski (testaa silti pytest + pitkä bp-ajo ostohetkellä).

Torjutut vaihtoehdot: RTX 3060 Ti / 2060 (vain 8 GB tai Turing-arkkitehtuuri lähempänä tuen loppua), RTX 4060 Ti 16GB (selvästi kalliimpi, hyöty vaiheeseen nähden pieni), RTX 3080/3090 (hinta, virrankulutus, jämäkoneen virtalähde).

Kortin vaihdon muistilista: torchbp käännettävä uudelleen (arch tunnistetaan paikallisesta GPU:sta), ja samalla voi purkaa apt hold -lukot ja siirtyä uusimpaan CUDA/torch-pariin — päivitä silloin tämä dokumentti.

## Muutosloki

- **2026-07-13** — Ristiviittaukset korjattu numeroituihin tiedostonimiin.
- **2026-07-13** — Lisätty rautaspeksi-osio (CPU/RAM/levy/virtalähde/BIOS-asetukset) ja GPU-päivityssuositus: käytetty RTX 3060 12GB (Ampere, cc 8.6, ~150–200 € käytettynä).
- **2026-07-11** — Ensimmäinen versio. Kolmikko ajuri 560 / CUDA 12.6 / torch cu126 valittu Pascal-rajoitteen perusteella (PyTorch ≥ 2.8 pudotti sm_61:n cu128/cu129-wheeleistä). Validoidut versiot kirjataan tähän kun kone on pystyssä.
