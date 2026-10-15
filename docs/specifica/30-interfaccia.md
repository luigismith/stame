# 30 — Interfaccia

Questa sezione descrive cosa si **vede** e come lo si **comanda**: il modello dati dell'interfaccia, il comportamento logico dell'Orchid (viste, overlay, liste, menu, looper, gesti), la **plancia nativa** della Miyoo Flip e, per l'hardware dedicato futuro, la resa al pixel sull'OLED 128×128. Il comportamento musicale (accordi, nomi, looper, performance) è nella sezione 10. I messaggi MIDI della MPK e i codici dei tasti della Flip sono nella sezione 40. Thread, SDL e persistenza sono nella sezione 50.

**Decisione di Luigi del 13/10/2026**, che regola tutta la sezione: «il display non deve essere clonato da orchid, ma visto che più grande, deve contenere tutto ciò che serve e/o è utile vedere in tempo reale». Quindi:
- sulla Flip **non** si emula l'OLED: niente 128×128 ingrandito e niente pannello virtuale. Lo schermo 640×480 a colori ospita una plancia pensata per suonare (§4);
- il **comportamento** dell'Orchid resta fedele: cosa si apre con quale gesto, il contenuto dei menu, la Waiting Room, i tempi degli overlay (§3). Cambia solo il modo di disegnarlo;
- le misure al pixel dell'OLED restano, ma valgono solo per l'hardware dedicato (§7, fase 2).

**Identità visiva (14/10/2026)**, chiesta da Luigi: «un'identità estetica originale, intuitiva, ordinata, stile retro classica futurista, a tema con il device, una lore». La plancia è un **vetrino a fluorescenza**: vetro scuro con la maglia dei VFD, scritte fisse stampate color sabbia, valori accesi nei fosfori, segmenti spenti visibili, nome dell'accordo a punti (Matrice), BPM a sette segmenti. La storia, il marchio dei tre stami, i caratteri, la palette e le regole stanno in `docs/identita/README.md`; qui sotto restano i requisiti che il renderer deve rispettare. Il codice è in `src/gfx/` e `src/ui_flip/`; la vetrina dimostrativa che lo mostra sulla Flip in `src/platform/vetrina/` e `src/platform/flip/` (sezione 50, §11).

**Plancia calma (15/10/2026).** Guardando le prime immagini Luigi ha scritto: «il display è estremamente pieno, sei sicuro che serva avere tutte quelle informazioni?». No: la prima plancia mostrava tutto insieme, ma a 50–70 cm si leggevano solo il nome dell'accordo e il BPM, e metà dello schermo ripeteva ciò che la mascherina del case (sezione 60) incide accanto ai comandi. Quindi, come sull'Orchid, che mostra l'accordo e per 3,4 s il controllo che si gira:
- mentre si suona si vedono quattro cose: **accordo**, **tempo**, **tastiera** e una **banda** con il controllo appena toccato (a riposo, il suono);
- **il case porta i nomi, lo schermo i valori**: niente legende fisse;
- le 11 celle dei comandi compaiono solo quando si usano i tasti della Flip (UI-142a). Il dettaglio (note, intervalli, finestre, Linneo, voci, carico, livelli) sta nella vista **Geek Out**, che sull'Orchid serve proprio a questo.

La decisione del 13/10/2026 resta: si disegna una plancia nativa e si vede in tempo reale ciò che serve; il resto arriva quando serve.

## 0. Convenzioni di questa sezione

### 0.1 Etichette
Le etichette seguono `CONVENZIONI.md`. Le fonti del vault usano un'altra convenzione: lì [V] vuol dire «verificato». La conversione è questa:

| Fonte del vault | Qui |
|---|---|
| figure 1 bit del manuale Coda, testo del manuale v4.1, changelog | `[M]` |
| fotogrammi dei video ufficiali (Quick Start, AMA), foto ufficiali, articolo It's Nice That | `[O]` |
| video e recensioni di terzi (Loopop, Garden Report, Tom Cosm, Molten, Splice, SOS) | `[O]` |
| deduzioni | `[D]` |
| dato mancante, con valore di default scelto qui | `[V]` con il riferimento al test `V-UI-nn` (§9.1) |

La plancia della Flip non esiste sull'originale: lì `[D]` indica una **scelta di progetto**. I dati sulla Flip verificati sulla console sono `[O]`.

### 0.2 Sigle delle fonti
- **MAN**: manuale ufficiale Coda v4.1, comprese le figure 1 bit 640×640 (128×128 ingrandito ×5).
- **QS**: Quick Start v3.04 (youtu.be/GKf50ib0tho), con i secondi. **QSb**: Quick Start brevi TZyPDD6IKSw e zOk7zvm69Ec.
- **AMA**: AMA con il prototipo di dicembre 2024 (youtu.be/8AvlFjjgBmk).
- **LP**: Loopop (youtu.be/pnm52ueo_mI). **GR**: Garden Report 03 (youtu.be/VmaFJIkYsNs). **INT**: It's Nice That su Love and Money.
- **FW**: changelog ufficiale del firmware. Il firmware di riferimento è il **3.92**; i dati presi da firmware più vecchi (QS è 3.04) valgono solo se il changelog non li contraddice.

### 0.3 Coordinate
- **Plancia**: pixel logici 640×480 (UI-116), x da 0 a 639 verso destra, y da 0 a 479 verso il basso. Un rettangolo si scrive `(x, y, w, h)`; gli intervalli «x 4..395» sono inclusivi.
- **OLED** (solo fase 2): coordinate e tolleranze in §7.1.

### 0.4 Lingua dei testi a schermo
I testi dell'Orchid restano **in inglese**, come sull'originale («Volume», «Counting in», «Exit»). Anche i testi della plancia e del menu della piattaforma sono in inglese, per non mescolare due lingue sullo stesso schermo (questione aperta in §9.3).

---

## 1. Architettura

**UI-001** [D] L'interfaccia DEVE essere divisa in questi moduli:

| Modulo | Dove | Cosa fa | Dipendenze |
|---|---|---|---|
| `core/ui` | nucleo | macchina a stati della UI, significato dei gesti, timer, overlay, liste e menu, fuoco; riempie la sua parte di `ui_model_t` | C11, `core` |
| `ui` | nucleo | definizione di `ui_model_t` (§2) e funzioni di formattazione condivise `ui_fmt_*` (UI-029) | C11 |
| `gfx` | nucleo | primitive su framebuffer software **RGB565** e **1 bit**, font bitmap incorporati, decodifica UTF-8 | C11 |
| `ui_flip` | nucleo, renderer | la **plancia** 640×480 a colori, disegnata da `ui_model_t` (§4) | C11, `ui`, `gfx` |
| `ui_oled` | nucleo, renderer (fase 2) | le 6 viste dell'Orchid al pixel su 128×128 a 1 bit (§7) | C11, `ui`, `gfx` |
| `platform/flip` | piattaforma | completa `ui_model_t` con i dati di piattaforma, presenta il framebuffer con SDL2, legge evdev | SDL2, evdev, ALSA |

**UI-002** [D] `core/ui`, `ui`, `gfx`, `ui_flip` e `ui_oled` NON DEVONO includere header di SDL, ALSA, evdev o del sistema operativo, NON DEVONO allocare memoria dinamica e NON DEVONO leggere l'orologio da soli: il tempo arriva come parametro (millisecondi monotoni, `uint32_t`). Valgono PLT-001 e PLT-002.

**UI-003** [D] Il disegno è una **funzione pura** del modello: stesso `ui_model_t` e stesso stato del renderer danno lo stesso framebuffer, pixel per pixel. Così le schermate si provano sul PC con immagini di riferimento (§8).

**UI-004** [D] Thread:
- `core/ui` fa parte di `core` e gira nel thread che possiede `core`: sulla Flip è il thread audio (PLT-006). Lì DEVE lavorare in tempo limitato e costante (niente cicli su liste intere: si copia solo la finestra visibile, UI-025);
- i renderer (`ui_flip`, `ui_oled`) e la presentazione girano **solo** nel thread UI e NON DEVONO mai bloccare il thread audio.

**UI-005** [D] Due renderer, un solo comportamento. Tutte le decisioni (quale overlay è attivo, quando scade, quale voce è selezionata, dove sta il fuoco) le prende `core/ui` e stanno nel modello. I renderer **scelgono come mostrare** lo stato e NON DEVONO cambiarlo né tenere timer di comportamento. L'unico stato ammesso nel renderer è quello puramente visivo: firme delle zone per il ridisegno, decadimento dei meter, lampeggi.

**UI-006** [D] Interfaccia dei renderer:

```c
/* gfx/gfx.h */
typedef struct { int16_t x, y, w, h; } gfx_rect_t;
typedef struct { uint16_t *px; uint16_t w, h, stride; gfx_rect_t clip; } gfx_fb16_t;   /* RGB565, stride in pixel; si disegna solo dentro clip */

/* ui_flip/ui_flip.h */
typedef struct ui_flip_state ui_flip_state_t;   /* firme delle zone, meter; memoria del chiamante */
/* Disegna le zone cambiate; scrive in dirty i rettangoli ridisegnati e ne ritorna il numero (0 = nulla da presentare). */
int      ui_flip_render(ui_flip_state_t *st, const ui_model_t *m, gfx_fb16_t *fb,
                        gfx_rect_t *dirty, int max_dirty);
/* Primo istante (orologio della piattaforma) in cui cambierà qualcosa di solo visivo:
   lampeggi, attività MIDI, decadimento dei meter. UINT32_MAX = nessuno. */
uint32_t ui_flip_next_visual_ms(const ui_flip_state_t *st, const ui_model_t *m);

/* ui_oled/ui_oled.h — fase 2 */
void     ui_oled_render(const ui_model_t *m, gfx_fb1_t *fb);
```

---

## 2. Il modello `ui_model_t`

**UI-020** [D] Il modello è lo **stato completo da mostrare**. `core` lo scrive con `stame_snapshot` (sezione 50) e lo pubblica nel triple buffer (PLT-017); a ogni frame il thread UI prende l'ultimo pubblicato, aggiunge i campi di piattaforma e lo passa al renderer. Si copia per valore: niente puntatori, tranne quello in sola lettura all'anello dell'oscilloscopio.

```c
/* ui/ui_model.h — C11, nessuna dipendenza oltre a core/input/panel.h (enc_id_t) */
typedef struct {
    uint32_t       seq;      /* cambia a ogni istantanea di core diversa dalla precedente */
    uint32_t       core_ms;  /* tempo di core all'istantanea (dal conteggio dei campioni)  */
    uint32_t       now_ms;   /* tempo del frame, orologio monotono della piattaforma        */
    ui_music_t     music;    /* accordo, note, tonalità, voicing          UI-021 */
    ui_tempo_t     tempo;    /* BPM, battuta, Beat                         UI-022 */
    ui_looper_t    looper;   /* stato e posizione del looper               UI-023 */
    ui_controls_t  ctl;      /* gli 11 controlli, fuoco, valori            UI-024 */
    ui_layer_t     layer;    /* overlay, lista, richiesta, livello di base UI-025 */
    ui_meters_t    meters;   /* voci, livello, clip, carico, oscilloscopio UI-026 */
    ui_prefs_t     prefs;    /* tema e opzioni di resa                     UI-027 */
    ui_platform_t  plat;     /* MPK, MIDI, batteria della Flip             UI-027 */
    ui_msg_t       msg_core, msg_plat;  /* avvisi                          UI-028 */
    ui_boot_t      boot;     /* avvio: tempo dall'inizio, righe, versione  UI-159 */
} ui_model_t;
```

| Parte | Chi la riempie | Quando |
|---|---|---|
| `music`, `tempo`, `looper` | `core` (motore della sezione 10, ACC-012, ACC-232) | a ogni pubblicazione dello snapshot (al massimo 120 Hz, PLT-017) |
| `ctl`, `layer`, `prefs`, `msg_core` | `core/ui`, con i valori presi da `core` e `dsp` | idem |
| `ctl.push`, `ctl.knob_lock`, `music.pocket_pc` | `core/input` (profili `mpk_stame`, `pad_brimford` e `flip_tasti`, sezione 40) | idem |
| `meters` (voci, picco, clip, oscilloscopio) | `dsp`, attraverso `core` | idem |
| `meters.dsp_load_pct`, `meters.xrun_count` | piattaforma, nel thread audio (PLT-021) | idem |
| `now_ms`, `plat`, `msg_plat` | piattaforma, nel thread UI (contatori atomici dei thread MIDI, batteria da PLT-090) | a ogni frame |

**Regola dei tempi**: i campi scritti da `core` si confrontano con `core_ms`, quelli della piattaforma con `now_ms`. Il renderer non confronta mai i due orologi tra loro.

### 2.1 Accordo e note

**UI-021** [D]

```c
#define UI_NOTES_MAX 16
typedef enum { ROLE_TREBLE, ROLE_BASS } ui_role_t;
typedef enum { CH_NONE, CH_SOUNDING, CH_LINGER, CH_GHOST } ui_chord_state_t;
typedef struct { uint8_t midi, role; char name[8]; } ui_note_t;  /* name UTF-8: "F♯3"           */

typedef struct {
    chord_label_t chord;              /* nome strutturato (UI-033)                         */
    uint8_t  chord_state;             /* ui_chord_state_t, deciso da core/ui (UI-042, UI-043) */
    uint8_t  single_note;             /* 1 = nota singola (UI-037)                         */
    uint8_t  single_midi;             /* la nota singola, per l'ottava                     */
    uint8_t  n_notes;
    ui_note_t notes[UI_NOTES_MAX];    /* note dal vivo, dalla più grave; basso compreso    */
    uint32_t live_treble[4], live_bass[4];  /* maschere a 128 bit, una per nota MIDI       */
    uint32_t loop_treble[4], loop_bass[4];  /* note che suona il looper                    */
    uint16_t pc_sounding;             /* classi treble che suonano (12 bit), viste ripiegate */
    uint16_t pc_in_key;               /* classi della tonalità; 0 con la Key mode spenta   */
    uint8_t  key_on, key_index;       /* tonalità 0..41 (sezione 10, §6)                   */
    char     key_name[16];            /* "F♯ Minor": grafia della sezione 10               */
    int8_t   transpose;               /* −12..+12                                          */
    uint8_t  v, W, vb, WB;            /* Chord e Bass Voicing grezzi e finestre (ACC-072..075) */
    uint8_t  single_notes;            /* SPLIT o FULL_OCTAVE                               */
    uint8_t  play_style, secret_chords;
    uint8_t  pocket_pc;               /* modo tascabile: classe scelta con la levetta; 255 = nessuna */
} ui_music_t;
```

- Le note e i loro nomi (ortografia enarmonica, ottava con Do centrale = 60 = «C4», VO-13) li decide la sezione 10; la UI non ricalcola nulla.
- Le maschere `live_*` e `loop_*` distinguono le note suonate dal vivo da quelle del looper; `notes[]` contiene solo quelle dal vivo.

**UI-033** [D] Il nome arriva da `core` già scomposto in parti; l'interfaccia decide solo dove e quanto grandi disegnarle.

```c
typedef struct {
    char root[2];       /* "C".."B"                                            */
    char acc[4];        /* "", "♯", "♭", "x"                                   */
    char quality[8];    /* in linea, minuscolo: "", "m", "dim", "sus", "+", "m(add4)" … */
    char sup[8];        /* apice: "", "7", "M7", "6", "9", "M79", "m6", "5", "7♯9",
                           "JAZZ" (3 estensioni), "WTF" (4 estensioni)          */
    char slash_root[2]; /* basso diverso dalla fondamentale (es. Dm/A), oppure "" */
    char slash_acc[4];
} chord_label_t;
```

La nomenclatura (quali parti, «JAZZ», «WTF», Secret Chords, enarmonie) è della sezione 10 [M MAN §3.4].

### 2.2 Tempo

**UI-022** [D]

```c
typedef enum { BEAT_OFF, BEAT_METRONOME, BEAT_PATTERN } ui_beat_mode_t;
typedef struct {
    uint16_t bpm;                 /* 60..200                                       */
    uint8_t  beats_per_bar;       /* 2, 3, 4, 6                                    */
    uint8_t  beat_unit;           /* 4 o 8                                         */
    uint8_t  running;             /* trasporto in moto                             */
    uint8_t  beat;                /* movimento corrente, 0..beats_per_bar−1        */
    uint32_t bar;                 /* battuta, da 1 all'avvio del trasporto         */
    uint16_t beat_phase;          /* 0..65535 dentro il movimento                  */
    uint8_t  beat_mode;           /* ui_beat_mode_t                                */
    uint8_t  beat_index;          /* Beat scelto, da 1                             */
    char     beat_name[24];
    uint8_t  beat_volume;         /* 0..99                                         */
    uint8_t  drums_on;            /* batteria da suonare (UI-097)                  */
} ui_tempo_t;
```

### 2.3 Looper

**UI-023** [D] Copia dello stato esposto dal motore (ACC-232). La UI non decide gli stati, li mostra.

```c
typedef enum { LP_IDLE, LP_WAITING_ROOM, LP_COUNT_IN, LP_REC, LP_PLAY, LP_OVERDUB, LP_PAUSE } ui_lp_state_t;
typedef enum { LPI_REC, LPI_PLAY, LPI_BACK, LPI_OVERDUB, LPI_PAUSE, LPI_CLEAR, LPI_STOP, LPI_UNDO } ui_lp_item_t;
typedef struct {
    uint8_t  state;               /* ui_lp_state_t                                       */
    uint8_t  free_mode;           /* 1 = Free («free» è un simbolo avvelenato da stame_base.h) */
    uint8_t  bars;                /* 1, 2, 4, 8, 16; in Free 0 finché il loop non è chiuso */
    uint8_t  cur_bar;             /* 1..bars                                             */
    uint16_t progress;            /* 0..65535 nel giro                                   */
    uint8_t  count_in;            /* movimenti che mancano; 0 = nessun count-in          */
    uint8_t  layers;              /* strati registrati                                   */
    uint8_t  loop_full;           /* memoria eventi piena (ACC-231)                      */
    uint8_t  slot;                /* 0 = nessuno, 1..10 = «Loop NN» caricato o salvato   */
    uint8_t  menu[3], menu_sel;   /* menu a tre voci (UI-088), voce selezionata 0..2     */
    uint8_t  wr_choice;           /* Waiting Room: 0 Free, 1, 2, 4, 8, 16 battute        */
} ui_looper_t;
```

### 2.4 Controlli

**UI-024** [D] Per ciascuno degli 11 controlli (`enc_id_t` della sezione 40) il modello dice se è premuto, se è «attivo» (ha un overlay in corso), lo stato dei suoi LED e il valore da mostrare.

```c
enum { CF_PRESSED = 1, CF_LED = 2, CF_LOCK = 4, CF_ACTIVE = 8, CF_SECONDARY = 16, CF_LEGACY = 32 };
typedef struct {
    uint8_t  flags;               /* CF_*                                                    */
    uint32_t pressed_since_ms;    /* core_ms della pressione, per la barra del tenuto        */
    uint16_t t_hold_ms;           /* soglia del tenuto di questo encoder (40, MIDI-103)      */
} ui_ctl_state_t;

typedef struct {
    ui_ctl_state_t st[ENC_COUNT];
    uint8_t  focus;               /* fuoco del pannello, condiviso (40, MIDI-104)            */
    uint8_t  turn_target;         /* encoder che ENC_FOCUS ruota adesso: proprietario della lista o fuoco */
    uint8_t  push;                /* PUSH (40, MIDI-084): 0 IDLE, 1 ARMED, 2 + k = TARGET(manopola k) */
    uint8_t  knob_lock;           /* Lock del macro pad (40, MIDI-131): M, m1, m2 = Sound, Perform, Key */
    /* Sound */
    uint8_t  sound_user, sound_num;           /* fabbrica 1..70, utente 1..30             */
    char     sound_name[17];
    uint8_t  sound_engine;                    /* VA, FM, RP                               */
    char     sound_cat[24];                   /* categoria (sezione 20, §12)              */
    /* Perform */
    uint8_t  perf_mode;           /* Off, Strum, Strum 2 Oct, Slop, Arpeggiate, Arp 2 Oct, Pattern, Harp */
    uint8_t  perf_amount;         /* quantità, oppure numero del pattern                     */
    uint8_t  arp_rate, arp_dir;
    /* FX */
    uint8_t  fx_main_type, fx_main_amount;    /* «effetto principale», 0..10              */
    struct { uint8_t type, amount; } fx[4];   /* Reverb, FX1, FX2, Filter (sezione 20)    */
    /* Bass e volumi */
    uint8_t  bass_on, bass_mode, bass_num;
    char     bass_name[17];
    uint8_t  volume, bass_volume;             /* 0..99                                    */
    /* Options */
    uint8_t  view;                            /* vista scelta in Options > System > View  */
} ui_controls_t;
```

