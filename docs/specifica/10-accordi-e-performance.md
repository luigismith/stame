# 10 — Accordi e performance

Questa sezione specifica il **motore degli accordi** di Stame, cioè la parte `core` che trasforma i gesti logici (tasto, tipo, estensioni, dial) in eventi di nota: tipi ed estensioni, Secret Chords, nomi, voicing a finestra, Key mode, basso, Play Style, performance (Strum, Slop, Arp, Pattern, Harp), BPM e clock interno, Beat, looper e gestione delle note lato accordi. È scritta per poter implementare `core/acc_*` e i suoi test unitari senza altre fonti.

## 0. Come leggere questa sezione

### 0.1 Etichette
Seguono `CONVENZIONI.md`. Corrispondenza con le fonti di ricerca:
- `[M]` manuale operativo v4.1 e v3.1, articoli del supporto ufficiale, changelog del firmware, brevetto (AU/US/EP);
- `[O]` osservato: video (anche quelli ufficiali), catture MIDI, analisi del firmware 3.92 fatta da terzi, recensioni, utenti;
- `[D]` dedotto o ricostruito, coerente con tutti i dati noti;
- `[V]` default scelto per ora, **da verificare sull'originale**; il riferimento `(T-nn)` rimanda alla tabella dei test in §14.

I requisiti di architettura, che non descrivono un comportamento dell'originale ma una scelta di progetto di Stame, non portano etichetta.

### 0.2 Numerazione dei requisiti
I requisiti sono `ACC-nnn`, a blocchi per paragrafo, con numeri liberi per inserimenti futuri:

| Blocco | Paragrafo |
|---|---|
| ACC-001…019 | §1 Modello, input logico, uscita |
| ACC-020…039 | §2 Tipi ed estensioni |
| ACC-040…049 | §3 Secret Chords |
| ACC-050…069 | §4 Nomi degli accordi |
| ACC-070…089 | §5 Voicing, note singole, transpose |
| ACC-090…109 | §6 Key mode |
| ACC-110…139 | §7 Play Style |
| ACC-140…159 | §8 Basso |
| ACC-160…199 | §9 Performance |
| ACC-200…219 | §10 BPM, clock, metronomo, Beat, batteria |
| ACC-220…249 | §11 Looper |
| ACC-250…269 | §12 Note e voci lato accordi |
| ACC-270…279 | §13 Vettori di test |

### 0.3 Notazione
- **pc** = pitch class 0…11 (C = 0). **k** = tasto logico 0…11 (C … B).
- **Nota MIDI**: intero 0…127, 60 = Do centrale. Nei nomi d'ottava Stame usa la convenzione **C3 = 60** (Yamaha), la stessa delle etichette d'ottava del dial (§5.2) `[D]`.
- `a mod 12` è sempre il resto non negativo (0…11), anche per `a` negativo.
- **Treble** = voci del suono principale (accordi, note singole, performance); **Bass** = voce del basso.
- **Tick** = unità del clock interno, 96 per semiminima (§10.1).

---

## 1. Modello, input logico, uscita

### 1.1 Architettura
- **ACC-001** Il motore degli accordi DEVE stare in `core`, in C11 puro: niente SDL, ALSA, evdev, I/O di file, `malloc`/`free` dopo l'inizializzazione, né chiamate bloccanti. Tutta la memoria è nella struttura di stato `acc_state`, allocata dal chiamante.
- **ACC-002** Il motore DEVE essere **deterministico**: dati lo stato iniziale, il seed del generatore casuale (§9.4) e la stessa sequenza di input con gli stessi timestamp, produce la stessa sequenza di uscita, bit per bit. È il presupposto dei vettori di test (§13).
- **ACC-003** Il motore NON DEVE conoscere la MPK mini Plus né i tasti della Flip. Riceve solo gli **input logici** di §1.2; la traduzione dai controlli fisici è in `40-midi-e-controlli.md`.
- **ACC-004** Il motore DEVE lavorare a blocchi audio: `acc_process()` riceve gli input del blocco con il loro offset in campioni e restituisce gli eventi di nota del blocco con offset al campione. La frequenza di campionamento e la dimensione del blocco arrivano dalla piattaforma (`50-piattaforma-flip.md`).

### 1.2 Input logici
**ACC-005** Il motore DEVE accettare questi input. Gli identificatori sono normativi per il codice.

| Input | Parametri | Note |
|---|---|---|
| `KEY_DOWN` | `k` 0…11, `vel` 1…127 | tasto della tastiera di un'ottava `[M]` |
| `KEY_UP` | `k` | |
| `TYPE_DOWN` / `TYPE_UP` | `t` ∈ {`DIM`=0, `MIN`=1, `MAJ`=2, `SUS`=3} | ordine del pannello, riga alta `[M]` |
| `EXT_DOWN` / `EXT_UP` | `e` ∈ {`E6`=0, `E7MIN`=1, `E7MAJ`=2, `E9`=3} | tasti 6, m7, M7, 9, riga bassa `[M]` |
| `VOICING_STEP` | `d` intero con segno | scatti del Chord Voicing; l'accelerazione è già applicata a monte |
| `BASS_VOICING_STEP` | `d` | scatti del Bass Voicing |
| `SINGLE_NOTES_TOGGLE` | — | pressione del Chord Voicing: Split ↔ Full Octave `[M]` |
| `KEY_MODE_TOGGLE`, `KEY_SELECT` | `key_index` 0…41 | §6 |
| `TRANSPOSE_STEP` | `d` | §5.5 |
| `BASS_TOGGLE`, `BASS_MODE_SET` | modo | §8 |
| `PERF_SET` | `mode`, `amount` | §9 |
| `BPM_SET`, `TRANSPORT_TOGGLE`, `METER_SET`, `BEAT_SELECT` | | §10 |
| `DRUMS_TOGGLE` | — | §10.5 |
| `LOOP_CMD` | comando | §11 |
| `OPTION_SET` | opzione, valore | §1.4 |

- **ACC-006** Gli input con lo stesso offset in campioni DEVONO essere elaborati nell'ordine in cui arrivano. Il motore NON DEVE riordinarli.
- **ACC-007** `KEY_DOWN` di un tasto già premuto e `KEY_UP` di un tasto non premuto DEVONO essere ignorati senza effetti.

### 1.3 Uscita
**ACC-008** Il motore DEVE produrre eventi di nota con questa forma:

```c
typedef enum { ACC_ROLE_TREBLE, ACC_ROLE_BASS, ACC_ROLE_CHORD_BLOCK, ACC_ROLE_DRUM } acc_role;
typedef struct {
    uint32_t offset;   /* campione nel blocco corrente */
    uint8_t  role;     /* acc_role */
    uint8_t  note;     /* nota MIDI, dopo il transpose; per DRUM: id strumento (§10.5) */
    uint8_t  vel;      /* 1..127 per note-on, 0 per note-off */
    uint8_t  on;       /* 1 = note-on, 0 = note-off */
} acc_note_ev;
```

- `TREBLE` va al motore di suono principale e al MIDI canale Performance; `BASS` al motore del basso e al canale Bass; `CHORD_BLOCK` solo al MIDI canale Chord (accordo a blocco, senza performance) `[M]`; `DRUM` al kit di batteria.
- **ACC-009** A parità di offset il motore DEVE emettere prima i note-off e poi i note-on dello stesso ruolo, così una nota ri-attaccata alla stessa altezza riparte pulita. Unica eccezione: il cambio di nota del basso in legato (ACC-147).
- **ACC-010** Per le note singole e gli accordi il motore DEVE emettere gli eventi `CHORD_BLOCK` prima di quelli `TREBLE` con lo stesso offset `[O]` (catture MIDI 3.92: il ch3 parte prima del ch1).
- **ACC-011** Il motore NON DEVE emettere due note-off consecutivi per la stessa nota e lo stesso ruolo. Il note-off doppio sul canale Chord osservato nel 3.92 è un difetto e non si replica `[O]`.
- **ACC-012** Il motore DEVE esporre, a ogni blocco, lo **stato visibile** per l'interfaccia: ultimo accordo risolto (note, basso, nome strutturato di §4), tasti tipo ed estensione premuti, valore di voicing e bass voicing con etichetta d'ottava, tonalità, transpose, modo e amount di performance, stato del trasporto (battuta, battito), stato del looper (§11.6). Il motore non disegna nulla.

### 1.4 Opzioni e default
**ACC-013** Le opzioni del menu Options > Instrument e Bass DEVONO avere questi valori e default.

| Opzione | Valori | Default | Etichetta |
|---|---|---|---|
| Play Style | `SIMPLE`, `ADVANCED`, `FREE` | `SIMPLE` | valori `[M]`; default `[O]` (attivo in 3.04/3.05), da confermare `[V]` (T-27) |
| Extension Addition | `ADD_NOTE`, `PLAY_CHORD` | `ADD_NOTE` | valori `[M]`; default `[V]` (T-27) |
| Secret Chords | `OFF`, `SIMPLE_ONLY`, `ALL` | `OFF` | valori `[M]`; default `[V]` (T-27) |
| Single Notes | `SPLIT`, `FULL_OCTAVE` | `FULL_OCTAVE` | valori `[M]`; default `[V]` (T-27) |
| Quantization (loop) | `NONE`, `Q4`, `Q8`, `Q8T`, `Q16`, `Q16T`, `Q32` | `NONE` | valori `[M]`; default `[V]` (T-27) |
| Velocity Sense | `ON`, `OFF` | `ON` | valori `[M]`; default `[V]` |
| Bass mode | `CHORDS_ONLY`, `UNISON_BASS`, `BASS_SINGLE_NOTES`, `SOLO` | `CHORDS_ONLY` | valori `[M]`; default `[V]` (T-27) |
| Basso acceso | on/off | off | `[V]` (T-27) |
| Key mode | on/off; tonalità 0…41 | off; C maggiore (0) | `[V]` |
| Transpose | −12…+12 | 0 | gamma `[V]` (T-14) |
| Chord Voicing `v` | 1…60 | 24 | gamma `[O]`; default `[V]` (T-02) |
| Bass Voicing `vb` | 0…48 | 23 | gamma `[O]`; default `[V]` (T-02) |
| BPM | 60…200 | 120 | gamma `[O]`; default `[V]` (T-13) |
| Metrica | `2/4`, `3/4`, `4/4`, `6/8` | `4/4` | valori `[O]`; default `[V]` |

- **ACC-014** Con Velocity Sense `OFF` ogni velocity in ingresso DEVE essere sostituita da `VEL_FIXED` = 100 prima di qualunque elaborazione `[V]` (T-10). I Pattern seguono questa regola `[M]` (FW 3.84).
- **ACC-015** La curva di velocity dei tasti fisici NON fa parte del motore: arriva già applicata dallo strato MIDI.

---

## 2. Tipi ed estensioni

### 2.1 Intervalli
**ACC-020** Ogni accordo DEVE essere rappresentato come maschera di 12 bit di pitch class relative alla fondamentale (bit `i` = intervallo `i` semitoni, modulo 12).

