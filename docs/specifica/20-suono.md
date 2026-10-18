# 20 — Suono: motori, basso, effetti, preset, voci

> Sezione della specifica funzionale di **Stame** per la Miyoo Flip. Descrive il modulo `dsp` (C11 puro): architettura audio, pool di voci, i tre modelli di sintesi (VA, FM, Reed Piano), il motore del basso, effetti, modulazioni, formato della patch, preset, macro esposte, budget CPU e test.
> Convenzioni generali in `CONVENZIONI.md`. Prefisso dei requisiti: `SND-`.

## 0. Ambito, termini e note sulle fonti

**Ambito.** Il modulo `dsp` riceve eventi logici (note, controller, parametri) dal `core` e produce audio stereo. Non conosce accordi, Perform, looper né MIDI fisico: quelli stanno in `10-accordi-e-performance.md` e `40-midi-e-controlli.md`.

**Termini**

| Termine | Significato |
|---|---|
| motore | Una delle due istanze del synth: **Sound** (accordi, indice 0) e **Bass** (indice 1). |
| modello | Il tipo di sintesi scelto dal parametro `MODEL`: VA, FM o Reed Piano (RP). |
| patch | Il blocco di 135 byte raw che descrive un motore. |
| raw | Valore intero del parametro: 0–127, oppure indice di un enum. |
| `x` | Nelle formule, `x = raw / 127` (0…1). |
| `v` | Velocity normalizzata, `v = vel / 127`. |
| blocco | 16 frame stereo consecutivi. |

**Etichette.** Le fonti di studio usano un sistema diverso; qui vale questa corrispondenza:
- manuale dell'editor dell'originale, articoli del supporto, post e video ufficiali → `[M]`;
- codice e tabelle dell'editor 1.0.2 dell'originale e del firmware 3.92 (analisi di terzi), catture MIDI, test di utenti, recensioni → `[O]`;
- ricostruzioni → `[D]`;
- valori scelti da Stame in assenza di dati → `[V]`, sempre con il rimando alla questione aperta (`QA-SND-nn`) che dice come verificarli.

**Dati privati.** I valori dei preset di fabbrica 3.92 non compaiono in questa sezione. Ne descriviamo solo il formato, la struttura e i nomi (§2.7, §12).

---

## 1. Architettura audio

### 1.1 Formato e temporizzazione

- **SND-001** Il `dsp` **DEVE** lavorare in virgola mobile a 32 bit (`float`), stereo, con frequenza di campionamento `fs` passata a `dsp_init`. Default per la Flip: **48 000 Hz** `[V → QA-SND-01]`. La frequenza dell'hardware originale non è nota; l'editor dell'originale dalla 0.1.12 è indipendente dalla frequenza `[M]`, quindi tutti i coefficienti **DEVONO** essere calcolati da `fs` e il modulo **DEVE** funzionare anche a 44 100 Hz.
- **SND-002** Il rendering **DEVE** avvenire a **blocchi di 16 frame**, con due buffer separati per canale: `dsp_render16(dsp, float L[16], float R[16], …)`. È la stessa granularità di `msynthesizer::generate16(float*, float*)` dell'editor dell'originale `[O]`. Lo strato `platform` chiama la funzione più volte per riempire un periodo ALSA (multiplo di 16, vedi `50-piattaforma-flip.md`).
- **SND-003** Gli eventi in ingresso (§1.4) **DEVONO** essere applicati al confine di blocco, nell'ordine di arrivo. Il jitter massimo (16 frame = 0,33 ms a 48 kHz) è accettato `[D]`.
- **SND-004** Il percorso audio **NON DEVE** allocare memoria, fare I/O, prendere lock o chiamare funzioni di sistema. Tutto lo stato del `dsp` sta in una struttura `dsp_t` allocata dal chiamante una volta sola.
- **SND-005** A parità di build, di `fs` e di sequenza di eventi l'uscita **DEVE** essere identica bit per bit. I generatori casuali (rumore, sorgente RANDOM, S&H) usano un PRNG interno (xorshift32) con seme impostabile da `dsp_init` e reimpostabile con `dsp_reseed`.

### 1.2 Due istanze dello stesso synth

- **SND-010** Il `dsp` **DEVE** contenere due motori identici, **Sound** (0) e **Bass** (1). Ciascuno ha la propria patch di 135 byte, il proprio stato di controller (bend, wheel, sustain), il proprio oggetto Reed Piano, i propri FX1 e FX2 `[O: firmware con due blocchi parametri, due oggetti RP da 0x680 byte e flag FX separati per motore]`.
- **SND-011** Il basso **NON DEVE** essere un motore semplificato: con la sua patch può essere VA, FM o RP, con tutti i 135 parametri `[O]`. Due bassi di fabbrica hanno "RP" nel nome `[O]`.
- **SND-012** Il riverbero **DEVE** essere unico e condiviso dai due motori, alimentato dalle mandate `REVSEND` di ciascuno, con `REVSIZE`, `REVLP` e `REVHP` presi dalla patch del **Sound** `[D: il setter del firmware ricalcola il riverbero solo quando cambiano i parametri del Sound]` `[V → QA-SND-10]`.

### 1.3 Pool di voci e voice stealing

- **SND-020** Il `dsp` **DEVE** avere un **pool unico di 16 voci**, condiviso tra Sound e Bass `[O: il firmware scorre 16 strutture voce da 1180 byte con un campo motore; 16 voci secondo le recensioni]`.
- **SND-021** Ogni voce ha uno stato: `FREE`, `HELD` (tasto premuto o tenuto dal sustain), `RELEASED` (in rilascio), `DYING` (in dissolvenza dopo lo stealing). Una voce `RELEASED` torna `FREE` quando la sua ampiezza scende sotto −90 dBFS per un blocco intero, oppure quando l'inviluppo d'ampiezza arriva a 0.
- **SND-022** Il numero massimo di voci del Bass **DEVE** essere configurabile; default **1** `[V → QA-SND-03]`. Le fonti divergono: il basso è descritto come monofonico da guida e recensioni `[O]`, ma il firmware lo tratta come un synth completo `[O]`. Nell'uso normale il `core` suona una sola nota di basso per accordo `[M]`.
- **SND-023** Allocazione di una nota sul motore `e` `[V → QA-SND-02]`, nell'ordine:
  1. se una voce di `e` suona già la stessa nota, la si riusa (retrigger, senza dissolvenza);
  2. se `e` ha già raggiunto il suo massimo di voci, si ruba la voce di `e` più vecchia (prima le `RELEASED`, poi le `HELD`);
  3. altrimenti si prende una voce `FREE`;
  4. altrimenti si ruba, tra le voci `RELEASED` di qualunque motore, quella con l'ampiezza corrente più bassa;
  5. altrimenti si ruba la voce `HELD` più vecchia del **Sound**. Una voce `HELD` del Bass **NON DEVE** essere rubata da una nota del Sound.
- **SND-024** Una voce rubata **NON DEVE** produrre click: il suo stato viene copiato in uno dei **16 slot di coda** (`DYING`), insieme a una copia della patch del suo motore, e lo slot lo dissolve linearmente a zero in **2 ms**, mentre la voce riparte subito con la nuova nota `[D]`. Se gli slot sono tutti occupati, si chiude il più vecchio. Gli slot di coda non contano come voci. (Il 15/10/2026 gli slot sono passati da 4 a 16: servono anche al cambio di patch, SND-026.)
- **SND-026** Cambio di patch con note in suono `[D, 15/10/2026]`: le voci del motore passano negli slot di coda con la patch vecchia. Le voci **tenute** si dissolvono in **10 ms** e le stesse note ripartono subito con la patch nuova (stessa velocity, stato del sustain conservato); le voci **in rilascio** finiscono il loro rilascio con la patch vecchia. Così girare Sound mentre si tiene un accordo fa sentire subito il suono nuovo, senza buchi né clic, anche fra modelli diversi. Se la patch nuova è **mono** (GLIDEMODE 2 o 3) riparte una voce sola, sull'ultima nota tenuta, e il note-off mono rilascia anche le voci tenute rimaste con la stessa nota (revisione del 15/10/2026: con un accordo tenuto e Heliotrope, Linnaeus Lead, Thistle Lead o Didgeridoo due note restavano accese per sempre). Una voce SMP ribattuta mentre suona passa in coda con una dissolvenza di 2 ms e la nota riparte in una voce nuova: il campione non salta più da capo con il VCA aperto (clic).
- **SND-025** `CC120 All Sound Off` **DEVE** azzerare all'istante tutte le voci, gli slot di coda e i due oggetti RP; `All Notes Off` **DEVE** mandare in rilascio tutte le voci `HELD`, ignorando il sustain `[O]`.

### 1.4 Interfaccia del modulo

- **SND-030** Il `dsp` **DEVE** esporre un'API C equivalente a questa (i nomi sono indicativi):

```c
typedef enum { DSP_SOUND = 0, DSP_BASS = 1 } dsp_engine;

void dsp_init(dsp_t *d, float fs, uint32_t seed);
void dsp_reseed(dsp_t *d, uint32_t seed);

/* eventi: applicati al prossimo confine di blocco */
void dsp_note_on (dsp_t *d, dsp_engine e, uint8_t note, uint8_t vel);   /* vel 1..127 */
void dsp_note_off(dsp_t *d, dsp_engine e, uint8_t note);
void dsp_chord_start(dsp_t *d, dsp_engine e);        /* nuovo accordo: riavvia gli LFO in modo MONO */
void dsp_pitch_bend(dsp_t *d, dsp_engine e, int16_t v);  /* -8192..8191 */
void dsp_mod_wheel (dsp_t *d, dsp_engine e, uint8_t v);  /* 0..127 */
void dsp_sustain   (dsp_t *d, dsp_engine e, bool on);
void dsp_reset_controllers(dsp_t *d, dsp_engine e);   /* wheel 0, bend 0, sustain off */
void dsp_all_notes_off(dsp_t *d);
void dsp_all_sound_off(dsp_t *d);

void dsp_setpar   (dsp_t *d, dsp_engine e, uint8_t idx, uint8_t raw);   /* idx 0..134 */
void dsp_load_patch(dsp_t *d, dsp_engine e, const uint8_t p[135], uint32_t flags);
#define DSP_LOAD_FXLOCK 0x1u      /* non sovrascrive i campi della maschera FX lock (§2.8) */
void dsp_get_patch(const dsp_t *d, dsp_engine e, uint8_t out[135]);

void dsp_set_bpm(dsp_t *d, float bpm);
void dsp_set_master_volume(dsp_t *d, uint8_t v);     /* 0..99 */
void dsp_set_bass_volume  (dsp_t *d, uint8_t v);     /* 0..99 */
void dsp_set_velocity_sense(dsp_t *d, bool on);

void dsp_render16(dsp_t *d, float *L, float *R,
                  const float *drum_L, const float *drum_R);   /* bus batteria, può essere NULL */
size_t dsp_scope_read(dsp_t *d, float *dst, size_t max); /* copia dell'uscita per la vista React */
```

- **SND-031** L'API **NON DEVE** essere thread-safe: la chiama un solo thread, quello audio. Il passaggio degli eventi dal thread del `core` passa da una coda SPSC lock-free gestita da `platform` (vedi `50-piattaforma-flip.md`).
- **SND-032** `dsp_setpar` **DEVE** accettare solo `idx ≤ 134` e limitare il valore al range del parametro (§2.2); per gli indici 118–134 aggiorna l'oggetto RP del motore `[O: setter del firmware]`. Il valore scritto **DEVE** essere quello restituito da `dsp_get_patch`.
- **SND-033** `dsp_scope_read` **DEVE** fornire l'uscita master mono (media L/R), con decimazione 4:1, in un ring buffer di almeno 2048 campioni, senza bloccare il thread audio. Serve alla vista React (`30-interfaccia.md`).

### 1.5 Frequenza di controllo e smoothing

- **SND-040** Inviluppi, LFO, matrice di modulazione e conversioni dei parametri **DEVONO** essere calcolati una volta per blocco e per voce (3 kHz di frequenza di controllo a 48 kHz) `[D]`. Ampiezza del VCA, cutoff e guadagni degli oscillatori **DEVONO** essere interpolati linearmente dentro il blocco.
- **SND-041** I parametri continui modificati da `dsp_setpar` (cutoff, risonanza, guadagni, pan, mandate, parametri degli FX) **DEVONO** essere filtrati con un passa-basso a un polo con costante di tempo di 5 ms `[V → QA-SND-28]`. I parametri RP lo sono con 20 ms `[O: l'editor dell'originale ha introdotto lo smoothing di HEIGHT nella 0.1.12]`. Gli enum cambiano al confine di blocco, senza smoothing. Al caricamento di una patch i parametri delle voci valgono subito (le voci passano in coda e ripartono con la patch nuova, SND-112), mentre quelli di FX, delay e riverbero scorrono con i 5 ms: un salto del tap o del guadagno di un effetto in suono faceva clic (16/10/2026).