- `CF_LED` riproduce i LED dell'originale (UI-106): Key mode accesa, basso acceso. `CF_LOCK` è il Lock di Perform e di FX.
- `CF_ACTIVE` vale finché è visibile un overlay di quell'encoder (UI-069). `CF_SECONDARY` vale durante «premere e ruotare».
- `CF_LEGACY` segnala sul Sound una patch nel formato vecchio (SND-104).
- I valori sono **strutturati**, non testi: i testi li compongono i renderer con le stesse funzioni `ui_fmt_*` (UI-029).

### 2.5 Livelli: overlay, liste, richieste

**UI-025** [D]

```c
typedef enum { OV_NONE, OV_VOLUME, OV_BASS_VOLUME, OV_BEAT_VOLUME, OV_BATTERY, OV_SOUND, OV_PERFORM,
               OV_ARP, OV_FX, OV_KEY, OV_KEY_TOGGLE, OV_TRANSPOSE, OV_BPM, OV_BASS_SOUND,
               OV_BASS_TOGGLE, OV_VOICING, OV_BASS_VOICING, OV_SINGLE_NOTES, OV_COUNT_IN,
               OV_SAVED, OV_DRUMS, OV_LOW_BATTERY } ui_ov_kind_t;
typedef struct { uint8_t kind, enc; int16_t value; uint32_t until_ms; } ui_overlay_t;

#define UI_LIST_WIN 9                  /* voci copiate attorno alla selezione */
typedef enum { MK_NONE, MK_CHECK, MK_DOT, MK_INDEX, MK_SUBMENU } ui_mark_t;
typedef struct {
    char    label[24];                 /* "Analog Flower", "Play Style"             */
    char    num[4];                    /* "03", "U05", ""                           */
    char    value[12];                 /* valore a destra: "Off", "08", "1/8"       */
    char    info[24];                  /* colonna informativa: "VA  pluck"          */
    uint8_t mark, enabled;
} ui_item_t;

typedef enum { LS_SOUND, LS_PERFORM, LS_FX, LS_BASS, LS_BEATS, LS_SAVE_SOUND, LS_SAVE_LOOP,
               LS_SLOTS, LS_OPTIONS, LS_WAITING_ROOM, LS_PLATFORM, LS_MPK_STATUS, LS_VERSION } ui_list_kind_t;
typedef struct {
    uint8_t   open, owner, kind;       /* owner: enc_id_t, oppure OWN_PLATFORM        */
    char      path[48];                /* "Options > Instrument > Play Style"         */
    uint16_t  n, sel, win_first;       /* voci totali, selezionata, prima copiata     */
    ui_item_t win[UI_LIST_WIN];        /* finestra attorno a sel                      */
    uint8_t   editing;                 /* voce numerica in modifica (UI-075)          */
} ui_list_t;

typedef struct {
    uint8_t      base;                 /* BOOT, PLAY, LOOPER (UI-109)                 */
    ui_overlay_t ov;                   /* overlay visibile; OV_NONE se nessuno        */
    ui_list_t    list;                 /* lista o menu in cima alla pila              */
    uint8_t      prompt;               /* NONE, SELECT_KEY (UI-096)                   */
    uint8_t      platform_menu;        /* 1 = la lista in cima è il menu della piattaforma */
    uint8_t      page;                 /* PAGE_PLAY, PAGE_CONTROLS (UI-142a)          */
} ui_layer_t;
```

- `page` lo decide `core/ui` (UI-005), come la durata degli overlay: i renderer non tengono timer.

- Il modello contiene **solo il livello in cima** di ogni tipo: chiusa una lista, `core/ui` ripubblica quella sotto.
- La finestra di 9 voci basta per qualunque renderer (5 righe visibili più margine) e tiene il costo costante, anche per la lista Sound con 100 voci.

### 2.6 Meter

**UI-026** [D]

```c
typedef struct {
    uint8_t  voices_used, voices_bass;   /* voci occupate su 16 (SND-020); di cui del basso   */
    uint16_t peak[2];                    /* picco L e R dall'ultimo snapshot, Q15 lineare, dopo
                                            il master e prima del soft clip (SND-046)          */
    uint32_t clip_count;                 /* contatore monotono dei periodi in cui il soft clip ha lavorato */
    uint8_t  dsp_load_pct;               /* tempo di render / periodo, media su 500 ms (PLT-021) */
    uint8_t  dsp_load_max_pct;           /* massimo dall'ultimo snapshot                       */
    uint32_t xrun_count;                 /* underrun del PCM dall'avvio                        */
    const int16_t *scope;                /* anello dell'oscilloscopio (SND-033), sola lettura   */
    uint16_t scope_len;
    const volatile uint32_t *scope_wr;   /* indice di scrittura atomico                        */
} ui_meters_t;
```

### 2.7 Preferenze e piattaforma

**UI-027** [D]

```c
typedef struct {                         /* scelte del menu della piattaforma (UI-129), salvate */
    uint8_t theme;                       /* THEME_DARK (default), THEME_LIGHT                    */
    uint8_t legend;                      /* 1 = legenda viva accesa (default)                    */
    uint8_t note_labels;                 /* LBL_OCTAVES (default), LBL_ALL, LBL_OFF              */
    uint8_t meters;                      /* 1 = voci, carico e livello nella testata (Geek Out) */
    uint8_t beat_flash;                  /* 1 = lampo sul numero del BPM a ogni movimento (default 0) */
    uint8_t ghost_chord;                 /* 1 = ultimo accordo in grigio dopo la persistenza (default 1) */
    uint8_t debug;                       /* 1 = riga di debug nella banda (default 0)            */
    uint8_t pocket;                      /* modo tascabile acceso (40, MIDI-094); non salvato    */
    uint8_t linnaeus;                    /* 1 = cartellino di Linneo nella zona accordo (UI-161, default 1) */
    uint32_t quit_seq;                   /* cambia quando si conferma «Quit Stame»               */
    uint32_t learn_pad_seq;              /* cambia quando si sceglie «Learn Pad» (40, MIDI-123)  */
} ui_prefs_t;

typedef enum { MPK_ABSENT, MPK_BUSY, MPK_OPEN, MPK_ERROR } ui_mpk_link_t;
typedef enum { PADL_ABSENT, PADL_OPEN, PADL_UNMAPPED, PADL_ERROR } ui_pad_link_t;   /* macro pad (40, §8.10) */
typedef struct {
    uint8_t  mpk_link;                   /* dalla piattaforma (40, MIDI-071, §11)               */
    uint8_t  pad_link;                   /* macro pad BRIMFORD: ui_pad_link_t (40, MIDI-124, MIDI-127) */
    uint8_t  pad_learn_step;             /* 0 = Learn Pad spento; 1..21 = passo in corso (MIDI-123) */
    uint32_t pad_learned;                /* un bit per passo già imparato                        */
    uint8_t  mpk_profile;                /* da core/input: STAME o FACTORY (40, MIDI-088)        */
    uint8_t  mpk_bank;                   /* banco stimato dei pad: sconosciuto, A, B (40, MIDI-089) */
    char     mpk_fw[8];                  /* "1.13" dall'Identity Reply (MIDI-073)                */
    char     mpk_last[24];               /* ultimo messaggio ricevuto, in esadecimale            */
    uint32_t midi_in_ms, midi_out_ms;    /* ultimo messaggio dalla MPK o dal DIN IN; verso il DIN OUT */
    uint8_t  battery_pct, charging;      /* batteria della Flip (PLT-090); 255 = sconosciuta     */
    uint8_t  audio_backend;              /* ALSA o SDL (PLT-023)                                  */
    uint16_t period_frames, periods;     /* configurazione audio, per la riga di debug           */
    uint16_t frame_us;                   /* tempo dell'ultimo disegno, per la riga di debug      */
} ui_platform_t;
```

- Le preferenze vivono in `core` (si scelgono dal menu della piattaforma, che è una lista di `core/ui`) e si salvano con le impostazioni (UI-111), tranne `pocket`. Il thread UI le legge dallo snapshot: così non serve una coda di ritorno dal thread audio. `quit_seq` è la richiesta di uscita: quando cambia, il thread UI avvia la chiusura (PLT-057, PLT-086). Allo stesso modo `learn_pad_seq` chiede alla piattaforma di avviare Learn Pad (UI-175).

### 2.8 Avvisi

**UI-028** [D] Due avvisi, uno di `core` e uno della piattaforma; il renderer mostra quello con priorità più alta (UI-154).

```c
typedef enum { MSG_NONE, MSG_INFO, MSG_WARN } ui_msg_level_t;
typedef struct { uint8_t id, level; uint32_t until_ms; char text[64]; } ui_msg_t;  /* until_ms 0 = finché dura la condizione */
```

L'elenco degli avvisi è in UI-156.

### 2.9 Assemblaggio e formattazione

**UI-029** [D] Regole:
- il thread audio pubblica lo snapshot al massimo a 120 Hz e solo se è cambiato (`seq`); `beat_phase` e `progress` cambiano di continuo solo mentre il trasporto o il looper sono in moto;
- a ogni frame il thread UI copia l'ultimo snapshot, scrive `now_ms`, `plat` e `msg_plat`, poi chiama il renderer;
- `ui_model_t` DEVE stare sotto i 4 KB, così la copia per valore costa poco;
- i testi derivati dai valori si compongono con funzioni condivise da tutti i renderer, in `ui/ui_fmt.c`: numeri a 2 o 3 cifre con lo zero davanti («07», «032»), «OFF» per i parametri che a zero si spengono (UI-062), segno del transpose («+3»), nomi brevi dei modi di Perform (UI-066), sigle degli effetti (REV, CHO, ENS, PHA, FLA, DRV, TRM, DLY, FLT), tonalità breve («F♯m»), nome di una nota MIDI («C♯4»). Così plancia e OLED non divergono.

---

## 3. Comportamento logico comune

Tutto ciò che segue vale per ogni renderer. Dove un requisito parla di «schermata», sulla plancia diventa una zona o un'evidenza (§4); sull'OLED è la schermata a tutto schermo (§7).

### 3.1 Controlli e gesti

L'Orchid ha 9 encoder infiniti e premibili (Sound, Perform, FX, Key, Bass, Loop, BPM, Volume, Options) e 2 manopole di voicing (Chord Voicing premibile, Bass Voicing premibile e usato come modificatore). Non c'è un tasto SHIFT [M MAN]. L'elenco `enc_id_t` è quello di 40 (MIDI-100).

**UI-100** [M] Gesti di base [M MAN]: **premere** = attiva o disattiva; **ruotare** = valore; **tenere premuto** = menu o lock; **premere e ruotare** = funzione secondaria.

**UI-101** Mappa completa dei gesti (firmware 3.92):

| Encoder | Ruotare | Premere (tap) | Tenere premuto | Premere e ruotare | Fonte |
|---|---|---|---|---|---|
| Volume | volume master 0–99 | schermata batteria | — | Bass Volume | [M] |
| Sound | suono per numero (fabbrica, poi utente) | lista per nome (dal 3.60) | Save / Save As / Delete | — | [M] |
| Perform | modo e parametro; tutto a sinistra = Off | lista dei modi | **Lock** (LED, nessun overlay) | — | [M; O QS 653-683] |
| FX | effetto principale | lista degli effetti | **Lock** (LED) | — | [M] |
| Key | tonalità | Key mode on/off (LED) | scelta rapida (+ Min per la minore) | **Transpose** | [M] |
| Bass | suono di basso | basso on/off (LED) | lista dei modi (1 s) | — | [M] |
| Loop | Waiting Room, battute, voci dei menu | entra, Rec, Stop, voce del menu | lista Save Loop / uscita morbida (2 s) | — | [M] |
| BPM | tempo | Beat o metronomo on/off | tempo in chiave e Beats (1 s) | Beat Volume | [M] |
| Options | scorre | apre, entra, conferma | — | — | [M] |
| Chord Voicing | voicing ±1 semitono per scatto | Split ↔ Octave | — | — | [M] |
| Bass Voicing | ottava del basso | — | modificatore (UI-104) | — | [M; O] |

- Premere e ruotare Sound, nei firmware prima del 3.60, sceglieva per nome [M]: Stame segue il 3.92 e non lo replica.
- Girare Options a menu chiuso non fa nulla [V V-UI-23].
- L'uscita morbida dal looper (Loop tenuto 2 s, poi Exit) e la lista Save Loop sono lo stesso gesto: la lista Save Loop contiene Exit [D da M MAN].

**UI-102** Soglie: valgono le costanti di 40 (MIDI-103). In sintesi: tenuto a **1 s** per tutti gli encoder ([M] per Bass e BPM, [V] VO-12 e V-UI-03 per gli altri); per Loop la lista Save Loop scatta al **secondo livello, 2 s** (`G_HOLD_LONG`, [M]); il primo livello di Loop (1 s) non ha effetto.

**UI-103** [D] Il riconoscitore è quello di 40 (MIDI-103): `core/ui` ne riceve i gesti già pronti, con `ENC_FOCUS` già risolto (MIDI-104), e dà loro questo significato:

| Gesto (40) | Per la UI |
|---|---|
| `G_TURN(e, n)` | ruotare `e` |
| `G_PRESS(e)` | tap di `e`: scatta **al rilascio**, così Key premuto e girato fa il transpose senza cambiare la Key mode [D da M MAN] |
| `G_HOLD(e)` | tenere premuto `e`: scatta **alla soglia**, senza aspettare il rilascio [O QS 653-683, il LED del Lock si accende con il tasto ancora premuto] |
| `G_HOLD_LONG(ENC_LOOP)` | lista Save Loop (UI-102) |
| `G_PRESS_TURN(e, n)` | funzione secondaria di `e`, se esiste (Volume, Key, BPM); per gli altri encoder vale come `G_TURN` |
| `G_RELEASE(e)` | fine della pressione; serve ai modificatori (UI-104) |

**UI-104** [M] Combinazioni con Bass Voicing tenuto (il «Shift» nascosto del changelog [M FW 3.84]):

| Combinazione | Effetto | Fonte |
|---|---|---|
| Bass Voicing tenuto + tap Loop | **uscita forzata** dal looper (perde il loop non salvato) | [M MAN, FW 3.84] |
| Bass Voicing tenuto + tap BPM | batteria da suonare (UI-097) | [O] |
| Bass Voicing tenuto + tap Bass | basso on/off | [O] |

Con Bass Voicing tenuto il tap dell'altro encoder NON DEVE eseguire la sua funzione normale.

**UI-105** [M] Altre combinazioni:
- durante la scelta rapida della tonalità (UI-096), un tasto della tastiera imposta la tonica e il tipo **Min** tenuto la rende minore [M MAN];
- Power tenuto 1 s (on/off), Power 10 s (riavvio forzato) e accensione con Bass premuto (bootloader) [M] **non** si replicano: sulla Flip li gestisce spruceOS [D].

### 3.2 Stati e livelli

**UI-109** [D] La UI ha uno **stato di base** e una **pila di livelli** sopra. L'OLED disegna la base e poi i livelli, ognuno a tutto schermo; la plancia mostra ogni livello in una zona propria (UI-142), senza coprire le zone critiche.

| Livello | Stati | Esce con |
|---|---|---|
| base | `BOOT` → `PLAY(view)` oppure `LOOPER(sub)` | — |
| 1 | `LIST(owner, items, sel)`, `OPTIONS(stack)` | Exit/Back, timeout, altro encoder (UI-076) |
| 2 | `PROMPT_KEY` (scelta rapida), `CONFIRM` (salvato) | tasto della tastiera, timeout |
| 3 | `OVERLAY(kind, value, until_ms)`, `BATTERY` | timeout (UI-069), `PNL_BACK` |
| 4 | `WARN_LOWBATT` | timeout |
| 5 | `PLATFORM_MENU` | MENU o Back |

`LOOPER(sub)` ha i sottostati `WAITING_ROOM`, `COUNT_IN`, `REC`, `PLAY`, `OVERDUB`, `PAUSE`, copiati dallo stato del looper di `core` (sezione 10).

```
BOOT        --init finita e (4 s trascorsi o tasto)-->       PLAY(view salvata)
PLAY        --core.looper != IDLE-->                         LOOPER(core.looper)
LOOPER      --core.looper == IDLE (Exit, uscita forzata)-->  PLAY
qualsiasi   --G_TURN/G_PRESS_TURN/G_PRESS che ha un overlay--> push/sostituisci OVERLAY
qualsiasi   --G_PRESS(SOUND|PERFORM|FX)-->                   apri LIST(owner)
qualsiasi   --G_HOLD(BASS|BPM|SOUND), G_HOLD_LONG(LOOP)-->   apri LIST(owner)
qualsiasi   --G_HOLD(KEY)-->                                 PROMPT_KEY
qualsiasi   --G_HOLD(PERFORM|FX)-->                          cambia il Lock (nessun livello nuovo)
PLAY/LOOPER --G_PRESS(OPTIONS)-->                            OPTIONS(radice)
LIST/OPTIONS --gesto di un encoder diverso dal proprietario--> chiudi, poi esegui il gesto
OVERLAY     --core_ms ≥ until_ms-->                          pop
batteria ≤ 10% (una volta) e ≤ 5% (una volta) -->            WARN_LOWBATT
MACRO_SYSTEM_MENU -->                                        PLATFORM_MENU, oppure chiudilo se è aperto
```

**UI-110** [D] Gli eventi musicali (tasti, pad degli accordi, pedale, ruote) NON DEVONO passare dalla macchina a stati della UI: vanno direttamente a `core` e suonano in qualunque stato, anche con un menu aperto. La UI ne vede solo l'effetto attraverso `ui_model_t`.

**UI-111** [D] Si salvano tra un avvio e l'altro: la vista, le preferenze del menu della piattaforma (tranne Pocket Mode, MIDI-094) e le impostazioni di Options (sezioni 10, 20, 40). Overlay, liste aperte, selezioni e fuoco non si salvano: all'avvio il fuoco è su Sound (MIDI-104).

**UI-112** [D] Tutti i tempi di comportamento (overlay, persistenza del nome, timeout delle liste, lampeggio delle voci in modifica) si calcolano in `core/ui` sul tempo di `core`. `core/ui` DEVE esporre `ui_next_deadline_ms()`, il primo istante in cui cambierà lo stato da mostrare; i tempi solo visivi li espone il renderer (UI-006).

### 3.3 Viste

Si scelgono da Options > System > View; la vista attiva ha la spunta [M MAN; O QS 950-975, LP 1441-1458]. La vista «Bliss Out» del prototipo del dicembre 2024 [O AMA 26-34] non esiste nel firmware di serie e NON DEVE essere implementata.

**UI-050** [V] La vista di fabbrica è **Chord** [V V-UI-29]. La vista scelta DEVE essere salvata tra un avvio e l'altro (formato: sezione 50).

**UI-051** [D] Le viste sono sei: React, Chord, Keyboard, Chord + Keyboard, Notes, Geek Out. La vista decide il contenuto della **zona principale**: sull'OLED tutto lo schermo nello stato `PLAY` (§7.4), sulla plancia la zona accordo (UI-147), che resta visibile anche con il looper attivo e con una lista aperta.

### 3.4 Nome dell'accordo e note

**UI-037** [V] Nota singola (Play Style Advanced o Free, oppure tasto senza tipo con la Key mode spenta): si mostra solo la nota, con le regole della fondamentale. L'indicatore di nota singola introdotto nel 3.60 [M FW] non ha immagini: sull'OLED nessun segno in più [V V-UI-07]; sulla plancia l'ottava si aggiunge come apice (ACC-051 lascia la scelta all'interfaccia) [D].

**UI-039** [D] Quali note si evidenziano: il modello dà tutte le note con il loro ruolo (UI-021). L'OLED mostra le classi dell'accordo ripiegate in un'ottava, senza il basso [V V-UI-06]; la plancia mostra le altezze vere, con treble, basso e loop distinti (UI-150).