| Tasto | Intervalli (semitoni) | Maschera | Etichetta |
|---|---|---|---|
| Maj | 0, 4, 7 | `0x091` | `[M]` (brevetto) |
| Min | 0, 3, 7 | `0x089` | `[M]` |
| Sus | 0, 5, 7 (sus4) | `0x0A1` | `[M]` indiretto: "Sus4-7", "Cm add4" |
| Dim | 0, 3, 6 | `0x049` | `[O]` |
| 6 | +9 | `0x200` | `[M]` nome; `[O]` semitoni |
| m7 | +10 | `0x400` | `[M]` |
| M7 | +11 | `0x800` | `[M]` (brevetto: maj7 = 0, 4, 7, 11) |
| 9 | +2 (add9, pitch class 2 dentro la finestra) | `0x004` | `[M]` (video ufficiale: A + 9 aggiunge solo B; fix 3.84 della 9 un'ottava sopra) |

```c
static const uint16_t ACC_TYPE_MASK[4] = { 0x049 /*DIM*/, 0x089 /*MIN*/, 0x091 /*MAJ*/, 0x0A1 /*SUS*/ };
static const uint8_t  ACC_EXT_PC[4]    = { 9 /*E6*/, 10 /*E7MIN*/, 11 /*E7MAJ*/, 2 /*E9*/ };
```

- **ACC-021** La maschera di un accordo normale DEVE essere `ACC_TYPE_MASK[t] | ⋃ (1 << ACC_EXT_PC[e])` per ogni estensione `e` tenuta ("what you play is what you get": un'estensione aggiunge sempre lo stesso intervallo, il 6 non diventa 13) `[M]`.
- **ACC-022** La 9 DEVE essere trattata come pitch class 2 e posizionata dentro la finestra come ogni altra nota, mai a +14 fisso `[M]`.
- **ACC-023** Dim + m7 DEVE dare {0, 3, 6, 10} (semidiminuito, m7♭5) con nome `Cdim⁷` `[V]` (T-01). Il dim7 vero è Dim + 6 = {0, 3, 6, 9}. Una variante di compatibilità (`ACC_COMPAT_DIM7_TRUE`, spenta) PUÒ dare {0, 3, 6, 9} anche con Dim + m7.
- **ACC-024** Le estensioni da sole, senza tipo e con Key mode spenta, NON DEVONO suonare: il tasto dà la nota singola `[M]`.
- **ACC-025** Con più tipi tenuti e nessun Secret Chord applicabile (§3), vale il **tipo premuto più di recente tra quelli ancora tenuti** `[D]` (FW 3.84 "pressioni multiple"; T-15).

### 2.2 Le 64 combinazioni (fondamentale C)
**ACC-026** Le 64 combinazioni tipo × sottoinsieme di estensioni DEVONO dare queste note e questi nomi. I nomi `[M]` coincidono con la tabella 6.5 del manuale (26 voci); i nomi `[D]` applicano la stessa regola (§4.2) e restano da verificare `[V]` (T-25). Le note seguono ACC-021 `[D]`; Dim + m7 segue ACC-023. Notazione delle note: pitch class.

| Estensioni | Maj | Min | Sus | Dim |
|---|---|---|---|---|
| — | C `[M]` · 0 4 7 | Cm `[M]` · 0 3 7 | Csus `[M]` · 0 5 7 | Cdim `[M]` · 0 3 6 |
| 6 | C⁶ `[M]` · 0 4 7 9 | Cm⁶ `[M]` · 0 3 7 9 | Csus⁶ `[M]` · 0 5 7 9 | Cdim⁶ `[M]` · 0 3 6 9 |
| m7 | C⁷ `[M]` · 0 4 7 10 | Cm⁷ `[M]` · 0 3 7 10 | Csusᵐ⁷ `[M]` · 0 5 7 10 | Cdim⁷ `[M]` · 0 3 6 10 |
| M7 | Cᴹ⁷ `[M]` · 0 4 7 11 | Cmᴹ⁷ `[M]` · 0 3 7 11 | Csusᴹ⁷ `[M]` · 0 5 7 11 | Cdimᴹ⁷ `[D]` · 0 3 6 11 |
| 9 | C⁹ `[M]` · 0 2 4 7 | Cm⁹ `[M]` · 0 2 3 7 | Csus⁹ `[M]` · 0 2 5 7 | Cdim⁹ `[M]` · 0 2 3 6 |
| 6+m7 | C⁷⁶ `[D]` · 0 4 7 9 10 | Cm⁷⁶ `[M]` · 0 3 7 9 10 | Csusᵐ⁷⁶ `[M]` · 0 5 7 9 10 | Cdim⁷⁶ `[D]` · 0 3 6 9 10 |
| 6+M7 | Cᴹ⁷⁶ `[M]` · 0 4 7 9 11 | Cmᴹ⁷⁶ `[D]` · 0 3 7 9 11 | Csusᴹ⁷⁶ `[D]` · 0 5 7 9 11 | Cdimᴹ⁷⁶ `[D]` · 0 3 6 9 11 |
| 6+9 | C⁶⁹ `[D]` · 0 2 4 7 9 | Cm⁶⁹ `[D]` · 0 2 3 7 9 | Csus⁶⁹ `[D]` · 0 2 5 7 9 | Cdim⁶⁹ `[D]` · 0 2 3 6 9 |
| m7+M7 | C⁷ᴹ⁷ `[D]` · 0 4 7 10 11 | Cm⁷ᴹ⁷ `[D]` · 0 3 7 10 11 | Csusᵐ⁷ᴹ⁷ `[D]` · 0 5 7 10 11 | Cdim⁷ᴹ⁷ `[D]` · 0 3 6 10 11 |
| m7+9 | C⁷⁹ `[D]` · 0 2 4 7 10 | Cm⁷⁹ `[M]` · 0 2 3 7 10 | Csusᵐ⁷⁹ `[D]` · 0 2 5 7 10 | Cdim⁷⁹ `[D]` · 0 2 3 6 10 |
| M7+9 | Cᴹ⁷⁹ `[M]` · 0 2 4 7 11 | Cmᴹ⁷⁹ `[D]` · 0 2 3 7 11 | Csusᴹ⁷⁹ `[M]` · 0 2 5 7 11 | Cdimᴹ⁷⁹ `[D]` · 0 2 3 6 11 |
| 6+m7+M7 | Cᴶᴬᶻᶻ `[D]` · 0 4 7 9 10 11 | Cmᴶᴬᶻᶻ `[D]` · 0 3 7 9 10 11 | Csusᴶᴬᶻᶻ `[D]` · 0 5 7 9 10 11 | Cdimᴶᴬᶻᶻ `[D]` · 0 3 6 9 10 11 |
| 6+m7+9 | Cᴶᴬᶻᶻ `[D]` · 0 2 4 7 9 10 | Cmᴶᴬᶻᶻ `[D]` · 0 2 3 7 9 10 | Csusᴶᴬᶻᶻ `[M]` · 0 2 5 7 9 10 | Cdimᴶᴬᶻᶻ `[M]` · 0 2 3 6 9 10 |
| 6+M7+9 | Cᴶᴬᶻᶻ `[D]` · 0 2 4 7 9 11 | Cmᴶᴬᶻᶻ `[D]` · 0 2 3 7 9 11 | Csusᴶᴬᶻᶻ `[D]` · 0 2 5 7 9 11 | Cdimᴶᴬᶻᶻ `[D]` · 0 2 3 6 9 11 |
| m7+M7+9 | Cᴶᴬᶻᶻ `[D]` · 0 2 4 7 10 11 | Cmᴶᴬᶻᶻ `[M]` · 0 2 3 7 10 11 | Csusᴶᴬᶻᶻ `[D]` · 0 2 5 7 10 11 | Cdimᴶᴬᶻᶻ `[D]` · 0 2 3 6 10 11 |
| tutte e 4 | Cᵂᵀᶠ `[D]` · 0 2 4 7 9 10 11 | Cmᵂᵀᶠ `[D]` · 0 2 3 7 9 10 11 | Csusᵂᵀᶠ `[D]` · 0 2 5 7 9 10 11 | Cdimᵂᵀᶠ `[M]` · 0 2 3 6 9 10 11 |

- **ACC-027** Un accordo normale ha da 3 a 7 note distinte `[D]`. Il motore NON DEVE duplicare una pitch class dentro la stessa voicing.

---

## 3. Secret Chords

### 3.1 Tabella
**ACC-040** I Secret Chords DEVONO essere una **tabella fissa**, non l'unione degli intervalli (Maj + Sus darebbe {0, 4, 5, 7}, non un aumentato) `[D]`. Combinazioni e stringhe a display `[M]` (griglia del manuale 3.84); note `[D]`; da verificare `[V]` (T-16).

| # | Tipi tenuti (insieme esatto) | Estensioni richieste | Display | Base | Apice | Note (pc) |
|---|---|---|---|---|---|---|
| S1 | Dim + Sus | — | `C⁵` | `C` | `5` | 0 7 |
| S2 | Maj + Sus | — | `C+` | `C+` | — | 0 4 8 |
| S3 | Min + Sus | — | `Cmᵃᵈᵈ⁴` | `Cm` | `add4` | 0 3 5 7 |
| S4 | Min + Dim | 6 | `Cmᵐ⁶` | `Cm` | `m6` | 0 3 7 8 |
| S5 | Maj + Dim | — (il 6, se tenuto, è assorbito) | `Cᵐ⁶` | `C` | `m6` | 0 4 7 8 |
| S6 | Maj + Min | m7 | `C7#⁹` | `C7#` | `9` | 0 3 4 7 10 |

```c
typedef struct { uint8_t types, req_ext, absorbed_ext; uint16_t mask; const char *base, *sup; } acc_secret;
/* bit dei tipi: 1<<DIM, 1<<MIN, 1<<MAJ, 1<<SUS; bit delle estensioni: 1<<E6, 1<<E7MIN, 1<<E7MAJ, 1<<E9 */
static const acc_secret ACC_SECRET[6] = {
  { (1<<DIM)|(1<<SUS), 0,          0,          0x081, "",   "5"    },
  { (1<<MAJ)|(1<<SUS), 0,          0,          0x111, "+",  ""     },
  { (1<<MIN)|(1<<SUS), 0,          0,          0x0A9, "m",  "add4" },
  { (1<<MIN)|(1<<DIM), 1<<E6,      1<<E6,      0x189, "m",  "m6"   },
  { (1<<MAJ)|(1<<DIM), 0,          1<<E6,      0x191, "",   "m6"   },
  { (1<<MAJ)|(1<<MIN), 1<<E7MIN,   1<<E7MIN,   0x499, "7#", "9"    },
};
```

### 3.2 Regole
- **ACC-041** Un Secret Chord si applica solo se l'opzione lo consente: `ALL` sempre; `SIMPLE_ONLY` solo con Play Style `SIMPLE`; `OFF` mai `[M]`.
- **ACC-042** Il confronto DEVE usare l'**insieme esatto** dei tipi tenuti in quel momento (2 tipi). Con 3 o 4 tipi tenuti non c'è Secret Chord e vale ACC-025 `[D]`.
- **ACC-043** Se l'insieme dei tipi coincide ma manca un'estensione richiesta (Min + Dim senza 6, Maj + Min senza m7), il Secret Chord NON si applica e vale ACC-025 `[V]` (T-16).
- **ACC-044** Le estensioni tenute oltre a quelle richieste o assorbite DEVONO aggiungere la loro pitch class alla maschera; il nome resta quello del Secret Chord, senza apici aggiunti `[V]` (T-16).
- **ACC-045** Il basso di un Secret Chord è la fondamentale `k` `[D]`. I tipi scavalcano la Key mode anche quando formano un Secret Chord `[D]`.
- **ACC-046** Il video ufficiale fa intendere che esistano altre combinazioni `[M]`: fino a verifica (T-16) Stame implementa solo le sei della tabella.

---

## 4. Nomi degli accordi

Il motore produce un **nome strutturato**; il disegno (font, apici, corpo) è in `30-interfaccia.md`.

### 4.1 Struttura
**ACC-050** Il nome DEVE avere questa forma:

```c
typedef enum { ACC_ACC_NONE, ACC_ACC_SHARP, ACC_ACC_FLAT, ACC_ACC_DSHARP, ACC_ACC_DFLAT } acc_accidental;
typedef struct { char letter; uint8_t acc; } acc_spelled;     /* 'A'..'G' + alterazione */
typedef struct {
    acc_spelled root;
    char  quality[5];  /* corpo pieno: "", "m", "sus", "dim", "+", "7#" */
    char  sup[6];      /* apice ASCII: "", "6", "9", "7", "m7", "M7", "76", "79", "M76", "M79",
                          "m76", "m79", "69", "7M7", "m7M7", "JAZZ", "WTF", "5", "add4", "m6" */
    uint8_t has_slash; acc_spelled slash;                     /* solo Key mode (§6.4) */
} acc_chord_name;
```

- Resa a display: doppio diesis = `x` `[M]`; doppio bemolle = `bb` `[V]`; apice `M7` = ᴹ⁷, `m7` = ᵐ⁷, `JAZZ` = ᴶᴬᶻᶻ, `WTF` = ᵂᵀᶠ.
- **ACC-051** La nota singola DEVE dare un nome con la sola radice (lettera e alterazione) più il numero di nota MIDI; l'interfaccia decide se e come mostrare l'ottava.

### 4.2 Regola degli apici (accordi normali)
**ACC-052** Il nome di un accordo normale DEVE seguire questo pseudocodice `[M]` (riproduce 26 nomi su 26 del manuale):

```text
nome(root, t, exts):
  quality = {MAJ:"", MIN:"m", SUS:"sus", DIM:"dim"}[t]
  n = |exts|
  se n == 0: sup = ""
  se n == 3: sup = "JAZZ"                                   [M]
  se n == 4: sup = "WTF"                                    [M]
  se n ∈ {1,2}:
      sette = (E7MIN ∈ exts ? (t == SUS ? "m7" : "7") : "") + (E7MAJ ∈ exts ? "M7" : "")
      resto = (E6 ∈ exts ? "6" : "") + (E9 ∈ exts ? "9" : "")
      sup = sette + resto                                   # prima la settima, poi 6 o 9
```

- Maj + m7 = `C⁷` (dominante) è voluto `[M]`.
- L'ordine per 6+9 (`⁶⁹`) e per m7+M7 (`⁷ᴹ⁷`) è `[D]`, da verificare `[V]` (T-25).
- Il manuale v3.1 usava `???` e `WTF?`: Stame segue il firmware attuale (3 = JAZZ, 4 = WTF) `[M]`.

### 4.3 Grafia della radice
- **ACC-053** Con Key mode **spenta** le radici alterate DEVONO usare i diesis: C, C#, D, D#, E, F, F#, G, G#, A, A#, B `[V]` (T-12).
- **ACC-054** Con Key mode **accesa** la grafia DEVE seguire la tonalità `[M]` (FW 3.21):
  - pitch class in scala: la grafia del grado (§6.2), che può contenere `x` o `bb`;
  - pitch class fuori scala (tipo premuto che scavalca la tonalità): se la somma delle alterazioni della scala è negativa, bemolle sulla lettera superiore; altrimenti diesis sulla lettera inferiore `[D]`. In C maggiore e A minore valgono quindi i diesis.
- **ACC-055** Il nome DEVE seguire il transpose `[M]` (FW 3.60): la radice nominata è `(root + transpose) mod 12`. Con Key mode accesa e transpose ≠ 0, la grafia usa la **tonalità effettiva**: fra le 42 tonalità con pitch class `(tonica + transpose) mod 12` e lo stesso modo, quella con meno alterazioni; a parità, quella con i diesis `[V]` (T-12).
- **ACC-056** Dopo il rilascio il nome resta visibile per un tempo breve `[M]` (FW 3.90). Il motore espone l'ultimo nome e l'istante del rilascio; la durata (`T_LINGER`, default 500 ms `[V]`, T-24) la gestisce l'interfaccia.

---

## 5. Voicing, note singole, transpose

### 5.1 Finestra
**ACC-070** Tutte le note dell'accordo DEVONO cadere in una finestra di un'ottava che parte dalla **nota d'inizio** `W` `[M]` (brevetto, rivendicazione 1):

```text
place(pc, W)  = W + ((pc - W) mod 12)                  # risultato in [W, W+11]
voicing(root, mask, W) = sort_asc( place((root + i) mod 12, W) per ogni bit i di mask )
```

- Riproduce gli esempi del brevetto: con la finestra da C, G maggiore = B D G e F maggiore = C F A `[M]`.
- **ACC-071** L'inversione NON è un parametro: è determinata da quali note cadono nella finestra `[M]`. Girando in su la nota più bassa sale di un'ottava; in giù la più alta scende `[M]`. Dodici scatti riportano la stessa voicing un'ottava sopra `[D]`.

### 5.2 Gamma e mappa del dial
- **ACC-072** Il Chord Voicing DEVE avere valore grezzo `v` ∈ 1…60 (5 ottave), un semitono per scatto, con saturazione agli estremi `[O]` (limiti nel firmware 3.92) e passo `[M]`.
- **ACC-073** La mappa DEVE essere `W = v + 24` `[V]` (T-02). Con il default `v = 24`, `W = 48`: l'accordo di Do maggiore suona 48 52 55. Gamma risultante: `W` 25…84, note 25…95.
- **ACC-074** L'etichetta d'ottava del dial DEVE essere `floor(v / 12)` `[D]` (24 = "second octave", 36 = "third" `[O]`).
- **ACC-075** Il Bass Voicing DEVE avere valore grezzo `vb` ∈ 0…48 `[O]` con `WB = vb + 13` `[V]` (T-02). Con i default (24 e 23) la finestra del basso (36…47) è l'ottava subito sotto quella degli accordi (48…59). Etichetta `floor(vb / 12)` (23 = "first", 35 = "second" `[O]`).
- **ACC-076** L'accelerazione dell'encoder NON è nel motore: `VOICING_STEP` porta già gli scatti effettivi `[V]` (T-20).

### 5.3 Re-trigger al movimento del dial
- **ACC-077** Se un accordo o una nota suona e un `VOICING_STEP` cambia l'insieme delle note, il motore DEVE fare **note-off di tutte le note treble e note-on della nuova voicing** allo stesso offset, con la velocity dell'attacco originale `[M]` (video Quick Start: l'accordo si ri-attacca quando il voicing si muove).
  - Se l'insieme non cambia (la finestra passa su una nota che non è dell'accordo), il motore NON DEVE emettere eventi `[V]` (T-04).
  - Variante di compatibilità `ACC_COMPAT_PARTIAL_RETRIGGER` (spenta): note-off/on solo delle note cambiate `[V]` (T-04).
  - Con una performance attiva vale ACC-179.
  - Gli eventi `CHORD_BLOCK` seguono lo stesso re-trigger `[D]`.
- **ACC-078** Un `BASS_VOICING_STEP` che cambia la nota del basso mentre suona DEVE ri-attaccare il basso (note-off vecchia, note-on nuova) `[D]`.
- **ACC-079** La variante del brevetto con finestra estesa (una nota fino a `W + 13`) NON DEVE essere attiva: non è osservata sullo strumento `[V]` (T-05).

### 5.4 Note singole
**ACC-080** La nota singola (tasto senza tipo, Key mode spenta) DEVE essere `[D]`:

```text
FULL_OCTAVE:  n = 12 * floor(W / 12) + k            # Do..Si dell'ottava che contiene W
SPLIT:        n = W + ((k - W) mod 12)              # la finestra applicata alla nota singola
```

- In Split il punto di divisione è `W mod 12` e il dial lo sposta `[M]`. Con questa formula i tasti **sotto** il punto di split suonano un'ottava sopra quelli dal punto in su; l'articolo del supporto dice il contrario a parole: lato da verificare `[V]` (T-18).
- **ACC-081** `SINGLE_NOTES_TOGGLE` DEVE alternare `SPLIT` e `FULL_OCTAVE` `[M]`; se una nota singola suona e la sua altezza cambia, si applica ACC-077.
- **ACC-082** La tastiera interna è **monofonica**: c'è un solo tasto attivo alla volta `[M]` (articolo sul MIDI In). Un nuovo `KEY_DOWN` con un tasto già attivo DEVE sostituirlo (priorità all'ultimo): note-off dell'accordo o nota precedente, risoluzione del nuovo. Il `KEY_UP` successivo del tasto sostituito DEVE essere ignorato; il rilascio del tasto attivo spegne tutto anche se un altro tasto è ancora fisicamente tenuto (nessun ritorno al tasto precedente) `[V]` (T-22).

### 5.5 Transpose
- **ACC-083** Il transpose DEVE spostare **tutta l'uscita** (treble, basso, chord block) di `transpose` semitoni, applicato dopo voicing e performance `[M]`. Gamma −12…+12 `[V]` (T-14). Le note fuori da 0…127 DEVONO essere scartate (né note-on né note-off).
- **ACC-084** Key mode, quantizzazione armonica e finestre lavorano sui tasti **non** trasposti `[D]`; il transpose non accende né spegne la Key mode `[M]` (FW 3.90).
- **ACC-085** Un cambio di transpose mentre suona un accordo DEVE ri-attaccarlo con la regola di ACC-077 `[V]`.

---

## 6. Key mode

### 6.1 Tonalità
**ACC-090** Le tonalità DEVONO essere 42: 21 radici × maggiore/minore, con grafie enarmoniche distinte, più lo stato spento `[O]` (tabella del firmware) `[M]` (`Off` dalla 3.90).

| Indice (magg. / min.) | Radice | pc | | Indice | Radice | pc |
|---|---|---|---|---|---|---|
| 0 / 21 | C | 0 | | 11 / 32 | G♭ | 6 |
| 1 / 22 | C# | 1 | | 12 / 33 | G | 7 |
| 2 / 23 | D♭ | 1 | | 13 / 34 | G# | 8 |
| 3 / 24 | D | 2 | | 14 / 35 | A♭ | 8 |
| 4 / 25 | D# | 3 | | 15 / 36 | A | 9 |
| 5 / 26 | E♭ | 3 | | 16 / 37 | A# | 10 |
| 6 / 27 | E | 4 | | 17 / 38 | B♭ | 10 |
| 7 / 28 | E# | 5 | | 18 / 39 | B | 11 |
| 8 / 29 | F♭ | 4 | | 19 / 40 | B# | 0 |
| 9 / 30 | F | 5 | | 20 / 41 | C♭ | 11 |
| 10 / 31 | F# | 6 | | | | |

- **ACC-091** Scale `[M]` (il minore è naturale, terzo video ufficiale di aggiornamento: Fa# minore = F# G# A B C# D E):

```c
static const uint8_t ACC_SCALE_MAJ[7] = { 0, 2, 4, 5, 7, 9, 11 };
static const uint8_t ACC_SCALE_MIN[7] = { 0, 2, 3, 5, 7, 8, 10 };   /* minore naturale */
```

- **ACC-092** Le scale modali, la minore armonica e la melodica NON DEVONO esserci nella configurazione di default (non esistono sull'originale) `[O]`.

### 6.2 Grafia dei gradi
**ACC-093** La grafia del grado `d` (0…6) DEVE essere calcolata così `[D]`:

```text
LETTERS = C D E F G A B,  NAT_PC = 0 2 4 5 7 9 11
lettera(d) = LETTERS[(lettera_tonica + d) mod 7]
pc(d)      = (pc_tonica + SCALA[d]) mod 12
alter(d)   = ((pc(d) - NAT_PC[lettera(d)] + 6) mod 12) - 6        # -2..+2 → bb, b, —, #, x
```

Esempio: D# maggiore = D# E# F𝄪 G# A# B# C𝄪 (a display `Fx`, `Cx`); F♭ maggiore = F♭ G♭ A♭ B𝄫 C♭ D♭ E♭.

### 6.3 Quantizzazione armonica
**ACC-094** Con Key mode accesa e **nessun tipo tenuto**, il tasto `k` DEVE dare l'accordo:

```text
in_scala(p) = ((p - tonica) mod 12) ∈ SCALA
q(p)        = p mod 12      se in_scala(p)
            = (p - 1) mod 12 altrimenti                 # la nota fuori scala scende di un semitono
note        = { q(k), q(k+4), q(k+7) }                  # pitch class
basso       = q(k)
```

- `[D]`, coerente con tutti gli esempi documentati `[M]`: C# in C = Csus; E♭ in C = D G A; F# in C = F A C; D in C = Dm; F in Fa# minore = Esus; in La maggiore E e poi Esus.
- `q(p)` è sempre in scala: nelle scale maggiore e minore naturale non ci sono due semitoni consecutivi fuori scala `[D]`.
- Sui tasti in scala dà le triadi diatoniche (in C: C, Dm, Em, F, G, Am, Bdim) `[M]`.
- **ACC-095** Con un **tipo tenuto** la tonalità è scavalcata: l'accordo è quello di §2 sulla radice `k` non quantizzata, con estensioni cromatiche (ACC-021) e basso `k` `[M]`.
- **ACC-096** Le estensioni DEVONO suonare anche senza tipo tenuto `[M]`, con note diatoniche `[D]`:

```text
d = indice di (q(k) - tonica) mod 12 in SCALA           # grado della nota quantizzata
E6            → tonica + SCALA[(d + 5) mod 7]
E9            → tonica + SCALA[(d + 1) mod 7]
E7MIN, E7MAJ  → tonica + SCALA[(d + 6) mod 7]           # le due settime danno la stessa nota [O]
```

Equivale a: 6, 9 e M7 scendono di un semitono se fuori scala, m7 sale. Esempi in C: E + 9 = F (♭9); G + M7 = F, nome `G⁷`.

### 6.4 Nome in Key mode
**ACC-097** Senza tipo tenuto il nome DEVE essere ricavato dalle note `[D]`:

```text
nomeDaNote(triade, basso b):
  candidati = [b] + altre pc della triade in ordine crescente di (p - b) mod 12
  per r in candidati:
      I = { (p - r) mod 12 per p in triade }
      se I == MAJ|MIN|SUS|DIM: radice = r, quality = tipo; break
  se nessuno: radice = b, quality = ""                   # non succede con le scale previste
  slash = (radice != b) ? b : nessuno                    # es. A# in C = "Dm/A"
  apici: E6 → "6", E9 → "9"; settima (E7MIN o E7MAJ) secondo l'intervallo reale fra la nota
         aggiunta e la radice: 11 → "M7"; altrimenti "7" (o "m7" se quality == "sus")   [M] FW 3.32
  n = numero di apici distinti (le due settime contano una); n == 3 → "JAZZ"; n == 4 → impossibile
```

- La stringa reale sui tasti fuori scala (es. A# in C) non è documentata: `Dm/A` è un default `[V]` (T-11).

### 6.5 Tabelle di riferimento (default di test)
**ACC-098** Il motore DEVE riprodurre queste tabelle `[D]`. Le colonne 6, 7 e 9 sono la nota aggiunta da ACC-096.

**Do maggiore**

| Tasto | | Note | Nome | 6 | 7 | 9 |
|---|---|---|---|---|---|---|
| C | in | C E G | C | A | B | D |
| C# | fuori | C F G | Csus | A | B | D |
| D | in | D F A | Dm | B | C | E |
| D# | fuori | D G A | Dsus | B | C | E |
| E | in | E G B | Em | C | D | F |
| F | in | F A C | F | D | E | G |
| F# | fuori | F A C | F | D | E | G |
| G | in | G B D | G | E | F | A |
| G# | fuori | G C D | Gsus | E | F | A |
| A | in | A C E | Am | F | G | B |
| A# | fuori | A D F | Dm/A | F | G | B |
| B | in | B D F | Bdim | G | A | C |

**Do minore (naturale)**

| Tasto | | Note | Nome | 6 | 7 | 9 |
|---|---|---|---|---|---|---|
| C | in | C E♭ G | Cm | A♭ | B♭ | D |
| C# | fuori | C F A♭ | Fm/C | A♭ | B♭ | D |
| D | in | D F A♭ | Ddim | B♭ | C | E♭ |
| E♭ | in | E♭ G B♭ | E♭ | C | D | F |
| E | fuori | E♭ A♭ B♭ | E♭sus | C | D | F |
| F | in | F A♭ C | Fm | D | E♭ | G |
| F# | fuori | F B♭ C | Fsus | D | E♭ | G |
| G | in | G B♭ D | Gm | E♭ | F | A♭ |
| A♭ | in | A♭ C E♭ | A♭ | F | G | B♭ |
| A | fuori | A♭ C E♭ | A♭ | F | G | B♭ |
| B♭ | in | B♭ D F | B♭ | G | A♭ | C |
| B | fuori | B♭ E♭ F | B♭sus | G | A♭ | C |

**La maggiore** (stesse note di Fa# minore)

| Tasto | | Note | Nome | | Tasto | | Note | Nome |
|---|---|---|---|---|---|---|---|---|
| C | fuori | B E F# | Bsus | | F# | in | F# A C# | F#m |
| C# | in | C# E G# | C#m | | G | fuori | F# B D | Bm/F# |
| D | in | D F# A | D | | G# | in | G# B D | G#dim |
| D# | fuori | D F# A | D | | A | in | A C# E | A |
| E | in | E G# B | E | | A# | fuori | A D E | Asus |
| F | fuori | E A B | Esus | | B | in | B D F# | Bm |

### 6.6 Comandi
- **ACC-099** `KEY_MODE_TOGGLE` accende e spegne la Key mode; `KEY_SELECT` sceglie l'indice 0…41 `[M]`. La selezione rapida (Key tenuto + tasto, con Min tenuto per il minore) è un gesto dell'interfaccia che produce `KEY_SELECT` e accende la Key mode `[M]` (FW 3.84).
- **ACC-100** Il cambio di tonalità o l'accensione della Key mode mentre suona un accordo NON DEVE ri-attaccarlo: vale dal tasto successivo `[V]`.

---

## 7. Play Style

### 7.1 Stato
**ACC-110** Il motore DEVE mantenere: tasto attivo (o nessuno) con velocity; tipi tenuti **in ordine di pressione**; estensioni tenute; accordo corrente (note treble attive, basso, nome); flag `locked` (solo `ADVANCED`); flag `chord_from_type` (l'accordo corrente viene da un tipo o dalla Key mode).

**ACC-111** La funzione di risoluzione, usata da tutti i Play Style, DEVE essere:

```text
resolve(k, types, exts, style):
  se |types| >= 2 e secret_consentito(style):
      s = match(types, exts)                           # §3
      se s: return CHORD(root=k, mask=s.mask | extra(exts), bass=k, name=s)
  se types non vuoto:
      t = ultimo premuto fra i tenuti                   # ACC-025
      return CHORD(root=k, mask=TYPE_MASK[t] | ext_mask(exts), bass=k, name=nome(k,t,exts))
  se key_mode:
      return KEYCHORD(note={q(k),q(k+4),q(k+7)} ∪ ext_in_key(k,exts), bass=q(k), name=nomeDaNote(...))
  return SINGLE(k)                                      # le estensioni sono ignorate
```

### 7.2 Simple
**ACC-112** In `SIMPLE` `[M]`:
- `KEY_DOWN(k)`: risolve con tipi ed estensioni tenuti **in quel momento** e suona.
- `TYPE_DOWN/UP`, `EXT_DOWN/UP` con il tasto tenuto: **nessun effetto sul suono**; valgono dal `KEY_DOWN` successivo. Con Maj + C che suona, rilasciare Maj e premere Min non cambia nulla `[O]` (video Quick Start).
- `KEY_UP(k)` del tasto attivo: note-off di tutto.
- Extension Addition non si applica.

### 7.3 Advanced
**ACC-113** In `ADVANCED` `[M]`:
- `KEY_DOWN(k)`: suona `resolve(...)`; senza tipo e senza Key mode è la nota singola. `locked = false`.
- `TYPE_DOWN(t)` con il tasto tenuto e `locked == false`: **ri-attacca** con `resolve(...)` (note-off di tutto il treble, note-on della nuova voicing). Vale anche per il passaggio da nota singola ad accordo (ordine nota → tipo) `[M]` (FW 3.84).
- `TYPE_UP(t)`: nessun effetto sul suono. Se dopo il rilascio non resta nessun tipo tenuto e l'accordo veniva da un tipo, `locked = true`: l'accordo resta fino al rilascio del tasto e i `TYPE_DOWN` successivi sono ignorati `[M]` (testo 2025: "rilasciando il tipo l'accordo resta fino al rilascio del tasto").
- `EXT_DOWN(e)` con un accordo che suona e almeno un tipo tenuto, oppure con un accordo di Key mode: si applica Extension Addition (§7.5) `[M]`. Ordine nota → tipo → estensione supportato `[M]` (FW 3.84).
- `EXT_DOWN(e)` con una nota singola, o con `locked == true`: ignorato `[D]`.
- `EXT_UP(e)`: nessun effetto sul suono (la nota resta fino al rilascio del tasto) `[V]` (T-26).
- `KEY_UP(k)` del tasto attivo: note-off di tutto.

### 7.4 Free
**ACC-114** In `FREE` vale `ADVANCED` con queste differenze `[M]` (testo 2026: gli accordi si cambiano o ri-attaccano più volte):
- `locked` non diventa mai vero: ogni `TYPE_DOWN` con il tasto tenuto ri-attacca, anche dopo che tutti i tipi sono stati rilasciati.
- `TYPE_UP`: l'accordo resta.
- `EXT_DOWN/UP` senza tipo tenuto (e fuori Key mode): non alterano le estensioni dell'accordo che suona `[M]` (FW 3.84).
- **ACC-115** Variante di compatibilità `ACC_COMPAT_FREE_2025` (spenta): quando, con il tasto tenuto, l'ultimo tipo viene rilasciato, l'accordo si spegne e torna la nota singola del tasto `[M]` (testo 2025) `[V]` (T-21).

### 7.5 Extension Addition
**ACC-116** Quando un'estensione si aggiunge a un accordo che suona (`ADVANCED` e `FREE`) `[M]`:
- `ADD_NOTE`: calcola la nuova voicing con la stessa `W`; emette note-on **solo** delle note nuove, con la velocity dell'attacco originale; le note già attive continuano.
- `PLAY_CHORD`: ri-attacco completo (note-off di tutto, note-on della nuova voicing).
- Con una performance attiva vale ACC-180.
- **ACC-117** Rilasciare o premere tipi ed estensioni NON DEVE produrre rumori o note spurie: nessun note-off/on per note che non cambiano, salvo il ri-attacco richiesto `[M]` (FW 3.21).

### 7.6 Tabella riassuntiva
| Sequenza | Simple | Advanced | Free |
|---|---|---|---|
| tasto da solo | nota singola `[M]` | nota singola `[M]` | nota singola `[M]` |
| tipo, poi tasto | accordo `[M]` | accordo `[M]` | accordo `[M]` |
| tasto, poi tipo | resta la nota singola `[M]` | accordo `[M]` | accordo `[M]` |
| tasto + tipo tenuti, secondo tipo | nessun cambio `[O]` | ri-attacco `[M]` | ri-attacco `[M]` |
| rilascio di tutti i tipi, tasto tenuto | l'accordo resta `[M]` | resta, bloccato `[M]` | resta, ri-attaccabile `[M]` |
| estensione con accordo attivo | dal tasto successivo `[D]` | Add Note / Play Chord `[M]` | Add Note / Play Chord `[M]` |
| estensione senza tipo tenuto | — | ignorata `[D]` | ignorata `[M]` |

---

## 8. Basso

- **ACC-140** Il basso DEVE essere la **fondamentale** dell'accordo nel registro del Bass Voicing: `nb = place(bass_pc, WB)` `[M]`. Gli slash chord non esistono; unica eccezione la Key mode, dove `bass_pc = q(k)` (es. Dm/A) `[D]`.
- **ACC-141** Il basso è **monofonico** lato motore: al massimo un note-on di basso attivo `[O]`.
- **ACC-142** Il basso NON DEVE passare dalla performance: niente strum, arp, pattern o harp; parte al `KEY_DOWN` (o al ri-attacco) e si spegne al `KEY_UP` `[O]`.
- **ACC-143** La velocity del basso è quella del tasto (dopo ACC-014) `[V]` (T-10).
- **ACC-144** Modi `[M]` (comportamento dettagliato `[D]`):

| Modo | Nota singola (tasto senza tipo, Key mode spenta) | Accordo (tipo, Secret o Key mode) |
|---|---|---|
| `CHORDS_ONLY` | treble: nota singola; basso: nessuno | treble: accordo; basso: fondamentale |
| `UNISON_BASS` | treble: nota singola; basso: stessa pc in `WB` | treble: accordo; basso: fondamentale |
| `BASS_SINGLE_NOTES` | treble: nessuno; basso: la nota in `WB` | treble: accordo; basso: fondamentale |
| `SOLO` | treble: nessuno; basso: la nota in `WB` | treble: nessuno; basso: fondamentale |

- **ACC-145** Con il basso **spento** non esce nessun evento `BASS`. In `BASS_SINGLE_NOTES` con basso spento la nota singola DEVE suonare sul treble `[M]` (FW 3.90). In `SOLO` con basso spento non suona nulla `[V]`.
- **ACC-146** In `SOLO` e quando il treble tace (tabella sopra) NON DEVONO uscire eventi `TREBLE` né `CHORD_BLOCK` `[V]`.
- **ACC-147** Al cambio di accordo con la nota di basso diversa (nuovo tasto in priorità all'ultimo, ri-attacco con fondamentale diversa), il motore DEVE emettere il note-on del nuovo basso **prima** del note-off del vecchio, allo stesso offset, così il motore del basso può applicare glide e modi legato `[D]`. Se la nota è uguale, il basso NON si ri-attacca su cambi di tipo o estensione `[V]`.
- **ACC-148** `BASS_TOGGLE` accende e spegne il basso; se il basso suona e viene spento: note-off immediato `[M]`. La scorciatoia Bass Voicing tenuto + Bass produce lo stesso comando `[O]`.
- **ACC-149** Volume del basso (0…99), suono di basso (12 preset), glide e bend sono parametri della sezione suono, non del motore `[M]`.

---

## 9. Performance

### 9.1 Modi
**ACC-160** I modi DEVONO essere questi; `amount = 0` = spento per tutti `[M]`.

| Indice | Modo | Etichetta overlay | Amount | Il valore regola | Etichetta |
|---|---|---|---|---|---|
| 0 | `OFF` | — | — | accordo a blocco | `[M]` |
| 1 | `STRUM` | Strum | 1…10 | durata dello strum, 1 = il più veloce | `[O]` |
| 2 | `STRUM2` | Strum 2 Oct | 1…10 | come Strum, su 2 ottave | modo `[M]`; gamma `[V]` (T-09) |
| 3 | `SLOP` | Slop | 1…10 | quantità di imprecisione | modo `[O]`; gamma `[V]` (T-09) |
| 4 | `ARP` | Arpeggiate | 1…6 | tipo di arpeggio (§9.5) | `[O]` |
| 5 | `ARP2` | Arp 2 Octaves | 1…6 | come Arp, su 2 ottave | modo `[M]`; gamma `[V]` |
| 6 | `PATTERN` | Pattern | 1…13 | numero del pattern | `[O]` |
| 7 | `HARP` | Harp | 1…10 | velocità della cascata | modo `[M]`; gamma `[V]` (T-09) |

- **ACC-161** Il modo interno "Two Note" (indice 8 nel firmware) NON DEVE essere esposto `[O]`.
- **ACC-162** Modo e amount appartengono al **Sound**: ogni preset ha i suoi default e uno User Sound li salva; con il **Lock** attivo restano invariati al cambio di Sound `[M]`. Il motore riceve `PERF_SET` dalla logica dei preset (`20-suono.md`); il Lock è stato dell'interfaccia.
- **ACC-163** La performance si applica solo al **treble** (canale Performance). Il `CHORD_BLOCK` esce sempre a blocco, qualunque sia la performance `[M]`; il basso segue ACC-142.
- **ACC-164** Tutte le modalità a tempo DEVONO usare il clock interno (§10.1) e quindi seguire il BPM `[M]`.
- **ACC-165** L'insieme di partenza della performance è la voicing treble corrente ordinata in senso crescente (`N[0]` la più bassa, `n` note). Vale anche per la nota singola (`n = 1`) `[D]`.
- **ACC-166** La velocity di ogni nota di Strum, Strum 2 Oct, Slop, Arp e Harp è quella del tasto `[V]` (T-10); per il Pattern vale ACC-177.

### 9.2 Strum e Strum 2 Oct
**ACC-167** Lo strum DEVE suonare le note dal basso verso l'alto, senza ripetizioni, tutte tenute fino al rilascio `[M]`:

```text
STRUM:   seq = N[0..n-1]
STRUM2:  seq = N[0..n-1] seguito da N[0..n-1] + 12           # ordinato crescente
dt       = 2 * amount   tick                                   [V] (T-06)
nota i:  note-on a t0 + i*dt; note-off al rilascio (o al ri-attacco)
```

- A 120 BPM un tick vale 5,208 ms: amount 1 = 10,4 ms fra due note, amount 10 = 104 ms `[V]`.
- La prima nota parte al `KEY_DOWN`, non sulla griglia; i ritardi successivi sono multipli di tick, quindi seguono il BPM (FW 3.84: Strum, Slop e Harp quantizzati) `[V]` (T-06).

### 9.3 Harp
**ACC-168** L'Harp DEVE essere una cascata ascendente su più ottave, tenuta fino al rilascio `[M]`:

```text
seq = N + 0, N + 12, N + 24   (concatenati, crescenti)        HARP_OCTAVES = 3   [V] (T-06)
dt  = amount tick                                              [V] (T-06)
```

- Le note oltre 127 si scartano; il limite di voci si applica con ACC-252.

### 9.4 Slop
**ACC-169** Lo Slop DEVE essere uno strum dal basso all'alto con ritardi casuali per nota, **diversi a ogni pressione** `[O]`:

```text
nota i:  t_i = t0 + i*2 + r_i   tick,   r_i uniforme in [0, 3*amount]         [V] (T-06)
```

- **ACC-170** Il generatore casuale DEVE essere uno xorshift32 nello stato del motore, inizializzabile con `acc_seed(uint32_t)` (seed 0 vietato: diventa 1). `r = x mod (3*amount + 1)` con un nuovo `x` per nota, nell'ordine delle note. Nessuna funzione `rand()` di libreria.

### 9.5 Arp e Arp 2 Oct
**ACC-171** Tipi dell'arpeggio per amount `[O]`:

| Amount | Tipo | Passo | Direzione |
|---|---|---|---|
| 1 | 8 Up | 1/8 = 48 tick | su |
| 2 | 8 Down | 48 tick | giù |
| 3 | 8 UpDown | 48 tick | su e giù |
| 4 | 16 Up | 1/16 = 24 tick | su |
| 5 | 16 Down | 24 tick | giù |
| 6 | 16 UpDown | 24 tick | su e giù |

**ACC-172** Sequenza e tempi:

```text
base = N (ARP) | N ∪ (N + 12) (ARP2), crescente; m = |base|
Up:      base[0], base[1], …, base[m-1]
Down:    base[m-1], …, base[0]
UpDown:  base[0..m-1] poi base[m-2..1]         # estremi non ripetuti; ciclo 2m-2 (m=1: ciclo 1; m=2: ciclo 2)   [V] (T-07)
gate     = 50% del passo                                                                                          [V] (T-07)
```

- Ogni nota della voicing entra nell'arpeggio: più note danno una sequenza più lunga `[M]`. Il ciclo si ripete finché il tasto è tenuto; niente latch `[O]`.
- **ACC-173** Fase `[V]` (T-07): al `KEY_DOWN` senza arpeggio in corso, l'arpeggio parte subito (passo 0 all'offset del tasto) e il suo orologio di passo riparte da lì. Con un nuovo tasto premuto **prima** di rilasciare il precedente (legato), l'arpeggio continua con la stessa fase e lo stesso indice (preso modulo la nuova lunghezza) sulle note nuove `[O]` (bisogna suonare legato per restare a tempo).
- **ACC-174** Il comportamento osservato nel 2025 "due tasti insieme danno un accordo semplice" è un difetto e NON DEVE essere replicato `[O]`.

### 9.6 Pattern
**ACC-175** I pattern DEVONO essere 13 sequenze ritmiche fisse, non programmabili, scelte per numero, con dinamica incorporata; il ritmo NON cambia con il numero di note; possono suonare 2–3 note insieme `[M]` `[O]`. Il loro contenuto è ignoto: Stame usa i default provvisori di ACC-178 `[V]` (T-08).

Formato dei dati (in `core/acc_patterns.c`, tabella costante):

```c
typedef struct { uint8_t step;      /* 0..15, passo di 1/16 = 24 tick */
                 uint8_t idx_mask;  /* bit i = indice di nota i (0..7) suonato insieme */
                 uint8_t vel; } acc_pat_ev;       /* velocity del passo 1..127 */
typedef struct { uint8_t len_steps; uint8_t n_ev; const acc_pat_ev *ev; } acc_pattern;
```

- **ACC-176** Mappa degli indici `[V]` (T-08): indice `i` → `N[i mod n] + 12 * floor(i / n)`. Durata di ogni nota: `PATTERN_GATE` = 20 tick `[V]`. Il pattern riparte da capo a fine battuta e segue la fase di ACC-173.
- **ACC-177** Velocity della nota: `round(vel_passo * vel_tasto / 127)`, minimo 1 `[M]` (FW 3.60); con Velocity Sense spento `vel_tasto = VEL_FIXED` `[M]` (FW 3.84).
- **ACC-178** Pattern provvisori `[V]` (T-08). Notazione: 16 passi da 1/16; `.` = pausa; cifre = indici suonati insieme; `!` = accento (vel 127); `'` = debole (vel 70); senza segno = vel 100.

| # | Passi 0…15 |
|---|---|
| 1 | `012! . . 012 . . 012 . 012! . . 012 . . 012 .` |
| 2 | `0! 12 . 12 0 12 . 12 0! 12 . 12 0 12 . 12` |
| 3 | `0! . 12 . 0 . 12 . 0! . 12 . 0 . 12 .` |
| 4 | `012! . . . . . 012 . . . 012 . . . . .` |
| 5 | `0! 1 2 1 0 1 2 1 0! 1 2 1 0 1 2 1` |
| 6 | `01! . 2 . 01 . 2 2 01! . 2 . 01 . 2 .` |
| 7 | `0! . . 0 . . 0 . 12! . . 12 . . 12 .` |
| 8 | `012! . 012' . 012 . 012' . 012! . 012' . 012 . 012' .` |
| 9 | `0! 2 1 2 0 2 1 2 0! 2 1 2 0 2 1 2` |
| 10 | `. 012! . 012 . 012! . 012 . 012! . 012 . 012! . 012` |
| 11 | `0! . 1 . 2 . 3 . 2 . 1 . 0 . 1 .` |
| 12 | `012! . . . . . . . 01 . 2 . 01 . 2 .` |
| 13 | `02! . 1 02 . 1 02 . 1 02 . 1 02 . 1 .` |

I preset di fabbrica usano i pattern 2, 3, 4, 6, 7, 8 e 13 `[O]`: sono i primi da registrare.

### 9.7 Interazioni
- **ACC-179** Un ri-attacco (dial, tipo in Advanced/Free, Play Chord, transpose) con performance attiva DEVE: per `STRUM`, `STRUM2`, `SLOP`, `HARP` spegnere tutto e ripartire dall'inizio della sequenza all'offset del ri-attacco; per `ARP`, `ARP2`, `PATTERN` continuare con la stessa fase e lo stesso indice sulle note nuove, senza ripartire `[V]` (T-04, T-19).
- **ACC-180** `ADD_NOTE` con performance attiva `[D]`: in `STRUM`, `STRUM2`, `SLOP`, `HARP` le note nuove partono subito (note-on immediato, versione a 2 o 3 ottave compresa); in `ARP`, `ARP2`, `PATTERN` le note nuove entrano nella sequenza dal passo successivo.
- **ACC-181** Al `KEY_UP` del tasto attivo ogni modo DEVE spegnere subito le note attive e cancellare gli eventi futuri già programmati (note-off corretti di Strum, Harp e Arp `[M]` FW 3.21/3.60).
- **ACC-182** Un `PERF_SET` mentre un accordo suona DEVE valere dal tasto successivo; l'accordo in corso continua con il modo precedente fino al rilascio `[V]`.
- **ACC-183** Gli eventi programmati nel futuro DEVONO stare in una coda statica ordinata per tick (capacità `ACC_SCHED_MAX` = 64 eventi); a coda piena gli eventi in eccesso si scartano e un contatore di diagnostica si incrementa.

---

## 10. BPM, clock, metronomo, Beat, batteria

### 10.1 Clock interno
- **ACC-200** Il clock interno DEVE avere **96 tick per semiminima** (`ACC_PPQN` = 96): divide in modo esatto 1/4 (96), 1/8 (48), 1/8t (32), 1/16 (24), 1/16t (16), 1/32 (12) e i 24 PPQN del MIDI clock (1 clock ogni 4 tick).
- **ACC-201** La durata del tick in campioni (`SR * 60 / (BPM * 96)`) DEVE essere accumulata in virgola fissa (32.32) per evitare deriva: dopo `N` tick l'errore cumulativo è sotto un campione. A 48 kHz e 120 BPM un tick vale esattamente 250 campioni.
- **ACC-202** Il BPM DEVE essere intero, 60…200, passo 1 `[O]`; default 120 `[V]` (T-13). Un cambio di BPM, anche mentre suonano Beat, arpeggi o loop, vale dal tick successivo senza riallineare la fase `[M]`.
- **ACC-203** Tap tempo e swing NON DEVONO esistere nella configurazione di default `[O]`.

### 10.2 Trasporto e metrica
- **ACC-204** Il trasporto è "in moto" quando suona il Beat, il metronomo o il looper (count-in, registrazione, riproduzione). All'avvio la posizione riparte da battuta 1, battito 1, tick 0. Il motore DEVE esporre gli eventi `TRANSPORT_START`, `TRANSPORT_STOP` e `CLOCK` (ogni 4 tick, solo in moto) per lo strato MIDI `[O]` (F8 a 24 PPQN solo a trasporto in moto).
- **ACC-205** `TRANSPORT_TOGGLE` (pressione di BPM) avvia o ferma il Beat selezionato; se nessun Beat è selezionato, il metronomo `[M]`. Mentre il looper suona, la pressione fa solo da mute di Beat o metronomo e il tempo del loop continua `[M]` (FW 3.60).
- **ACC-206** Metriche e lunghezza della battuta `[O]` (menu 3.92): `2/4` = 192 tick, `3/4` = 288, `4/4` = 384, `6/8` = 288 (6 crome). Le metriche "continuous" e "off" delle versioni precedenti NON sono implementate `[O]`.

### 10.3 Metronomo
- **ACC-207** Il metronomo DEVE emettere un click per battito (semiminima; in 6/8 per croma) con accento sul primo battito della battuta (in 6/8 accento sulla 1 e sulla 4) `[V]`. Il suono (Beep o Hi Hat) è della sezione suono `[M]`; il motore emette `ACC_ROLE_DRUM` con gli id `CLICK_ACCENT` / `CLICK`.

### 10.4 Beat
- **ACC-208** Il menu dei Beat DEVE avere 16 voci: i 4 tempi in chiave (2/4, 3/4, 4/4, 6/8), che selezionano solo la metrica del metronomo, e 12 Beat con nome, in quest'ordine: Saint Germain, Bossanova, Trap, Disco, Old Skool, Techno, Latin, Millionaire, Bronson, North Soul, Back Beat, Apartment `[O]`. Lo shop parla di 20 Beat: la differenza è aperta (T-29).
- **ACC-209** Ogni Beat DEVE essere una tabella costante di eventi di batteria su griglia di 1/16, lunga una battuta di 4/4, in loop finché il Beat suona; il BPM è globale `[O]`. Formato come `acc_pat_ev` con `idx_mask` sostituito dall'id dello strumento.
- **ACC-210** Il contenuto dei Beat è ignoto: tutti e 12 usano per ora lo stesso pattern provvisorio `[V]` (T-29):

| Strumento | Passi 0…15 |
|---|---|
| `KICK` | `x . . . x . . . x . . . x . . .` |
| `SNARE` | `. . . . x . . . . . . . x . . .` |
| `CLOSED_HAT` | `x . x . x . x . x . x . x . x .` |

  Velocity: 110 sui battiti, 80 sugli altri passi `[V]`.

### 10.5 Batteria a tastiera
- **ACC-211** `DRUMS_TOGGLE` (Bass Voicing tenuto + BPM; dal 16/10/2026 anche T11 del macro pad, `40` MIDI-133; la drum machine dal vivo con kit, Roll, Accent e i pad del banco B è in `40` MIDI-135) DEVE alternare la modalità batteria: i tasti suonano un kit fisso, registrabile nel loop e quantizzabile `[O]`. In questa modalità tipi ed estensioni sono ignorati, il basso tace, nessuna performance; `KEY_DOWN` emette un evento `DRUM` con la velocity del tasto `[D]`.
  - Stame (15/10/2026, Luigi: «lo stesso principio semplice dell'originale per creare loop di batteria») `[D]`: il kit è quello del Beat scelto (`20` SND-537), il colpo suona subito e, se il looper registra o sovraincide, entra nel loop con ruolo `DRUM` al **sedicesimo più vicino della griglia del loop** (24 tick contati da t0, l'inizio del giro; sul tick assoluto ogni colpo finiva spostato fino a 60 ms: revisione del 15/10/2026), senza note-off e senza transpose. Un colpo già sentito dal vivo e che la testina raggiungerebbe subito dopo (quantizzato in avanti in overdub, o oltre la fine della registrazione e quindi a t = 0) si segna e si salta una volta: niente flam. Uno quantizzato all'indietro è già dietro la testina e suona dal giro dopo. Alla commutazione gli accordi tenuti si rilasciano; Reset e demo spengono la modalità. Sulla plancia: «DRUMS» nella zona accordo e le sigle degli strumenti sui tasti C4…B4, che si accendono al colpo (`30` UI-150b).
- **ACC-212** Mappa provvisoria tasti → strumenti, kit in stile CR-78 `[V]` (T-30):

| k | C | C# | D | D# | E | F | F# | G | G# | A | A# | B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| id | `KICK` | `RIMSHOT` | `SNARE` | `CLAP` | `CLOSED_HAT` | `TOM_LO` | `OPEN_HAT` | `TOM_HI` | `MARACAS` | `CONGA` | `COWBELL` | `CYMBAL` |

  La sintesi degli strumenti è in `20-suono.md`.

### 10.6 La batteria che si inventa
- **ACC-215** `[D]` (18/10/2026, `40` MIDI-139) Il Beat può venire da un **generatore** invece che dalla tabella di un Beat (`core/inventa.c`). Il loop è lungo **due battute di 4/4 in sedicesimi** (32 passi) e ha **cinque parti**: cassa, rullante (o battimani o rimshot, secondo lo stile), charleston chiuso, charleston aperto, percussioni.
  - Ogni **stile** dà a ogni passo di ogni parte una **priorità** da 0 (mai) a 9 (sempre: lo **scheletro** dello stile). Stili: Techno, Rock, Funk, Break, Halftime, Dub, Bossa, Electro e, dal 18/10/2026 sera, Acid e Industrial; ognuno ha il suo kit (Techno, Dub e Industrial il kit techno, Rock e Funk studio, Break, Halftime, Electro e Acid 808, Bossa jazz), salvo un kit scelto a mano (MIDI-135). Dal 19/10/2026 (ACC-218) altri venti, ognuno con un kit della libreria sintetizzata (`20` SND-541): House (909 House), Garage (2-Step), Jungle e DnB (Jungle), Dubstep e Trap (808 Trap), Synthwave (Gated 80s), Synthpop (Hex Toms), Lo-Fi (Lo-Fi Dust), Trip Hop (Tape Crate), Chiptune (8-Bit), Glitch (Glitch Bits), EBM (Iron Mill), Afrobeat (Afro Hand), Tabla (Tabla Mist: il teental, con il bayan che tace nel khali), Salsa (Latin Perc: la clave 3-2 come scheletro del rullante), Reggaeton (808 Boom: il dembow), Jazz (Brushes: il ride e il piede del charleston sul 2 e sul 4), Arena (Stadium Rock), Preset (606 Tick). Trenta in tutto; m1 li scorre nell'ordine.
  - La **densità** di una parte, 0…10, fa suonare i passi con priorità ≥ 10 − densità: 0 tace, 1 suona solo lo scheletro, 10 tutto quello che lo stile prevede. I colpi di una densità restano a quella dopo.
  - La **variazione**, 0…99, sposta le priorità di una quantità pseudocasuale **ripetibile** (dipende solo da stile, variazione, parte e passo): da un livello alla variazione 1 fino a tre livelli, pesata per parte (le percussioni si muovono più di cassa e rullante). Lo scheletro non si sposta; un passo a 0 può prendere una priorità bassa e comparire alle densità alte. La variazione sceglie anche fra tre percussioni dello stile. Nella seconda battuta i primi dodici sedicesimi sono uguali alla prima; gli ultimi quattro hanno una variazione loro e rullante e percussioni più probabili: una piccola chiusa. Alla variazione 0 le due battute sono uguali.
  - Velocity: 52 + 7 × priorità, più 6 sui battiti. Charleston chiuso e aperto non suonano insieme.
  - Il **Fill** (T4, MIDI-133) aggiunge tre punti di densità alle parti che suonano e rende più probabili rullante e percussioni negli ultimi quattro sedicesimi della battuta.
  - Il passo è contato dal tick della battuta 1 del trasporto (ACC-204), quindi resta allineato al looper.
- **ACC-216** `[D]` (19/10/2026, `40` MIDI-135, deciso da Luigi il 16/10/2026: «Swing sulla griglia del loop e dei Beat») **Swing.** I sedicesimi dispari, il secondo e il quarto di ogni quarto, suonano `s` tick dopo il loro posto, con `s` = 0…12: 0 è dritto, 12 mette il sedicesimo dispari al 75 % dell'ottavo (a 96 PPQN un tick vale circa il 2 %). Lo swing vale:
  - per i passi del Beat, della tabella o del loop inventato, contati dalla battuta 1 del trasporto; lo swing di un passo si fissa al suo posto dritto, così cambiarlo mentre suona non salta né raddoppia un passo;
  - per i colpi di batteria del loop, contati da t0: il loop li tiene sulla griglia dritta e lo swing li sposta a ogni giro, quindi vale anche per quello che è già registrato. Un colpo dal vivo va al punto più vicino della griglia spostata (a pari distanza quello dopo) e si registra al suo posto dritto;
  - per il Roll (`40` MIDI-135): una ripetizione che cade su un sedicesimo dispari suona spostata ed entra nel loop dritta.
  Metronomo e count-in restano dritti; le note degli accordi non si quantizzano e non si spostano. Il default è 0: senza toccare K4 sotto DRUMS lo swing non c'è, come vuole ACC-203 per la configurazione di default.
- **ACC-217** `[D]` (19/10/2026, `40` MIDI-140) **Drop.** Finché è attivo, i colpi del Beat e quelli di batteria del loop non partono e il motore Bass tace (`20` SND-539); passi del Beat e loop vanno avanti in silenzio, così al rientro sono a tempo. Il Drop comincia subito. Al rilascio finisce sul **battito dopo** della metrica in uso (96 tick in 4/4), oppure subito se il rilascio cade entro un sedicesimo (24 tick) dopo un battito: chi lascia un filo in ritardo sull'uno non perde una battuta. A trasporto fermo finisce subito; una nuova pressione durante l'attesa la annulla. Metronomo, count-in, colpi suonati dal vivo e accordi non cambiano.

### 10.7 La libreria dei Beat
- **ACC-218** `[D]` (19/10/2026, `40` MIDI-141; Luigi: «voglio anche una libreria enorme di batterie») Ai 19 Beat della vetrina si aggiungono **41 Beat di genere**, sessanta in tutto (`BEAT_COUNT` = 61 con il provvisorio di ACC-210). Sono tabelle come quelle di ACC-209 (una battuta di 4/4 in sedicesimi, fino a sei strumenti, `X` = 110, `x` = 80), ognuna con il suo **fill** (MIDI-133) e un **kit della libreria sintetizzata** (`20` SND-541): i Beat suonano anche senza il banco dei campioni. I primi diciannove e i loro kit non cambiano; il menu dei Beat dell'originale (ACC-208) resta quello che è, questa è la lista dei Beat di Stame.

| Genere | Beat (kit) |
|---|---|
| house e techno | House e Deep House (909 House), Tech House (Minimal Click), Rave (909 Rave) |
| garage e breaks | Garage (2-Step), Breakbeat, Jungle e Drum & Bass (Jungle) |
| bassi pesanti | Dubstep (Iron Mill), Footwork (808 Trap), Reggaeton e Dancehall (808 Boom) |
| elettronica | Robot (Robot Pop), Synthwave (Gated 80s), Italo (Linn Pop), Syndrum (Syndrum Disco), Sci-Fi (Laser Lab) |
| lo-fi e downtempo | Lo-Fi (Lo-Fi Dust), Trip Hop (Tape Crate), Ambient Pulse (Deep Space), Steppers (Dub Yard) |
| chip e glitch | Chiptune (8-Bit), Arcade (Arcade), Glitch (Glitch Bits), IDM (Data Rot) |
| industriale | EBM (Iron Mill), Factory (Scrap Yard) |
| acustici | Rock (Acoustic Room), Swing Jazz e Brush Ballad (Brushes), Unplugged e Flamenco (Cajon Box), Rhythm Box (CR Rhythm) |
| dal mondo | Afrobeat e Djembe (Afro Hand), Teental (Tabla Mist: i sedici matra dha dhin dhin dha…), Gamelan (il ciclo con il gong, il kempul e il kenong), Salsa e Cumbia (Latin Perc: clave 3-2, campana, tumbao; il guiro), Taiko, Maqsum (Darbuka Sand: dum tek . tek dum . tek .) |

  Ogni Beat ha uno stile vicino della batteria che si inventa (ACC-215, `inv_groove_of_beat`): il primo tocco delle manopole sotto DRUMS parte da lì (House → House, Teental → Tabla, Rock → Arena…). Nella lista dei Beat accanto a ogni nome c'è il suo kit (`30` UI-177). TV-123.

---

## 11. Looper

### 11.1 Che cosa registra
- **ACC-220** Il looper DEVE registrare **eventi**, non audio `[M]`: gli eventi di uscita `TREBLE`, `BASS` e `DRUM` (già passati dalla performance, prima del transpose), con il tempo in tick relativo all'inizio del loop. Il `CHORD_BLOCK` non si registra `[V]`. Cambiando il BPM cambia la velocità del loop, perché gli eventi sono in tick `[M]`.
- **ACC-221** In riproduzione gli eventi registrati DEVONO uscire con il transpose corrente e passare dai limiti di voce di §12; il suono è quello corrente (non si può cambiare suono durante la registrazione, né fare overdub con un suono diverso) `[O]`.

### 11.2 Macchina a stati
**ACC-222** Stati e transizioni `[M]` (comandi `LOOP_CMD` nella colonna Evento):

| Stato | Evento | Prossimo stato | Azione |
|---|---|---|---|
| `IDLE` | `OPEN` (premi o ruota Loop) | `WAITING` | mostra la Waiting Room |
| `WAITING` | `SYNC_SET(s)` | `WAITING` | `s` ∈ {`FREE`, `BARS_1`, `BARS_2`, `BARS_4`, `BARS_8`, `BARS_16`} |
| `WAITING` | `REC`, sync a battute | `COUNT_IN` | trasporto riavviato; count-in di 1 battuta con metronomo `[M]` (FW 3.90) |
| `WAITING` | `REC`, sync `FREE` | `ARMED` | attende la prima nota |
| `ARMED` | primo evento registrabile | `RECORDING` | t = 0 al primo evento `[M]` |
| `COUNT_IN` | fine della battuta | `RECORDING` | t = 0 all'inizio della battuta successiva |
| `RECORDING` | sync a battute, fine delle N battute | `PLAYING` | lunghezza = N × battuta; strato 0 chiuso |
| `RECORDING` | `STOP`, sync `FREE` | `PLAYING` | lunghezza = tick trascorsi; strato 0 chiuso |
| `PLAYING` | `PAUSE` | `PAUSED` | note-off di tutte le note del loop |
| `PAUSED` | `PLAY` | `PLAYING` | riparte da t = 0 `[V]`; il trasporto riparte con il loop, così Beat e loop restano allineati `[D]` |
| `PLAYING` | `OVERDUB` | `OVERDUB` | apre un nuovo strato |
| `OVERDUB` | `STOP` | `PLAYING` | chiude lo strato `[M]` |
| `PLAYING`, `PAUSED` | `UNDO` | stesso | toglie l'ultimo strato; con il solo strato 0 il comando diventa `CLEAR` `[M]` |
| `OVERDUB` | `UNDO` o `CLEAR` | `PLAYING` | annulla lo strato in corso `[M]` |
| `PLAYING`, `PAUSED` | `CLEAR` | `WAITING` | cancella tutti gli strati `[V]` |
| qualunque ≠ `IDLE` | `EXIT` (Loop tenuto 2 s → Exit; T10 Save Loop del macro pad) | `IDLE` | ferma la riproduzione; il loop resta in RAM fino allo spegnimento `[M]`. Fatto il 16/10/2026 (`LOOP_C_EXIT`, `40` MIDI-133): in REC e OVERDUB chiude prima lo strato, nel count-in non tiene niente; Clear da fermo svuota la RAM `[D]` |
| qualunque | `HARD_EXIT` (Bass Voicing tenuto + Loop) | `IDLE` | ferma e **cancella** il loop non salvato; ripristina metronomo e anello `[M]` (FW 3.84, 3.90) |
| `IDLE` con loop in RAM | `OPEN` | `PLAYING` | riprende il loop in memoria da t = 0 `[V]` (fatto il 16/10/2026: `LOOP_C_PRESS` da `IDLE` con eventi in RAM) |

- **ACC-223** Count-in: 1 battuta della metrica corrente `[M]`; il click del count-in ha un suono distinto `[O]`. Il comportamento in 3/4 e 6/8 è da verificare `[V]` (T-28).
  - Il metronomo clicca durante il count-in qualunque Beat sia scelto o acceso; con un Beat la metrica è 4/4 (ACC-209) `[D]`. Per ora il clic è quello del metronomo, non un suono distinto `[D]`.
  - Le note suonate nell'ultimo sedicesimo del count-in (`LOOP_EARLY` = 24 tick) entrano nel loop a t = 0: chi attacca un filo prima della battuta non perde l'accordo `[D]`.
- **ACC-224** In `RECORDING` e `OVERDUB` il loop già registrato continua a suonare e a ripetersi; in `OVERDUB` tutte le ripetizioni finiscono nello stesso strato. Gli strati sono illimitati sull'originale `[M]`; Stame ne gestisce `ACC_LOOP_LAYERS` = 32.
- **ACC-225** Una nota ancora tenuta quando la registrazione o lo strato si chiude DEVE ricevere un note-off registrato alla fine del loop; una nota tenuta oltre il punto di giro durante l'overdub DEVE avere il note-off registrato a `t mod L` `[D]`.
- **ACC-226** Durante la riproduzione, gli eventi dello stesso tick DEVONO uscire nell'ordine registrato; a ogni giro il motore DEVE chiudere le note del giro precedente rimaste aperte prima dei nuovi note-on della stessa altezza.

### 11.3 Quantizzazione
- **ACC-227** La Quantization DEVE valere solo per la registrazione nel loop, mai per la performance dal vivo `[M]`. Griglie in tick: `Q4` 96, `Q8` 48, `Q8T` 32, `Q16` 24, `Q16T` 16, `Q32` 12 `[M]` (valori) `[D]` (tick).
- **ACC-228** La quantizzazione DEVE spostare **gesti interi**, non singole note `[D]`: ogni evento registrato porta l'istante del `KEY_DOWN` (o del ri-attacco) che l'ha generato; al momento della registrazione si calcola `delta = round_to_grid(t_gesto) - t_gesto` (arrotondamento al multiplo più vicino, a metà verso l'alto) e si applica a tutti gli eventi del gesto. Così strum, slop e arpeggi conservano i loro tempi interni. Gli eventi `DRUM` sono gesti di un solo evento. Il tempo quantizzato si prende modulo la lunghezza del loop.

### 11.4 Salvataggio
- **ACC-229** DEVONO esserci 10 slot, `Loop 01`…`Loop 10`, con `SAVE_AS_NEXT` (primo slot libero), `SAVE_AS(n)` (sovrascrive se occupato), `LOAD(n)`, `DELETE(n)` `[M]` (FW 3.84).
- **ACC-230** Il formato salvato DEVE contenere: versione del formato, metrica, sync, lunghezza in tick, BPM al momento della registrazione (solo informativo), numero di strati e gli eventi `{tick, role, note, vel, on, strato}`. La scrittura su file è della piattaforma (`50-piattaforma-flip.md`); il motore serializza in un buffer fornito dal chiamante.

### 11.5 Capacità
- **ACC-231** Il buffer degli eventi DEVE essere statico: `ACC_LOOP_EVENTS` = 8192 eventi in tutto `[D]` (valore da tarare con il budget di memoria della piattaforma). A buffer pieno gli eventi nuovi non si registrano e lo stato visibile segnala `loop_full`.

### 11.6 Stato per l'interfaccia
- **ACC-232** Il motore DEVE esporre: stato della macchina, sync, numero di battute, posizione corrente e lunghezza in tick (per l'anello di avanzamento con una fessura per battuta), battuta del count-in, numero di strati, `loop_full`, slot caricato.

---

## 12. Note e voci lato accordi

- **ACC-250** Numero di note treble per accordo: 1 (nota singola), 2…8 per i Secret Chords con estensioni extra, 3…7 per gli accordi normali e di Key mode `[D]`. Con `STRUM2`, `ARP2` le note candidate raddoppiano, con `HARP` triplicano.
- **ACC-251** L'allocazione delle voci di sintesi (pool di **16 voci** condiviso fra treble e basso `[O]`) è della sezione suono. Il motore DEVE garantire un limite a monte, così l'allocatore non deve mai rubare una voce ancora tenuta:
  - al massimo `ACC_TREBLE_MAX` = 14 note treble con gate aperto in ogni istante, live e loop insieme `[V]`;
  - al massimo 1 nota di basso con gate aperto (2 per un istante nel cambio legato di ACC-147);
  - così restano almeno 1–2 voci per le code di rilascio, gestite dalla sezione suono.
  La sezione suono DEVE confermare questi numeri (`20-suono.md`, voci).
- **ACC-252** Se un note-on treble porterebbe oltre `ACC_TREBLE_MAX`, il motore DEVE prima emettere il note-off della nota treble aperta da più tempo (allo stesso offset) `[D]`.
- **ACC-253** Se una nota treble già aperta riceve un nuovo note-on alla stessa altezza (live sopra il loop, Strum 2 Oct sopra Harp, ecc.), il motore DEVE emettere prima il suo note-off, così il conteggio resta coerente e non si accumulano voci sulla stessa nota `[D]`. Implementato il 15/10/2026 in `core/motore.c` con un conteggio delle sorgenti per nota (dal vivo e loop, treble e basso): la voce riparte, e si spegne solo quando la rilasciano tutte, così il loop non taglia una nota tenuta dal vivo e viceversa.
  - Revisione del 15/10/2026, looper: una nota suonata in overdub si registra e il giro corrente non la risuona (prima ogni nota sovraincisa partiva due volte); una nota sul tick t0 + len, il primo battere dopo la registrazione, non entra nel loop (diventava un bordone lungo tutto il giro); al punto di giro le note aperte non si chiudono più tutte, così una nota tenuta oltre il giro ha il suo note-off a `t mod L` (ACC-225) e le altre si chiudono prima del loro note-on successivo (ACC-226); `LOOP_C_RESET` svuota il loop in ogni stato (Reset, uscita forzata, fine della demo), mentre Clear in overdub resta l'Undo dello strato.
- **ACC-254** Le note `DRUM` non usano il pool delle 16 voci `[V]` (dipende da `20-suono.md`).

---

## 13. Vettori di test

- **ACC-270** La suite di test unitari di `core` DEVE contenere almeno tutti i vettori di questo paragrafo. Salvo indicazione diversa: `v = 24` (`W = 48`), `vb = 23` (`WB = 36`), basso spento, Key mode spenta, transpose 0, Play Style `SIMPLE`, Single Notes `FULL_OCTAVE`, performance `OFF`, Velocity Sense `ON`, 48 kHz, 120 BPM (1 tick = 250 campioni). I vettori ereditano l'etichetta della regola che verificano; quelli su default `[V]` vanno aggiornati con i risultati dei test di §14.
- **ACC-271** Notazione: `T` = treble, `B` = basso, `H` = chord block; `@n` = offset in campioni dall'evento d'ingresso; "ON T 48 52 55 v100" = note-on treble di 48, 52, 55 a velocity 100.

### 13.1 Accordi e nomi (stato fermo)
| ID | Input | Note treble attese | Nome |
|---|---|---|---|
| TV-01 | Maj + C | 48 52 55 | `C` |
| TV-02 | Maj + G | 50 55 59 | `G` |
| TV-03 | Maj + F | 48 53 57 | `F` |
| TV-04 | Min + A | 48 52 57 | `Am` |
| TV-05 | Dim + B | 50 53 59 | `Bdim` |
| TV-06 | Sus + D | 50 55 57 | `Dsus` |
| TV-07 | Maj + M7 + C | 48 52 55 59 | `C` + `M7` |
| TV-08 | Maj + m7 + C | 48 52 55 58 | `C` + `7` |
| TV-09 | Sus + m7 + C | 48 53 55 58 | `Csus` + `m7` |
| TV-10 | Maj + 9 + C | 48 50 52 55 | `C` + `9` |
| TV-11 | Min + m7 + 9 + D | 48 50 52 53 57 | `Dm` + `79` |
| TV-12 | Maj + M7 + 6 + C | 48 52 55 57 59 | `C` + `M76` |
| TV-13 | Dim + m7 + C | 48 51 54 58 | `Cdim` + `7` |
| TV-14 | Dim + 6 + C | 48 51 54 57 | `Cdim` + `6` |
| TV-15 | Min + m7 + M7 + 9 + C | 48 50 51 55 58 59 | `Cm` + `JAZZ` |
| TV-16 | Dim + 6 + m7 + M7 + 9 + C | 48 50 51 54 57 58 59 | `Cdim` + `WTF` |
| TV-17 | Maj + C# (Key off) | 49 53 56 | `C#` |
| TV-18 | 6 + C (nessun tipo, Key off) | 48 (nota singola) | `C` |
| TV-19 | Maj tenuto, poi Min tenuto, poi C (Secret `OFF`) | 48 51 55 | `Cm` |

### 13.2 Secret Chords (`ALL`)
| ID | Input | Note attese | Nome |
|---|---|---|---|
| TV-20 | Dim + Sus + C | 48 55 | `C` + `5` |
| TV-21 | Maj + Sus + C | 48 52 56 | `C+` |
| TV-22 | Min + Sus + C | 48 51 53 55 | `Cm` + `add4` |
| TV-23 | Min + Dim + 6 + C | 48 51 55 56 | `Cm` + `m6` |
| TV-24 | Maj + Dim + C | 48 52 55 56 | `C` + `m6` |
| TV-25 | Maj + Min + m7 + C | 48 51 52 55 58 | `C7#` + `9` |
| TV-26 | Maj + Min + C (manca m7; Min premuto per ultimo) | 48 51 55 | `Cm` |
| TV-27 | Maj + Sus + C con Secret `SIMPLE_ONLY` e Play Style `ADVANCED` (Sus premuto per ultimo) | 48 53 55 | `Csus` |

### 13.3 Voicing e basso
| ID | Input | Note attese |
|---|---|---|
| TV-30 | Maj + C, `v = 25` (W 49) | 52 55 60 |
| TV-31 | Maj + C, `v = 28` (W 52) | 52 55 60 |
| TV-32 | Maj + C, `v = 29` (W 53) | 55 60 64 |
| TV-33 | Maj + C, `v = 32` (W 56) | 60 64 67 |
| TV-34 | Maj + C, `v = 1` (W 25) | 28 31 36 |
| TV-35 | Maj + C, `v = 60` (W 84) | 84 88 91 |
| TV-36 | Maj + M7 + C, `v = 25` | 52 55 59 60 |
| TV-37 | `VOICING_STEP +1` a `v = 60` | `v` resta 60, nessun evento |
| TV-38 | basso on, Maj + C | T 48 52 55; B 36 |
| TV-39 | basso on, Maj + G | T 50 55 59; B 43 |
| TV-40 | basso on, Maj + C, `vb = 24` (WB 37) | B 48 |
| TV-41 | basso on, Maj + C, `vb = 0` / `vb = 48` | B 24 / B 72 |
| TV-42 | transpose +2, Maj + C, basso on | T 50 54 57; B 38; nome `D` |
| TV-43 | transpose −12, `v = 1`, Maj + C | 16 19 24 |

### 13.4 Note singole
| ID | Input | Nota attesa |
|---|---|---|
| TV-45 | E, `FULL_OCTAVE`, `v = 24` | 52 |
| TV-46 | E, `FULL_OCTAVE`, `v = 29` (W 53) | 52 |
| TV-47 | E, `SPLIT`, `v = 29` | 64 |
| TV-48 | G, `SPLIT`, `v = 29` | 55 |
| TV-49 | C, `SPLIT`, `v = 24` | 48 |

### 13.5 Key mode
| ID | Tonalità | Input | Note treble | Basso (on) | Nome |
|---|---|---|---|---|---|
| TV-50 | C magg. | D | 50 53 57 | 38 | `Dm` |
| TV-51 | C magg. | C# | 48 53 55 | 36 | `Csus` |
| TV-52 | C magg. | F# | 48 53 57 | 41 | `F` |
| TV-53 | C magg. | A# | 50 53 57 | 45 | `Dm/A` |
| TV-54 | C magg. | B | 50 53 59 | 47 | `Bdim` |
| TV-55 | C magg. | G + M7 | 50 53 55 59 | 43 | `G` + `7` |
| TV-56 | C magg. | E + 9 | 52 53 55 59 | 40 | `Em` + `9` |
| TV-57 | C magg. | C + 6 | 48 52 55 57 | 36 | `C` + `6` |
| TV-58 | C magg. | Maj + D (tipo che scavalca) | 50 54 57 | 38 | `D` |
| TV-59 | C min. | G | 50 55 58 | 43 | `Gm` |
| TV-60 | C min. | C# | 48 53 56 | 36 | `Fm/C` |
| TV-61 | C min. | E | 51 56 58 | 39 | `Ebsus` (`E` + `b`, quality `sus`) |
| TV-62 | A magg. | F | 52 57 59 | 40 | `Esus` |
| TV-63 | F magg. | Maj + A# | 50 53 58 | 46 | `Bb` |
| TV-64 | D# magg. | E + M7 (E fuori scala → D#) | 50 51 56 58 | 39 | `D#sus` + `M7`; la nota aggiunta (pc 2) si scrive `Cx` |

### 13.6 Play Style (sequenze; basso on dove indicato)
**TV-70 Simple, cambio tipo ignorato**
1. `TYPE_DOWN MAJ` → nessun evento.
2. `KEY_DOWN C v100` → ON H 48 52 55; ON T 48 52 55 v100.
3. `TYPE_UP MAJ`, `TYPE_DOWN MIN` → nessun evento.
4. `KEY_UP C` → OFF H 48 52 55; OFF T 48 52 55.

**TV-71 Advanced, nota → tipo → estensione (`ADD_NOTE`), basso on (`CHORDS_ONLY`)**
1. `KEY_DOWN C v90` → ON H 48; ON T 48 v90 (nota singola, nessun basso).
2. `TYPE_DOWN MIN` → OFF H 48; OFF T 48; ON H 48 51 55; ON T 48 51 55 v90; ON B 36 v90.
3. `EXT_DOWN E7MAJ` → ON H 59; ON T 59 v90.
4. `EXT_UP E7MAJ` → nessun evento.
5. `KEY_UP C` → OFF H 48 51 55 59; OFF T 48 51 55 59; OFF B 36.

**TV-72 Advanced, `PLAY_CHORD`**: Maj + C, poi `EXT_DOWN E9` → OFF T 48 52 55; ON T 48 50 52 55.

**TV-73 Advanced, blocco dopo il rilascio dei tipi**: Maj tenuto, `KEY_DOWN C`, `TYPE_UP MAJ` (nessun evento), `TYPE_DOWN MIN` → nessun evento; suona ancora 48 52 55.

**TV-74 Free, ri-attacco dopo il rilascio**: come TV-73 ma `FREE` → al `TYPE_DOWN MIN`: OFF T 48 52 55; ON T 48 51 55.

**TV-75 Free 2025 (variante accesa)**: Maj tenuto, `KEY_DOWN C`, `TYPE_UP MAJ` → OFF T 48 52 55; ON T 48.

**TV-76 Priorità all'ultimo tasto**: Maj tenuto, `KEY_DOWN C`, `KEY_DOWN G` → OFF T 48 52 55; ON T 50 55 59. `KEY_UP C` → nessun evento. `KEY_UP G` → OFF T 50 55 59.

**TV-77 Dial con accordo tenuto**: Maj + C (48 52 55), `VOICING_STEP +1` → OFF T 48 52 55; ON T 52 55 60. `VOICING_STEP +1` (W 50) → nessun evento (insieme invariato).

**TV-78 Basso legato**: basso on, Maj tenuto, `KEY_DOWN C`, `KEY_DOWN G` → stesso offset: ON B 43 prima di OFF B 36.

### 13.7 Basso, modi
| ID | Modo | Input | Treble | Basso |
|---|---|---|---|---|
| TV-80 | `UNISON_BASS` | E (singola) | 52 | 40 |
| TV-81 | `BASS_SINGLE_NOTES` | E (singola) | — | 40 |
| TV-82 | `BASS_SINGLE_NOTES`, basso spento | E | 52 | — |
| TV-83 | `SOLO` | Maj + C | — (né T né H) | 36 |
| TV-84 | `CHORDS_ONLY`, Key mode C magg. | D | 50 53 57 | 38 |

### 13.8 Performance (tempi in campioni a 120 BPM, 48 kHz)
| ID | Modo, amount | Input | Eventi treble attesi |
|---|---|---|---|
| TV-90 | `STRUM` 1 | Maj + C v100 | ON 48 @0, 52 @500, 55 @1000; tutti OFF al rilascio |
| TV-91 | `STRUM` 10 | Maj + C | ON 48 @0, 52 @5000, 55 @10000 |
| TV-92 | `STRUM2` 1 | Maj + C | ON 48 @0, 52 @500, 55 @1000, 60 @1500, 64 @2000, 67 @2500 |
| TV-93 | `HARP` 1 | Maj + C | ON 48, 52, 55, 60, 64, 67, 72, 76, 79 a @0, 250, …, 2000 |
| TV-94 | `ARP` 4 (16 Up) | Maj + C | ON 48 @0, OFF 48 @3000, ON 52 @6000, OFF @9000, ON 55 @12000, OFF @15000, ON 48 @18000 … |
| TV-95 | `ARP` 3 (8 UpDown) | Maj + C | passi ogni 12000: 48, 52, 55, 52, 48, 52 …; gate 6000 |
| TV-96 | `ARP` 2 (8 Down) | Maj + M7 + C | 59, 55, 52, 48, 59 … ogni 12000 |
| TV-97 | `ARP2` 1 (8 Up) | Maj + C | 48, 52, 55, 60, 64, 67, 48 … ogni 12000 |
| TV-98 | `ARP` 4, legato | Maj tenuto; C a @0; G a @7000 senza rilasciare C | 48 @0; a @7000 OFF di 52 se aperta, poi il passo 2 a @12000 suona l'indice 2 di {50 55 59} = 59 |
| TV-99 | `PATTERN` 5 (provvisorio) | Maj + C v127 | passo 0: 48 v127 @0; passo 1: 52 v100 @6000; passo 2: 55 @12000; passo 3: 52 @18000; gate 5000 |
| TV-100 | `PATTERN` 5, v64 | Maj + C v64 | passo 0 vel `round(127*64/127)` = 64; passo 1 vel `round(100*64/127)` = 50 |
| TV-101 | `SLOP` 5, seed 1 | Maj + C | proprietà: nota i a `@(i*500 + r_i*250)`, `r_i` ∈ [0, 15]; stessa sequenza con lo stesso seed; sequenza diversa alla pressione successiva |
| TV-102 | qualunque | Maj + C con basso on | B 36 @0 in tutti i modi, senza ritardi |
| TV-103 | `STRUM` 1 | Maj + C, `KEY_UP` a @700 | ON 48 @0, 52 @500; OFF 48 52 @700; il 55 non parte |

### 13.9 Clock e looper
| ID | Scenario | Atteso |
|---|---|---|
| TV-110 | 120 BPM, 48 kHz, 9600 tick | posizione = 2.400.000 campioni esatti |
| TV-111 | 97 BPM, 44,1 kHz, 1.000.000 tick | errore cumulativo < 1 campione rispetto al calcolo in doppia precisione |
| TV-112 | metronomo 4/4 | CLICK_ACCENT a tick 0, CLICK a 96, 192, 288, CLICK_ACCENT a 384 |
| TV-113 | loop `BARS_1`, 4/4: `REC` a tick 0 | count-in tick 0…383; `RECORDING` da 384; `PLAYING` da 768, lunghezza 384 |
| TV-114 | loop Q16: `KEY_DOWN` a tick di loop 16 con `STRUM` 1 | eventi registrati a 24, 26, 28 (gesto spostato di +8, tempi interni conservati) |
| TV-115 | loop Q16: `KEY_DOWN` a tick di loop 380, lunghezza 384 | gesto quantizzato a 384 → registrato a 0 |
| TV-116 | `UNDO` con il solo strato 0 | comportamento di `CLEAR`, stato `WAITING` |
| TV-117 | `HARD_EXIT` da `PLAYING` con loop non salvato | stato `IDLE`, loop cancellato, nessuna nota aperta |
| TV-118 | 2 strati che suonano 15 note treble insieme | 14 note aperte; la più vecchia riceve note-off prima della 15ª |
| TV-119 | batteria che si inventa (ACC-215): ogni stile, variazioni 0, 7, … 98, densità 0…10 | stessa variazione = stessa griglia; scheletro fermo; i colpi di d restano a d + 1; 0 tace, 1 è lo scheletro; il fill aggiunge colpi; un Beat del menu la spegne |
| TV-120 | swing (ACC-216) di 6 e di 12 tick: Beat con un colpo sul passo 1, colpi dal vivo nel loop a pos 37 e 100, Roll a 1/16 in overdub | il passo 1 suona a 30, non a 24; i pari restano dritti; il colpo a pos 37 va a t = 24 e suona a 36 nel giro dopo, quello a 100 resta a 96; il Roll suona a 174 e non a 168, a 192 dritto, e registra solo sulla griglia dritta; senza swing tutto torna dritto |
| TV-122 | Drop (ACC-217): Beat sui passi 0, 4, 8, metronomo acceso; pressione a pos 100, rilascio a 230, di nuovo a 300 e rilascio a 394, poi con un piatto del Beat che suona | dopo 5 ms nessuna voce del Beat e basso a zero; durante il Drop il Beat tace, il metronomo e un colpo dal vivo suonano; rilasciato a 230 aspetta e rientra a 288, con il primo colpo pieno; rilasciato a 394 rientra subito; il piatto di prima non ricompare; da fermo il rilascio è subito |
| TV-123 | libreria dei Beat e degli stili (ACC-218, ACC-215): i 60 Beat e i 30 stili | i primi 19 Beat e i primi 10 stili tengono il loro kit; i nuovi hanno un kit della libreria (`20` SND-541); ogni Beat suona sul passo 0, ha almeno 6 colpi e un fill di almeno 6; nomi unici entro 23 e 11 caratteri; ogni kit della libreria è di almeno un Beat o uno stile; ogni Beat ha uno stile vicino |
| TV-121 | FX del bus della batteria (`20` SND-538): drive 0…10, filtro −10…+10, clic del metronomo | spento (anche dopo essere stato acceso) il bus è identico bit per bit; drive 10 alza l'energia della cassa di oltre il 30 % con il picco sotto 1,2; passa-basso chiuso: il charleston sotto il 5 %; passa-alto aperto: la cassa sotto il 10 %; il clic identico con il filtro chiuso |

---

## 14. Questioni aperte

Tutte le voci confluiscono in `90-questioni-aperte.md`. Per ognuna Stame usa il default indicato finché il test non è fatto. Strumento: l'originale con firmware 3.92, MIDI out su un monitor MIDI (canali 1, 2, 3, con clock), video del display.

| Test | Incognita | Default di Stame | Prova sull'originale |
|---|---|---|---|
| T-01 | Note di Dim + m7 | {0,3,6,10} (ACC-023) | Dim + m7 + C: su ch3 esce B♭ (m7♭5) o A (dim7)? |
| T-02 | Mappa `v` → W, default dopo il Reset, offset del basso | `W = v+24`, `WB = vb+13`, default 24/23 (ACC-073, ACC-075) | Reset; Maj + C con i default; leggere le note; ripetere a `v` = 1, 12, 13, 60 e `vb` = 0, 48 |
| T-03 | Posizione della 9 | sempre in [W, W+11] (ACC-022) | C + 9 su più voicing |
| T-04 | Re-trigger del dial: totale o parziale; con insieme invariato; con performance | totale, solo se l'insieme cambia; strum riparte, arp continua (ACC-077, ACC-179) | Maj + C, uno scatto alla volta; ripetere con Strum e Arp |
| T-05 | Finestra estesa (W+13) | spenta (ACC-079) | C⁹ e Cᴹ⁷: compare una nota oltre W+11? |
| T-06 | Tempi di Strum, Slop, Harp e numero di ottave dell'Harp | dt = 2·amount tick; Slop + 0…3·amount; Harp amount tick, 3 ottave | timestamp a 60, 120, 200 BPM con amount 1, 5, 10 |
| T-07 | Arp: gate, estremi di UpDown, fase, ordine di Arp 2 Oct | gate 50%, estremi non ripetuti, parte al tasto (ACC-172, ACC-173) | monitor MIDI con clock: durate, ripetizioni, partenza rispetto alla griglia |
| T-08 | Contenuto dei 13 pattern, mappa degli indici, gate | tabella provvisoria ACC-178, gate 20 tick | registrare ogni pattern con accordi da 3, 4 e 5 note |
| T-09 | Gamma dell'amount di Strum 2 Oct, Slop, Harp, Arp 2 Oct | 1…10, 1…10, 1…10, 1…6 | girare fino a fondo scala e leggere CC103 |
| T-10 | Curva della velocity, valore di Sense Off, velocity di basso e performance | velocity del tasto; `VEL_FIXED` 100 | velocity in uscita su ch1/ch2 contro la forza; Sense Off |
| T-11 | Key mode: nome sui tasti fuori scala e radice delle estensioni | `Dm/A`, estensioni dal grado di q(k) (ACC-096, ACC-097) | A# + 7 in Do maggiore: nota aggiunta e display |
| T-12 | Grafia della radice con Key off e con transpose | diesis; tonalità effettiva con meno alterazioni | Key off: i tasti neri come C# o D♭? Transpose +1 in C maggiore |
| T-13 | BPM di default, fine corsa | 120; 60…200 | Reset; girare fino agli estremi leggendo CC112 |
| T-14 | Gamma del transpose | −12…+12 | premi e gira il Key fino a fondo scala |
| T-15 | Più tipi senza Secret | vince l'ultimo premuto (ACC-025) | Maj tenuto + Min, poi tasto |
| T-16 | Secret Chords: estensioni extra, estensione richiesta mancante, Maj + Dim con o senza 6, altre combinazioni | ACC-043, ACC-044; S5 senza 6 | Maj + Sus + 9; Min + Dim senza 6; Maj + Dim + 6; tutte le coppie e terne |
| T-17 | Two Note | non esposto | solo se attivabile senza modificare il firmware |
| T-18 | Lato dello Split | formula della finestra (ACC-080) | Single Notes Split, `v = 30`: quali tasti salgono |
| T-19 | Dial e cambio d'accordo durante l'arp | l'arp continua | girare il dial con l'arp in corso |
| T-20 | Accelerazione dell'encoder | fuori dal motore | giro lento contro giro veloce |
| T-21 | Semantica di Free (2025 contro 2026) | 2026, variante spenta | Free: tasto + Maj, rilasciare Maj |
| T-22 | Due tasti tenuti | priorità all'ultimo, nessun ritorno | tenere C, premere G, rilasciare G |
| T-23 | Glide dei bassi | `20-suono.md` | ascolto legato e staccato |
| T-24 | Durata del nome dopo il rilascio | 500 ms | video a 60 fps |
| T-25 | Apici di 6+9 e m7+M7 | `⁶⁹`, `⁷ᴹ⁷` | combinazioni a due estensioni |
| T-26 | Rilascio dell'estensione con accordo attivo | nessun note-off | Advanced: Maj + C + 9, rilasciare 9 |
| T-27 | Default dopo il Reset di Play Style, Secret Chords, Extension Addition, Single Notes, Quantization, Bass mode, basso on/off | tabella ACC-013 | Reset e lettura dei menu |
| T-28 | Count-in in 3/4 e 6/8 | 1 battuta della metrica | registrare un loop in ogni metrica |
| T-29 | Beat: 12 o 20, contenuto, metrica, lunghezza | 12, pattern provvisorio unico | registrare l'audio di ogni Beat a 120 BPM; contare le voci del menu |
| T-30 | Kit e mappa della batteria a tastiera | tabella ACC-212 | Bass Voicing + BPM, suonare i 12 tasti |
| T-31 | Looper: `PLAY` dopo `PAUSE`, `CLEAR`, riapertura dopo `EXIT`, cosa registra (note o gesti), canale Chord nel loop | da capo; `WAITING`; riprende; note di uscita; Chord non registrato | prove sul menu del loop con monitor MIDI su ch1/ch3 |
| T-32 | Cambio di tonalità con accordo tenuto; `PERF_SET` con accordo tenuto | dal tasto successivo (ACC-100, ACC-182) | cambiare tonalità o modo mentre si tiene un accordo |
| T-33 | Uscita su ch1/ch3 in modo `SOLO` | niente su ch1 e ch3 | Bass Solo + accordo, monitor MIDI |

Altre questioni di progetto:
- `ACC_TREBLE_MAX` = 14 e il limite del basso vanno confermati con l'allocatore e il budget di CPU della sezione suono.
- `ACC_LOOP_EVENTS` e `ACC_LOOP_LAYERS` vanno tarati sul budget di memoria della Flip.
- I nomi dei Beat e i preset sono contenuti del costruttore dell'originale: per una distribuzione pubblica vanno valutati i diritti (vedi `CONVENZIONI.md`, Dati privati).

---

## 15. Dipendenze da altre sezioni

| Sezione | Che cosa serve |
|---|---|
| `20-suono.md` | Consuma `acc_note_ev` con ruolo `TREBLE` e `BASS`; alloca il pool di 16 voci e conferma `ACC_TREBLE_MAX` = 14 e il basso monofonico (ACC-251); gestisce glide e legato del basso (ACC-147); fornisce i default di performance di ogni Sound e lo User Sound (ACC-162); sintetizza kit di batteria e click del metronomo (ACC-207, ACC-212); volumi di basso e Beat. |
| `30-interfaccia.md` | Disegna il nome strutturato (apici, `x`, `bb`, slash) e la sua permanenza (ACC-050, ACC-056); overlay di voicing, performance e BPM; liste di Perform, Beat, Options; Waiting Room e anello del looper (ACC-232); gesti tenuto/premi-e-ruota che generano i comandi logici, compresi Lock, selezione rapida della tonalità e shift del Bass Voicing. |
| `40-midi-e-controlli.md` | Traduce MPK mini Plus e tasti della Flip negli input logici di §1.2 (tasti → `k` e velocity con curva, pad → tipi ed estensioni, manopole → encoder); manda in MIDI out i ruoli `TREBLE`/`BASS`/`CHORD_BLOCK` su ch1/ch2/ch3, con canali disattivabili; clock 24 PPQN da `CLOCK`, Start/Stop dal trasporto (ACC-204); CC di stato opzionali. |
| `50-piattaforma-flip.md` | Frequenza di campionamento e dimensione del blocco; timestamp al campione degli input; budget di latenza e CPU di `acc_process()`; memoria per `acc_state` e looper; salvataggio di loop e opzioni su file (ACC-230). |
| `00-panoramica.md` | Glossario (treble, tick, W, pc) e posizione di `core/acc_*` nell'architettura. |