### 1.6 Livelli

- **SND-045** Ogni voce lavora con picco nominale ±1. La somma delle voci di un motore **DEVE** essere scalata di −12 dB (×0,25) prima degli FX, per lasciare spazio a 16 voci `[V → QA-SND-28]`.
- **SND-046** L'uscita master **DEVE** passare da un soft clipper senza latenza: lineare fino a ±0,89 (−1 dBFS), poi curva cubica fino a ±1 `[V → QA-SND-23]`. Il binario dell'editor dell'originale contiene un probabile compressore a 3 bande (`mbcpr3band`) dal ruolo ignoto `[O]`: Stame non lo implementa finché il ruolo non è chiarito.

---

## 2. Formato della patch

### 2.1 Il blocco da 135 byte

- **SND-101** Una patch **DEVE** essere un array di 135 byte raw, uguale per i tre modelli, con gli indici, i range e gli enum della §2.2 `[O: tabella Parinfo dell'editor 1.0.2 dell'originale = blocco del firmware 3.92]`. In C: `typedef struct { uint8_t p[135]; } snd_patch_t;` più un `enum` con gli indici (`SND_P_VER = 0`, …, `SND_P_RPTSTEREO = 134`).
- **SND-102** Ogni byte **DEVE** essere ≤ 127. Al caricamento i valori fuori range vengono limitati (`clamp`) al massimo del parametro, senza errore.
- **SND-103** Tutti i campi **DEVONO** essere conservati anche quando non sono usati dal modello attivo: oscillatori in RP, campi RP in VA, SHAPE in FM, P1–P6 di un FX con tipo OFF o intensità 0. I preset contano su slot FX "parcheggiati" (tipo scelto, intensità a 0) e l'interruttore FX alterna il tipo lasciando i valori `[O]`.
- **SND-104** `VER` (idx 0) **DEVE** valere 2 in ogni patch scritta da Stame. Una patch con `VER = 0` (formato vecchio) **DEVE** essere caricata così com'è, segnalando all'interfaccia che è "legacy": nel formato 0 l'elenco delle sorgenti della matrice era probabilmente diverso `[D]` `[V → QA-SND-25]`.

### 2.2 Mappa dei byte

Fonte: Parinfo dell'editor 1.0.2 dell'originale = firmware 3.92 `[O]`. "Def" è il default della tabella Parinfo; "INIT" è il valore scritto dalla patch INIT del modello (§2.5). Dove non diversamente indicato il range è 0–127.

| Idx | Nome | Range | Def | Significato e codifica |
|---:|---|---|---:|---|
| 0 | VER | 2 | 2 | Versione del formato (§2.1). |
| 1 | MODEL | 0–3 | 0 | 0 = VA, 1 = REED PIANO, 2 = FM; 3 = SMP, il campionatore di Stame (§7b), che nei byte 118…122 legge SMPSET, SMPLOOP, SMPSTART e SMPTUNE al posto dei parametri RP. |
| 2 | FMALG | 0–7 | 0 | Algoritmo FM, mostrato "1"–"8" (§6.3). |
| 3 | HIGHPASS | | 0 | Passa-alto di tastiera (§4.3). 0 = spento. |
| 4 | GLIDE | | 0 | Tempo di glide (§4.1). 0 = spento. |
| 5 | GLIDEMODE | 0–3 | 0 | 0 = POLY, 1 = POLY LEGATO, 2 = MONO, 3 = MONO LEGATO. |
| 6 | BENDRANGE | 0–12 | 2 | Semitoni del pitch bend. |
| 7 | UNISON | 0–4 | 0 | Unisono; nessun controllo nell'editor dell'originale (§5.5). |
| 8 | UDETUNE | | 0 | Detune dell'unisono; nessun controllo nell'editor dell'originale. |
| 9 | HPKT | | 0 | Keytrack del passa-alto di tastiera. |
| 10–14 | O1SHAPE, O1SEMI, O1DETUNE, O1PW, O1GAIN | | 1, 64, 64, 64, 64 | Oscillatore 1. SHAPE 0–3: OFF, SAW, PULSE, TRI. SEMI e DETUNE bipolari (64 = 0). In FM: PW = livello dell'operatore, GAIN = sensibilità alla velocity. |
| 15–19 | O2… | | 0, 64, 64, 64, 0 | Oscillatore 2, come sopra. |
| 20–24 | O3… | | 0, 64, 64, 64, 0 | Oscillatore 3, come sopra. |
| 25–29 | O4… | | 0, 64, 64, 64, 0 | Oscillatore 4, come sopra. |
| 30 | O4KT | 0–1 | 1 | 0 = FIXED, 1 = KEYTRACK. |
| 31 | O4SYNC | 0–1 | 0 | 0 = NORMAL, 1 = O3 SYNC (solo VA). |
| 32 | O4FB | | 0 | Feedback dell'operatore 4 (solo FM). |
| 33 | NOISE | | 0 | Livello del rumore. |
| 34 | PINK | 0–1 | 0 | 0 = WHITE, 1 = PINK. |
| 35–39 | E1A, E1H, E1D, E1S, E1R | | 0, 0, 64, 64, 64 | Inviluppo 1 (filtro). |
| 40–44 | E2A … E2R | | 0, 0, 64, 127, 64 | Inviluppo 2 (ampiezza). |
| 45–49 | E3A … E3R | | 0, 0, 64, 127, 64 | Inviluppo 3; l'editor dell'originale chiama "DELAY" il secondo stadio (§8.1). |
| 50–54 | E4A … E4R | | 0, 0, 64, 127, 64 | Inviluppo 4, come il 3. |
| 55–57 | L1SHAPE, L1RATE, L1MODE | 0–6, 0–127, 0–3 | 0, 0, 0 | LFO 1. SHAPE: SINE, TRI, SQU, SAW, SAW−, RAND, S&H. MODE: RESET, FREE, MONO, ONESHOT. |
| 58–60 | L2… | | 0, 0, 0 | LFO 2. |
| 61–63 | L3… | | 0, 0, 0 | LFO 3. |
| 64–66 | L4… | | 0, 0, 0 | LFO 4. |
| 67 | FTYPE | 0–3 | 1 | 0 = OFF, 1 = LOWPASS, 2 = BANDPASS, 3 = HIGHPASS. |
| 68 | CUTOFF | | 127 | Frequenza di taglio; è anche il "Filter" dell'encoder FX (§11). |
| 69 | RESONANCE | | 0 | Q; al massimo auto-oscilla `[M]`. |
| 70 | FENV | | 0 | Quantità di ENV1 sul cutoff (unipolare). |
| 71 | FVELO | | 0 | Velocity sul cutoff. |
| 72 | FKT | | 0 | Keytrack del cutoff. |
| 73 | GAIN | | 64 | Volume della patch. |
| 74 | GVELO | | 0 | Velocity sul volume. |
| 75 | PAN | | 64 | 0 = sinistra, 64 = centro. |
| 76–78 | M1S, M1D, M1A | 0–14, 0–33, 0–127 | 0, 0, 64 | Slot 1 della matrice: sorgente, destinazione, quantità bipolare (§8.3). |
| 79–99 | M2… M8 | | 0, 0, 64 | Slot 2–8, stessa struttura (stride 3). |
| 100 | FX1TYPE | 0–6 | 0 | OFF, CHORUS, ENSEMBLE, PHASER, FLANGER, DRIVE, TREMOLO. |
| 101–106 | FX1P1…FX1P6 | | 0 | Parametri di FX1, secondo il tipo (§10.3). |
| 107 | FX2TYPE | 0–7 | 0 | Come FX1, più 7 = DELAY. |
| 108–113 | FX2P1…FX2P6 | | 0 | Parametri di FX2. |
| 114 | REVSEND | | 0 | Mandata al riverbero. |
| 115 | REVSIZE | | 100 | Grandezza del riverbero. |
| 116 | REVLP | | 120 | Passa-basso sulla coda. |
| 117 | REVHP | | 10 | Passa-alto sulla coda. |
| 118 | RPHEIGHT | | 10 | RP: distanza verticale pickup–lamella. |
| 119 | RPDISTANCE | | 10 | RP: distanza orizzontale dal punto di colpo. |
| 120 | RPKT | | 64 | RP: keytrack del pickup. |
| 121 | RPICKUP | 0–3 | 0 | NORMAL, MELLOW, SHARP, ODD. |
| 122 | RPDECAY | | 110 | RP: smorzamento della lamella. |
| 123 | RPRELEASE | | 32 | RP: coda al rilascio. |
| 124 | RPTONE | | 64 | RP: tono, da scuro a brillante. |
| 125 | RPVELCURVE | | 90 | RP: effetto della velocity su tono e volume. |
| 126 | RPCLANK | | 32 | RP: quantità di clank. |
| 127 | RPCLANCURVE | | 32 | RP: dipendenza del clank dalla velocity. |
| 128 | RPCKT | | 32 | RP: keytrack del clank. |
| 129 | RPTREMOLO | | 0 | RP: profondità del tremolo interno. |
| 130 | RPTREMRATE | | 80 | RP: velocità del tremolo. |
| 131 | RPVOL | | 127 | RP: volume del modello, prima degli FX. |
| 132 | RPHAMMER | | 16 | RP: rumore del martelletto. |
| 133 | RPKEYOFF | | 16 | RP: rumore dello smorzatore al rilascio. |
| 134 | RPTSTEREO | | 0 | RP: tremolo stereo, 0 = mono, 127 = L e R in opposizione. |

- **SND-105** I nomi della colonna "Nome" **DEVONO** essere usati identici nei file `.inc` (con prefisso `TREBLE_`) e come identificatori nel codice e nell'interfaccia di edit.

### 2.3 Conversioni di presentazione

Servono all'interfaccia e agli editor; il `dsp` le espone come funzioni pure.

| Grandezza | Formula | Fonte |
|---|---|---|
| Percentuale come nell'editor dell'originale | `floor(raw * 100 / 127)` | `[O]` 92 → 72 %, 63 → 49 % |
| Bipolare come nell'editor dell'originale | `(raw − 64) / 1.28` % (±50 %) | `[M]` matrice ±50 % |
| Display dell'originale per Reverb e FX | `d = round(raw / 12.7)`; `d = 0` → "Off", altrimenti due cifre "01"–"10" | `[O]` 92 → 07, 63 → 05, 13 → 01, 0 → Off |
| Display dell'originale per Filter | raw a tre cifre, "000"–"127" | `[O]` |
| Normalizzazione verso un host | `raw / 127`; enum `indice / (n − 1)`; BENDRANGE `/ 12` | `[O]` |
| Tempo libero del delay in % | `round((raw − 3) / 124 * 100)` per raw ≥ 3 | `[O]` |

- **SND-106** Le formule della tabella **DEVONO** stare in un solo file (`dsp/present.c`) e l'interfaccia **DEVE** usare solo quelle.

### 2.4 Patch INIT

- **SND-110** Stame **DEVE** avere tre patch INIT, una per modello (`INIT - VA`, `INIT - REED PIANO`, `INIT - FM`), con i valori scritti dal frontend dell'editor 1.0.2 dell'originale `[O]`:
  - VER 2, MODEL scelto, FMALG 0, HIGHPASS / GLIDE / HPKT 0, GLIDEMODE POLY, BENDRANGE 2, UNISON e UDETUNE 0;
  - OSC1: SAW, SEMI / DETUNE / PW / GAIN 64; OSC2–4: OFF, SEMI / DETUNE / PW 64, GAIN 0;
  - O4KT KEYTRACK, O4SYNC 0, O4FB 0, NOISE 0, WHITE;
  - ENV1: A 0, H 0, D / S / R 64; ENV2–4: A 0, H 0, D 64, S 127, R 64;
  - LFO: tutti i campi a 0 (SINE, rate 0, RESET);
  - FTYPE LOWPASS, CUTOFF 127, RESONANCE / FENV / FVELO / FKT 0; GAIN 64, GVELO 0, PAN 64;
  - matrice: sorgente 0, destinazione OFF, AMT 64;
  - FX1 e FX2 OFF con P1–P6 a 0; REVSEND 0, REVSIZE 100, REVLP 120, REVHP 10;
  - campi RP: in `INIT - REED PIANO` HEIGHT 64, DISTANCE 64, KT 64, NORMAL, DECAY 110, RELEASE 32, TONE 64, VELCURVE 90, CLANK 32, CLANCURVE 32, CKT 32, TREMOLO 0, TREMRATE 80, VOL 64, HAMMER 16, KEYOFF 16, STEREO 0; negli altri due INIT i default Parinfo.