**UI-041** [O] Elenco delle note: dalla più grave alla più acuta, separate da uno spazio; «F A D» è un Re minore in primo rivolto [O GR, LP]. Senza note che suonano l'elenco è vuoto [O QS 960].

**UI-042** [M] Dal 3.90 il nome dell'accordo resta visibile un attimo dopo il rilascio [M FW 3.90]. Default: **1000 ms** dal rilascio dell'ultimo tasto (`CH_LINGER`), poi il nome si toglie [V V-UI-02]. Prima del 3.90 restava solo la tonalità [O LP 1459-1461]. La sezione 10 propone 500 ms (ACC-056): da allineare (§9.4).

**UI-043** [D] Un nuovo accordo durante la persistenza sostituisce subito il nome vecchio. Tastiera ed elenco delle note seguono il suono e non la persistenza: si spengono al rilascio. Finita la persistenza `core/ui` passa a `CH_GHOST` se `prefs.ghost_chord` è acceso, altrimenti a `CH_NONE`; l'OLED tratta `CH_GHOST` come `CH_NONE`.

### 3.5 Overlay

Sull'Orchid un overlay è una schermata temporanea che compare quando si gira o si preme un encoder. Sulla plancia diventa un'**evidenza**: la banda in fondo mostra nome e valore del controllo in grande (UI-154), senza coprire l'accordo; nella pagina dei comandi si accende anche la sua cella.

**UI-065** I contenuti degli overlay sono questi. Le gamme dei valori e i nomi sono delle sezioni 10 e 20; l'impaginazione al pixel sull'OLED è in UI-061..UI-068.

| Gesto | Tipo | Valore mostrato | Etichetta | Fonte |
|---|---|---|---|---|
| Volume, ruotare | `OV_VOLUME` | 00–99, con livello | «Volume» | [M] |
| Volume, premere e ruotare | `OV_BASS_VOLUME` | 00–99, con livello | «Bass Volume», funzione secondaria | [M MAN] |
| Volume, premere | `OV_BATTERY` | batteria (della Flip) | — | [M] |
| Sound, ruotare | `OV_SOUND` | «07»; Sound utente «U05» | «Sound» | [O QS] |
| Perform, ruotare | `OV_PERFORM` | quantità o numero del pattern; 0 → «OFF» | nome breve del modo (UI-066) | [O QS 444-520, AMA] |
| Perform, ruotare (Arpeggiate) | `OV_ARP` | velocità («16», «08») e direzione («UP», «DOWN», «UP/DOWN») | «Arpeggiate» | [O QS 452, 486, 659.5] |
| FX, ruotare | `OV_FX` | 01–10; 0 → «OFF» | nome dell'effetto principale | [O QS 653-664] |
| Key, ruotare | `OV_KEY` | tonalità | «Key» | [O GR 186-192, QS 700] |
| Key, premere | `OV_KEY_TOGGLE` | tonalità oppure «Off» | «Key» | [M; V V-UI-09] |
| Key, premere e ruotare | `OV_TRANSPOSE` | «+3», «-2»; 0 → «OFF» | «Transpose», funzione secondaria | [O QS 754; formato V V-UI-10] |
| BPM, ruotare | `OV_BPM` | «96», «117» | «BPM» | [O QS 863; V V-UI-09] |
| BPM, premere e ruotare | `OV_BEAT_VOLUME` | 00–99, con livello | «Beat Volume», funzione secondaria | [M] |
| Bass, ruotare | `OV_BASS_SOUND` | «03» | «Bass Sound» | [O QS 810-842] |
| Bass, premere | `OV_BASS_TOGGLE` | acceso: «03» / spento: «OFF» | «Bass Sound» / «Bass» | [V V-UI-09] |
| Chord Voicing, ruotare | `OV_VOICING` | **sempre 3 cifre**, «032» | «Voicing» | [O QS 738] |
| Bass Voicing, ruotare | `OV_BASS_VOICING` | «07» | «Bass Voicing» | [O QS 810-842] |
| Chord Voicing, premere | `OV_SINGLE_NOTES` | «Split» / «Octave» | «Single Notes» | [V V-UI-07] |
| Perform o FX, tenere premuto (Lock) | **nessun overlay** | — | si accende solo il LED | [O QS 653-683] |
| BPM, premere (Beat o metronomo) | nessun overlay | — | — | [V V-UI-09] |
| count-in del looper | `OV_COUNT_IN` | «04» … «01» | «Counting in» | [O LP 1398; QS] |
| salvataggio riuscito | `OV_SAVED` | «Saved» | slot («U05», «Loop 03») | [V V-UI-12, V-UI-13] |
| batteria da suonare | `OV_DRUMS` | «Drums» | «On» / «Off» | [V V-UI-09] |
| batteria bassa | `OV_LOW_BATTERY` | percentuale | «Low Battery» | [M MAN; V V-UI-14] |

- I volumi a zero mostrano «00» [V V-UI-11]; gli altri parametri che a zero si spengono (effetti, quantità di Perform, transpose) mostrano «OFF» [O QS 662.5, 754].

**UI-066** [O] Etichette brevi dei modi di Perform: «Strum», «Strum 2 Oct», «Slop», «Arpeggiate», «Pattern», «Harp» [O QS 444-520, AMA]. «Arp 2 Oct» per Arpeggiate 2 Octaves e l'etichetta di Perform a zero («OFF» + nome del modo) sono `[V]` (V-UI-25).

**UI-069** [V] Un overlay resta visibile **3400 ms** dall'ultima azione che lo ha aggiornato [D da QS; V V-UI-01]. Ogni nuova rotazione dello stesso encoder riparte da zero.

**UI-070** [D] Un overlay nuovo sostituisce subito quello vecchio, anche se di un altro encoder. Alla scadenza si torna allo stato sotto. `PNL_BACK` chiude subito l'overlay.

### 3.6 Liste e menu

**UI-072** [O] Marcatori delle voci (`ui_mark_t`):
- **valore** a destra, per le voci con un valore (Volumes, MIDI Channels, effetti);
- **spunta ✓** sulla scelta corrente;
- **pallino ●** sul modo Perform attivo [O QS 444-520] e sugli slot occupati di Save As (UI-078);
- **indice** al posto del pallino per Arpeggiate: «Arpeggiate 03» [O QS 444-520];
- **sottomenu**: voce che apre un livello sotto.

**UI-073** [M] Struttura: la radice di ogni lista ha **«Exit»** in cima, ogni sottomenu ha **«Back»** in cima [O QS 937-1136]. La lista NON DEVE ricominciare dall'inizio dopo l'ultima voce [D; V V-UI-23]. La selezione resta **al centro** delle righe visibili e la lista scorre sotto; agli estremi le righe senza voce restano vuote [M fig. «quant»].

**UI-074** [D] Rotazione e pressione: girando in senso orario (+1) la selezione passa alla voce successiva. Premere sceglie: entra in un sottomenu, applica una scelta (la ✓ si sposta subito) oppure, su Exit e Back, risale di un livello. Una scelta applicata lascia la lista aperta, salvo dove indicato. Per i tasti direzionali vale UI-157.

**UI-075** [V] Voci numeriche (per esempio Volumes > Master): premere entra in modifica, il valore lampeggia (500 ms acceso, 250 spento), girando cambia, premendo di nuovo si conferma [V V-UI-16].

**UI-076** [V] Chiusura:
- Exit o Back alla radice;
- **liste aperte da un encoder** (Sound, Perform, FX, Bass, Beats, Save): dopo **10 s** senza azioni [V V-UI-16];
- **Options** e menu della piattaforma: nessun timeout [V V-UI-16];
- un gesto su un **altro** encoder chiude la lista o il menu ed esegue l'azione di quell'encoder [V V-UI-16];
- `PNL_BACK` equivale a Back.

Il manuale dice che si esce anche «ripremendo Options» [M]; dato che premere Options conferma la voce selezionata, il conflitto resta aperto (V-UI-16) e per ora vale la conferma.

**UI-077** I contenuti delle liste degli encoder sono:

| Lista | Si apre con | Voci | Marcatore | Fonte |
|---|---|---|---|---|
| Sound | premere Sound | Exit, «01 Orchid EP» … «70 …», poi «U01» … «U30» (solo gli slot occupati) | ✓ sul suono attivo | [O QS, LP; M FW 3.60] |
| Perform | premere Perform | Exit, Strum, Strum 2 Octaves, Slop, Arpeggiate, Arp 2 Octaves, Pattern, Harp | ● sul modo attivo; indice per Arpeggiate | [O QS 444-520] |
| FX | premere FX | Exit, poi gli slot del suono (Reverb, FX1, FX2, Filter) con il nome dell'effetto e il valore («Off» o 1–10) | valore | [O QS 653-664] |
| Bass | tenere Bass 1 s | Exit, Chords Only, Unison, Bass Single Notes, Solo | ✓ | [M MAN; O QS 810-842, LP 1356] |
| Beats | tenere BPM 1 s | Exit, 2/4, 3/4, 4/4, 6/8, poi i Beat «01 Nome» … | ✓ | [M MAN; V V-UI-20] |
| Save Sound | tenere Sound | Exit, Save, Save As, Delete | — | [M MAN; V V-UI-13] |
| Save Loop | tenere Loop 2 s | Exit, Save As Loop XX, Save As, Load Loop, Delete Loop | — | [M MAN; V V-UI-12] |

- Nella lista Sound i nomi sono in maiuscole e minuscole («NN Nome»); quelli di fabbrica, con motore e categoria, sono nella sezione 20.
- Nella lista Perform, dopo la scelta di un modo, girare regola il suo parametro con l'overlay di UI-065 [M MAN].
- Nella lista FX, premendo una voce e girando si regola la sua intensità [M MAN].
- Le voci di Bass sono quelle del manuale 3.90; nel 3.04 erano «With chords only, Unison, Bass single notes, Solo» [O QS]. Maiuscole esatte `[V]` (V-UI-20).

**UI-078** [V] Save As (Sound e Loop) apre una seconda lista di slot: «U01» … «U30» oppure «Loop 01» … «Loop 10», con ● sugli slot occupati; salvare su uno slot occupato lo sovrascrive [M MAN]. Dopo un salvataggio compare `OV_SAVED` [V V-UI-12, V-UI-13].

**UI-079** [M] Albero del menu Options del firmware 3.90 e successivi [M MAN, supporto]. Profondità massima 3 livelli.

```
Options                         (radice: Exit in cima)
├─ Exit
├─ System
│  ├─ Back
│  ├─ View              Back / React / Chord / Keyboard / Chord + Keyboard / Notes / Geek Out   (✓)
│  ├─ Battery           → batteria (OV_BATTERY)
│  ├─ Auto Power Off    Back / 10 min / 30 min / Never   (✓)
│  └─ Version           → versione (UI-098)
├─ Instrument
│  ├─ Back
│  ├─ Play Style          Back / Simple / Advanced / Free   (✓)
│  ├─ Secret Chords       Back / Off / Simple PlayStyle only / All PlayStyle   (✓)
│  ├─ Single Notes        Back / Split Keyboard / Full Octave Keyboard   (✓)
│  ├─ Extension Addition  Back / Add Note / Play Chord   (✓)
│  ├─ Quantization        Back / None / 1/4 / 1/8 / 1/8t / 1/16 / 1/16t / 1/32   (✓)
│  └─ Velocity Sense      Back / On / Off   (✓)
├─ Bass                   Back / Chords Only / Unison / Bass Single Notes / Solo   (✓)
├─ Audio and MIDI
│  ├─ Back
│  ├─ Audio Output        Back / Auto / Headphones / Speakers / Both   (✓)
│  ├─ MIDI Channels       Back / Performance NN / Bass NN / Chord NN   (valori 01–16 o Off)
│  ├─ Volumes             Back / Master NN / Bass NN / Drums NN   (valori 00–99)
│  └─ Metronome Click     Back / Beep / Hi Hat   (✓)
└─ Upgrade Firmware       (non replicato sulla Flip, UI-081)
```

- Il significato delle impostazioni e i loro default sono nelle sezioni 10, 20 e 40.
- I nomi esatti delle voci nel 3.90 vengono dal manuale; le schermate dei sottomenu del 3.90 non sono mai state riprese da vicino, quindi maiuscole e abbreviazioni sono `[V]` (V-UI-20).
- Nel 3.04 il menu era piatto: Exit, Battery, View, Audio Output, MIDI Channels, Play Style, Single notes, Metronome Click, Velocity Sense, Extension Addition, Version, Upgrade firmware [O QS 937-1136]. Stame segue il 3.90.

**UI-080** [D] Sulla Flip:
- Battery mostra la batteria della **console**;
- **Audio Output** resta nel menu per fedeltà e la scelta si salva, ma non ha effetto: l'uscita la sceglie spruceOS e Stame non tocca il mixer (PLT-026). Sulla plancia la voce porta l'informazione «set by spruceOS»;
- Auto Power Off, alla scadenza, salva lo stato e chiude l'app tornando a spruceOS; non scatta durante la carica [M per la regola della carica; D per la chiusura].

**UI-081** [D] «Upgrade Firmware» NON DEVE comparire sulla Flip: l'aggiornamento di Stame passa da spruceOS. Le schermate «Ready for Firmware» e «Select USB Mode / Enable USB MIDI» dell'originale [M MAN] non si replicano, perché la Flip non fa da dispositivo USB MIDI.

### 3.7 Looper

Il comportamento del looper (stati, battute, overdub, undo, salvataggio) è nella sezione 10. Qui c'è cosa si mostra.

**UI-086** [V] Registrazione in Free: finché il loop non è chiuso la lunghezza non si conosce (`bars = 0`); il progresso si mostra come indeterminato e si riempie dal primo giro dopo la chiusura [V V-UI-21].

**UI-087** [O] Si entra nella Waiting Room premendo o girando Loop [M MAN]. Lista **Exit / Free / 1 Bar / 2 Bars / 4 Bars / 8 Bars / 16 Bars** con la selezione fissa al centro, più l'anteprima delle battute della scelta selezionata [O QS 851-870; D; V V-UI-21].

**UI-088** [O] Durante registrazione e riproduzione c'è un menu di tre voci, comandato da Loop; qui la selezione **si sposta** sulla voce (non è fissa al centro) [O QS 870-934; LP 1338-1406].

| Stato del looper (sezione 10) | Voci | Fonte |
|---|---|---|
| registrazione | Rec / Play / Back (Rec selezionato) | [O QS] |
| riproduzione dopo la registrazione | Overdub / Pause / Clear | [O QS, LP] |
| overdub | Stop / Play / Clear | [O QS] |
| riproduzione dopo un overdub | Overdub / Pause / Undo | [O QS] |
| riproduzione dopo un undo | Overdub / Pause / Clear | [O QS] |
| pausa | Overdub / Play / Clear | [V V-UI-26] |

**UI-089** [O] Count-in: `OV_COUNT_IN` da «04» a «01» con l'etichetta «Counting in» [O LP 1398; QS]. In un tempo diverso da 4/4 il conto parte dal numero di movimenti della battuta («03» in 3/4) [V V-UI-27].

### 3.8 Altre schermate