- **SND-111** All'avvio, se mancano i banchi di preset (§2.7), il Sound **DEVE** caricare `INIT - VA` e il Bass una patch di basso di Stame (§9).

### 2.5 File `.inc` dell'editor dell'originale

- **SND-120** Stame **DEVE** leggere e scrivere i file `.inc` dell'editor dell'originale `[M: 5 file reali distribuiti dal produttore]`. Formato esatto in scrittura:
  - ASCII senza BOM, **135 righe** separate da **CRLF**, **senza** a capo dopo l'ultima;
  - riga *i*: `0x` + due cifre esadecimali **maiuscole** + `,` + TAB + `//` + indice decimale + spazio + `TREBLE_` + nome (§2.2);
  - dimensione sempre **3414 byte**;
  - prefisso sempre `TREBLE_`, anche per una patch di basso: il file descrive un singolo motore.

```
0x02,	//0 TREBLE_VER
0x00,	//1 TREBLE_MODEL
…
0x10,	//133 TREBLE_RPKEYOFF
0x00,	//134 TREBLE_RPTSTEREO
```

- **SND-121** In lettura il parser **DEVE** essere tollerante: accetta LF o CRLF, esadecimale minuscolo, spazi al posto del TAB, a capo finale, prefissi `TREBLE_` o `BASS_`. Il valore viene preso dall'esadecimale e l'indice dalla posizione della riga; se il commento riporta un indice diverso dalla posizione, il file viene rifiutato. Un file con meno di 135 righe valide viene rifiutato.
- **SND-122** Lettura e riscrittura di un `.inc` valido scritto dall'editor dell'originale **DEVONO** dare un file identico byte per byte (test T-SND-20).

### 2.6 Maschera FX lock

- **SND-125** Con il flag `DSP_LOAD_FXLOCK`, `dsp_load_patch` **NON DEVE** sovrascrivere: FX1TYPE, FX1P1–P6, FX2TYPE, FX2P1–P6, REVSEND, REVSIZE, REVLP, REVHP, FTYPE, CUTOFF, RESONANCE, FENV, FVELO, FKT `[O: elenco letterale di shouldSkipFxParameter nell'editor dell'originale]`. Che l'FX lock dell'originale usi la stessa maschera non è verificato `[V → QA-SND-22]`.

### 2.7 Banchi di preset su disco

- **SND-130** Il repository e i pacchetti distribuiti di Stame **NON DEVONO** contenere i valori dei preset di fabbrica dell'originale. Se l'utente li possiede, li mette in una cartella dati (percorso in `50-piattaforma-flip.md`) e Stame li carica a runtime.
- **SND-131** Un banco è una cartella con un indice testuale `bank.idx` e un `.inc` per voce. Ogni riga dell'indice: `NN<TAB>Nome<TAB>file.inc<TAB>perform_mode<TAB>perform_amount` (gli ultimi due campi sono definiti in `10-accordi-e-performance.md`; per i bassi valgono 0). Banchi previsti:
  - `sound/`: 70 slot di fabbrica, numerati 01–70;
  - `bass/`: 12 slot di fabbrica, numerati 01–12;
  - `user/`: 30 slot User Sound, numerati U01–U30, che nella lista seguono i 70 di fabbrica `[M]`.
- **SND-132** Struttura del record di fabbrica nel firmware, a scopo documentale `[O]`: record da 40 byte con un puntatore ai 135 parametri a +0x20 e Perform e amount di default a +0x24 e +0x25; tabella dei Sound e tabella dei Bass separate. Stame non legge il firmware.
- **SND-133** Se il banco di fabbrica manca, Stame **DEVE** mostrare comunque i 70 nomi (§12) e caricare per ciascuno la patch INIT del modello indicato in §12, oppure una patch di Stame se esiste; l'interfaccia lo segnala.

---

## 3. Curve raw → grandezze fisiche

Il manuale dà solo percentuali `[M]`; le curve reali (Hz, ms) non sono note. Le curve qui sotto sono default di Stame da sostituire con misure (§14.4).

- **SND-150** Ogni conversione raw → grandezza fisica **DEVE** essere una tabella di 128 `float` in `dsp/curves.c`, generata dalle formule di questa sezione e sostituibile con una tabella misurata (CSV di 128 righe) senza toccare il resto del codice. Le grandezze modulate (matrice, keytrack) si interpolano linearmente tra due voci di tabella.