**UI-091** [O] All'avvio l'Orchid mostra il logo per circa 4 s, poi la schermata di gioco [O QS 112-118]. Stame NON DEVE usare il logo né il marchio di Telepathic Instruments: serve un logo proprio, in due versioni (a colori per la plancia, bitmap 1 bit 128×128 per l'OLED) [D].

**UI-092** [D] Sulla Flip la schermata d'avvio copre l'inizializzazione di audio e MIDI. Resta al massimo 4 s; finita l'inizializzazione, un tasto qualsiasi la salta. Sull'Orchid toccare i tasti durante il logo può creare problemi [O supporto], sulla Flip no.

**UI-093** [M] Se il transpose salvato è diverso da zero, dopo l'avvio si vede subito [M FW 3.04].

**UI-095** [V] Batteria bassa: avviso `OV_LOW_BATTERY` al 10% [M MAN], ripetuto al 5% [V V-UI-14]. Sulla Flip vale per la batteria della console; al livello critico Stame salva lo stato prima che spruceOS spenga la console (sezione 50).

**UI-096** [M] Tenendo premuto Key compare la richiesta «select key»; si preme la tonica sulla tastiera, tenendo il tipo **Min** per la minore (dal 3.84; dal 3.90 senza ottava nel prompt) [M MAN, FW]. La richiesta resta finché non si preme un tasto, finché non scade la durata di un overlay o finché non si tocca un altro encoder; dopo la scelta compare `OV_KEY` [V V-UI-15].

**UI-097** [O] Bass Voicing tenuto + BPM attiva la batteria da suonare sulla tastiera [O, guida corretta il 13/10/2026; comportamento nella sezione 10]. Si mostra `OV_DRUMS` con «On» / «Off» [V V-UI-09].

**UI-098** [D] System > Version mostra «Stame» e la versione («1.0.0»), finché non si preme o gira Options o non arriva `PNL_BACK`.

**UI-099** [V] L'Orchid non ha uno screensaver documentato; l'occhio in pixel art delle foto ufficiali potrebbe essere solo marketing [O INT; D]. Stame NON DEVE avere uno screensaver [V V-UI-24].

### 3.9 Indicatori

**UI-106** [O] LED dell'originale, bianchi e piccoli, in alto a destra del loro encoder [O QS 653-683; QSb zOk7zvm69Ec 30-33; LP 1441-1461]. Nel modello diventano `CF_LED` e `CF_LOCK` (UI-024):

| LED | Acceso quando | Nel modello | Fonte |
|---|---|---|---|
| Key | Key mode attiva | `st[ENC_KEY]` `CF_LED` | [M; O] |
| Bass | basso attivo | `st[ENC_BASS]` `CF_LED` | [O] |
| Perform | Lock di Perform | `st[ENC_PERFORM]` `CF_LOCK` | [M; O] |
| FX | Lock di FX | `st[ENC_FX]` `CF_LOCK` | [M; O] |
| vicino a Volume | alimentazione e batteria; lampeggia sempre più in fretta mentre la batteria scende | `plat.battery_pct` | [M MAN] |

**UI-108** [D] Sulla Flip i LED diventano contrassegni nelle celle dei controlli (UI-153) e l'icona della batteria nella testata (UI-126). I LED del trasporto della MPK seguono 40 (MIDI-085): Rec in registrazione e overdub (lampeggia nel count-in), Play con Beat o metronomo attivi, Stop con il loop in pausa.

### 3.10 Thread e tempi

**UI-113** [D] Sulla Flip:
- `core/ui` gira nel thread audio con `core` (UI-004) e pubblica `ui_model_t` nel triple buffer (PLT-017);
- il thread principale (UI) legge evdev, prende lo snapshot, completa i campi di piattaforma, disegna con `ui_flip` e presenta con SDL;
- il thread audio scrive l'anello dell'oscilloscopio (SND-033); la UI lo legge senza lock e accetta di vedere ogni tanto un campione strappato.

La disposizione dei thread è della sezione 50.

---

## 4. La plancia della Flip

### 4.1 Principi

**UI-116** [O] Lo schermo della Miyoo Flip è **640×480** [O nota Flip; tabella hardware di 50]. Le app native aprono una finestra KMSDRM a schermo intero con dimensione logica 640×480 (`SDL_RenderSetLogicalSize(640, 480)`, PLT-059).

**UI-140** [D] Principi della plancia (plancia calma, 15/10/2026):
1. **Niente clone dell'OLED** (decisione di Luigi, in testa alla sezione): si disegna una plancia nativa a colori, che mostra in tempo reale ciò che serve per suonare.
2. **Mentre si suona, solo ciò che si legge a un braccio.** La Flip sta accanto alla MPK, a circa 50–70 cm. A quella distanza una maiuscola deve essere alta almeno 16 minuti d'arco, cioè circa 3 mm (27 px a 9 px/mm). La pagina di gioco mostra quattro cose: **accordo**, **tempo**, **tastiera** e la **banda** con il controllo appena toccato. Il resto non scompare: arriva quando serve (punti 3 e 4).
3. **Il case porta i nomi, lo schermo i valori.** La mascherina incide accanto a ogni comando della MPK la sua funzione (sezione 60): sullo schermo niente legende fisse e niente sigle dei controlli. Toccando un controllo, la banda ne mostra nome e valore in grande per la durata dell'overlay (UI-069), come fa l'Orchid.
4. **Il dettaglio a richiesta.** Le 11 celle dei comandi e la legenda dei tasti della Flip compaiono solo nella pagina dei comandi (UI-142a), che si apre con i tasti del fuoco e si chiude da sola. Note scritte, intervalli, finestre, Play Style, cartellino di Linneo, attività MIDI, voci, carico e livelli stanno nella vista **Geek Out** (UI-051).
5. **Lo stato tace.** Quando tutto va bene la testata mostra solo la batteria; un problema (MPK assente, clip, xrun, batteria scarica) compare solo finché dura.
6. **Posti fissi**: ogni informazione ha un posto che non cambia e nulla compare sopra un'altra. Tastiera e comandi condividono lo stesso rettangolo e se ne vede uno alla volta.
7. **Le zone critiche non si coprono mai**: accordo, tempo e loop restano visibili anche con una lista aperta, la pagina dei comandi o un avviso.
8. **Colore con un ruolo fisso**, sempre accompagnato da una forma o da una posizione: treble, basso e loop si distinguono anche per registro e marcatori, non solo per il colore.
9. **Due inchiostri** (identità, 14/10/2026): le scritte fisse (titoli, BPM, SOUND, nomi dei tasti nella legenda) sono «stampate» in `dim`, color sabbia; i valori che cambiano si accendono in `text` e nei colori dei ruoli.
10. **Segmenti spenti visibili**: il nome dell'accordo in Matrice e le cifre a sette segmenti mostrano anche i punti e i segmenti spenti, in `seg_off`; le celle dei movimenti e le barre sono fatte di celle che si accendono. Le parole lunghe in Matrice della banda (nomi dei suoni) non mostrano i punti spenti: diventerebbero una griglia. Il fondo di ogni zona è il vetro: `bg` con un punto `mesh` ogni 4 pixel, a righe sfalsate.

**UI-141** [D] Classi di testo. Le misure in millimetri valgono per lo schermo da 3,5" della Flip, circa 9 px/mm [D, da misurare: VF-UI-01].

| Classe | Font (UI-144) | Altezza delle maiuscole | Circa | Uso |
|---|---|---|---|---|
| XL | Matrice 5×7, punti con passo 6–14 px (UI-146) | 42–98 px | 4,7–11 mm | nome dell'accordo (passo 14 di norma); valore dell'overlay nella banda (passo 6) |
| L | Spleen 16×32; cifre a sette segmenti alte 32–50 px | 22 px | 2,4 mm | tonalità, transpose, stato del looper, avvisi nella banda; BPM e numeri della banda a sette segmenti |
| M | Spleen 12×24 | 16 px | 1,8 mm | valori delle celle, voci delle liste, metrica in Geek Out |
| S | Spleen 8×16 | 11 px | 1,2 mm | titoli delle celle, testata, etichette della banda, legenda, dettagli |
| XS | Spleen 6×12 | 8 px | 0,9 mm | legende dei controlli MPK nelle celle, etichette delle ottave |

Le classi M, S e XS si leggono solo da vicino: NON DEVONO portare informazioni che servono mentre si suona. Nella pagina di gioco (vista Chord, nessun overlay) compaiono solo come etichette stampate (BPM, SOUND, dettaglio del suono, nomi delle ottave) e negli avvisi della testata; i valori usano Matrice, le sette cifre o la classe L.

### 4.2 Layout

**UI-142** [D] Zone della plancia, dall'alto. Z4 e Z5 occupano lo stesso rettangolo: nella pagina di gioco (`PAGE_PLAY`) si vede la tastiera, nella pagina dei comandi (`PAGE_CONTROLS`, UI-142a) o con una lista aperta si vedono le celle o la lista.

| Zona | Rettangolo (x, y, w, h) | Contenuto | Requisiti |
|---|---|---|---|
| Z1 testata | 0, 0, 640, 24 | batteria; avvisi solo quando servono. In Geek Out la barra completa: MPK, attività MIDI, voci, carico, livello e clip, macro pad, modo tascabile | UI-126 |
| Z2 zona accordo | 0, 24, 416, 216 | tonalità e transpose, **nome dell'accordo**; contenuto secondo la vista | UI-145..UI-147 |
| Z3 tempo e loop | 416, 24, 224, 216 | **BPM** e movimenti; il looper quando lavora; in Geek Out metrica, ritmo e battuta | UI-148, UI-149 |
| Z4 tastiera | 0, 240, 640, 144 | 4 ottave che seguono le finestre, con treble, basso e loop, marcatori della tonalità; le finestre del voicing mentre lo si gira e in Geek Out | UI-150 |
| Z5 zona comandi | 0, 240, 640, 144 | gli **11 controlli** con valore, fuoco e legenda; oppure la lista o il menu aperto. Solo nella pagina dei comandi | UI-151..UI-153, UI-157 |
| Z6 banda | 0, 384, 640, 96 | **il controllo appena toccato** in grande (overlay), avvisi, richiesta della tonalità; a riposo il suono; nella pagina dei comandi la legenda dei tasti della Flip | UI-154..UI-156 |

- Separatori di 1 px nel colore `line` a y = 24, 240, 384 e a x = 416 tra Z2 e Z3.
- **Perché quest'ordine**: in alto, dove l'occhio arriva per primo, ci sono il nome dell'accordo (cosa suona) e il tempo (dove sono nella battuta e nel loop). Subito sotto la tastiera, che mostra le stesse note in forma spaziale: voicing, rivolti, basso e loop. In fondo la banda, che risponde a ciò che la mano ha appena toccato. La testata in cima è sottile e quasi sempre vuota: se la MPK cade o l'audio va in clip, lì lo si vede subito.
- La zona comandi riprende l'ordine del fuoco (MIDI-092): da sinistra a destra e dall'alto in basso, così L1/R1 spostano il fuoco in un percorso di lettura naturale.

**UI-142a** [D] **Pagina dei comandi.** `core/ui` porta `layer.page` a `PAGE_CONTROLS` quando arriva dalla Flip un tasto del fuoco: L1, R1, croce, A o X (anche ripetuti). La pagina resta aperta finché arrivano quei tasti e si chiude **5000 ms** dopo l'ultimo, oppure subito con B quando non c'è una lista da chiudere. Una lista o un menu aperti tengono la pagina aperta finché non si chiudono. I comandi che arrivano dalla MPK, dal macro pad o dalle scorciatoie dirette della Flip (Y, SELECT, START) **non** aprono la pagina: accendono solo la banda (UI-154), perché chi li usa ha già i nomi sotto le dita. Il valore di 5000 ms è da provare. Fa eccezione **T15 Page** del macro pad (40 MIDI-132, deciso da Luigi il 15/10/2026): `MACRO_CONTROLS_PAGE` apre la pagina e la **tiene aperta**, senza i 5 s, finché non arriva un altro `MACRO_CONTROLS_PAGE` o `PNL_BACK`. **T14 View** (`MACRO_VIEW_TOGGLE`) porta in Geek Out e, al tocco dopo, alla vista di prima.

**UI-143** [D] Mockup delle due pagine (1 carattere ≈ 8×16 px; nella tastiera 2 caratteri = 1 tasto bianco, 4 ottave da C2 a B5; `#` = pieno, `T` treble, `B` basso, `L` loop). Stato: Do♯ minore settima con il basso, looper in riproduzione, MPK collegata.

Pagina di gioco, a riposo (la banda mostra il suono):

```
+------------------------------------------------------------------------------+
|                                                                      87% [==]|
+----------------------------------------------------+-------------------------+
| F# Minor                                 Trans +3  |  888                    |
| .                                               .  |  8 8 BPM                |
|    ####   # #               7                      |                         |
|   ##  ## #####                                     | [#####] [   ] [   ] [   ]|
|   ##      # #  ## ##  ##                           |                         |
|   ##     ##### ### ### ##                          | > PLAY           L2 2/4 |
|   ##  ##  # #  ##  ##  ##                          | [######|###---|   |   ] |
|    ####        ##  ##  ##                          | [OVERDUB][PAUSE][CLEAR] |
| .                                               .  |                         |
+----------------------------------------------------+-------------------------+
|  B #   # # #   T #   # T #   # #   # # #   # #   # # #                       |
| C D E F G L B C D T F G L T C D L F G A B C D E F G A B                      |
| C2            C3            C4            C5                                 |
+------------------------------------------------------------------------------+
| SOUND                                                             VA  pluck  |
| 03 Analog Flower                                                             |
+------------------------------------------------------------------------------+
```

Pagina dei comandi (dopo L1 o R1, fuoco su FX; la banda mostra la legenda della Flip):

```
+----------------------------------------------------+-------------------------+
|                 (testata, accordo e tempo come sopra)                         |
+-------------------------+-------------------+#################+--------------+
|SOUND                    |PERFORM       LOCK #>FX              #KEY          *|
|03 Analog Flower         |Arpeggiate         #Reverb 04        #F# Minor      |
|VA  pluck                |16  UP/DOWN        #REV4 CHO3 DLY5   #Trans +3      |
|K1                       |K2 B3              #K3               #K4 B1         |
+-----------------+---------+----------+---------+-------+----------+----------+
|BASS     UNISON *|LOOP     |BPM      *|VOLUME   |OPTIONS|CH.VOICING|BS.VOICING|
|On  03           |Play     |120       |72       |Chord  |025       |24        |
|Fifth Organ Bass |bar 2/4  |Beat 03   |Bass 70  |Simple |C#3 Oct   |C#2       |
|K5 B2            |K6 B5 Rec|K7 B6 Play|K8       |B7 SEL |B4        |Y         |
+-----------------+---------+----------+---------+-------+----------+----------+
|                                                                              |
|   L1 R1 focus  + turn  A press  B back  X push  Y bs.voic  SEL opt  START bpm |
|                                                                              |
+------------------------------------------------------------------------------+
```

Nel disegno vero: il nome è in Matrice (UI-146), il BPM a sette segmenti alti 50 px, la cella con il fuoco ha una cornice di 2 px nel colore `focus` e il titolo in negativo, il pannello del looper ha la cornice rossa durante registrazione e overdub. Le immagini di riferimento sono in `docs/identita/img/`.

### 4.3 Font

**UI-144** [D] La plancia usa i font bitmap **Spleen** di Frederic Cambus (licenza **BSD 2-Clause**), nelle misure 6×12, 8×16, 12×24, 16×32 e 32×64 [D]:
- monospazio, disegnati per lo schermo, nitidi senza antialiasing: si copiano in RGB565 con due colori (primo piano e sfondo), senza fusioni, quindi il disegno costa poco;
- si convertono una volta da BDF in array C (`src/gfx/font_spleen_*.c`) con uno strumento del repository; la licenza va in `third_party/spleen/LICENSE` e in testa ai file generati;
- ingrandimento solo per fattori interi (×2, ×3), nearest-neighbour;
- i glifi che Spleen non ha (♯, ♭, ●, ○, ◉, ✓, ✚, ▶, ■, ❚❚, ◀, ▲, ▼, «, », lampo della carica) si disegnano in un font di simboli di Stame nelle stesse misure; la copertura esatta di Spleen va controllata all'importazione (VF-UI-03);
- riserva, se Spleen non andasse bene: **Terminus** (SIL OFL 1.1), fino a 16×32.

Fatto il 14/10/2026: `tools/bdf2c.py` converte Spleen 2.1.0 (ASCII, Latin-1 e pochi simboli; il 32×64 solo ASCII); `tools/simboli.py` disegna i simboli di Stame nelle stesse celle (a mano nelle misure 6×12 e 8×16, da forme geometriche nelle altre), con in più il trattino lungo e medio e il marchio a U+E000. VF-UI-03 è risolta: Spleen non ha ♯ ♭ ◉ ✓ ✚ ▶ ◀ né i trattini, e nella misura 6×12 neanche ● ○ ▲ ▼ ■ ….

**UI-144a** [D] Due caratteri propri di Stame, per le scritte grandi (identità, `docs/identita/README.md` §3.2):
- **Matrice**: font a punti 5×7 con due righe di discendente, 77 glifi, larghezza da 1 a 5 punti (`tools/matrice.py` → `src/gfx/font_matrice.c`). Ogni punto acceso è un cerchio pieno con il bordo in `edge` (il colore mescolato con il fondo); i punti spenti della cella si disegnano in `seg_off`. Il diametro è circa il 75% del passo (`gfx_matrix`);
- **sette segmenti** inclinati di 5°, con i segmenti spenti in `seg_off`, per i numeri che cambiano mentre si suona: BPM (UI-148) e valori numerici delle evidenze (UI-154) (`gfx_seg7`).

I font dell'OLED sono diversi e propri (§7.2).

**UI-019** [D] Le stringhe arrivano a `gfx` in UTF-8. Oltre all'ASCII stampabile DEVONO essere riconosciuti almeno `♯` (U+266F), `♭` (U+266D), `✓` (U+2713), `●` (U+25CF), `°` (U+00B0) e i simboli di UI-144. Un carattere sconosciuto diventa `?`. I testi restano in inglese (§0.4).

### 4.4 Testata

**UI-126** [D] Z1 (0, 0, 640, 24), testo in classe S alle righe 4..19. **Fuori da Geek Out lo stato tace**: la testata mostra a destra la batteria e, da x = 8 verso destra e solo finché servono, «NO MPK» (lampeggia), «MPK BUSY», «MPK ERROR», «MPK FACTORY», «PAD» (macro pad in errore o senza mappa), «POCKET», «LOCK» seguito da «SOUND PERFORM KEY» in `dim` (Lock delle manopole del macro pad acceso, 40 MIDI-131: è uno stato che cambia cosa fanno le mani, come il LED del Caps Lock), «CLIP» (1500 ms) e «XRUN» (2 s), con 16 px tra l'uno e l'altro; «NO MPK» tiene il suo posto anche quando è spento, così il resto non si sposta. Attività MIDI, voci, carico e livelli non si disegnano e non ridisegnano la zona. Nella vista **Geek Out** la testata è la barra completa:

| Elemento | x | Contenuto |
|---|---|---|
| MPK | 4..99 | contrassegno, seguito dal **banco stimato dei pad** in `dim` («A», «B» o «?», MIDI-089): «MPK STAME» (`focus`), «MPK FACTORY» (`active`, programma di fabbrica, funzioni ridotte, MIDI-088), «MPK BUSY» (`warn`, porta occupata da un'altra app, MIDI-071), «MPK ERROR» (`warn`), «NO MPK» (`warn`, lampeggia: 500 ms acceso, 500 spento) |
| attività MIDI | 108..187 | «IN» e «OUT» con un pallino acceso per **50 ms** a ogni messaggio: IN = dalla MPK o dal DIN IN, OUT = verso il DIN OUT |
| voci | 208..279 | «VOX 07/16»; sopra 14 il numero va in `active`, a 16 in `warn` |
| carico | 292..347 | «CPU 23%»: carico del thread audio (`dsp_load_pct`); sopra il 70% in `active`, sopra il 90% in `warn`; per 2 s dopo un underrun la scritta diventa «XRUN» in `warn` |
| livello | 360..447 | due barre (L e R) di 88×4 px alle righe 7..10 e 13..16, scala −48..0 dBFS, picco con caduta di 20 dB/s e tenuta di 1 s; in `text` fino a −6 dBFS, in `active` sopra |
| clip | 452..487 | «clip» in `dim`; in negativo su `warn` per **1500 ms** dopo ogni aumento di `clip_count` |
| macro pad | 492..523 | contrassegno «PAD» (40, §8.10): in `focus` se collegato e aperto in esclusiva (`PADL_OPEN`); in `warn` se non si apre in esclusiva (`PADL_ERROR`) o manda codici che nessuna mappa conosce (`PADL_UNMAPPED`); nascosto se assente. Con il Lock delle manopole acceso (MIDI-131) diventa «LOCK» in `active` |
| modo tascabile | 528..575 | contrassegno «POCKET» in `active`, solo se acceso |
| batteria | 576..635 | «87%» e un'icona da 28×12 px con il riempimento proporzionale e il lampo durante la carica; sotto il 15% in `warn` (PLT-090), sotto il 10% lampeggia a 1 Hz |

- In Geek Out, con `prefs.meters` spento si nascondono voci, carico, livello e clip.
- Le informazioni di piattaforma stanno solo qui, nel menu della piattaforma e negli avvisi (UI-156).

**UI-127** [D] Collegamento e scollegamento della MPK o del macro pad a caldo: cambia il contrassegno MPK o «PAD» e compare un avviso breve (UI-156); con il macro pad cambiano anche le legende (UI-152, UI-155). Il riconoscimento è della sezione 40 (§11, MIDI-127).

### 4.5 Zona accordo

**UI-145** [D] Z2 (0, 24, 416, 216), margini interni x 12..403. Nella vista Chord (UI-147), quella di fabbrica, ci sono solo tre cose:

| Righe | Contenuto |
|---|---|
| 30..61 | **tonalità** in classe L a x = 12 («F♯ Minor»); con la Key mode spenta non si scrive nulla. **Transpose** in classe L, allineato a destra a x = 404 («Trans +3»), in `active`, solo se diverso da zero |
| 68..231 | **nome dell'accordo** (UI-146), in un vetrino: quattro angoli a squadra in `line` (x 4..411, righe 68..231) |

- Colore del nome (identità, 14/10/2026): l'accordo in `treble` e il basso dopo la barra in `bass`, gli stessi colori dei tasti accesi, durante il suono e la persistenza; tutto in `ghost` in `CH_GHOST`; con `CH_NONE` il vetrino resta vuoto.
- Le note che suonano non si scrivono: le mostra la tastiera (Z4). Si scrivono nelle viste Notes e Geek Out.
- Play Style e Secret Chords si vedono nella cella Options della pagina dei comandi, nel loro overlay e in Geek Out. Con il modo tascabile acceso, «STICK E» in XS in `focus` allineato a destra a x = 404 sulla riga 222.
- Nota singola (UI-037): fondamentale e alterazione come un accordo, l'ottava come apice in `dim`.
- Richiesta della tonalità (UI-096): al posto del nome, «Select Key» in Matrice con passo 6 in `active`, centrato.

**UI-146** [D] Impaginazione del nome, in **Matrice** (UI-144a). Le parti di `chord_label_t` si disegnano da sinistra, a partire da x = 16, nell'ordine fondamentale, alterazione, qualità, apice, «/», basso. Si sceglie la **scala più grande** (4, 3, 2 o 1) per cui il nome sta in 384 px. I numeri sono i passi dei punti in pixel:

| Parte | s = 4 | s = 3 | s = 2 | s = 1 | Allineamento verticale |
|---|---|---|---|---|---|
| fondamentale | 14 (lettera 70×98) | 12 | 9 | 6 | sulla linea di base |
| alterazione (♯ ♭ x) | 10 | 8 | 6 | 4 | in alto, sulla cima della fondamentale |
| qualità (m, dim, sus, +, m(add4)) | 10 | 8 | 6 | 4 | sulla linea di base |
| apice (7, M7, 9, JAZZ, WTF…) | 7 | 6 | 4 | 3 | in alto, sulla cima della fondamentale |
| «/» e basso | 10 | 8 | 6 | 4 | sulla linea di base; l'alterazione del basso al passo dell'apice, in alto |

- Linea di base: 149 + 7·p/2, dove p è il passo della fondamentale (riga 198 per s = 4, 191 per s = 3, 180 per s = 2, 170 per s = 1): le maiuscole sono centrate sulla riga 149, a metà del vetrino.
- Spazio tra le parti: un punto del passo della qualità; tra fondamentale e alterazione mezzo punto della fondamentale (il ♯ si avvicina, come sull'originale).
- Esempi: «F♯m7» a s = 4 occupa circa 230 px; «C♯m(add4)M79/G♯» passa a s = 2 o 1.
- La fondamentale **non** si allarga per riempire lo spazio (l'impaginazione elastica è dell'OLED, UI-035): sulla plancia il nome resta a sinistra, con la stessa misura per tutti gli accordi della stessa lunghezza, così l'occhio non deve riadattarsi.

**UI-147** [D] La vista (UI-051) decide il contenuto di Z2; testata (righe 30..61) uguale in tutte, tranne React:

| Vista | Righe 68..231 |
|---|---|
| **Chord** (default) | nome (UI-146) nel vetrino, e basta |
| **Chord + Keyboard** | nome con s ≤ 3 in x 12..247, sulla linea di base della vista Chord; a destra (x 264..403, righe 76..227) una tastiera di un'ottava con le classi ripiegate: treble in `treble`, basso in `bass`, marcatori della tonalità |
| **Keyboard** | tastiera di un'ottava con le classi ripiegate su tutta la larghezza (x 12..403, righe 72..227) |
| **Notes** | nome con s = 1, linea di base 116; note in 32×64 alle righe 140..203, nei colori dei ruoli, centrate, ristrette a 16×32 (riga 160) se non stanno |
| **Geek Out** | nome con s ≤ 2, linea di base 136; tre righe in classe S alle righe 152, 172 e 192: note con l'ottava («C♯2 : E3 G♯3 B3»); intervalli dalla fondamentale («INT 1 ♭3 5 ♭7»); finestre «W 48 C3 · WB 36 C2 · Octave». Alla riga 220, a destra, i tre Play Style («SIMPLE ADV FREE»: l'attivo in `text`, gli altri in `seg_off`), «SECRET» e «STICK». In alto a destra la classe di Linneo (UI-161) |
| **React** | oscilloscopio dell'uscita (SND-033): traccia di 1 px in `treble` su 392 punti, centrata sulla riga 150, ±64 px a fondo scala; nome con s = 1 allineato a destra a x = 404, linea di base 74; niente testata |

In Geek Out cambiano anche le altre zone: la testata diventa la barra completa (UI-126), Z3 aggiunge metrica, ritmo e battuta (UI-148), la tastiera mostra sempre le finestre (UI-150). La tastiera a 4 ottave di Z4 c'è in tutte le viste, tranne quando la pagina dei comandi o una lista ne prendono il posto.

**UI-161** [D] **Cartellino di Linneo** (identità, 14/10/2026). Linneo classificava le piante contando gli stami; Stame conta le note: una classe di nota è uno stame. Nella vista **Geek Out**, in alto a destra (riga 74, allineato a x = 404), il marchio piccolo (U+E000, classe XS) e il nome della classe in XS stampato: le classi di nota distinte delle note che suonano danno «MONANDRIA» (1), «DIANDRIA» (2), «TRIANDRIA» (3), «TETRANDRIA» (4) … «DODECANDRIA» (11, 12) (`ui_fmt_linnaeus`). Dal 15/10/2026 non compare più nella vista Chord: è un dettaglio da guardare da vicino (UI-140).
- Si disegna solo se non tocca il nome: fra la fine del nome e il cartellino restano almeno 16 px.
- In `dim`; in `ghost` con l'accordo in `CH_GHOST`; nascosto con `CH_NONE` e con `prefs.linnaeus` spento (menu della piattaforma, *Linnaeus Tag*, default acceso).

### 4.6 Zona tempo e loop

**UI-148** [D] Z3 (416, 24, 224, 216), margini interni x 428..631. Parte del tempo:

| Righe | Contenuto |
|---|---|
| 36..85 | **BPM** a sette segmenti alti 50 px a x = 428 (tre cifre, quelle spente in `seg_off`: « 96» mostra l'otto spento davanti) e «BPM» stampato in XS accanto, alla riga 76. Solo in Geek Out, la **metrica** in classe M allineata a destra a x = 632 («4/4», «6/8») |
| 94..109 | solo in Geek Out, in classe S: a sinistra la sorgente del ritmo («BEAT 03 Funk», «METRO», «BEAT OFF» in `dim`, «LOOP 03» con uno slot caricato); a destra «BAR 12» con il trasporto in moto |
| 116..143 | **celle dei movimenti**: una per movimento della battuta, larghe `(204 − 6·(n − 1)) / n` px con 6 px di spazio. Movimento corrente pieno in `text` (il primo della battuta in `focus`), gli altri pieni in `seg_off` (spenti ma visibili); da fermo tutte in `seg_off` |

- Con `prefs.beat_flash` acceso, il fondo del numero del BPM (x 424..535, righe 32..89) lampeggia in `bar` per 60 ms a ogni movimento.
- Durante il count-in le celle mostrano al centro i numeri che mancano, in classe M.
- Il ritmo che suona si riconosce dalle celle che si accendono; il nome del pattern compare nella banda quando lo si cambia (overlay) e nella cella BPM della pagina dei comandi.

**UI-149** [D] Parte del looper. Si disegna **solo quando il looper lavora** (stato diverso da `LP_IDLE`) o quando Loop è il bersaglio della rotazione (`turn_target`); a riposo le righe 152..233 restano vuote, senza l'aiuto «Rec / B5: loop» (lo dice la mascherina).

| Righe | Contenuto |
|---|---|
| 152..183 | **stato** in classe L con il simbolo: «● REC» e «◉ DUB» in `warn`, «▶ PLAY» in `loop`, «❚❚ PAUSE» in `dim`, «WAIT» nella Waiting Room, «COUNT» nel count-in, «LOOP» in `dim` se Loop è solo toccato. A destra la battuta corrente su quelle totali in classe L («2/4»; «FREE» in Free) e, prima, gli strati in classe S («L2») |
| 190..201 | **barra di avanzamento** di 204×12 px divisa in `bars` segmenti (2 px di spazio tra uno e l'altro): parte suonata in `loop` (in `warn` in registrazione), resto in `seg_off`, testina di 2 px in `text`. In Free durante la prima registrazione: tratteggio che scorre (UI-086). Nella Waiting Room: segmenti della scelta selezionata, vuoti |
| 210..233 | **menu a tre voci** (UI-088): tre pulsanti da 65×24 (x 428..492, 497..561, 566..630) con il testo in classe S centrato. La voce selezionata è piena: in `focus` se Loop è il bersaglio della rotazione, altrimenti in `bar` |

- Durante registrazione, overdub e count-in il bordo di Z3 diventa una cornice di 2 px in `warn`: si capisce da lontano che si sta registrando.
- `loop_full` aggiunge «FULL» in `warn` sopra lo stato.
- Con il looper attivo l'accordo resta visibile in Z2: sulla plancia non vale UI-090, che riguarda solo l'OLED.

### 4.7 Tastiera

**UI-150** [D] Z4 (0, 240, 640, 144). Tastiera di **4 ottave che segue le finestre del voicing**, 28 tasti bianchi larghi 21 px. Decisione di Luigi del 13/10/2026 («riducila»): tasti più grandi e leggibili a distanza di braccio, al posto delle 8 ottave fisse della prima bozza.

Gamma visibile: da `kb_lo` a `kb_lo + 47`, dove `kb_lo` è sempre un Do (multiplo di 12).
- All'avvio `kb_lo` = il Do dell'ottava che contiene WB: con WB = 37 la gamma va da C2 a B5.
- A ogni fotogramma la gamma DEVE contenere le due finestre, da min(W, WB) a max(W, WB) + 11. Se ci stanno già, `kb_lo` **non cambia**, così girare il voicing dentro la gamma non fa muovere nulla. Se una finestra esce, `kb_lo` si sposta del minimo numero di ottave intere, di colpo e senza animazione.
- Se le due finestre insieme superano 4 ottave, ha la precedenza la finestra treble; il resto si segnala con i triangoli.

| Elemento | Geometria e colore |
|---|---|
| tasto bianco `i` (0..27) | x = 12 + 22·i, largo 21 px, righe 262..361, colore `kb_white`; la colonna x + 21 è lo spazio in `bg` |
| tasto nero dopo il bianco `i` | x = 12 + 22·i + 15 .. + 27 (13 px, centrato sullo spazio), righe 262..321, colore `kb_black` |
| note dal vivo | tasto pieno nel colore del ruolo: `treble` o `bass`; se la stessa altezza è sia treble sia basso, metà sinistra `treble` e metà destra `bass` |
| note del looper | striscia in `loop` in fondo al tasto: righe 350..361 sui bianchi, 314..321 sui neri; si vede anche sopra un tasto pieno |
| marcatori della tonalità | con la Key mode accesa, un **granello di polline** in `in_key` sulle classi di `pc_in_key`: punto tondo di diametro 6 px centrato sulla riga 342 sui bianchi, 5 px sulla riga 308 sui neri; su un tasto pieno si disegna in `bg` |
| finestra treble | **solo mentre si gira un voicing** (overlay `OV_VOICING`, `OV_BASS_VOICING`, `OV_SINGLE_NOTES`) **e in Geek Out**: barra di 2 px in `treble` alle righe 246..247, dal bordo sinistro del tasto W al bordo destro del tasto W + 11 |
| finestra del basso | come la treble, in `bass`, righe 252..253, da WB a WB + 11 |
| antere delle finestre | identità: a ogni capo delle due finestre un punto tondo di raggio 3 px nel colore della finestra (il filamento con le sue antere) |
| ottava delle note singole | con le finestre, in Full Octave, linea tratteggiata in `treble` alla riga 256 sull'ottava che contiene W (ACC-080) |
| note fuori gamma | triangolo di 8×16 px nel colore del ruolo: ◀ a x 2..9 per le note sotto `kb_lo`, ▶ a x 630..637 per quelle sopra `kb_lo + 47`, righe 300..315. Capita con Strum 2 Oct, Arp 2 Oct, Harp e con il loop |
| modo tascabile | i tasti della classe `pocket_pc` dentro la finestra treble hanno un contorno di 2 px in `focus` |
| etichette | righe 364..379, classe S: «C2» … «C5» sotto ogni Do, cioè il nome reale dell'ottava visibile (il Do centrale, C4, in `text`, gli altri in `dim`). Con `note_labels` = All anche la lettera di ogni tasto bianco in classe XS; con Off nessuna |

Le finestre mostrano la **posizione del voicing**: girando Chord Voicing compaiono, la barra treble scorre di un semitono per scatto e si vede come cambia il rivolto; finito l'overlay spariscono. Le righe 241..261 restano vuote quando non servono.

### 4.8 Zona comandi

**UI-151** [D] Z5 (0, 240, 640, 144), **solo nella pagina dei comandi** (UI-142a), contiene le 11 celle dei controlli in due file da 72 px, nell'ordine del fuoco (MIDI-092):

| Fila | Celle (larghezza in px) |
|---|---|
| 1, righe 240..311 | Sound 208 · Perform 160 · FX 144 · Key 128 |
| 2, righe 312..383 | Bass 144 · Loop 80 · BPM 88 · Volume 80 · Options 72 · Chord Voicing 88 · Bass Voicing 88 |

Interno di una cella con origine `(x, y)` e larghezza `w`, margine di 4 px:

| Righe | Contenuto |
|---|---|
| y + 2 .. y + 17 | titolo in classe S; contrassegni a destra (UI-153) |
| y + 18 .. y + 41 | valore in classe M; per Volume, Chord Voicing e Bass Voicing, dietro il testo, una barra in `bar` lunga in proporzione al valore |
| y + 43 .. y + 58 | dettaglio in classe S |
| y + 60 .. y + 71 | legenda dei controlli in classe XS, in `dim` (nascosta con `prefs.legend` spento) |

Un testo che non sta nella cella si tronca con «…».

**UI-152** [D] Contenuto delle celle (testi composti con `ui_fmt_*`):

| Controllo | Titolo | Valore (M) | Dettaglio (S) | Legenda senza macro pad (XS) | Legenda con il macro pad (XS) |
|---|---|---|---|---|---|
| Sound | SOUND | «03 Analog Flower», «U05 Nome» | motore e categoria («VA  pluck»), «legacy» se `CF_LEGACY` | K1 | K1 T1 |
| Perform | PERFORM | modo breve (UI-066) o «Off» | parametro: «Amount 07», «16  UP/DOWN», «Pattern 05» | K2 B3 | K2 T2 |
| FX | FX | effetto principale e valore: «Reverb 04», «Chorus OFF» | slot con intensità diversa da zero: «REV4 CHO3 DLY5» | K3 | K3 T3 |
| Key | KEY | «F♯ Minor» o «Off» | «Trans +3» (in `active`) o «Trans 0» (in `dim`) | K4 B1 | K4 T4 |
| Bass | BASS | «On  03» o «Off  03» | nome del basso | K5 B2 | K5 T5 |
| Loop | LOOP | «Rec», «Dub», «Play», «Pause», «Wait», «Count», «—» | «bar 2/4», «Free», «Loop 03» | K6 B5 Rec | K6 T6 Rec |
| BPM | BPM | «120» | «Beat 03», «Metro», «Off» | K7 B6 Play | K7 T7 Play |
| Volume | VOLUME | «72» | «Bass 70» | K8 | K8 T8 |
| Options | OPTIONS | vista breve: «React», «Chord», «Keybd», «Ch+Kb», «Notes», «Geek» | Play Style | B7 SEL | m2 T9 SEL |
| Chord Voicing | CH.VOICING | «032» (3 cifre, come l'overlay) | nota d'inizio e modo: «C♯3 Oct», «C♯3 Split» | B4 | M |
| Bass Voicing | BS.VOICING | «23» | nota d'inizio: «C♯2» | Y | m1 Y |

- Le legende riprendono la mappa di 40 (§8.5, §8.10, §9.1): sono la **legenda viva** della MPK e del macro pad. Restano nelle celle anche con la plancia calma: la pagina dei comandi si guarda da vicino e, finché il case non c'è, è l'unico promemoria della mappa. Con il macro pad collegato (`pad_link` = `PADL_OPEN`) si usa l'ultima colonna: manopola della MPK, tasto o manopola del macro pad e, dove c'è, la scorciatoia sempre a portata (trasporto o tasto della Flip). I pad del banco B, che con il macro pad sono una riserva, non compaiono. Ogni legenda sta nella sua cella con le misure di UI-151 (XS = 6 px per carattere).
- Options non ha una manopola sulla MPK: si ruota con m2, « », joystick o croce dopo averlo premuto, perché la pressione porta lì il fuoco (MIDI-104). Senza macro pad lo stesso vale per Chord Voicing e Bass Voicing, che dal 13/10/2026 non hanno più una manopola sulla MPK: si raggiungono con L1/R1 o premendo B4 o Y.

**UI-153** [D] Stati di una cella, cumulabili:

| Stato | Resa |
|---|---|
| **fuoco** (`ctl.focus`) | cornice di 2 px in `focus` lungo tutta la cella e titolo in negativo (testo `bg` su `focus`) |
| **premuto** (`CF_PRESSED`) | barra di 2 px in `text` sul bordo alto della cella che cresce da sinistra a destra in `t_hold_ms` (dal `pressed_since_ms`); a soglia raggiunta resta piena finché il controllo è tenuto. Con `CF_SECONDARY` la barra sparisce e il titolo mostra la funzione secondaria («TRANSPOSE», «BASS VOL», «BEAT VOL») |
| **attivo** (`CF_ACTIVE`) | riga del valore in negativo su `active` per la durata dell'overlay |
| **LED** (`CF_LED`) | pallino ● in `text` a destra del titolo |
| **Lock** (`CF_LOCK`) | contrassegno «LOCK» in negativo su `active` a destra del titolo |
| **PUSH bersaglio** (`push` = TARGET(k)) | la cella dell'encoder di Kn mostra lo stato «premuto», anche se la pressione arriva da B8 o da X. Con il macro pad la pressione di Tn è una pressione normale (`CF_PRESSED`) |

### 4.9 Banda

**UI-154** [D] Z6 (0, 384, 640, 96) mostra **una sola cosa alla volta**, in quest'ordine di priorità:
1. avviso `MSG_WARN` (UI-156), in classe L in `warn`, con una barra di 6 px in `warn` a sinistra;
2. **evidenza dell'overlay** attivo (`layer.ov`): il controllo appena toccato;
3. richiesta della tonalità (UI-096): «Select Key» in classe L in `active` e, sotto, «press a key (hold Min for minor)» in classe S;
4. avviso `MSG_INFO`, in classe L;
5. riga di debug, se `prefs.debug` è acceso (UI-155);
6. un aiuto di contesto (UI-155): pagina dei comandi, lista aperta, PUSH armato, Bass Voicing tenuto, modo tascabile, nessuna MPK, Learn Pad;
7. **a riposo, il suono**: «SOUND», il numero e il nome.

Resa dell'evidenza, la stessa per tutti gli overlay (UI-065):
- **etichetta** dell'overlay in classe S maiuscola, con un pixel di spaziatura, in `dim`, a x = 16, riga 394; il **dettaglio** in classe S in `dim`, allineato a destra a x = 624;
- **valore** alle righe 420..467: le cifre a sette segmenti alte 48 px, poi il testo in Matrice con passo 6 (5, 4 o 3 se non sta, altrimenti classe L troncata), **senza** i punti spenti; per Volume, Bass Volume, Beat Volume e i due voicing, dopo il valore, una barra a celle alta 24 px (celle da 6 px, spazio 2) proporzionale al valore;
- una barra di 4 px in `active` lungo il bordo sinistro dice che il controllo è stato appena toccato;
- **funzioni secondarie** (Transpose, Bass Volume, Beat Volume: premi e gira): l'etichetta è in negativo (`bg` su `active`, come il tasto tenuto) e il valore è in `active`.

A riposo la banda usa la stessa impaginazione un gradino sotto: niente barra a sinistra, cifre alte 32 px e nome in Matrice con passo al massimo 4, a partire dalla riga 428. Quando si tocca un controllo, il valore cresce: si nota anche con la coda dell'occhio. Esempi:

| Overlay | Banda |
|---|---|
| `OV_SOUND` | SOUND … «VA  pluck» · **03** **Analog Flower** |
| `OV_ARP` | ARPEGGIATE · **16** **UP/DOWN** |
| `OV_FX` | REVERB · **04** |
| `OV_KEY`, `OV_KEY_TOGGLE` | KEY · **F♯ Minor** / **Off** |
| `OV_TRANSPOSE` | TRANSPOSE in negativo · **+3** in `active` |
| `OV_VOLUME` | VOLUME · **72** e la barra a celle |
| `OV_BASS_VOLUME`, `OV_BEAT_VOLUME` | etichetta in negativo · **70** e la barra in `active` |
| `OV_VOICING` | VOICING · **032** **C♯3** e la barra |
| `OV_BATTERY` | BATTERY … «Charging» / «No cable detected» · **87** **%** |
| `OV_COUNT_IN` | COUNTING IN · **03** |
| `OV_SAVED` | SAVED · **U05** |
| `OV_LOW_BATTERY` | LOW BATTERY · **10** **%** |

L'evidenza dura quanto l'overlay (UI-069) e la chiude `PNL_BACK` (UI-070).

**UI-155** [D] Aiuto di contesto: una riga in classe S centrata nella banda (riga 424), o due righe (riga 404 e 436) dove serve; i nomi dei tasti in negativo (`bg` su `dim`), le funzioni in `text`. **Non c'è più una legenda fissa** della MPK e del macro pad: i loro nomi sono incisi sulla mascherina (sezione 60) e nella pagina dei comandi ogni cella porta la sua sigla. Restano gli aiuti che servono in un momento preciso:

| Contesto | Riga |
|---|---|
| pagina dei comandi | «L1 R1 focus  ✚ turn  A press  B back  X push  Y bs.voic  SEL opt  START bpm» |
| lista o menu aperto | «✚ ▲▼ scroll  A select  B back  MENU menu» |
| PUSH armato (B8 o X tenuto) | «PUSH: touch or turn a knob to press it» |
| Bass Voicing tenuto (m1 o Y) | «BASS VOICING held: Loop = hard exit  BPM = drums  Bass = bass on/off» |
| modo tascabile | due righe: «L-stick note  A play  L2 L1 R1 R2 Dim Min Maj Sus  ✚ 6 m7 M7 9» e «R-stick X voicing, Y turn  R3 press  X Y focus  L3 bs.voicing  B back» |
| nessuna MPK, a riposo | «No MPK: Flip keys only.  MENU > Pocket Mode to play without MPK» (con il macro pad: «No MPK: macro pad and Flip keys.  MENU > Pocket Mode to play notes») |
| Learn Pad in corso (UI-175) | due righe: «LEARN PAD 05/21: press T5 (Bass)» e «B = previous step  MENU = cancel  a code already used must be repeated» |
| debug | «frame 2.1 ms  dsp 23/31%  period 256x2  xrun 0  ALSA  snap 6 ms» |

Con `prefs.legend` spento non compaiono le righe della pagina dei comandi e delle liste; avvisi, evidenze, richieste e gli altri aiuti si vedono comunque.

**UI-156** [D] Avvisi:

| Avviso | Quando | Testo | Livello | Durata |
|---|---|---|---|---|
| MPK occupata | `EBUSY` all'apertura (MIDI-071) | «MPK busy: used by another app» | warn | finché dura; si riprova ogni secondo |
| programma non STAME | passaggio a `mpk_fabbrica` (MIDI-119) | «STAME program not active: reduced functions» | warn | 5 s, una volta per collegamento |
| audio di riserva | ALSA non si apre (PLT-023) | «ALSA unavailable: SDL audio, higher latency» | warn | 3 s |
| memoria del loop piena | `loop_full` (ACC-231) | «Loop memory full» | warn | 3 s |
| banco di fabbrica assente | SND-133 | «Factory bank missing: INIT sounds» | warn | 5 s all'avvio |
| patch del formato vecchio | SND-104 | «Legacy patch (format 0)» | info | 3 s al caricamento |
| MPK collegata / persa | `PNL_SRC_CONNECTED` / `PNL_SRC_LOST` di `SRC_MPK` | «MPK connected» / «MPK disconnected» | info / warn | 2 s |
| macro pad collegato / perso | `PNL_SRC_CONNECTED` / `PNL_SRC_LOST` di `SRC_MACROPAD` (MIDI-127) | «Pad connected» / «Pad disconnected» | info / warn | 2 s |
| macro pad occupato | `EVIOCGRAB` fallito (MIDI-124) | «Pad busy: grabbed by another app» | warn | finché dura; si riprova ogni secondo |
| macro pad senza mappa | 5 codici sconosciuti di fila (MIDI-123) | «Pad not mapped: MENU > Learn Pad» | warn | 5 s, una volta per collegamento |
| Learn Pad | codice già usato in un passo precedente; mappa salvata (MIDI-123) | «Code already used by T3: try again» / «Pad map saved» | warn / info | 2 s |
| modo tascabile | MENU > Pocket Mode (MIDI-094) | «Pocket Mode on» / «off» | info | 2 s |
| panic | `MACRO_PANIC` | «Panic: all notes off» | info | 2 s |

### 4.10 Liste e menu

**UI-157** [D] Una lista o un menu aperto (UI-025) prende il posto della tastiera o delle celle in **Z5**, anche dalla pagina di gioco (UI-142a); Z2 e Z3 non cambiano.

| Righe | Contenuto |
|---|---|
| 240..263 | intestazione in classe S: percorso a x = 8 («OPTIONS > INSTRUMENT > PLAY STYLE»), posizione a destra («3/4»); fondo `panel` |
| 264..383 | **5 righe da 24 px**, testo in classe M a x = 16. La voce selezionata sta **sempre nella riga centrale** (righe 312..335), piena in `focus` con il testo in `bg` (UI-073) |

- Colonne: numero («03», «U05») a x = 16; etichetta a x = 64 (o a x = 16 se non c'è numero); colonna informativa in classe S in `dim` a x = 448 (lista Sound: motore e categoria); valore allineato a destra a x = 604; marcatore (✓, ●, indice, ›) a x = 616.
- Barra di scorrimento di 3 px a x 636..638, righe 264..383.
- Voce numerica in modifica (UI-075): il valore in negativo, con il lampeggio di UI-075.
- Voci senza effetto sulla Flip (Audio Output, UI-080): colonna informativa «set by spruceOS».
- **Direzione dei tasti**: in una lista la croce e il joystick verso l'alto DEVONO portare alla voce precedente (più in alto sullo schermo) e verso il basso alla successiva; le rotazioni restano orario = successiva (UI-074). Con la mappa di 40, dove croce su e joystick su valgono +1, i due versi sono opposti: come risolverlo è in §9.4.
- La Waiting Room (UI-087) è una lista in Z5 con proprietario Loop; Z3 ne mostra l'anteprima (UI-149).
- MPK Status e Version (`LS_MPK_STATUS`, `LS_VERSION`) usano le stesse 5 righe come testo non selezionabile; si esce con Back.

**UI-158** [D] Mockup degli stati con una lista aperta (solo Z5 e Z6; il resto è come in UI-143).

Options > Instrument > Play Style, con la selezione su Advanced e la spunta su Simple:

```
+------------------------------------------------------------------------------+
|OPTIONS > INSTRUMENT > PLAY STYLE                                          3/4|
|  Back                                                                        |
|  Simple                                                                    ✓ |
|##Advanced####################################################################|
|  Free                                                                        |
|                                                                              |
+------------------------------------------------------------------------------+
|+ up/dn scroll  A select  B back  MENU menu                                   |
|<< >> joy up/dn scroll  joy> select  joy< back                                |
+------------------------------------------------------------------------------+
```

Lista Sound, aperta premendo Sound, con il suono attivo selezionato:

```
+------------------------------------------------------------------------------+
|SOUND                                                                     4/76|
|  01    Orchid EP                                    RP  piano elettrico      |
|  02    Ghost                                        VA  pad / pluck          |
|##03####Analog Flower################################VA##pluck#############✓##|
|  04    Cherry Blossom                               VA  pad                  |
|  05    Eraserhead                                   FM  organo               |
+------------------------------------------------------------------------------+
```

Evidenza di una funzione secondaria (Key premuto e girato), in Z6:

```
+------------------------------------------------------------------------------+
|#Transpose########+3##########################################################|
|##############################################################################|
+------------------------------------------------------------------------------+
```

### 4.11 Altre schermate

**UI-159** [D]
- **Avvio** (UI-091, UI-092): l'unico stato a tutto schermo, sul vetro con la maglia, con le squadre di una tavola botanica agli angoli e «TAB. I» in alto a sinistra (identità, `docs/identita/README.md` §3.5):
  - 0–800 ms: crescono i tre filamenti del marchio (centro 320, 150; alto 170 px), in `treble`;
  - 800, 1000 e 1200 ms: si accendono le antere, dalla più bassa (prima sono in `seg_off`);
  - dai 1200 ms: «STAME» in Matrice (passo 9, linea di base 318), celle spente subito, una lettera accesa ogni 80 ms;
  - dai 1600 ms: «STAMEN HARMONICUM · TRIANDRIA» in XS stampato;
  - in basso, in classe S stampata, le righe dell'inizializzazione: «Audio  ALSA hw 48 kHz 256x2  ok», «MIDI   MPK mini Plus  ok» oppure «searching…», «Sounds 70 factory · 3 user»; versione in basso a destra;
  - **logo sonoro** (`assets/suoni/stame_avvio.wav`): tre note che salgono con le antere. Nello Stame vero è un'opzione del menu della piattaforma (*Boot Sound*) **spenta per default**; nella vetrina suona.
- **Batteria** (premere Volume): evidenza `OV_BATTERY` (UI-154).
- **Scelta rapida della tonalità**: «Select Key» in Z2 (UI-145), richiesta in Z6, cella Key attiva.
- **MPK Status** (menu della piattaforma): in Z5 cinque righe: dispositivo e firmware («MPK mini Plus 09e8:0054  fw 1.13»), porte («Port 1 open (controller)  Port 2 open (DIN)»), programma («STAME» o «factory, reduced functions»), ultimo messaggio ricevuto e da quanto («B0 48 01  12 ms ago»), LED del trasporto («ok» o «unknown», VM-13).
- **Version**: in Z5 «Stame 1.0.0», data e identificativo della build.

### 4.12 Temi e colori

**UI-128** [D] Due temi; i colori sono token che `ui_flip` legge da una tabella costante (`src/ui_flip/tema.c`). Default: **Dark**, cioè **Notte**, un display a fluorescenza (VFD); **Light** è **Giorno**, un LCD riflettente (identità, 14/10/2026). Nel menu restano «Dark» e «Light».

| Token | Ruolo | Notte (Dark) | Giorno (Light) |
|---|---|---|---|
| `bg` | vetro | `#050C0B` | `#CED4C2` |
| `mesh` | maglia del vetro: un punto ogni 4 px, righe sfalsate | `#0A1614` | `#C8CEBB` |
| `panel` | fondo delle intestazioni, delle liste e della testata | `#0A1715` | `#D9DECE` |
| `line` | separatori, contorni, angoli del vetrino | `#1B302C` | `#A2AA95` |
| `seg_off` | punti e segmenti spenti, celle spente, Play Style non attivi | `#10221F` | `#C1C8B4` |
| `bar` | barre di valore, traccia del progresso | `#123029` | `#B5BDA7` |
| `ghost` | ultimo accordo dopo la persistenza, legende dei comandi nelle celle | `#3F655D` | `#879180` |
| `text` | valori accesi, LED | `#DDFBF1` | `#141B18` |
| `dim` | scritte stampate: titoli, unità, nomi dei tasti (sabbia) | `#A99F86` | `#424C47` |
| `treble` | accordo, note treble, finestra del voicing, oscilloscopio | `#3FE3CB` | `#005A51` |
| `bass` | basso, nota e finestra del basso | `#FFAE4A` | `#853A00` |
| `loop` | note e avanzamento del looper | `#B996FF` | `#4A2894` |
| `focus` | fuoco, selezione nelle liste, «MPK STAME», primo movimento | `#A4F06A` | `#285C00` |
| `active` | evidenza degli overlay, transpose diverso da zero, LOCK, avvertenze lievi | `#FFDD5E` | `#634A00` |
| `warn` | avvisi, registrazione, clip, batteria bassa | `#FF6156` | `#9E160C` |
| `kb_white` | tasti bianchi spenti | `#183632` | `#E3E7D8` |
| `kb_black` | tasti neri spenti | `#08110F` | `#252D29` |
| `in_key` | granelli di polline (note della tonalità) | `#6FA597` | `#424C47` |

- **Contrasto** (rapporto WCAG): i token di testo (`text`, `dim`, `treble`, `bass`, `loop`, `focus`, `active`, `warn`) DEVONO avere almeno **4,5:1** su `bg` e su `panel`; il testo in negativo almeno 4,5:1 sul suo fondo; i colori dei ruoli almeno **3:1** su `kb_white`. `ghost` è volutamente tenue (2–3,5:1): indica un ricordo, non un dato attivo. `seg_off` sta fra 1,05 e 1,6:1: si intuisce, non si legge. I valori della tabella rispettano queste soglie (T-UI-20, `tests/unit/test_plancia.c`).
- Colori derivati, calcolati una volta al cambio di tema: `edge` (il bordo dei punti accesi di Matrice, il colore mescolato con `bg`) e `soft`.
- Nel tema Notte i tasti bianchi sono verde-grigio scuro: i tasti accesi nei colori dei ruoli spiccano come segmenti accesi. Il verde del fuoco richiama l'unico accento verde dell'Orchid [O INT], senza logo né marchio.
- Cambiare tema ridisegna tutto subito.

### 4.13 Disegno e aggiornamento

**UI-115** [D] Frequenza di aggiornamento:
- al massimo **60 fps**, con la presentazione in vsync (PLT-063);
- **si ridisegna solo quando cambia qualcosa**: a ogni vsync il thread UI controlla `seq`, i campi di piattaforma e `ui_flip_next_visual_ms()`; se nulla è cambiato non disegna e non presenta. A riposo la UI non consuma CPU apprezzabile (ridisegnare solo quando serve ha portato un'app nativa della Flip dal 17% al 2,5% di CPU [O nota Flip]; PLT-014);
- cose che cambiano da sole: celle dei movimenti (a ogni movimento), barra del looper (quando avanza di almeno un pixel), livello (30 Hz, poi caduta), voci e carico (4 Hz), pallini MIDI (50 ms), lampeggi (1 Hz), oscilloscopio nella vista React (30 Hz), batteria (ogni 5 s, PLT-090);
- latenza dall'azione allo schermo: al massimo **50 ms**, obiettivo due fotogrammi;
- il thread UI resta separato dal thread audio (UI-113): un disegno lento fa perdere fotogrammi, mai campioni.

**UI-160** [D] Percorso di disegno:
1. framebuffer **RGB565 640×480** (600 KB) della piattaforma, statico;
2. `ui_flip_render` calcola per ogni zona (Z1..Z6, e dentro Z5 ogni cella) una **firma** a 64 bit dei campi che la zona usa e dei suoi stati visivi (lampeggio, decadimento); ridisegna da zero solo le zone con la firma cambiata e ne restituisce i rettangoli;
3. la piattaforma carica solo quei rettangoli in una texture streaming `SDL_PIXELFORMAT_RGB565` (`SDL_UpdateTexture` con `SDL_Rect`), poi copia e presenta (PLT-063);
4. solo rettangoli interi e glifi bitmap: niente fusioni alfa, niente antialiasing, niente scalature non intere.

Budget sulla Flip (A55 a 1,8 GHz): disegno di un fotogramma tipico (trasporto in moto) **≤ 4 ms**, ridisegno completo ≤ 8 ms [D; V T-PLT-11]. Il simulatore su PC usa lo stesso renderer (PLT-078); il render offline (`stame-render`) scrive i fotogrammi come PNG a colori.

Misura del 14/10/2026 con `stame --prova` sulla Flip, lanciato via SSH con la console nel menu di spruce (CPU al passo ridotto, fino a 1,1 GHz, e condivisa con il menu): 70 s della demo della vetrina, 3449 fotogrammi disegnati, **0,6 ms in media** in quattro prove; ridisegno completo fra 2,3 e 18 ms secondo il momento. Il fotogramma peggiore (19–31 ms) non è il primo e cambia da una prova all'altra: più probabile un'interruzione del processo che un costo del disegno [D]. La firma dei pixel è uguale in tutte le prove (UI-003). T-PLT-11 resta da chiudere con l'app in primo piano a 1,8 GHz.

---

## 5. Menu della piattaforma

**UI-129** [D] Il tasto MENU della Flip (`MACRO_SYSTEM_MENU`, 40 MIDI-092) apre e chiude il menu della piattaforma: una lista di `core/ui` (proprietario `OWN_PLATFORM`, livello 5) resa in Z5 con il titolo «STAME MENU». Le note continuano a suonare. Voci, in inglese come il resto:

```
Back
Panic          → All Notes Off e reset dei controller (MACRO_PANIC, 40 §7)
Pocket Mode    Off / On                          (✓)  non ricordato tra un avvio e l'altro (MIDI-094)
MPK Status     → scheda (UI-159)
Learn Pad      → procedura guidata per il macro pad (UI-175); grigia se il macro pad non è collegato
Theme          Dark / Light                      (✓)
Legend         On / Off                          (✓)
Note Labels    Octaves / All / Off               (✓)
Meters         On / Off                          (✓)
Beat Flash     Off / On                          (✓)
Ghost Chord    On / Off                          (✓)
Linnaeus Tag   On / Off                          (✓)  cartellino di Linneo (UI-161)
Boot Sound     Off / On                          (✓)  logo sonoro all'avvio (UI-159), spento per default
Debug          Off / On                          (✓)
Quit Stame     → Back / Quit now
```

- **Quit Stame** è l'**unica** uscita dall'app, oltre a `SIGTERM` (MIDI-095, PLT-057): nessuna combinazione di tasti è riservata. Apre una conferma a due voci per evitare uscite involontarie mentre si suona; «Quit now» salva lo stato ed esce verso spruceOS (PLT-086), attraverso `prefs.quit_seq` (UI-027).
- Panic è in seconda posizione perché deve essere raggiungibile in fretta: MENU, giù, A. Dalla MPK c'è anche B8 + Stop (MIDI-078); dal macro pad T12 tenuto 1 s (MIDI-126). T11 del macro pad apre questo menu come il tasto MENU.
- **Learn Pad** serve solo se il macro pad non è stato programmato con i codici di 40 MIDI-122.

**UI-175** [D, 13/10/2026] Schermata di **Learn Pad** (40, MIDI-123). Scegliendo la voce, `core` cambia `prefs.learn_pad_seq` e la piattaforma avvia la procedura; ne riporta l'avanzamento in `ui_platform_t` (`pad_learn_step`, `pad_learned`). Resa in Z5, al posto del menu:
- titolo «LEARN PAD  05/21» in classe S;
- a sinistra uno schema del macro pad: la griglia 4×3 di T1…T12 (celle da 40×28 px con il nome del tasto e, sotto, la funzione: «Sound», «Back», «Panic»…) e le tre manopole M, m1, m2 con ◀ ● ▶ per antioraria, pressione e oraria. La posizione delle manopole nello schema segue l'unità vera [V VP-5 di 40];
- passi già imparati in `text`, passo in corso in negativo su `focus`, passi mancanti in `dim`;
- a destra la richiesta in classe M: «Press T5 (Bass)», «Turn M one click counterclockwise», «Press m1».

  Durante la procedura la piattaforma intercetta B (passo precedente) e MENU (annulla senza salvare) della Flip; la riga 1 e la riga 2 della legenda viva seguono UI-155. Alla fine compare «Pad map saved» (UI-156) e si torna al menu della piattaforma.
- Le migliorie musicali (latch, clock in…) non stanno qui: sono nell'appendice delle opzioni, spente di default.

---

## 6. Da dove arrivano le azioni

Questa è la mappa **logica**. Il riferimento normativo è la sezione 40: numeri di CC, canali, porte, codici evdev, programma «STAME» e macchina a stati del PUSH sono lì. Qui c'è solo una sintesi, che NON DEVE contraddirla; in caso di differenza vale la 40.

**UI-130** [D] `core/ui` riceve solo gli eventi del pannello di 40 (MIDI-100), già passati dal riconoscitore (MIDI-103) e con `ENC_FOCUS` già risolto (MIDI-104):

| Evento | Effetto sulla UI |
|---|---|
| gesti `G_*` dell'encoder `e` | i gesti di UI-101 e UI-103 |
| `PNL_BACK` | chiude l'overlay o risale di un livello nella lista o nel menu; senza livelli non fa nulla |
| `PNL_FOCUS_STEP(±1)` | sposta il fuoco nel giro di MIDI-092 |
| `PNL_ENC_DOWN(e)` da qualunque sorgente | porta anche il fuoco su `e` (MIDI-104) |
| `PNL_MACRO(MACRO_SYSTEM_MENU)` | apre o chiude il menu della piattaforma (UI-129) |
| `PNL_MACRO(MACRO_PANIC)` | va a `core`; la UI mostra l'avviso «Panic» |
| `PNL_MACRO(MACRO_LOOP_STOP)`, `(MACRO_LOOP_CLEAR)`, `(MACRO_LOOP_UNDO)`, `(MACRO_LOOP_OVERDUB)` | vanno al looper; la UI mostra lo stato che ne risulta |
| `PNL_MACRO(MACRO_KNOB_LOCK, b)` | `ctl.knob_lock = b`; la testata mostra «LOCK» (UI-126) |
| `PNL_MACRO(MACRO_VIEW_TOGGLE)` | Geek Out, oppure la vista in uso prima di entrarci (T14 del macro pad, 40 MIDI-132) |
| `PNL_MACRO(MACRO_CONTROLS_PAGE)` | apre la pagina dei comandi e la tiene aperta; un altro `MACRO_CONTROLS_PAGE` o `PNL_BACK` la chiude (UI-142a) |
| `PNL_SRC_CONNECTED`, `PNL_SRC_LOST` | stato della MPK o del macro pad (UI-126), legende (UI-152, UI-155) e avviso (UI-156) |

Gli eventi musicali (`PNL_KEY_*`, `PNL_CHORD_*`, `PNL_BEND`, `PNL_MOD`, `PNL_SUSTAIN`) non passano dalla UI (UI-110).

**UI-131** [D] Sintesi della mappa della MPK mini Plus e del macro pad (decisa da Luigi il 13/10/2026; manopole rimappate il 13/10/2026 per il macro pad; normativa in 40 §8.5, §8.6 e §8.10):

| Controllo della MPK | Funzione |
|---|---|
| pad del **banco A** | gli 8 tasti accordo dell'Orchid, nella stessa disposizione: fila alta **Dim, Min, Maj, Sus**; fila bassa **6, m7, M7, 9** |
| **K1 … K8** | rotazione di **Sound, Perform, FX, Key** (fila alta) e **Bass, Loop, BPM, Volume** (fila bassa), nella stessa posizione dei tasti T1–T8 del macro pad |
| pad del **banco B** (riserva senza macro pad) | pulsanti funzione: **B1 Key, B2 Bass, B3 Perform, B4 Chord Voicing, B5 Loop, B6 BPM, B7 Options, B8 PUSH** |
| **B8 tenuto, oppure X della Flip tenuto**, + tocco o rotazione di Kn (riserva) | pressione dell'encoder di Kn: premere, tenere, premere e ruotare (MIDI-084) |
| **Rec** | Loop (doppione di T6 e di B5) |
| **Play** | BPM: Beat o metronomo (doppione di T7 e di B6) |
| **Stop** | stop o pausa del loop; tenuto 1 s = Clear |
| **B8 + Stop** | Panic (dal macro pad: T12 tenuto 1 s) |
| **« »**, **joystick su / giù** | ruotano l'encoder con il fuoco (liste, Options e, senza macro pad, Chord Voicing e Bass Voicing) |
| **joystick →** / **←** | conferma (pressione dell'encoder con il fuoco) / indietro (`PNL_BACK`) |
| tasti, ruote, pedale | eventi musicali (sezioni 10 e 40) |

| Comando del macro pad (40 §8.10) | Funzione |
|---|---|
| **T1 … T8** | pulsanti degli encoder di K1 … K8, nella stessa posizione: Sound, Perform, FX, Key / Bass, Loop, BPM, Volume |
| **Tn tenuto + Kn** | premere e ruotare: T4 + K4 = transpose, T8 + K8 = volume del basso, T7 + K7 = volume del beat |
| **T9 / T10 / T11** | Options / indietro / menu della piattaforma (UI-129) |
| **T12** tenuto 1 s | Panic |
| **T13** | **Lock** delle manopole, a scatto come il Caps Lock (40 MIDI-131): acceso, M, m1 e m2 sono Sound, Perform e Key con tutti i loro gesti; la testata mostra «LOCK» (UI-126) |
| **T14** | **View**: Geek Out e ritorno alla vista di prima (40 MIDI-132) |
| **T15** | **Page**: apre la pagina dei comandi e la tiene aperta; un altro tocco o B la chiude (UI-142a, 40 MIDI-132) |
| manopola grande **M** | Chord Voicing: rotazione; pressione = Split ↔ Octave |
| manopola piccola **m1** | Bass Voicing: rotazione; pressione o tenuta = il modificatore |
| manopola piccola **m2** | liste e fuoco: rotazione (orario = voce successiva, UI-074); pressione = conferma |

- Combinazioni con il Bass Voicing tenuto (m1 del macro pad premuta, oppure Y della Flip): + T6, Rec o B5 = uscita forzata dal looper; + T7, Play o B6 = batteria da suonare; + T5 o B2 = basso on/off (UI-104).
- LED del trasporto: MIDI-085 (UI-108).
- Le legende delle celle (UI-152) e gli aiuti della banda (UI-155) DEVONO essere generate da questa mappa: se la 40 cambia, cambiano anche loro.

**UI-132** [D] Sintesi dei tasti della Flip, **schema a fuoco sempre attivo**, con o senza MPK (deciso da Luigi il 13/10/2026; normativa in 40 §9.1):

| Tasto della Flip | Funzione |
|---|---|
| L1 / R1 | sposta il fuoco sugli 11 controlli, in giro: Sound, Perform, FX, Key, Bass, Loop, BPM, Volume, Options, Chord Voicing, Bass Voicing |
| croce | ruota l'encoder con il fuoco, oppure scorre la lista aperta (con ripetizione, MIDI-082) |
| A | pressione dell'encoder con il fuoco: conferma; tenuto = tenere; A tenuto + croce = premere e ruotare |
| B | indietro (`PNL_BACK`) |
| X | PUSH, come B8 (UI-131): riserva per quando il macro pad non c'è |
| Y | Bass Voicing premuto, come m1 del macro pad: il modificatore (Y + A con il fuoco su Loop = uscita forzata) |
| SELECT | Options |
| START | BPM (Beat o metronomo) |
| MENU | menu della piattaforma (UI-129) |
| L2, R2, L3, R3, levette | liberi |

- Il fuoco è **uno solo**, condiviso da tutte le sorgenti, e si sposta anche premendo un encoder da qualunque sorgente (MIDI-104). All'avvio è su Sound.
- Con il macro pad collegato i tasti della Flip restano tutti attivi: T10 e T11 fanno quello che fanno B e MENU, m2 quello che fanno croce e A (UI-131).
- **Modo tascabile** (40 §9.2): opzionale, spento per default, si accende da MENU > «Pocket Mode» e non viene ricordato. Sulla plancia: contrassegno «POCKET» (UI-126), legenda dedicata (UI-155), classe della levetta in Z2 e Z4.
- Volume e accensione della Flip restano a spruceOS (PLT-058).

---

## 7. Renderer OLED per l'hardware (fase 2)

Questo capitolo **non** fa parte del perimetro della Flip. Descrive `ui_oled`, che disegna le 6 viste dell'Orchid al pixel su un OLED 128×128 a 1 bit per l'hardware dedicato futuro, a partire dallo stesso `ui_model_t`. Le misure vengono da fotogrammi e figure e restano qui, insieme alle loro `[V]`.

### 7.1 Coordinate e tolleranze
- Pixel del display: x da 0 a 127, y (riga) da 0 a 127, intervalli inclusivi.
- Le misure ricavate dai video hanno una tolleranza di ±1 px (±2 px nelle riprese oblique). I test usano ±2 px per i dati `[O]` e il valore esatto per i dati `[M]`.

### 7.2 Framebuffer, primitive e font

**UI-010** [M] Il display dell'Orchid è di fatto a **1 bit**: testo, barre e riempimenti hanno la stessa luminanza e i grigi sono retini [M figure MAN; O LP 1442-1461]. Il framebuffer DEVE essere a 1 bit per pixel.

**UI-011** [D] Formato:

```c
typedef struct {
    uint8_t *bits;      /* fornito dal chiamante: 128 × 128 / 8 = 2048 byte                 */
    uint16_t w, h;      /* 128×128                                                           */
    uint16_t stride;    /* byte per riga = (w + 7) / 8 = 16                                  */
    uint8_t  dirty[16]; /* una riga sporca = un bit                                          */
} gfx_fb1_t;
```

Ordine per righe; nel byte il bit 7 è il pixel più a sinistra; 1 = acceso. `dirty` serve a inviare solo le pagine cambiate al controller (SH1107 è il candidato [D]); la conversione verso le pagine verticali spetta alla piattaforma.

**UI-012** [D] `gfx_fb1_t` accetta dimensioni diverse da 128×128 solo per i test (glifi e strisce isolate).

**UI-013** [D] Primitive, con modo `GFX_SET`, `GFX_CLR` o `GFX_XOR` e clipping senza errori: `gfx_clear`, `gfx_pixel`, `gfx_hline`, `gfx_vline`, `gfx_line` (Bresenham), `gfx_rect`, `gfx_fill_rect`, `gfx_round_rect`, `gfx_fill_round_rect(r)`, `gfx_fill_pattern(rect, pat, mode)` con `PAT_50`, `PAT_25`, `PAT_75`, `gfx_blit` (bitmap 1 bit), `gfx_text_*`, `gfx_glyph_fit`, `gfx_invert_rect`.

**UI-014** [O] Il retino al 50% è una scacchiera di 1 px: acceso se `((x + y) & 1) == 0` [O GR 195, LP; fase `[D]`]. Lo usano i tasti che suonano e la parte non suonata dell'anello del looper.

L'Orchid usa un solo stile grafico in tre usi: testo piccolo, una variante sottile per la riga in alto e un font «elastico» per nomi e numeri grandi [O LP, QS, GR]. Il carattere su misura si chiama «Chunky Roll» [O INT]: altezza 14–18 px, aste verticali di 2 px e orizzontali di 1 px. I glifi vanno ridisegnati da zero ricalcando i fotogrammi, senza copiare file di font.

**UI-015** [M] `FONT_SMALL`, proporzionale: cap **11 px**, discendenti **3 px** [M figura «quant»]; x-height 8 px [O; V V-UI-18]; minuscole larghe 5–7 px, spaziatura **1 px** [O ±1; V V-UI-18]; aste verticali 2 px e orizzontali 1 px [O INT].

**UI-016** [O] `FONT_HEAD`, proporzionale sottile: cap **9 px** («Trans +3» alle righe 2..10) [O QS 754-770]; la tonalità occupa le righe 0..11, discendenti fino alla 14 [O QS 730, 770]; tratti di 1 px; «C Major» occupa x 0..45 [O QS 730].

**UI-017** [O] `FONT_FIT`, elastico: ogni glifo riempie un riquadro qualsiasi `(x, y, w, h)` [O LP, QS, GR]. Grottesco tondo; il ♭ è una «b» minuscola e il ♯ ha le aste inclinate [O QS 730, 770]; il doppio diesis si scrive «x» [M].

**UI-018** [D] Ogni glifo di `FONT_FIT` è uno **scheletro di tratti** in una griglia normalizzata:

```c
typedef enum { ST_VSTEM, ST_HBAR, ST_ARC, ST_DIAG } gfx_stroke_kind_t;
typedef struct { uint8_t kind, x0, y0, x1, y1, quadrant; } gfx_stroke_t;  /* coordinate in 1/64 del riquadro */
tv = max(2, round(h / 8.0));   /* aste verticali e diagonali   [V] V-UI-18 */
th = max(1, round(h / 16.0));  /* tratti orizzontali           [V] V-UI-18 */
r  = round(min(w, h) * 0.30);  /* raggio delle curve           [V] V-UI-18 */
```

Ogni glifo ha un rapporto naturale `aspect = w/h`. Set minimo: `0–9`, `A–Z`, `a–z`, `+ - / ( ) ♯ ♭ x °`. Sotto i 16 px di altezza si usa `FONT_SMALL` [D].

### 7.3 Elementi comuni

**UI-030** [O] **Tonalità** in alto a sinistra, `FONT_HEAD`, x = 0, cap alle righe 1..10 [O QS 730, 770]; formato «C Major», «F♯ Minor» («Minor» `[V]` V-UI-19). Con la Key mode spenta la testata resta vuota [O QS 754-770, 3.04]; «Off» nel 3.92 è `[V]` (V-UI-19).

**UI-031** [O] **Transpose** in alto a destra, `FONT_HEAD`, «Trans +3», allineato a destra a x = 124, righe 2..10, solo se diverso da zero [O QS 754-770]. Il nome dell'accordo tiene già conto del transpose [M FW 3.60].

**UI-032** [D] La testata compare in tutte le viste tranne React [V V-UI-17].

**UI-034** [O] Impaginazione del nome nel riquadro `B = (bx, by, bw, bh)`, ordine da sinistra: fondamentale, alterazione, qualità, apice, «/», basso.

| Parte | Altezza | Allineamento | Fonte |
|---|---|---|---|
| fondamentale | `bh` | in basso; si allarga per riempire lo spazio libero | [O QS 730, 770] |
| alterazione | `round(2/3 · bh)` | in alto, subito dopo la fondamentale; sovrapposizione fino a 3 px | [O QS 730, 770] |
| qualità | `round(0.70 · bh)` | sulla linea di base | [O LP 1220; V V-UI-18] |
| apice | `round(1/2 · bh)` | in alto; bordo destro a `bx + bw − 3` | [O QS 730, 770; LP 161-178] |
| «/» e basso | `bh` | dopo la qualità; alterazione del basso alta 2/3 | [O LP 1220] |

**UI-035** [D] Algoritmo: `wn[p] = round(altezza[p] · aspect) + 2` (−3 per l'alterazione dopo la radice); se `Σ wn ≤ bw` la fondamentale prende tutto lo spazio libero, altrimenti ogni parte si stringe a `floor(wn[p] · bw / Σ)` con un minimo di 4 px per glifo; l'apice si allinea a destra su `bx + bw − 3`. Il modo esatto di stringere i nomi lunghi è `[V]` (V-UI-18) [O SOS, FM].

**UI-036** [O] Misure di riferimento:

| Caso | Riquadro | Misure |
|---|---|---|
| G♯ᴹ⁷, Chord | x 0..127, righe 32..127 | G x 1..66; ♯ x 67..92, righe 32..96; M x 92..106 e 7 x 109..124, righe 32..80 [O QS 730] |
| E♭ᴹ⁷, Chord | idem | E x 0..70; ♭ x 67..90, righe 34..96; M7 x 92..124, righe 32..80 [O QS 770] |
| C⁹, Geek Out senza tonalità | righe 2..52 | C x 0..100; 9 x 102..125, righe 4..27 [O GR/LP] |
| Dm/A, Geek Out | righe 18..54 | D x 0..38; m x 40..77, righe 30..54; / x 79..103; A x 104..127 [O LP 1220] |
| C^JAZZ | righe 2..52 | C x 1..85; J 89..96, A 99..105, Z 109..116, Z 119..126, righe 2..26 [O LP 161-178] |
| C^WTF | righe 2..52 | C x 1..82; W 87..98, T 101..113, F 116..127 [O LP 161-178] |

**UI-038** [O] Tastiera di un'ottava, Do–Si, nel riquadro righe `yt..127` [O GR 176-195, LP 1450-1453]:

| Elemento | Geometria |
|---|---|
| tasti bianchi | **accesi**, passo 18 px, x 0..125; separatori spenti di 1 px a x 17, 35, 53, 71, 89, 107; riga spenta `yt − 1` |
| tasti neri | **spenti**: C♯ x 13..24, D♯ 31..41, F♯ 67..78, G♯ 86..97, A♯ 104..114; righe `yt + 1` .. `yk = yt + round(0.58 · (128 − yt))` |
| marker in tonalità | bianchi: barretta **spenta** 10 × 4 alle righe 122..125; neri: barretta **accesa** 10 × 4 alle righe `yk − 4 .. yk − 1` (dal 3.04, solo con la Key mode) |
| tasti che suonano | retino al 50%, marker compresi; classi di `pc_sounding`, senza basso [V V-UI-06] |

**UI-040** [V] Split (dal 3.84, nessuna immagine): linea verticale tratteggiata sul bordo sinistro del tasto `W mod 12`, per tutta l'altezza della tastiera [V V-UI-07]. In Octave nulla.

**UI-174** [O] **Banda delle note** (ordine delle note in UI-041) [O GR 176-195, LP 1450-1453]: banda accesa alle righe 59..76 con i nomi **spenti**, separatore spento alla riga 77; `FONT_SMALL`, cap alle righe 64..74 [V V-UI-18], primo carattere a x = 3 («F A D», «G C Eb», cap a x 3, 15, 28); alterazioni in ASCII «b» e «#» [O; diesis V V-UI-28]; senza note la banda resta accesa e vuota [O QS 960].

### 7.4 Le sei viste

**UI-052** [O] **React**: traccia di 1 px su x 0..127 centrata sulla riga 64; da ferma piatta, con un accordo a volume medio circa ±10 px; campionamento libero, non agganciato [O AMA 29.7-30.7; INT].

**UI-053** [V] Parametri di React [V V-UI-17]: somma mono `(L + R) / 2` dopo il master; ultimi 256 campioni a 48 kHz, uno ogni 2 (128 punti); `y = 64 − round(s · 40)` tagliata a 0..127; punti uniti con `gfx_line`; nessuna testata.

**UI-054** [D] Il buffer dell'oscilloscopio è quello di SND-033; React si ridisegna a 30 fps.

| Requisito | Vista | Contenuto e righe | Fonte |
|---|---|---|---|
| **UI-055** | Chord | testata; nome nel riquadro x 0..127, righe 32..127; dopo la persistenza resta la testata; il riquadro non cambia con la testata vuota | [O QS 730, 770, 754-770; LP 1459-1461] |
| **UI-056** | Keyboard | testata e tastiera con `yt = 56` (righe 56..127), senza nome | [O QS 2, 7; altezza V V-UI-05] |
| **UI-057** | Chord & Keyboard | testata; nome x 0..127, righe 17..71; tastiera con `yt = 74`; niente banda; nella lista si chiama «Chord + Keyboard» | [O QSb TZyPDD6IKSw 10.5-12, ±3 px] |
| **UI-058** | Notes | testata 0..11; nome righe 17..64; banda accesa 72..127 con le note spente in `FONT_FIT` alte 36 px (righe 82..117), separate da 6 px, centrate, strette come in UI-035 se oltre 120 px | [M «nome ed elenco delle note»; V V-UI-04] |
| **UI-059** | Geek Out | testata 0..11; nome 18..54 (2..52 senza tonalità); banda 59..76; separatore 77; tastiera `yt = 78` (neri 79..107); a riposo testata, banda vuota e tastiera | [O LP 1220, 1450-1453; GR 176-195; QS 960-1111] |

### 7.5 Overlay

**UI-060** [M] Schema: numero grande in `FONT_FIT` alle righe **1..108**; etichetta centrata in `FONT_SMALL`, cap alle righe **114..124** [M MAN; O QS].

**UI-061** [O] Numero di `n` caratteri: di norma 2 cifre con lo zero davanti, 3 se servono; celle `c = (128 − 2·(n − 1)) / n`, carattere `i` a `x = i·(c + 2)`; 2 cifre x 0..62 e 65..127; 3 cifre circa x 0..42, 44..84, 86..125 [O QS 738, 863].

**UI-062** [O] «OFF» al posto di «00» per i parametri che a zero si spengono: O x 1..41, F x 43..84, F x 90..116 [O QS 662.5, 754].

**UI-063** [M] Funzioni secondarie (Transpose, Beat Volume, Bass Volume): etichetta in una barra piena alle righe 111..126, x 0..127, testo in negativo [M; O QS 754; D per Bass Volume].

**UI-064** [M] Volumi: riempimento di livello in **XOR** dietro il numero [M figura «Volume»]; default da x 0 a `round(v · 128 / 99) − 1`, righe 0..109 [V V-UI-08].

**UI-067** [O] Arpeggiate: due righe in `FONT_FIT`, velocità («16», «08») alle righe 0..53 e direzione («UP», «DOWN», «UP/DOWN») alle righe 55..110; «Arpeggiate» in `FONT_SMALL` alle righe 114..127, circa x 30..98 [O QS 452, 486, 659.5].

**UI-068** [O] Key [O GR 186-192; QS 700]: maggiore senza alterazione = lettera a tutta larghezza, x 0..127, righe 2..102; con alterazione o minore = fondamentale x 0..62, alterazione x 64..125 righe 2..48, «m» righe 54..102 [D per le combinazioni]; Key Off = «Off» in `FONT_FIT` righe 2..102 [M 3.90]; etichetta «Key» righe 114..124, x 53..80. GR mostra anche un «F♭», segnalato come errore [O GR 324].

**UI-171** [O] Formati specifici: Sound utente «U05»; Chord Voicing sempre 3 cifre; Single Notes = parola «Split» / «Octave» in `FONT_FIT` alle righe 1..108 [V V-UI-07]; count-in «04»…«01» alle righe 2..109 con «Counting in» alle righe 116..126 [O LP 1398]; «Saved» con lo slot come etichetta [V V-UI-12]; «Drums» con «On» / «Off» [V V-UI-09].

### 7.6 Liste

**UI-071** [M] Geometria [M fig. «quant» bl-XmlINMmhrh; O QS 937-1136, LP]: **5 righe da 24 px**, cap della riga `i` alle righe `24·i + 6 .. 24·i + 16`; selezione fissa nella riga centrale, barra piena alle righe **48..71**, x **0..126** (colonna 127 spenta), testo in negativo; testo `FONT_SMALL` a **x = 4**. Marcatori: valori e ✓ allineati a destra a x = 124 (dentro la barra la ✓ è spenta); ● pieno di circa 11 px a x 114..124 [O QS 444-520].

### 7.7 Looper

Sull'OLED la schermata del looper **sostituisce la vista** finché il looper è attivo.

**UI-082** [O] Anello spesso 17 px lungo i quattro lati: righe 1..17 e 111..127, colonne 1..16 e 111..127; riga 0 e colonna 0 spente; interno x 17..110, righe 18..110; angoli esterni con raggio circa 12, interni quasi vivi [O LP 1338-1406; QS 851-934].

**UI-083** [O] N battute = N fessure radiali larghe 2–3 px agli angoli `k · 360° / N` da ore 12 in senso orario; con 8 battute anche le diagonali degli angoli; in Free anello continuo [O LP; QS].

**UI-084** [O] Parte suonata piena, resto a scacchiera (UI-014); avanza in senso orario da ore 12 e riparte a ogni giro [O QS 870-934; LP 1338-1406].

**UI-085** [D] Algoritmo, con una tabella degli angoli calcolata una volta (127 × 127 `uint16_t`, circa 32 KB, anche alla compilazione):

```
c = (63.5, 63.5);  ang(x,y) = atan2(x − 63.5, 63.5 − y) in [0, 65536)   // 0 = ore 12, orario
per (x,y) nella maschera dell'anello:
    fessura = ∃ k < N: |distanza perpendicolare di (x,y) − c dalla semiretta k·65536/N| ≤ 1.0, dalla parte della semiretta
    fessura → spento;  ang < progress → acceso;  altrimenti acceso se ((x + y) & 1) == 0
```

**UI-090** [V] Con il looper attivo i nomi degli accordi non si vedono; gli overlay degli encoder compaiono sopra la schermata del looper [V V-UI-21].

**UI-172** [O] Waiting Room: anello con le fessure della scelta selezionata e lista al centro; barra di selezione x 20..105 alta 24 px; tre righe visibili 26..49, 50..73, 74..97, selezione fissa al centro, testo centrato [O QS 851-870; D; V V-UI-21]. Menu a tre voci: stesse righe, testo centrato in `FONT_SMALL`, la barra si sposta sulla voce [O QS 870-934].

### 7.8 Altre schermate e LED

**UI-094** [O] Batteria (premere Volume): sagoma della pila con la carica e, senza caricatore, «No cable detected» [O QS 168-172, 940; M]. Default [V V-UI-14]: pila arrotondata (raggio 3) x 24..99, righe 28..68, polo x 100..103, righe 42..54; barra x 28 .. `28 + round(68 · pct / 100) − 1`, righe 32..64; «NN%» in `FONT_HEAD` centrata, cap 80..88; «No cable detected» / «Charging» / «Low Battery» in `FONT_SMALL`, cap 104..114. Dura quanto un overlay.

**UI-173** [V] Default delle altre schermate: logo di Stame bitmap 128×128 per circa 4 s; «Select Key» in `FONT_SMALL` centrata, cap 58..68 [V V-UI-15]; «Drums» in `FONT_FIT` con «On» / «Off» come etichetta [V V-UI-09]; Version: «Stame» in `FONT_HEAD` e la versione in `FONT_SMALL`, centrati.

**UI-107** [V] LED di Volume: fisso sopra il 25%; sotto, periodo da 1600 ms (25%) a 200 ms (5% e sotto) in modo lineare, 50% acceso [V V-UI-22]. Gli altri LED sono monocolore [D].

**UI-114** [O] Sull'Orchid si vedono aggiornamenti a bande (tearing) [O QS 964, 1073; GR 187]: circa 30 fps con scrittura per pagine [D]. Stame NON DEVE simulare il tearing; sull'hardware si ridisegna solo quando cambia il modello, a 30 fps per le schermate animate.

---

## 8. Test di accettazione

**UI-133** [D] Ogni schermata DEVE avere un test sul PC che costruisce un `ui_model_t`, chiama il renderer e confronta il risultato con un'immagine di riferimento salvata nel repository (PPM a colori per la plancia, PBM per l'OLED) e con le misure della specifica. Il renderer è deterministico (UI-003), quindi il confronto della plancia è esatto. Per l'OLED: ±2 px per i dati `[O]`, esatto per `[M]`, `[D]` e `[V]`.

### 8.1 Comportamento comune

| Test | Verifica |
|---|---|
| T-UI-09 | Gesti con tempi simulati, con il riconoscitore di 40: tap, tenuto alla soglia, premere e ruotare, Loop a 1 s e a 2 s, Bass Voicing + Loop |
| T-UI-10 | Overlay: scadenza a 3400 ms, ripartenza a ogni rotazione, sostituzione, chiusura con `PNL_BACK` |
| T-UI-11 | Persistenza del nome: 1000 ms, sostituzione con un nuovo accordo, passaggio a `CH_GHOST` o `CH_NONE` secondo `ghost_chord` |
| T-UI-13 | Navigazione completa di Options e del menu della piattaforma con i soli tasti della Flip, con i soli controlli della MPK e con il solo macro pad (T9, T11, m2, T10); su e giù portano alla voce sopra e sotto (UI-157), m2 in senso orario alla successiva |
| T-UI-14 | A riposo (trasporto fermo, nessun timer): nessun disegno, nessuna presentazione; `ui_next_deadline_ms()` e `ui_flip_next_visual_ms()` restituiscono «nessuna scadenza» |

### 8.2 Plancia della Flip

| Test | Verifica |
|---|---|
| T-UI-15 | Immagini di riferimento, nei due temi: riposo; Do♯m⁷ con basso e loop (UI-143); pagina dei comandi con il fuoco su FX; looper in registrazione 2/4; count-in; lista Options; lista Sound; menu della piattaforma; evidenza Volume e Transpose; avviso «MPK busy»; modo tascabile; nessuna MPK; le sei viste |
| T-UI-16 | Zone: ogni zona disegna solo dentro il suo rettangolo (UI-142); aprendo una lista, la pagina dei comandi o un overlay i pixel di Z2 e Z3 restano identici; con un overlay diverso dai voicing restano identici anche quelli di Z4 |
| T-UI-17 | Testi: i 70 nomi di fabbrica, i 12 bassi, nomi utente di 16 caratteri larghi («WWWWWWWWWWWWWWWW»), tutte le voci di Options e del menu della piattaforma, tutte le evidenze e le legende stanno nel loro riquadro o vengono troncati con «…» |
| T-UI-18 | Nome dell'accordo: scala scelta e riquadri delle parti per C, C♯m⁷/G♯, B♭dim^WTF/E♭, C♯m(add4)ᴹ⁷⁹/G♯, nota singola C♯4 (UI-146) |
| T-UI-19 | Tastiera: MIDI 12 a x = 12, MIDI 107 nell'ultimo tasto; ruoli, metà e metà, strisce del loop, marcatori della tonalità, finestre W e WB, triangoli fuori gamma (UI-150) |
| T-UI-20 | Contrasto dei token nei due temi secondo UI-128, calcolato dalla tabella dei colori |
| T-UI-21 | Fuoco: L1/R1 percorrono le 11 celle nell'ordine dello schermo; `PNL_ENC_DOWN` dalla MPK sposta la cornice; barra del tenuto alla soglia giusta |
| T-UI-22 | Legenda: testi attesi nei contesti di UI-155, tutti entro 78 caratteri, coerenti con la mappa di 40 |
| T-UI-23 | Priorità della banda: avviso warn > evidenza > richiesta > avviso info > aiuto di contesto > suono a riposo |
| T-UI-24 | Aggiornamento: con il trasporto in moto si ridisegnano solo Z3, le celle interessate e i meter; sulla Flip fotogramma tipico ≤ 4 ms e completo ≤ 8 ms (T-PLT-11); CPU a riposo ≤ 5% (PLT-014) |
| T-UI-25 | Latenza dall'azione al pixel ≤ 50 ms (marca temporale nella riga di debug, oppure ripresa ad alta velocità) |
| T-UI-26 | Testata: stati della MPK, stati del macro pad («PAD»), pallini MIDI di 50 ms, clip per 1500 ms, «XRUN» per 2 s, soglie della batteria al 15% e al 10% |
| T-UI-27 | Menu della piattaforma: tutte le voci; Quit con conferma; Pocket Mode non salvato; tema e opzioni salvati; Learn Pad grigia senza macro pad, schermata di UI-175 a ogni passo |
| T-UI-28 | Plancia calma (UI-140, UI-142a): la pagina di gioco disegna 5 zone e nessuna cella; fuori da Geek Out attività MIDI, voci e carico non ridisegnano la testata; girare il voicing non ridisegna la banda a riposo; L1/R1, croce, A e X aprono la pagina dei comandi, 5000 ms senza quei tasti o B la chiudono; i comandi della MPK non la aprono |

### 8.3 Renderer OLED (fase 2)

| Test | Verifica |
|---|---|
| T-UI-01 | Lista: barra alle righe 48..71, x 0..126, colonna 127 spenta; cap alle righe 6, 30, 54, 78, 102; testo a x = 4 |
| T-UI-02 | Vista Chord con G♯ᴹ⁷ e E♭ᴹ⁷: ingombri di UI-036 |
| T-UI-03 | Geek Out con Dm/A, C⁹, C^JAZZ, C^WTF: ingombri di UI-036; tastiera e marker di UI-038 |
| T-UI-04 | Overlay «07 Sound», «117» BPM, «032 Voicing», «OFF Chorus»: celle di UI-061/062, etichetta alle righe 114..124 |
| T-UI-05 | Overlay Volume a 50: XOR del riempimento sulle cifre (UI-064) |
| T-UI-06 | Overlay Transpose: barra 111..126 con testo in negativo |
| T-UI-07 | Overlay Key per C, F♯m, Cm, G♭m (UI-068) |
| T-UI-08 | Anello del looper con 1, 2, 4, 8, 16 battute e Free; progresso 0%, 25%, 50%, 99% |

T-UI-12 (OLED ingrandito sulla Flip) è ritirato.

---

## 9. Questioni aperte

### 9.1 Da verificare su un Orchid vero

La colonna «Vale per» dice se il dato serve anche alla Flip (comportamento o testi) o solo al renderer OLED dell'hardware.

| Test | Cosa verificare | Default scelto | Vale per |
|---|---|---|---|
| V-UI-01 | Durata di un overlay (girare Volume e cronometrare; ripetere con BPM e Sound) | 3400 ms | Flip e HW |
| V-UI-02 | Persistenza del nome dopo il rilascio (3.90+) | 1000 ms | Flip e HW |
| V-UI-03 | Soglie del tenuto di Perform, FX, Sound, Key (= VO-12 di 40) | 1000 ms | Flip e HW |
| V-UI-04 | Impaginazione della vista Notes | UI-058 | solo HW |
| V-UI-05 | Altezza della tastiera nella vista Keyboard | righe 56..127 | solo HW |
| V-UI-06 | Tasti a retino: note dell'accordo o tasto premuto; basso compreso o no | note dell'accordo, senza basso | solo HW |
| V-UI-07 | Indicatore Split/Octave (3.60), grafica dello split (3.84), nota singola | overlay «Split»/«Octave», linea tratteggiata, solo il nome | Flip (overlay) e HW |
| V-UI-08 | Verso e area del riempimento dei volumi | da sinistra, righe 0..109 | solo HW |
| V-UI-09 | Overlay per Key premuto, Bass on/off, BPM premuto, batteria da suonare; testo dell'etichetta BPM | UI-065, UI-097 | Flip e HW |
| V-UI-10 | Formato del transpose («+3» o «+03») e gamma | «+3» | Flip e HW |
| V-UI-11 | Volume a zero: «00» o «OFF» | «00» | Flip e HW |
| V-UI-12 | Schermate Save / Load / Delete del looper e conferma | UI-077/078, «Saved» | Flip e HW |
| V-UI-13 | Schermate Save / Save As / Delete dei Sound e conferma (3.84) | idem | Flip e HW |
| V-UI-14 | Misure della pila; testo dell'avviso di batteria bassa; ripetizione al 5% | UI-094, UI-095 | Flip (soglie, testo) e HW |
| V-UI-15 | Impaginazione e fine della richiesta «select key» | UI-096 | Flip (fine) e HW |
| V-UI-16 | Timeout di liste e Options; «ripremere Options» per uscire; altri encoder con un menu aperto; voci numeriche | 10 s / nessuno / chiude ed esegue | Flip e HW |
| V-UI-17 | React: finestra, ampiezza, sorgente, testata | 256 campioni, ±40 px, dopo il master, nessuna testata | solo HW |
| V-UI-18 | Font elastico, qualità minuscola, nomi lunghi, font piccolo, cap della banda | UI-015, UI-018, UI-034, UI-035 | solo HW |
| V-UI-19 | Testata in minore («A Minor»?) e con la Key mode spenta nel 3.92 | «Minor», vuota | Flip (testo) e HW |
| V-UI-20 | Nomi e maiuscole esatte delle voci dei sottomenu 3.90, liste Bass e Beats | testi di UI-077/079 | Flip e HW |
| V-UI-21 | Looper: selezione della Waiting Room, anello in Free, accordi e overlay sopra il looper | UI-086, UI-087, UI-090, UI-172 | Flip (Free) e HW |
| V-UI-22 | Ritmo del lampeggio del LED di Volume | UI-107 | solo HW |
| V-UI-23 | Liste cicliche o no; Options girato a menu chiuso | non cicliche; nulla | Flip e HW |
| V-UI-24 | Esistenza di uno screensaver | nessuno | Flip e HW |
| V-UI-25 | Etichette di Arp 2 Octaves e di Perform a zero | «Arp 2 Oct», «OFF» + modo | Flip e HW |
| V-UI-26 | Menu del looper in pausa | Overdub / Play / Clear | Flip e HW |
| V-UI-27 | Count-in in 3/4 e 6/8 | parte dal numero di movimenti | Flip e HW |
| V-UI-28 | Banda delle note: grafia del diesis, basso, nota singola | «#», senza basso | solo HW |
| V-UI-29 | Vista di fabbrica | Chord | Flip e HW |

### 9.2 Da verificare sulla Flip

| Test | Cosa verificare | Default scelto |
|---|---|---|
| VF-UI-01 | Diagonale e densità reali dello schermo; leggibilità delle classi XL, L, M, S a 50–70 cm con la Flip appoggiata accanto alla MPK (immagini di T-UI-15 mostrate sulla console) | 3,5", circa 9 px/mm; S e XS solo da vicino |
| VF-UI-02 | Colori sul pannello IPS della Flip: angolo di visione, tema Light alla luce del giorno, distinzione di treble, basso e loop | tabella di UI-128 |
| VF-UI-03 | Copertura dei glifi di Spleen (♯ ♭ ✓ ● frecce) e resa del 16×32 ingrandito ×3 per la fondamentale | simboli propri di Stame; ×3 |
| VF-UI-04 | Tempo di disegno e di caricamento della texture RGB565 (KMSDRM) | ≤ 4 ms tipico (T-PLT-11) |

### 9.3 Decisioni da confermare con Luigi
- **Ultimo accordo in grigio** (`CH_GHOST`): sull'Orchid il nome sparisce; sulla plancia resta tenue, perché è un'informazione utile. È un'opzione (Ghost Chord), accesa per default.
- **Lingua**: testi in inglese come l'Orchid. Spleen copre l'ISO 8859-1, quindi un menu della piattaforma in italiano sarebbe possibile. Le categorie dei Sound della sezione 20 sono in italiano («piano elettrico»): o si traducono in 20, o la cella Sound mescola le lingue.
- **Tema di default**: Dark.
- ~~Plancia con tutto in vista~~: **decisa il 15/10/2026**, plancia calma (UI-140): quattro cose mentre si suona, i comandi a richiesta, il dettaglio in Geek Out. Da provare sulla Flip: la durata della pagina dei comandi (5000 ms) e se il suono a riposo nella banda è utile o è già troppo.
- ~~Tastiera fissa a 8 ottave~~: **decisa il 13/10/2026**, 4 ottave che seguono le finestre del voicing, con tasti larghi 21 px (UI-150).
- **Panic** nel menu della piattaforma oltre che su PUSH (B8 o X) + Stop e su T12 del macro pad tenuto 1 s: va bene in seconda posizione?

### 9.4 Allineamenti con altre sezioni
- **Persistenza del nome**: qui 1000 ms (V-UI-02), in 10 ACC-056 500 ms (T-24). Va scelto un solo default.
- **Rotazione con l'encoder tenuto**: il riconoscitore di 40 (MIDI-103) ignora le rotazioni nello stato `HELD`; la versione precedente di questa sezione le mandava alla lista appena aperta dal tenuto (per esempio Save Sound). Da decidere in 40, eventualmente con una verifica sull'Orchid.
- ~~Su e giù nelle liste~~ (UI-157): **risolto** in 40 con il flag `PNL_F_VERTICAL` (MIDI-105): con una lista aperta `core/ui` inverte il verso dei comandi verticali.
- **Batteria**: 50 (PLT-090) avvisa sotto il 15%; qui l'icona diventa `warn` al 15% e gli avvisi dell'Orchid restano al 10% e al 5% (UI-095).
- ~~Sezione 50~~: **allineata** il 13/10/2026 (PLT-014, albero dei sorgenti, firma di `ui_flip_render`).

### 9.5 Altre questioni
- **Font dell'OLED** (fase 2): va disegnato da zero ricalcando i fotogrammi (QS 730, 770, 863, 662.5; LP 161-178, 1220; GR 186-192), in una sessione dedicata con i fotogrammi a piena risoluzione.
- **Logo di Stame**: da disegnare, in versione a colori per la plancia e bitmap 128×128 a 1 bit, senza richiami al logo TI.
- **LED del trasporto della MPK**: se l'host li possa accendere su Linux non è verificato (VM-13). Senza, lo stato si legge solo sulla plancia.
- **Pressione e rotazione con la croce della Flip**: A tenuto + croce = premere e ruotare (UI-132). Va provato se è comodo con una mano sola; Tn del macro pad + Kn, oppure X + manopola della MPK, sono le alternative.
- **Macro pad**: la posizione delle tre manopole (VP-5 di 40) decide lo schema di Learn Pad (UI-175); la comodità di Tn + Kn a due mani va provata sul tavolo.

---

## 10. Dipendenze da altre sezioni

| Sezione | Cosa serve da lì |
|---|---|
| `00-panoramica.md` | moduli `core/ui`, `ui`, `gfx`, `ui_flip`, `ui_oled` nell'architettura; glossario (plancia, zona, evidenza, fuoco, overlay, vista) |
| `10-accordi-e-performance.md` | `chord_label_t` (nomenclatura, «JAZZ», «WTF», Secret Chords, slash, enarmonie); note dal vivo e del looper con il ruolo e il nome; Key mode, tonalità e loro nomi; transpose; W e WB; Split/Octave; Play Style; modi e parametri di Perform; BPM, metrica, battuta e movimento; Beat, metronomo e batteria da suonare; stato del looper (ACC-232); default della persistenza (ACC-056) |
| `20-suono.md` | nomi, motori e categorie dei 70 Sound, dei 12 bassi e degli User Sound; slot degli effetti ed «effetto principale», gamme 0–10; volumi; voci occupate su 16; picco e intervento del soft clip (SND-046); oscilloscopio (SND-033); segnalazioni di patch legacy e banco mancante (SND-104, SND-133) |
| `40-midi-e-controlli.md` | eventi del pannello (MIDI-100), riconoscitore e soglie (MIDI-103), fuoco ed `ENC_FOCUS` (MIDI-104), mappa della MPK e PUSH (§8.5, §8.6) e del macro pad (§8.10, MIDI-120…129) per le legende, il contrassegno «PAD» e Learn Pad, tasti della Flip (§9.1), modo tascabile (§9.2, `pocket_pc`), LED del trasporto (MIDI-085), stati della MPK (MIDI-071, MIDI-088, MIDI-089), dati per MPK Status; verso dei comandi verticali nelle liste (§9.4) |
| `50-piattaforma-flip.md` | triple buffer dello snapshot (PLT-017), tempo di render e underrun (PLT-021), framebuffer RGB565 e texture streaming (PLT-062, PLT-063), vsync e 60 Hz, batteria (PLT-090), salvataggio delle preferenze, uscita (PLT-057, PLT-086), audio di riserva (PLT-023), Audio Output senza effetto (PLT-026), font in `third_party`, simulatore su PC (PLT-078) e render offline |
| `90-questioni-aperte.md` | raccoglie V-UI-01 … V-UI-29, VF-UI-01 … VF-UI-04 e le questioni di §9.3–§9.5 |

---

## Appendice — ID ritirati

Questi ID descrivevano l'OLED ingrandito e il pannello virtuale sulla Flip, tolti dalla decisione del 13/10/2026. NON DEVONO essere riusati.

| ID | Contenuto ritirato |
|---|---|
| UI-117 | OLED ingrandito ×3 in (128, 48, 384, 384) |
| UI-118 | percorso di disegno della texture 128×128 |
| UI-119 | colori dell'OLED simulato (Cold White, Amber…) |
| UI-120 | opzione «Pixel Grid» |
| UI-121 | zone del pannello virtuale attorno all'OLED |
| UI-122 | pannello disegnato a 1 bit 320×240 ingrandito ×2 |
| UI-123 | celle delle manopole del pannello virtuale |
| UI-124 | tasti accordo disegnati sotto l'OLED |
| UI-125 | opzione «Panel: Off» |
| T-UI-12 | test dell'OLED ingrandito |