| Curva | Formula di default (`x = raw/127`) | Esempi | Etichetta |
|---|---|---|---|
| `T_att` attacco | `0.0005 + 1.5 * x^1.585` s | 64 → 0,50 s; 127 → 1,5 s | `[V → QA-SND-05]`, coerente con "50 % ≈ mezzo secondo, 100 % ≈ 1–2 s" `[M]` |
| `T_hold` hold / delay | `2.0 * x^1.585` s | 127 → 2 s | `[V → QA-SND-05]` |
| `T_dec` decay e release | `0.002 + 6.0 * x^1.585` s (tempo per −60 dB) | 102 → 4,2 s | `[V → QA-SND-05]`, coerente con "release 80–100 % = alcuni secondi" `[M]` |
| `T_glide` | 0 → spento; `0.003 + 2.0 * x^1.585` s (tempo per arrivare a −60 dB dall'intervallo) | | `[V → QA-SND-07]` |
| `f_lfo` rate LFO | interpolazione logaritmica tra i punti (x, Hz): (0; 0,033), (0,2; 0,1), (0,3; 1), (0,6; 4), (0,7; 8), (1; 60) | 0 → 30 s/ciclo | `[V → QA-SND-06]`, coerente con le fasce del manuale `[M]` |
| `f_cut` cutoff | `20 * 1000^x` Hz, limitato a `0.45 * fs` | 64 → 640 Hz; 1 passo ≈ 0,94 semitoni | `[V → QA-SND-04]` |
| `k_res` risonanza | `k = √2 * (1 − x^0.8)` (smorzamento dell'SVF): raw 0 = Butterworth, −3 dB a `f_cut` come chiede T-SND-06; 127 → auto-oscillazione | 0 → k 1,414 (Q 0,71) | `[V → QA-SND-04]`; auto-oscillazione `[M]`. Il 15/10/2026 il fattore 2 è diventato √2: con k = 2 a `f_cut` c'erano −6 dB, in contrasto con T-SND-06 |
| `f_hp` passa-alto di tastiera | 0 → bypass; `20 * 100^x` Hz | 127 → 2 kHz | `[V → QA-SND-04]` |
| `g_vol` GAIN di patch, RPVOL | `(raw / 64)^2` | 64 → 0 dB; 127 → +11,9 dB | `[V → QA-SND-28]` |
| `g_osc` GAIN dell'oscillatore VA | `raw / 64` | 64 → 0 dB; 127 → +6 dB | `[V → QA-SND-28]` |
| `g_lin` livelli generici (NOISE, mandate) | `x` | | `[V → QA-SND-28]` |
| `g_master` volume 0–99 | `(v / 99)^2` | 0 → silenzio | `[V → QA-SND-28]` |
| `f_fx_rate` rate di chorus, phaser, flanger, tremolo | `0.05 * 200^x` Hz | 127 → 10 Hz | `[V → QA-SND-20]` |
| `t_delay_free` tempo libero del delay | raw 3–127: `0.010 * 150^((raw − 3) / 124)` s | 127 → 1,5 s | `[V → QA-SND-08]` |
| `t_rp_decay` | `0.3 * (20 / 0.3)^x` s (T60 della fondamentale a C4) | 127 → 20 s | `[V → QA-SND-15]` |
| `t_rp_release` | `0.02 * (3 / 0.02)^x` s (T60 dopo il rilascio) | | `[V → QA-SND-15]` |
| `f_rp_trem` | `0.5 * 24^x` Hz | 80 → 3,7 Hz | `[V → QA-SND-15]` |

---

## 4. Parte comune: pitch, tastiera, filtro, amplificatore

Valida per VA e FM; per RP vedi §7.3.

### 4.1 Pitch, bend, glide e modi di tastiera

- **SND-201** Pitch dell'oscillatore *n* in semitoni MIDI:
  `p_n = nota + (SEMI_n − 64) + (DETUNE_n − 64) / 64 + bend + glide_off + mod_pitch + mod_osc_n`
  dove `bend = BENDRANGE * pb / 8192`. Frequenza: `440 * 2^((p − 69) / 12)`. SEMI in semitoni `[D]`; DETUNE ±64 raw = ±1 semitono, circa 1,56 cent per passo `[D]` `[V → QA-SND-29]`.
- **SND-202** Con `O4KT = FIXED`, l'oscillatore 4 **DEVE** ignorare la nota, il bend e il glide: `p_4 = 60 + (SEMI_4 − 64) + (DETUNE_4 − 64) / 64 + mod_osc_4` `[V → QA-SND-14]`. La modulazione PITCH globale si applica comunque.
- **SND-203** Glide (`GLIDE > 0`): lo scostamento `glide_off` parte dalla differenza tra l'ultima nota suonata sul motore e la nuova, e decade esponenzialmente a 0 con il tempo `T_glide` `[V → QA-SND-07]`. In POLY ogni nuova voce parte dall'ultima nota del motore; alla prima nota dopo l'accensione non c'è glide.
- **SND-204** Modi di tastiera (`GLIDEMODE`) `[M]` per i comportamenti, `[V → QA-SND-31]` per i dettagli:
  - **POLY**: ogni nota una voce, inviluppi riattaccati.
  - **POLY LEGATO**: ogni nota una voce; se sul motore c'è già almeno un tasto tenuto, la nuova voce parte con inviluppi in decay/sustain al livello corrente della voce più recente, senza attacco.
  - **MONO**: una voce sola, priorità all'ultima nota, inviluppi riattaccati a ogni nota; al rilascio torna all'ultima nota ancora tenuta.
  - **MONO LEGATO**: come MONO, ma gli inviluppi si riattaccano solo se prima erano stati rilasciati tutti i tasti.
- **SND-205** Sustain (`dsp_sustain`): con il pedale premuto i note-off vengono memorizzati e applicati al rilascio del pedale. Ogni motore ha il suo sustain `[O]`.

### 4.2 Filtro per voce

- **SND-210** Ogni voce **DEVE** avere un filtro **state variable a 2 poli (12 dB/ottava) in topologia TPT**, con uscite LP, BP e HP scelte da `FTYPE`; `FTYPE = OFF` = bypass `[D: un solo enum LP/BP/HP suggerisce un SVF]` `[V → QA-SND-04]`.
- **SND-211** Cutoff efficace in unità raw, poi convertito con `f_cut`:
  `c = CUTOFF + 127 * ENV1 * FENV / 127 + FVELO * v * 0.5 + (FKT / 127) * 1.058 * (nota − 60) + mod_cutoff`
  - FENV è unipolare (127 = +127 raw, circa +10 ottave con inviluppo pieno) `[V → QA-SND-04]`;
  - FKT 127 = 100 % di keytrack (1,058 raw per semitono = un'ottava per ottava), centrato su C4 `[V → QA-SND-04]`.
- **SND-212** La risonanza `k_res` a 127 **DEVE** portare il filtro in auto-oscillazione stabile `[M]`: lo stato del passa-banda passa da una saturazione `tanh` che limita l'ampiezza a circa ±1.
- **SND-213** I coefficienti (`g = tan(π f / fs)`) si calcolano una volta per blocco e si interpolano linearmente dentro il blocco. `tan` può essere un'approssimazione con errore < 0,1 % sotto `0.45 fs`.

### 4.3 Passa-alto di tastiera

- **SND-215** `HIGHPASS > 0` **DEVE** inserire, dopo il filtro, un passa-alto a 1 polo (6 dB/ottava) con frequenza `f_hp`, spostata da HPKT come il keytrack del filtro (127 = un'ottava per ottava, centro C4) `[M: "passa-alto leggero"]` `[V → QA-SND-04]`.

### 4.4 Amplificatore, velocity e pan

- **SND-220** Guadagno della voce: `a = ENV2 * g_vol(GAIN + mod_volume) * vel_gain`, con `vel_gain = (1 − s) + s * v^2` e `s = GVELO / 127` `[V → QA-SND-26]`.
- **SND-221** Pan a potenza costante: `θ = (PAN + mod_pan) / 127 * π/2`, `L = cos θ`, `R = sin θ`, normalizzato in modo che PAN 64 dia −3 dB per canale.
- **SND-222** Con Velocity Sense spento (opzione del `core`) il `dsp` **DEVE** usare velocity 100 per tutte le note `[V → QA-SND-26]`.

---

## 5. Modello VA

### 5.1 Schema a blocchi

```
 OSC1 ──┐
 OSC2 ──┤  ×g_osc(GAINn)
 OSC3 ──┼──────────────► Σ ─► SAT ─► FILTRO SVF ─► HP tastiera ─► VCA ─► PAN ─► bus del motore
 OSC4 ──┤                     tanh   (FTYPE)        (HIGHPASS)    ENV2·GAIN·vel
 NOISE ─┘ ×NOISE                       ▲ CUTOFF, Q, ENV1·FENV, FVELO, FKT
   OSC3 ──sync──► OSC4 (O4SYNC)
```

`[M]` per l'ordine oscillatori → mixer → filtro → amplificatore → effetti; `[D]` per la posizione del passa-alto e della saturazione.

### 5.2 Oscillatori

- **SND-250** Ogni oscillatore **DEVE** generare SAW, PULSE o TRI limitati in banda: PolyBLEP per SAW e PULSE, PolyBLAMP (o equivalente) per TRI. SHAPE = OFF = uscita nulla e calcolo saltato `[M]`.
- **SND-251** SAW è una rampa crescente da −1 a +1. PULSE ha duty `d = (PW + mod_pw·127) / 127`, limitato a [0, 1], ed è privo di componente continua (si sottrae la media `2d − 1`): così PW 0 e 127 danno silenzio, PW 64 un'onda quadra `[M]`. PW non agisce su SAW e TRI `[V → QA-SND-27]`. Il duty si interpola per campione dentro il blocco, come i guadagni: a gradini di 16 campioni una modulazione di PW ronzava a 3 kHz (16/10/2026).
- **SND-252** Fase iniziale alla nota: casuale per gli oscillatori VA (comportamento "analogico") `[V → QA-SND-27]`, salvo O4 con sync attivo che riparte con l'OSC3.
- **SND-253** Hard sync (`O4SYNC = 1`, solo VA): a ogni ciclo dell'OSC3 la fase dell'OSC4 **DEVE** ripartire da 0, con correzione BLEP alla posizione frazionaria del reset `[M]`.
- **SND-254** L'accumulatore di fase è `float` in [0, 1); niente `double` nel percorso audio.

### 5.3 Rumore

- **SND-260** NOISE: bianco da xorshift32 normalizzato a ±1; rosa con il filtro di Paul Kellet (versione economica a 3 poli) sul bianco. Livello `g_lin(NOISE + mod_noise)`, sommato nel mixer `[M]`.

### 5.4 Mixer

- **SND-265** Il mixer somma i 4 oscillatori (×`g_osc`) e il rumore, poi applica `y = 1.5 * tanh(x / 1.5)`: trasparente con un oscillatore a GAIN 64, distorce con più oscillatori alti, come avverte il manuale `[M]` `[V → QA-SND-28]`.

### 5.5 Unisono

- **SND-270** UNISON e UDETUNE **DEVONO** essere conservati ma ignorati dal suono: nessun preset li usa e l'editor dell'originale non li espone `[O]` `[V → QA-SND-19]`. La sorgente di matrice UNISON vale 0.

---

## 6. Modello FM

### 6.1 Schema a blocchi

```
        ┌────────── algoritmo FMALG (§6.3) ──────────┐
 OP4 ◄─┐│  OP4 ─► OP3 ─► OP2 ─► OP1 ─► (portanti)    │
  FB ──┘└────────────────────────────────────────────┘
 Σ portanti ─► Σ con NOISE ─► FILTRO SVF ─► HP tastiera ─► VCA ─► PAN ─► bus del motore
```

Inviluppi, LFO, matrice, filtro e amplificatore sono quelli comuni (§4, §8) `[M]`. Non ci sono inviluppi per operatore.

### 6.2 Operatori

- **SND-300** 4 operatori sinusoidali in modulazione di fase. Frequenza dell'operatore *i* come in SND-201 (SEMI e DETUNE dell'oscillatore *i*), quindi i rapporti sono in semitoni temperati: +12 = 2:1, +19 ≈ 2,997:1 `[D]`. O4KT = FIXED vale anche in FM (SND-202).
- **SND-301** Campi riusati in FM `[O: etichette del frontend dell'editor dell'originale]`:
  - `OnPW` = **livello** dell'operatore (GAIN);
  - `OnGAIN` = **sensibilità alla velocity** (VELOCITY);
  - `O4FB` = feedback dell'operatore 4;
  - `OnSHAPE` **DEVE** essere ignorato `[D: preset FM con SHAPE residui suonano come se fossero tutti attivi]` `[V → QA-SND-13]`.
- **SND-302** Ampiezza dell'operatore: `L_i = (lv_i / 127)^2 * ((1 − s_i) + s_i * v)`, con `lv_i = OnPW + mod_level_i`, `s_i = OnGAIN / 127` `[V → QA-SND-12]`.
- **SND-303** Uscita: `o_i = L_i * sin(2π φ_i + I_max * Σ_j o_j)` sui modulatori *j* di *i*, con `I_max = 4π` `[V → QA-SND-12]`. Le portanti si sommano senza normalizzazione. Gli operatori si calcolano in ordine topologico (modulatori prima delle portanti).
- **SND-304** Feedback dell'OP4: `o_4 = L_4 * sin(2π φ_4 + β * (o_4[n−1] + o_4[n−2]) / 2)`, con `β = 1.5π * O4FB / 127` `[V → QA-SND-12]`. Il manuale: 20–40 % arricchisce, 60–80 % metallico, 90–100 % quasi rumore `[M]`.
- **SND-305** Alla nota le fasi di tutti gli operatori ripartono da 0 `[V → QA-SND-27]`.
- **SND-306** Il seno **DEVE** venire da una tabella di 2048 punti con interpolazione lineare, oppure da un polinomio con errore < −90 dB.

### 6.3 Algoritmi

Il testo del manuale descrive 8 routing con l'OSC 4 come portante `[M]`, ma i preset di fabbrica sono compatibili con una numerazione **speculare** (portante OP1) per gli algoritmi "1", "2", "5", "6", mentre "8" si comporta come 4 portanti in parallelo `[D]`. La fonte giusta sono i diagrammi `FM1.png`–`FM8.png` dentro l'editor dell'originale, non ancora visti.

- **SND-310** Stame **DEVE** implementare questa tabella, definita in un solo punto del codice per poterla correggere `[V → QA-SND-11]`:

| FMALG raw | Display | Modulazioni (→ = modula) | Portanti | Base |
|---:|---|---|---|---|
| 0 | 1 | 4 → 3 → 2 → 1 | 1 | speculare del manuale `[D]` |
| 1 | 2 | 2, 3, 4 → 1 | 1 | speculare `[D]` |
| 2 | 3 | 4 → 2, 3 → 1 | 1, 2 | speculare `[D]` |
| 3 | 4 | 4 → 2, 3 → 2, 2 → 1 | 1 | ipotesi di scambio 4 ↔ 8 `[V]` |
| 4 | 5 | 4 → 3, 2 → 1 | 1, 3 | speculare `[D]` |
| 5 | 6 | 4 → 3 → 1, 2 → 1 | 1 | speculare `[D]` |
| 6 | 7 | 4 → 1, 4 → 2, 4 → 3 | 1, 2, 3 | scelta di Stame: il testo del manuale ripete l'algoritmo 1 `[V]` |
| 7 | 8 | nessuna | 1, 2, 3, 4 | dai preset (organi) `[D]` |

- **SND-311** Il feedback agisce sempre sull'OP4, qualunque sia l'algoritmo `[M]`.

### 6.4 Destinazioni della matrice in FM

- **SND-315** In FM le destinazioni della matrice agiscono così `[V → QA-SND-12]`:
  - `GAINn` → livello dell'operatore *n* (in raw, sommato a `OnPW`) `[D: i preset FM usano GAINn come keyboard scaling dei modulatori]`;
  - `PW1`–`PW3` → livello dell'operatore, come `GAINn`;
  - `PW4/FB` → `O4FB` `[O: etichetta del frontend]`;
  - `OSCn` → pitch dell'operatore *n*.

---

## 7. Modello Reed Piano

Modello fisico di piano elettrico a lamelle anni '60, con campioni dei rumori meccanici nell'originale `[M]`. L'implementazione interna non è nota: lo schema qui sotto è un modello di Stame che rispetta il significato dei 17 parametri `[V → QA-SND-15]`.

### 7.1 Schema a blocchi

```
 note-on ─► martelletto (vel, VELCURVE) ─► modi della lamella (3 risonatori, DECAY, KT)
                                              │
                                              ▼
                                  PICKUP non lineare (HEIGHT, DISTANCE, RPKT, tipo)
                                              │
 CLANK (2 risonatori brevi) ──────────────────┤
 HAMMER (rumore filtrato, note-on) ───────────┤
 KEY OFF (rumore filtrato, note-off) ─────────┤
                                              ▼
                                    TONE (tilt) ─► ×RPVOL·GAIN ─► PAN ─► Σ voci
                                                                          │
                              oggetto RP del motore: TREMOLO stereo ◄─────┘ ─► FX1 ─► FX2
```

### 7.2 Componenti

- **SND-350** **Lamella**: tre risonatori a 2 poli eccitati da un impulso alla nota:
  - modo 0: frequenza `f0` della nota, ampiezza 1, T60 = `t_rp_decay(RPDECAY) * 2^(−(nota − 60) / 24)`;
  - modo 1: `6.267 * f0`, ampiezza `0.08 * h`, T60 / 6;
  - modo 2: `17.55 * f0`, ampiezza `0.02 * h`, T60 / 20;
  - un modo sopra `0.45 fs` non si calcola. `h` è la brillantezza del colpo: `h = (1 − s) + s * v`, con `s = RPVELCURVE / 127`.
  I rapporti sono quelli di una trave a sbalzo `[D]`.
- **SND-351** **Ampiezza del colpo**: `A = (1 − s) + s * v^1.5`, con `s = RPVELCURVE / 127` (il manuale consiglia 60–90 %) `[M]` per il significato, `[V]` per la formula. Nel codice A sta sull'impulso che eccita i risonatori, non sull'uscita: per un colpo è lo stesso (i risonatori sono lineari), ma una ribattuta più piano della stessa nota non scala la coda ancora in suono, che era un clic (revisione del 16/10/2026) `[D]`.
- **SND-352** **Pickup**: `y = Φ(A·x + d) − Φ(d)` con `Φ(u) = u / sqrt(u² + h_p²)`:
  - `h_p = (1.5 − 1.3 * HEIGHT / 127) * 2^((RPKT / 127) * (nota − 60) / 24)`: HEIGHT più alto = pickup più vicino = più forte e brillante `[M]`;
  - la voce toglie la **componente continua** del pickup con un blocco DC a un polo a 12 Hz (−0,2 dB a 65 Hz): con `d ≠ 0` la curva è asimmetrica e ogni nota lasciava una continua fino al 60 % del valore medio, che dimezzava l'headroom, faceva un tonfo sulle dissolvenze e girava nel delay (revisione del 16/10/2026) `[D]`;
  - `d = 0.8 * RPDISTANCE / 127`: l'asimmetria aggiunge armoniche, come chiede il manuale per i valori alti `[M]`;
  - tipi: **NORMAL** come sopra; **MELLOW** con `h_p × 1,3` e passa-basso a 1 polo a 1,2 kHz; **SHARP** con `h_p × 0,7` e shelving +6 dB sopra 2 kHz; **ODD** con `Φ(u) = 0.6 * sin(2.5 * u / h_p)` (wavefolder, armoniche "strane", lo-fi) `[M]` per il carattere, `[V]` per le formule.
- **SND-353** **Rilascio**: al note-off (o al rilascio del sustain) i T60 di tutti i modi diventano `min(T60, t_rp_release(RPRELEASE))`.
- **SND-354** **Clank**: due risonatori a 2,1 kHz e 3,4 kHz × `2^((RPCKT / 127) * (nota − 60) / 48)`, T60 60 ms, ampiezza `0.3 * RPCLANK / 127 * ((1 − c) + c * v^2)` con `c = RPCLANCURVE / 127`.
- **SND-355** **Rumori**: l'originale usa campioni `[M]`; Stame li sintetizza e **PUÒ** caricare campioni WAV dell'utente al loro posto:
  - HAMMER: rumore bianco in un passa-banda a 2 kHz (Q 1), decadimento 8 ms, livello `0.3 * RPHAMMER / 127 * v`;
  - KEY OFF: rumore bianco in un passa-banda a 400 Hz (Q 0,7), decadimento 25 ms, livello `0.2 * RPKEYOFF / 127`, al rilascio effettivo dello smorzatore.
- **SND-356** **TONE**: tilt EQ a 1 polo con perno a 800 Hz, da −12 dB a +12 dB sugli acuti (64 = piatto).
- **SND-357** **Tremolo interno**, nell'oggetto RP del motore (uno per motore, non per voce) `[O]`: guadagno `g_L = 1 − D * (1 − cos φ) / 2`, `g_R` uguale con fase `φ + π * RPTSTEREO / 127`; `D = RPTREMOLO / 127`, rate `f_rp_trem(RPTREMRATE)`. Si applica alla somma delle voci RP del motore, prima di FX1.
- **SND-358** Volume: `g_vol(RPVOL)` per voce, prima degli FX `[M]`.

### 7.3 Cosa resta attivo in RP

Le fonti divergono: il manuale dice che spariscono oscillatori, filtro e parte della tastiera e restano inviluppi, LFO, Reverb e FX `[M]`; l'editor 1.0.2 dell'originale nasconde anche inviluppi, LFO, NOISE, KEYBOARD e matrice `[O]`.

- **SND-360** In RP Stame **DEVE** applicare `[V → QA-SND-15]`:
  - **sì**: GAIN, PAN, BENDRANGE, GLIDEMODE, matrice e LFO limitati alle destinazioni PITCH, VOLUME e PAN, FX1, FX2, REVSEND;
  - **no**: oscillatori, NOISE, filtro (bypass), HIGHPASS, GLIDE, GVELO, ENV2 come VCA (l'ampiezza la decide il modello), le altre destinazioni della matrice.
- **SND-361** Un flag di compilazione `STAME_RP_FILTER` **DEVE** permettere di attivare il filtro anche in RP, per i test d'ascolto di QA-SND-15.

---

## 7b. Modello SMP: il campionatore di Stame

Aggiunta di Stame, decisa il 15/10/2026 (Luigi: «se possibile scarica e aggiungi dei samples magari di strumenti noti»; regola «tutto l'originale, e di più»). L'originale non ha un campionatore: il modello esiste solo nelle patch di Stame (MODEL = 3) e non altera gli altri tre. `src/dsp/smp.c`, `tools/campioni.py`, test T-SND-50…54 (`tests/unit/test_smp.c`).

### 7b.1 Schema

```
 note-on ─► zona del set (nota, velocity) ─► lettura a 4 punti (Hermite) al passo rate/fs · 2^(semi/12)
                                                     │  loop: da loop_end si torna a loop_start (dissolvenza già nel file)
                                                     ▼
                                   catena comune: filtro SVF, passa-alto, ENV2 come VCA, matrice, LFO, pan ─► FX1 ─► FX2
```

- **SND-370** Una patch con MODEL = 3 **DEVE** usare la catena comune del VA (filtro, passa-alto, inviluppi, LFO, matrice, GAIN, GVELO, PAN, FX) con il campione al posto degli oscillatori: NOISE, O1…O4, FM e le destinazioni degli oscillatori non hanno effetto. Il rumore della sezione VA resta disponibile (NOISE).
- **SND-371** Nei byte RP la patch SMP legge: **SMPSET** = RPHEIGHT (118), l'indice del set nel banco; **SMPLOOP** = RPDISTANCE (119): 0 = il loop della zona se c'è, 1 = sempre one-shot; **SMPSTART** = RPKT (120): inizio della lettura fino al 25 % della zona (mai oltre il loop_start); **SMPTUNE** = RPDECAY (122): ±50 cent (64 = 0). La patch INIT del modello: SMPSET 0, SMPLOOP 0, SMPSTART 0, SMPTUNE 64, FTYPE OFF, E2R 50.
- **SND-372** Il **banco** è un blob in sola lettura che la piattaforma carica prima che l'audio parta (`stame.smp` accanto al binario sulla Flip; `build/campioni/stame.smp` o `STAME_SMP` nel render) e che non cambia mentre si suona: le voci tengono puntatori dentro di esso. Senza banco una nota SMP tace e la voce si libera subito; l'avvio lo scrive nel log.
- **SND-373** La **zona** di una nota è quella del set che copre la nota (lo…hi) con il layer di velocity più alto (`vel_lo`) non superiore alla velocity; il passo di lettura è `rate / fs · 2^((pitch − root + tune) / 12)` con `pitch` la nota con bend, glide e matrice PITCH, ricalcolato a ogni blocco. La lettura interpola a 4 punti (Hermite); oltre la fine del one-shot la voce scrive zeri e si libera anche se la nota è tenuta; in loop continua finché ENV2 non finisce il rilascio.
- **SND-374** Formato del file `stame.smp` (little-endian): testa di 20 byte (`"STMP"`, u16 versione = 1, u16 n_set, u16 n_zone, u16 0, u32 offset dei dati (multiplo di 4), u32 numero di campioni); n_set record da 32 byte (nome 24 byte terminato da 0, u16 prima zona, u16 numero di zone, u16 flag: bit 0 = loop, u16 0); n_zone record da 32 byte (u32 offset in campioni, u32 lunghezza ≥ 4, u32 loop_start, u32 loop_end (0 = one-shot), u32 rate 8000…96000, f32 gain 0…16, u8 root, lo, hi, vel_lo); poi i campioni int16 mono. Limiti del lettore: 64 set, 640 zone. Un loop deve stare nella zona e durare almeno 16 campioni (`SMP_LOOP_MIN`, il passo di lettura massimo), così un salto indietro per campione basta; i controlli si fanno senza somme che girano in 32 bit (revisione del 15/10/2026: un loop_start vicino a 2³² passava e faceva leggere fuori dal banco). Un file non valido si rifiuta per intero.
- **SND-375** `tools/campioni.py` costruisce il banco solo da campioni **CC0** (VCSL, Sonic Pi) e scrive `assets/campioni/FONTI.md` con ogni file e la sua licenza, e `src/platform/vetrina/campioni_idx.h` con gli indici dei set per le patch. Il banco non entra nel repo (si rigenera); va nel pacchetto della Flip. Preparazione: mono, senza continua, 32 kHz, testa tagliata a −45 dBFS, picco a −1 dBFS; one-shot tagliati sotto −66 dBFS con dissolvenza di 30 ms; loop cercato fra 0,4 e 1,5 s dalla fine con la giunzione più simile e dissolvenza di 30 ms incollata nel file, più 2 campioni oltre loop_end per l'interpolazione.
- **SND-376** Set del banco (seconda versione, 15/10/2026; con il kit techno 46 set, 546 zone, ≈ 94 MB a 32 kHz): 42 strumenti di VCSL — pianoforti (`piano_kawai`, `piano_upright`, `upright_knight`, `tx_piano`, `fm_piano`, `clavisynth`), clavicembali (`harpsichord`, `harpsi_italian`, `harpsi_lute`), organi (`organ`, `organ_loud`, `organ_ren`, `organ_full`, in loop), fiati in loop (`recorder`, `recorder_sop`, `recorder_ten`, `recorder_bass`, `ocarina`, `harmonica`, `harmonica_chrom`, `sax`, `saxello`, `didgeridoo`), corde (`harp`, `strumstick`, `dan_tranh`, `psaltery_bow` in loop, `psaltery_pluck`), lamellofoni (`kalimba`, `mbira`, `nyunga`, `kalimba_kenya`), percussioni intonate (`vibes`, `vibes_bowed` in loop, `marimba`, `balafon`, `xylophone`, `glock`, `tub_glock`, `chimes`, `hand_chimes`), `wine_glasses` in loop — e i kit `kit_studio`, `kit_jazz`, `kit_808`, `kit_techno` (§10.6, SND-537). Per l'hardware dedicato servirà un banco ridotto `[D]`.
- **SND-376a** La nota di ogni zona viene dal nome del file più la convenzione d'ottava del set (colonna `oct` di `STRUMENTI`: VCSL chiama «C4» il Do5, i nomi scientifici valgono 0, i nomi Yamaha del TX81Z +12, il Clavisynth suona un'ottava sopra la tastiera, il glockenspiel a tubi è nominato a caso), e `tools/campioni.py` la **verifica misurando la fondamentale** di ogni campione: un setaccio armonico sullo spettro (vince il candidato che spiega meglio i picchi, con penali per le armoniche mancanti e per i picchi fuori serie) confermato dall'autocorrelazione. La misura non sposta mai una zona da sola: se almeno due terzi delle zone attendibili di un set contraddicono la convenzione della stessa ottava, cambia la convenzione del set, con un avviso; i set dai parziali inarmonici (campane, lamelle, barre) non votano. Il primo banco aveva gli acuti sopra 2 kHz un'ottava sotto per un limite dell'autocorrelazione: da qui la regola.
- **SND-377** Costo per voce `[D]`: ~40 cicli/campione (lettura e Hermite) più la catena comune; sta dentro il budget di SND-700.

---

## 8. Modulazioni

### 8.1 Inviluppi

- **SND-400** Ogni voce **DEVE** avere 4 inviluppi AHDSR: ENV1 → filtro (via FENV), ENV2 → VCA, ENV3 ed ENV4 liberi per la matrice `[M]`.
- **SND-401** Forma `[V → QA-SND-05]`:
  - attacco lineare da 0 a 1 in `T_att(A)` (riparte dal livello corrente se la voce viene riattaccata);
  - hold a 1 per `T_hold(H)`;
  - decay esponenziale verso `S = raw / 127` con tempo `T_dec(D)` per −60 dB;
  - release esponenziale verso 0 con `T_dec(R)`, dal livello corrente.
- **SND-402** Per ENV3 ed ENV4 l'editor dell'originale chiama il secondo stadio **DELAY** invece di HOLD `[O]`. Default di Stame: è un HOLD come per ENV1 ed ENV2 `[V → QA-SND-16]`. Il codice **DEVE** prevedere la variante DADSR (ritardo prima dell'attacco), attivabile con un flag.
- **SND-403** Le destinazioni `ENVnT` scalano tutti i tempi dell'inviluppo *n* per `2^(4m)`, con `m` la modulazione (§8.3): positivo = più lento `[V → QA-SND-18]`. Le destinazioni `ENVnS` agiscono sul sustain in raw.

### 8.2 LFO

- **SND-410** Ogni motore **DEVE** avere 4 LFO con uscita bipolare −1…+1 e frequenza `f_lfo(LnRATE + mod_rate)`. Non hanno una profondità propria: la si dosa con la matrice `[M]`. Non c'è sync al tempo `[O]`.
- **SND-411** Forme `[M]`: SINE; TRI; SQU; SAW = sale piano e scende di colpo; SAW− = il contrario; RAND = valore casuale nuovo a ogni ciclo, raccordato linearmente; S&H = valore casuale a gradini `[V → QA-SND-17]` per la differenza tra RAND e S&H.
- **SND-412** Modi `[M]` per il significato, `[D]` per l'implementazione:
  - **RESET**: un LFO per voce, fase 0 a ogni note-on (il seno parte da 0 salendo);
  - **FREE**: un LFO per motore, che corre libero e non si riavvia mai `[V → QA-SND-17]`;
  - **MONO**: un LFO per motore, riavviato da `dsp_chord_start`, cioè uno per accordo condiviso dalle sue voci. Con il MIDI in ingresso si riavvia al primo note-on dopo che tutti i tasti del motore sono stati rilasciati;
  - **ONESHOT**: come RESET, ma si ferma dopo un ciclo e tiene il valore finale.

### 8.3 Matrice di modulazione

- **SND-420** Ogni voce **DEVE** valutare 8 slot `(MnS, MnD, MnA)`. Contributo di uno slot: `m = src * amt(MnA)`, con `amt(r) = sign(r − 64) * ((|r − 64|) / 64)^2` (curva quadratica, ±1 agli estremi) `[V → QA-SND-18]`. Più slot sulla stessa destinazione si sommano.

**Sorgenti (`MnS`)** `[O]` per l'elenco, `[M]` per il significato

| raw | Sorgente | Valore |
|---:|---|---|
| 0 | KEYTRACK | `(nota − 60) / 60`, bipolare |
| 1 | VELOCITY | `v`, 0…1 |
| 2 | UNISON | indice nello stack di unisono; 0 finché l'unisono è ignorato (SND-270) |
| 3 | RANDOM | valore casuale −1…+1 fissato al note-on |
| 4–7 | LFO1–LFO4 | −1…+1 |
| 8–11 | ENV1–ENV4 | 0…1 |
| 12 | WHEEL | mod wheel 0…1 |
| 13 | BEND | pitch bend −1…+1 |
| 14 | ? | non documentata; vale 0 `[V → QA-SND-18]` |

**Destinazioni (`MnD`)** `[O]` per l'elenco; scale `[V → QA-SND-18]`. "raw" = si somma `m * 127` al raw del parametro, si limita a 0–127 e si converte con la curva del parametro.

| raw | Destinazione | Effetto per `m = ±1` |
|---:|---|---|
| 0 | OFF | — |
| 1 | PITCH | ±12 semitoni su tutti gli oscillatori |
| 2, 5, 8, 11 | OSC1–OSC4 | ±12 semitoni sull'oscillatore |
| 3, 6, 9 | PW1–PW3 | duty ±0,5 (VA); livello dell'operatore (FM, §6.4) |
| 12 | PW4/FB | duty ±0,5 (VA); O4FB in raw (FM) |
| 4, 7, 10, 13 | GAIN1–GAIN4 | raw su `OnGAIN` (VA); livello dell'operatore (FM) |
| 14 | GLIDE | raw su GLIDE |
| 15 | CUTOFF | raw sul cutoff efficace |
| 16 | Q | raw su RESONANCE |
| 17 | VOLUME | raw su GAIN (idx 73) |
| 18 | PAN | raw su PAN |
| 19–22 | LFO1–LFO4 | raw sul rate dell'LFO |
| 23, 25, 27, 29 | ENV1T–ENV4T | scala dei tempi (SND-403) |
| 24, 26, 28, 30 | ENV1S–ENV4S | raw sul sustain |
| 31, 32 | MOD7, MOD8 | si somma `m` alla quantità (dopo la curva) dello slot 7 o 8, limitata a ±1 |
| 33 | NOISE | raw su NOISE |

- **SND-421** Ordine di valutazione per blocco: prima i valori delle sorgenti (inviluppi e LFO del blocco), poi gli slot che puntano a MOD7 o MOD8 con le quantità non modulate, poi tutti gli altri slot con le quantità di 7 e 8 già modulate. Niente ricorsione: uno slot che modula sé stesso usa la sua quantità non modulata `[D]`.
- **SND-422** Le modulazioni di LFO rate e di ENVnT valgono per voce; per gli LFO condivisi (FREE, MONO) si usa la modulazione della voce più recente del motore `[D]`.

### 8.4 Controller

- **SND-430** Pitch bend, mod wheel e sustain sono per motore `[O]`. `dsp_reset_controllers` azzera wheel e bend e rilascia il sustain `[O]`.

---

## 9. Motore del basso

- **SND-450** Il Bass **DEVE** essere la seconda istanza descritta in §1.2, con patch, FX1, FX2 e oggetto RP propri, e la mandata `REVSEND` della propria patch verso il riverbero condiviso.
- **SND-451** Le note del basso arrivano dal `core` (una per accordo nell'uso normale, modalità Chords Only, Unison, Single Notes e Solo in `10-accordi-e-performance.md`) o dal MIDI sul canale 2 `[M]`.
- **SND-452** Con il massimo di voci a 1 (SND-022) una nuova nota del basso **DEVE** rubare la precedente con la dissolvenza di SND-024, oppure seguire le regole MONO / MONO LEGATO se la patch le chiede.
- **SND-453** `dsp_set_bass_volume` (0–99) **DEVE** scalare con `g_master` l'uscita del Bass dopo FX2, mandata al riverbero compresa `[D]`.
- **SND-454** I parametri dei 12 bassi di fabbrica non sono noti `[O]`. Stame **DEVE** fornire 12 patch di basso proprie, progettate a orecchio sul carattere suggerito dal nome (§12.2) e marcate come "patch di Stame", finché non sono disponibili dati migliori `[V → QA-SND-24]`.

---

## 10. Effetti e catena del segnale

### 10.1 Topologia

```
 Sound: Σ voci ─► TREM RP* ─► FX1 ─► FX2 ─┬───────────────────────────────┐
                                          └─► ×REVSEND(S) ──┐             │
 Bass:  Σ voci ─► TREM RP* ─► FX1 ─► FX2 ─► ×BassVol ─┬─────┼─────────────┤
                                                      └─► ×REVSEND(B) ─┐  │
                                                                       ▼  │
                                   RIVERBERO (SIZE, LP, HP del Sound) ─►──┤
 Batteria (bus stereo da 10-accordi-e-performance, già con i Drum FX) ───►┤
                                                                          ▼
                                                        Σ ─► ×Master ─► soft clip ─► uscita
 * solo con MODEL = REED PIANO
```

- **SND-500** Stame **DEVE** usare questa topologia: per ogni motore FX1 → FX2 in serie, riverbero unico a mandata, presa **dopo** FX2 `[D: indizi nel firmware]` `[V → QA-SND-10]`.
- **SND-501** Il manuale descrive invece synth → Reverb → FX1 → FX2 → uscita `[M]`. Un flag di compilazione `STAME_CHAIN_MANUAL` **DEVE** permettere quella catena (riverbero in serie per motore, dry/wet = REVSEND) per il confronto d'ascolto.
- **SND-502** Al massimo due effetti più il riverbero per motore `[M]`; Delay solo in FX2 `[O]`. Un `FX1TYPE = 7` (fuori range) viene limitato a 6.

### 10.2 Regole comuni degli slot

- **SND-505** Gli effetti leggono i parametri direttamente dalla patch del motore (come `mfx::update` dell'editor dell'originale `[O]`): un `dsp_setpar` su un parametro FX ha effetto dal blocco successivo, con lo smoothing di SND-041. Gli LFO di chorus, ensemble, flanger e tremolo avanzano **per campione** (fase del blocco più rate·i), come il coefficiente del phaser: fermi per 16 campioni facevano saltare il ritardo di lettura fino a 5 campioni per blocco, cioè bande laterali a ±3 kHz a −44 dB (misura del 16/10/2026).
- **SND-506** Con intensità 0 (P2, oppure P1 per il TREMOLO) ogni effetto **DEVE** essere inudibile: sull'originale il display mostra "Off" e i preset usano slot parcheggiati con intensità 0 `[O]`.
- **SND-507** Un cambio di tipo **DEVE** fare una dissolvenza incrociata di 10 ms tra il vecchio e il nuovo effetto. I buffer del nuovo effetto si azzerano a pezzi (al massimo 4096 campioni per blocco) prima di essere usati, per non sforare il tempo di un blocco.

### 10.3 Tipi di FX1 e FX2

Etichette dei parametri `[O: frontend dell'editor 1.0.2 dell'originale]`; descrizioni `[M]`; algoritmi e scale `[V → QA-SND-20]`. `d = P / 127`.

| Tipo (raw) | P1 | P2 (intensità) | P3 | P4 | P5 | P6 | Algoritmo di Stame |
|---|---|---|---|---|---|---|---|
| OFF (0) | | | | | | | bypass |
| CHORUS (1) | RATE `f_fx_rate` | DEPTH | PHASE: fase L/R 0–180° | | | | una linea per canale, ritardo base 7 ms, modulazione `0.5 + 4.5·d2` ms; `y = x·(1 − 0.5·d2) + wet·0.5·d2` |
| ENSEMBLE (2) | RATE | DEPTH | RATE2 | DEPTH2 | | | 3 linee per canale sfasate di 120°, ritardo base 10 ms; LFO lento (RATE/DEPTH) più LFO veloce (RATE2/DEPTH2, ×4 il rate); wet scalato da DEPTH |
| PHASER (3) | RATE | DEPTH | FEEDBACK 0–0,9 | STEREO: fase L/R 0–180° | | | 6 all-pass del 1° ordine, spazzata 200 Hz–4 kHz; DEPTH = ampiezza della spazzata e mix (0 = bypass); stabile al massimo del feedback `[M: firmware 3.90]` |
| FLANGER (4) | RATE | DEPTH | FEEDBACK 0–0,9 | STEREO | | | ritardo 0,3–8 ms modulato; DEPTH = profondità e mix |
| DRIVE (5) | PREG: guadagno 0…+36 dB | POST | | | | | `w = tanh(g·x) / tanh(g)` con sovracampionamento 2×; `y = x + d2·(w − x)`; POST = quantità e compensazione `[M: POST compensa il volume]` |
| TREMOLO (6) | RATE | DEPTH | PHASE: fase L/R 0–180° | | | | `g = 1 − d2·(1 − cos φ)/2`, fase iniziale 0: con RATE 0 il guadagno resta 1, quindi inudibile |
| DELAY (7, solo FX2) | TIME | MIX | FEEDBACK | FILTER | SPREAD | HP | §10.4 |

- **SND-510** La scelta "fase iniziale 0, guadagno 1" del tremolo **DEVE** essere mantenuta: rende inudibili sia gli slot con DEPTH 0 sia quelli con RATE 0, come richiedono gli slot parcheggiati dei preset `[D]`. Quale dei due sia davvero l'intensità sull'originale è da verificare `[V → QA-SND-20]`.

### 10.4 Delay

- **SND-520** TIME (`FX2P1`): raw 0 = **1/4**, 1 = **1/8**, 2 = **1/16** al BPM corrente; raw 3–127 = tempo libero `t_delay_free` `[O]` per la codifica, `[V → QA-SND-08]` per i millisecondi. Il delay segue il BPM, come sull'originale `[D: la routine BPM del firmware aggiorna il delay]` e `[M]`.
- **SND-521** Buffer di 2 s per canale (copre 1/4 fino a 30 BPM). Un cambio di tempo o di BPM **DEVE** essere morbido: il tempo di lettura scorre verso il nuovo valore con una costante di 50 ms, come un nastro `[M: delay "più morbidi" dal firmware 3.90]` `[V]`.
- **SND-522** MIX: `y = x + d2 · wet` (il dry resta sempre a 1) `[V → QA-SND-08]`.
- **SND-523** FEEDBACK: guadagno `d3`; a 127 vale 1,0 e le ripetizioni sono infinite `[M]`. Nel loop c'è un soft clip `tanh` che impedisce la crescita oltre ±1.
- **SND-524** FILTER: passa-basso a 1 polo nel loop, `500 * 40^d4` Hz (127 = 20 kHz). HP: passa-alto a 1 polo nel loop, 0 = spento, altrimenti `20 * 100^d6` Hz. SPREAD: quantità di incrocio tra i canali, 0 = due delay mono identici, 127 = ping-pong completo `[V → QA-SND-08]`.

### 10.5 Riverbero

- **SND-530** Riverbero stereo a **rete di ritardi con feedback (FDN) a 8 linee** con matrice di Hadamard, due diffusori all-pass in ingresso e una leggera modulazione delle linee `[V → QA-SND-09]`. Le lunghezze delle linee scorrono verso REVSIZE con interpolazione per campione dentro il blocco (16/10/2026).
  - REVSIZE: RT60 `0.3 * (10 / 0.3)^x` s e lunghezze delle linee scalate tra 0,5× e 1× `[V]`;
  - REVLP: passa-basso a 1 polo in ogni linea, `1000 * 20^x` Hz (127 = 20 kHz) `[M: toglie gli alti dalla coda]`;
  - REVHP: passa-alto a 1 polo all'ingresso, `20 * 50^x` Hz `[M: toglie i bassi dalla coda]`;
  - uscita: solo wet (il dry passa per il percorso diretto di §10.1).
- **SND-531** Le mandate sono `g_lin(REVSEND)` per motore `[O: il parametro interno si chiama "send"]`.

### 10.6 Bus della batteria e master

- **SND-535** `dsp_render16` **DEVE** sommare un bus stereo della batteria fornito dal chiamante, già processato dai suoi Drum FX (Reverb e Saturator, `10-accordi-e-performance.md`), dopo il riverbero e prima del volume master.
- **SND-536** Volume master: `g_master(v)` con `v` 0–99 `[M: master 0–99]`, poi il soft clipper di SND-046.
- **SND-537** **Kit a campioni** (aggiunta di Stame, 15/10/2026: le batterie sintetizzate «fanno cagare», Luigi). Ogni Beat ha un kit: il nome di un set del banco (SND-374) le cui zone hanno per nota l'id dello strumento di `drums.h` (0 = cassa … 11 = piatto) e, dove serve, layer di velocity (`vel_lo`); oppure nessun kit, e suona la sintesi in stile CR-78 (il kit «Chip»). `drums_hit` prende la zona dello strumento dal kit del Beat corrente e la legge con interpolazione lineare al passo `rate / fs`, senza intonazione; se lo strumento non è nel kit (i clic del metronomo, o un kit parziale) ricade nella sintesi. Il charleston chiuso strozza l'aperto anche quando è un campione (dissolvenza di 6 ms). Kit della prima versione: `kit_studio` (VCSL: cassa, rullante a due layer, cross stick, battimani, charleston, tom, shaker, conga, campanaccio, piatto), `kit_jazz` (Sonic Pi e VCSL), `kit_808` (Sonic Pi), e dal 15/10/2026 notte `kit_techno` (Sonic Pi più il battimani di VCSL, scelto misurando i candidati: cassa `bd_klub`, charleston `hat_bdu` e `hat_gump`, ride `ride_tri`) per i Beat Techno e Dub. I 14 Beat della vetrina e i loro kit sono in `src/core/beat.c`.

---

## 11. Controlli esposti e macro

Sull'originale si regola solo l'intensità degli effetti e il filtro; il tipo degli effetti lo decide il preset e si cambia nel suo editor `[M]`. Le macro scrivono sempre parametri della patch, così il salvataggio di un User Sound (suono + Perform + FX + filtro `[M]`) non richiede stato extra.

- **SND-600** Il `dsp` (o il `core`, che poi chiama `dsp_setpar`) **DEVE** offrire queste macro sul motore **Sound**; il motore Bass non ha macro FX `[D]`.

| Macro | Parametro scritto | Range | Display (§2.3) | Fonte |
|---|---|---|---|---|
| Reverb | REVSEND (114) | 0–127 | 0–10 / Off | `[O]` |
| FX1 | FX1P2, oppure FX1P1 se FX1TYPE = TREMOLO | 0–127 | 0–10 / Off | `[O]` nell'editor dell'originale; sull'originale `[V → QA-SND-20]` |
| FX2 | FX2P2, oppure FX2P1 se FX2TYPE = TREMOLO | 0–127 | 0–10 / Off | come sopra |
| Filter | CUTOFF (68) | 0–127 | 000–127 | `[O]` |
| FX1 on/off, FX2 on/off | FXnTYPE: 0 ↔ ultimo tipo non nullo (CHORUS se non ce n'è uno); P1–P6 restano | — | — | `[O]` |
| Filter on/off | FTYPE: 0 ↔ LOWPASS | — | — | `[O]` nell'editor dell'originale; sull'originale `[V → QA-SND-21]` |
| FX principale | la macro dello slot "principale" (SND-601) | 0–127 | 0–10 / Off | `[M]` |
| FX lock | flag `DSP_LOAD_FXLOCK` ai cambi di suono (§2.6) | on/off | LED | `[M]` |
| Volume master | `dsp_set_master_volume` | 0–99 | 0–99 | `[M]` |
| Volume basso | `dsp_set_bass_volume` | 0–99 | 0–99 | `[M]` |

- **SND-601** L'encoder FX senza menu regola l'effetto "più importante" del suono `[M]`; la regola non è nota. Default: al richiamo del suono, il primo slot con intensità > 0 nell'ordine FX1, FX2, Reverb; se sono tutti a 0, FX1 se il suo tipo non è OFF, altrimenti Reverb `[V → QA-SND-21]`.
- **SND-602** Le macro scrivono il raw con risoluzione piena (0–127). Il passo dell'encoder e la mappa delle manopole della MPK mini Plus stanno in `30-interfaccia.md` e `40-midi-e-controlli.md`.
- **SND-603** L'editing completo dei 135 parametri per motore **DEVE** essere possibile via `dsp_setpar`, che è il punto d'arrivo di SysEx `0x47`, dei blocchi `0x34` / `0x3E` e degli NRPN (`40-midi-e-controlli.md`).

---

## 12. Preset di fabbrica: nomi e categorie

Solo nomi e categorie; i valori sono dati privati (§2.7). Il motore (VA, FM, RP) viene dal firmware 3.92 `[O]`; la categoria è una sintesi di Stame dal carattere del suono `[D]`. Nessuna fonte ufficiale assegna categorie ai singoli suoni, a parte LEAD / BASS / DRUM nel Sound Sampler dello shop `[M]`. Tutti i suoni sono attribuiti a uno stesso autore `[M]`.

- **SND-650** La lista dei Sound **DEVE** usare questi numeri e queste grafie, maiuscole e apostrofi compresi (es. "Raphael's Defeat", "90s Hit", "Upsidedown", "Whoops A Daisy", "Plumerai La Tete", "SNES") `[O]`.

### 12.1 I 70 Sound

Totale: 48 VA, 16 FM, 6 RP `[O]`.

| N | Nome | Motore | Categoria |
|---:|---|---|---|
| 01 | EP | RP | piano elettrico |
| 02 | Ghost | VA | pad / pluck |
| 03 | Analog Flower | VA | pluck |
| 04 | Cherry Blossom | VA | pad |
| 05 | Eraserhead | FM | organo |
| 06 | Whoosh | VA | pad (swell) |
| 07 | Neighbour | VA | pluck / flauto |
| 08 | Diamond Cave | VA | pluck |
| 09 | Creepy Crawlies | VA | pluck |
| 10 | Organ Stab | FM | organo |
| 11 | Porcelain Doll | FM | campana |
| 12 | Malarky | FM | pluck |
| 13 | Smokey EP | RP | piano elettrico |
| 14 | Hymn | VA | pad / organo |
| 15 | Opening Credits | VA | pad |
| 16 | Raphael's Defeat | VA | pad / lead |
| 17 | Rich Toy Piano | VA | tastiera |
| 18 | Trembling Silver | VA | arpa |
| 19 | Tarbox Whirl | RP | piano elettrico |
| 20 | Talkie | VA | pad |
| 21 | Late Five | VA | pluck / piano elettrico |
| 22 | Breakfast | FM | piano elettrico / organo |
| 23 | FM Harp One | FM | arpa |
| 24 | Distarp | VA | lead (distorto) |
| 25 | Space Harpsi | VA | tastiera (clavicembalo) |
| 26 | Organ With Fifth | FM | organo |
| 27 | Fighter Jet | VA | lead / pad |
| 28 | Forest | FM | tastiera |
| 29 | Rise And Shine | VA | brass / pad |
| 30 | Shouting | VA | lead / brass |
| 31 | Nebula Swamp | VA | pluck |
| 32 | Frodo | VA | pad |
| 33 | Piano Lesson | RP | piano elettrico |
| 34 | 90s Hit | VA | stab |
| 35 | Abyss | VA | pad |
| 36 | Silo | VA | pluck |
| 37 | Waiting | FM | pad |
| 38 | Pulsar | VA | pluck |
| 39 | Saw Stairs | VA | lead (distorto) |
| 40 | SNES | VA | lead (chiptune) |
| 41 | Serengeti | VA | pad |
| 42 | Nicholson | VA | pluck / lead |
| 43 | Upsidedown | VA | pluck |
| 44 | Solaw | VA | pluck |
| 45 | Basement | FM | piano elettrico / organo |
| 46 | Warp World | RP | piano elettrico |
| 47 | Pigs | VA | organo / lead |
| 48 | Garden Gnome | VA | lead |
| 49 | FM Bongo | FM | percussione |
| 50 | Arctic | VA | effetto (vento) |
| 51 | Cat Choir | VA | lead |
| 52 | Slow Strings | VA | archi |
| 53 | Molly Buzz | VA | pluck |
| 54 | Scooby | VA | lead |
| 55 | Steel Drum | FM | percussione |
| 56 | In Reverse | VA | pad (reverse) |
| 57 | Falling Star | FM | campana / pad |
| 58 | Stylo Foam | VA | lead / organo |
| 59 | Space Sitar | FM | plettro |
| 60 | Access | VA | lead / pad |
| 61 | Dead Punk | VA | lead |
| 62 | Lemon | VA | lead |
| 63 | Logical | RP | piano elettrico |
| 64 | DX Guitar | FM | plettro |
| 65 | Diapason | VA | organo |
| 66 | Whoops A Daisy | VA | organo / lead |
| 67 | Trout | VA | lead |
| 68 | Plumerai La Tete | VA | pad / lead |
| 69 | Bitron | VA | pluck |
| 70 | Cosmic Day Spa | FM | pad |

### 12.2 I 12 bassi

Nomi dal firmware `[O]`; motore e parametri non noti; carattere dedotto solo dal nome `[D]`. Lo shop scrive due di questi nomi in un'altra grafia `[M]`: Stame usa quelle del firmware.

| N | Nome | Carattere [D] |
|---:|---|---|
| 01 | PWM bass | VA a impulso con PWM |
| 02 | RP bass | Reed Piano |
| 03 | Klub bass | basso da club |
| 04 | PBass | basso elettrico tipo Precision |
| 05 | Thriller | basso synth anni '80 |
| 06 | 808 | sub tipo 808 |
| 07 | RP chill bass | Reed Piano morbido |
| 08 | Fuzzy | basso distorto |
| 09 | Fifth Organ Bass | organo con quinta |
| 10 | Meadow Bass | ignoto (morbido?) |
| 11 | String Split | ignoto |
| 12 | Rezdist bass | risonante e distorto |

### 12.3 User Sound

- **SND-655** 30 slot User Sound, "U01"–"U30", dopo i 70 di fabbrica; ognuno salva la patch del Sound (FX e filtro compresi) e il Perform `[M]`. Gli indici MIDI corrispondenti sono 70–99 `[O]`. Gli slot per bassi utente esistono nell'editor dell'originale ma non sono confermati sull'originale `[O]`: Stame non li prevede nella modalità fedele.

---

## 13. Budget CPU e memoria sulla Miyoo Flip

Dettagli della piattaforma (RK3566, 4 × Cortex-A55, frequenze, affinità dei thread, periodo ALSA) in `50-piattaforma-flip.md`. Le stime qui sotto sono `[D]`, in cicli per campione a 48 kHz, per codice C scalare compilato con `-O2`, già maggiorate del 50 % per la pipeline in ordine dell'A55.

| Blocco | Cicli/campione | Note |
|---|---:|---|
| Voce VA, 4 oscillatori + rumore + SVF + HP + VCA | ~160 | PolyBLEP ~12 cicli per oscillatore |
| Controllo per voce (4 ENV, 4 LFO, 8 slot, curve, `tan`) | ~40 | ~600 cicli per blocco / 16 |
| Voce FM, 4 operatori + filtro | ~150 | seno da tabella |
| Voce RP, 5 risonatori + pickup + rumori | ~120 | `sqrt` e divisione nel pickup |
| **16 voci VA (caso peggiore)** | **~3200** | ≈ 154 Mcicli/s |
| FX per motore, caso peggiore ENSEMBLE + DELAY | ~140 | × 2 motori |
| Riverbero FDN 8 linee | ~300 | |
| Master, scope, mix | ~20 | |
| **Totale caso peggiore** | **~3800** | ≈ 182 Mcicli/s ≈ 10 % di un core a 1,8 GHz |

- **SND-700** Nel caso peggiore (16 voci VA con 4 oscillatori attivi, ENSEMBLE in FX1 e DELAY in FX2 su entrambi i motori, riverbero attivo) il `dsp` **DEVE** usare al massimo il **30 %** di un core A55 della Flip, misurato con il benchmark T-SND-40. Il margine copre l'errore della stima.
- **SND-701** Il `dsp` **DEVE** usare `float` a 32 bit; niente fixed-point e niente `double` nel percorso audio. Motivi: l'A55 ha FPU e NEON, l'originale gira su un Cortex-M7 con FPU, e il suo editor rende in `float` `[O]`. Lo stesso codice deve poter girare su un futuro hardware dedicato.
- **SND-702** Il codice di riferimento **DEVE** essere C11 scalare portabile. Una versione NEON (4 voci per vettore `float32x4_t`, layout SoA delle voci) **PUÒ** esistere in `dsp/neon/`, attivata da `STAME_DSP_NEON`, con risultati entro −90 dB dalla versione scalare (T-SND-41).
- **SND-703** Il thread audio **DEVE** girare con flush-to-zero dei denormali (FPCR.FZ su AArch64, impostato da `platform`; dal 15/10/2026 lo fa il callback di `audio.c` a ogni periodo). In più le linee con feedback (filtri, riverbero, delay) **DOVREBBERO** azzerare gli stati sotto 1e−15 una volta per blocco, per non dipendere dal flag.
- **SND-704** Memoria statica indicativa: 16 voci + 4 slot di coda ≤ 2 KB ciascuno; delay 2 motori × 2 canali × 2 s × 48 kHz × 4 B ≈ 1,5 MB; linee di chorus, ensemble, flanger e phaser 4 slot × 2 canali × 4096 campioni ≈ 128 KB; riverbero ≤ 256 KB; tabelle (seno 2048 punti, curve 128 punti) ≤ 32 KB. Totale < 2,5 MB. Per l'hardware futuro: l'originale ha circa 564 KB di RAM interna `[O]`, quindi i suoi buffer di delay sono certamente più piccoli `[D]` (QA-SND-08).

---

## 14. Test di riferimento

### 14.1 Render offline

- **SND-800** Il progetto **DEVE** includere uno strumento host `stame-render` (Linux/Windows/macOS, stesso codice `dsp`) che legge: una o due patch `.inc` (Sound, Bass), una sequenza di eventi (file di testo `t_ms evento argomenti`, oppure un file MIDI di tipo 0 con canale 1 = Sound e canale 2 = Bass), BPM, `fs` e seme; e scrive un WAV float a 32 bit stereo.
- **SND-801** Il render **DEVE** essere deterministico (SND-005): due esecuzioni con gli stessi ingressi danno file identici.

### 14.2 Test unitari

| ID | Test | Criterio |
|---|---|---|
| T-SND-01 | Intonazione: SAW su note 24–108, SEMI/DETUNE a 64 | frequenza misurata entro ±0,1 cent |
| T-SND-02 | DETUNE 0 e 127 | −1 e +63/64 semitoni entro ±0,5 cent |
| T-SND-03 | Aliasing: SAW a C7 (2093 Hz) a 48 kHz | componenti non armoniche sotto −50 dB rispetto alla fondamentale nella banda 0–20 kHz |
| T-SND-04 | PULSE con PW 0, 64, 127 | silenzio (< −90 dBFS), quadra, silenzio |
| T-SND-05 | Hard sync OSC3 → OSC4 | periodo dell'uscita = periodo dell'OSC3 |
| T-SND-06 | Filtro LP, CUTOFF 0…127 a passi di 16, Q 0, rumore bianco | −3 dB a `f_cut` ±5 % |
| T-SND-07 | Q 127 senza ingresso | auto-oscillazione stabile, picco tra 0,5 e 1, nessun NaN dopo 60 s |
| T-SND-08 | Inviluppi: A, D, R a 0, 32, 64, 96, 127 | tempi entro ±5 % delle curve di §3 |
| T-SND-09 | LFO: rate 0, 32, 64, 96, 127 | frequenza entro ±1 % di `f_lfo` |
| T-SND-10 | LFO MONO | voci dello stesso accordo con la stessa fase; riavvio a `dsp_chord_start` |
| T-SND-11 | Matrice MOD7/MOD8 | ordine di SND-421, nessuna ricorsione |
| T-SND-12 | FM algoritmo 8, quattro operatori a livello 127 | spettro con le sole 4 frequenze degli operatori |
| T-SND-13 | FM feedback 0 → 127 | aumento monotono delle armoniche, nessuna esplosione |
| T-SND-14 | RP: nota singola, RPDECAY 0 e 127 | T60 entro ±10 % di `t_rp_decay` |
| T-SND-15 | Tremolo FX con RATE 0 e con DEPTH 0 | uscita identica al bypass entro −90 dB |
| T-SND-16 | Delay a 120 BPM, TIME 0/1/2 | ritardo 500/250/125 ms ±1 campione |
| T-SND-17 | Delay FEEDBACK 127, 60 s | ripetizioni che non decadono più di 1 dB ciascuna e picco ≤ 1,0 |
| T-SND-18 | Intensità 0 su tutti i tipi FX | uscita identica al bypass entro −90 dB (SND-506) |
| T-SND-20 | `.inc`: lettura e riscrittura di file di prova nel formato dell'editor dell'originale | identità byte per byte, 3414 byte |
| T-SND-21 | `.inc` con LF, minuscole, spazi | caricato; indice incoerente → rifiutato |
| T-SND-22 | `dsp_load_patch` con FX lock | i 24 campi della maschera restano invariati |
| T-SND-30 | Pool: 17 note sul Sound | la 17ª ruba secondo SND-023 |
| T-SND-31 | Basso tenuto + 16 note del Sound | la voce del basso non viene rubata |
| T-SND-32 | Stealing di una voce a pieno volume | nessun salto campione-campione > 0,05 oltre il contenuto del segnale; dissolvenza di 2 ms |
| T-SND-33 | CC120 | silenzio entro un blocco, stati RP azzerati |

### 14.3 Golden file

- **SND-810** Il repository **DEVE** contenere render di riferimento (WAV o hash SHA-256 dei WAV) solo per patch distribuibili: le tre INIT, le patch di Stame e i file di prova dei test. Ogni modifica che cambia un hash va giustificata nel commit.
- **SND-811** I render dei preset di fabbrica **PUÒ** farli solo chi ha i banchi privati, in locale; i risultati non vanno nel repository.

### 14.4 Confronto con l'originale e calibrazione delle curve

- **SND-820** Ogni default `[V]` di §3 **DEVE** avere un test di calibrazione: una serie di `.inc` che cambia un solo parametro (raw 0, 16, 32, …, 112, 127) su una patch semplice (un oscillatore SAW, filtro aperto, nessun FX), da suonare nell'editor standalone dell'originale a 48 kHz e, quando possibile, sull'originale (uscita cuffie). L'editor sembra usare lo stesso DSP dell'hardware, ma la bit-identità non è provata `[D]` (QA-SND-32).
- **SND-821** Misure da ricavare: frequenza di taglio a −3 dB (rumore bianco), tempi degli inviluppi (soglie −3 dB e −60 dB), frequenza degli LFO (LFO → PITCH), tempo del glide, millisecondi del delay libero, RT60 del riverbero, livelli in dB di GAIN e del volume master. I risultati sostituiscono le tabelle di `dsp/curves.c` (SND-150).
- **SND-822** Criteri di confronto preset per preset, sulla stessa sequenza di note: spettro medio a 1/3 d'ottava entro ±3 dB tra 100 Hz e 10 kHz; inviluppo RMS (finestre di 10 ms) entro ±1 dB e tempi entro ±10 %; intonazione entro ±1 cent; per gli effetti modulati, frequenza della modulazione entro ±5 %.

---

## Questioni aperte

| ID | Questione | Default attuale | Come verificarla |
|---|---|---|---|
| QA-SND-01 | Frequenza di campionamento, profondità in bit, DAC e oversampling dell'originale | 48 kHz, `float` | Spettro dall'uscita cuffie di una SAW acuta (immagini e alias); sigla del DAC dal teardown |
| QA-SND-02 | Criterio di voice stealing e priorità tra accordi e basso nel pool da 16 | SND-023 | Più di 16 note via MIDI sul canale 1 con un basso tenuto sul canale 2 |
| QA-SND-03 | Il basso è monofonico? Polifonia via MIDI sul canale 2 | 1 voce | Due note sovrapposte sul canale 2 |
| QA-SND-04 | Curve di cutoff, risonanza, passa-alto di tastiera e keytrack; pendenza e topologia del filtro | SVF 12 dB, curve di §3 | Calibrazione SND-820 con rumore bianco |
| QA-SND-05 | Curve dei tempi degli inviluppi e forma degli stadi | §3, SND-401 | Calibrazione SND-820 |
| QA-SND-06 | Curva del rate degli LFO | punti di §3 | LFO → PITCH, misura della frequenza |
| QA-SND-07 | Curva del glide e comportamento in POLY | §3, SND-203 | Due note con GLIDE a vari valori, in POLY e MONO |
| QA-SND-08 | Delay: tempo libero in ms, tempo massimo (RAM dell'originale), significato di SPREAD e HP, MIX con o senza dry | §3, §10.4 | Impulsi nel delay con ogni parametro isolato |
| QA-SND-09 | Algoritmo e grandezza del riverbero | FDN 8 linee | RT60 e densità degli echi da un impulso |
| QA-SND-10 | Catena: riverbero a mandata o in serie; mandata prima o dopo gli FX; riverbero unico | mandata dopo FX2, unico | patch con DRIVE in FX2 e Reverb al massimo: coda distorta = serie, pulita = mandata |
| QA-SND-11 | Topologia reale degli 8 algoritmi FM | SND-310 | Diagrammi `FM1.png`–`FM8.png` nel popup ROUTING dell'editor dell'originale |
| QA-SND-12 | Curva del livello degli operatori, indice di modulazione, scala del feedback, effetto di GAINn e PWn in FM | SND-302–304, SND-315 | Operatore singolo e coppia modulatore/portante a livelli noti nell'editor dell'originale; prove con la matrice |
| QA-SND-13 | SHAPE in FM ignorato o forma d'onda dell'operatore | ignorato | Stessa patch FM con SHAPE diversi |
| QA-SND-14 | Frequenza di riferimento di O4 FIXED | C4 + SEMI | Patch con il solo OSC4 FIXED |
| QA-SND-15 | Modello RP: curve, rumori campionati; filtro, inviluppi, LFO e matrice in RP | §7, SND-360 | Registrazioni con un parametro RP alla volta; patch RP con CUTOFF basso; LFO → PITCH su una patch RP |
| QA-SND-16 | ENV3/ENV4: secondo stadio HOLD o DELAY | HOLD | ENV3 → PITCH con H alto: il salto arriva dopo l'attacco (hold) o prima (delay)? |
| QA-SND-17 | LFO: FREE per voce o per motore; MONO; differenza RAND / S&H; valore finale di ONESHOT | SND-411, SND-412 | Accordi con LFO → PITCH in ciascun modo |
| QA-SND-18 | Matrice: curva della quantità, scala di ogni destinazione, sorgente 14 "?", UNISON | SND-420, tabella di §8.3 | Ogni destinazione con quantità note, misurata |
| QA-SND-19 | UNISON e UDETUNE | ignorati | `.inc` con UNISON 1–4 nell'editor dell'originale |
| QA-SND-20 | Algoritmi e scale degli FX; intensità del Tremolo su P1 o P2; DRIVE POST | §10.3 | Alzare P1 e P2 di un Tremolo separatamente; misure di ogni tipo |
| QA-SND-21 | Regola dell'effetto "principale" dell'encoder FX; Filter on/off sull'originale | SND-601, FTYPE 0 ↔ LP | Prove sull'hardware; byte +0x26 e +0x27 dei record preset (non decodificati) |
| QA-SND-22 | Maschera dell'FX lock sull'originale | maschera dell'editor dell'originale | Cambio di suono con lock attivo e filtro modificato |
| QA-SND-23 | Ruolo di `mbcpr3band` (compressore master o della batteria?) | non implementato, soft clip | Misure di dinamica sull'uscita con accordi forti e deboli |
| QA-SND-24 | Parametri dei 12 bassi di fabbrica | patch di Stame | Lettura nell'editor dell'originale, modalità B |
| QA-SND-25 | Semantica di VER 0 (sorgenti della matrice) | caricata così com'è | Patch VER 0 aperta nell'editor dell'originale |
| QA-SND-26 | Curve di velocity (GVELO, FVELO, OnGAIN); velocity con Velocity Sense spento | SND-220, 100 | Note a velocity diverse, misura del livello |
| QA-SND-27 | Fase iniziale degli oscillatori VA e degli operatori FM; PW su SAW e TRI | casuale VA, 0 FM; PW ignorato | Note ripetute registrate: forma d'onda all'attacco |
| QA-SND-28 | Curve di volume (GAIN, GAIN dell'oscillatore, master, basso), headroom e saturazione del mixer | §3, SND-045, SND-265 | Misure di livello in dB |
| QA-SND-29 | Scala del DETUNE (±1 semitono?) | ±1 semitono | Battimenti tra due oscillatori con DETUNE noti |
| QA-SND-30 | Chi specifica la sintesi del kit di batteria e i Drum FX | `10-accordi-e-performance.md` | Decisione tra le sezioni |
| QA-SND-31 | Comportamento esatto di POLY LEGATO | SND-204 | Note legate con inviluppo lento |
| QA-SND-32 | Bit-identità tra l'editor dell'originale e l'hardware | non assunta | Stesso preset registrato dall'editor e dall'originale, confronto SND-822 |

## Dipendenze da altre sezioni

- **`00-panoramica.md`**: divisione in `core`, `dsp`, `gfx`, `platform`; glossario (motore, modello, patch, raw).
- **`10-accordi-e-performance.md`**: genera le note per Sound e Bass, una nota di basso per accordo e le modalità del basso; chiama `dsp_chord_start` a ogni nuovo accordo; fornisce BPM (delay a tempo), Velocity Sense, Perform di default dei preset (campi di `bank.idx`) e il bus stereo della batteria con i Drum FX (QA-SND-30).
- **`30-interfaccia.md`**: formati di display (§2.3), liste "NN Nome" e "U01"–"U30", overlay di Sound e "Bass Sound", gesti dell'encoder FX (rotazione, lista, lock), vista React (SND-033), avviso di patch legacy e di banco mancante.
- **`40-midi-e-controlli.md`**: note sui canali 1 e 2 verso i motori; CC1, CC64, pitch bend, CC120, CC121, CC123; SysEx `0x34`, `0x3E`, `0x47`, `0x48` e NRPN verso `dsp_setpar` / `dsp_load_patch`; mappa delle manopole della MPK mini Plus sulle macro di §11.
- **`50-piattaforma-flip.md`**: thread audio, periodo ALSA multiplo di 16, `fs` a 48 kHz, coda SPSC degli eventi, flush-to-zero, affinità dei core e misura della CPU (SND-700), percorsi delle cartelle dei banchi e dei campioni RP, flag di compilazione (`STAME_DSP_NEON`, `STAME_CHAIN_MANUAL`, `STAME_RP_FILTER`).
- **`90-questioni-aperte.md`**: riprende QA-SND-01…32.
