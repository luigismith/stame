# 50 — Piattaforma: Miyoo Flip

Questa sezione descrive come Stame gira sulla **Miyoo Flip** come app nativa: hardware e sistema, architettura del codice, thread e code, audio, MIDI, ingressi, video, persistenza, build, test, packaging, deploy, gotcha, regole di portabilità verso Teensy 4.1 e piano di sviluppo.

Il comportamento musicale (accordi, suono, interfaccia, mappa MIDI) sta nelle sezioni 10–40. Qui si definisce solo **dove** e **come** quel comportamento viene eseguito.

> **Etichette in questa sezione.** Quasi nessun dato riguarda l'Orchid, quindi `[V]` indica un **default da verificare sulla Flip o sulla MPK mini Plus**. Ogni `[V]` rimanda a un test di piattaforma `T-PLT-nn` (§16) oppure a un test della guida alla Plus (`Plus §18 test n`). `[O]` = osservato o verificato sulla Flip; `[M]` = documentazione ufficiale (kernel Linux, spruceOS, PJRC, Akai); `[D]` = dedotto o proposto.

---

## 1. La piattaforma

### 1.1 Hardware della Flip

| Voce | Valore | Etichetta |
|---|---|---|
| SoC | Rockchip **RK3566** | [O] |
| CPU | 4 × Cortex-A55 (aarch64); spruce la tiene a **1,1 GHz** massimo nel menu (memoria a 324 MHz); quando parte un'app `principal.sh` chiama `set_performance` e la porta a **1,8 GHz** | [O] |
| Profili CPU | `set_smart` lascia 2 core e la memoria lenta: **da evitare** per un'app audio | [O] |
| GPU | Mali-G52 (non usata da Stame, a parte il compositing di SDL) | [D] |
| RAM | da misurare; Stame ne usa comunque meno di 32 MB | [V] T-PLT-01 |
| Schermo | **640×480**, usato da SDL2 con KMSDRM a schermo intero | [O] |
| Codec audio | integrato nel PMIC **RK817** (il chip compare negli script di alimentazione di spruce); controllo ALSA `Playback Path` per altoparlante e cuffie | [O] chip e controllo; [D] che il codec sia quello del RK817 |
| Uscita cuffie | jack con rilevamento su `gpio150`; il `mixer_watchdog` di spruce cambia uscita. Accoppiata in alternata, circa 1 V: va bene per l'audio e per impulsi di sync, non per il CV | [O] |
| Altoparlante | sotto i **250–300 Hz** quasi non suona: una nota grave quasi sinusoidale (82 Hz) sparisce | [O] |
| Microfono | assente (Stame non lo usa) | [O] |
| USB-C | **due porte**. Quella **di sopra è OTG** (controller `fcc00000.dwc3`, PHY `fe8a0000.usb2-phy`, modo in `/sys/devices/platform/fe8a0000.usb2-phy/otg_mode`, valore normale `otg`). Con la MPK collegata lì la Flip passa da sola in host, le dà corrente e la riconosce | [O] |
| Rete | Wi-Fi; SSH (dropbear) da attivare nelle impostazioni di spruce | [O] |
| Tasti | pad «MIYOO Player1» letto via evdev; croce, A/B/X/Y, L1/R1, L2/R2 analogici, SELECT, START, MENU, due levette con L3/R3 (§7) | [O] |
| Formato | a conchiglia: la chiusura del coperchio e il tasto di accensione sono gestiti da spruce | [D]; comportamento [V] T-PLT-07 |

### 1.2 Sistema

| Voce | Valore | Etichetta |
|---|---|---|
| Sistema | **spruceOS 4.5.2** sulla SD (`/mnt/SDCARD`, FAT32); il firmware Miyoo sta nella memoria interna | [O] |
| Interfaccia | PyUI (Python 3.10 + SDL2). Quando parte un'app, PyUI esce e `principal.sh` la rilancia all'uscita dell'app | [O] |
| Utente | le app girano come **root** | [D] dalla guida alla Plus §17.4; [V] T-PLT-06 |
| Kernel | BSP Rockchip; versione da leggere | [V] T-PLT-01 |
| glibc | i binari compilati per **glibc 2.27** girano; la versione reale è più alta o uguale | [O] 2.27 funziona; [V] T-PLT-01 versione esatta |
| SDL2 | **non** di sistema con il SONAME standard: c'è quella di PyUI, `/mnt/SDCARD/App/PyUI/dll/libSDL2-2.0.so` (SDL 2.32) | [O] |
| alsa-lib | presenza di `libasound.so.2` non verificata; Stame **non** ne dipende | [V] T-PLT-01 |
| Driver USB MIDI | `snd-usb-audio` presente: le tastiere class compliant compaiono come `/dev/snd/midiC*D*` | [O] |
| Sequencer ALSA (`snd-seq`) | non verificato; Stame non lo usa | [V] Plus §18 test 25 |
| Strumenti sulla console | busybox, `evtest`, Python 3.10 (`/mnt/SDCARD/spruce/flip/bin/python3`), `kmsgrab` per le schermate (`/mnt/SDCARD/spruce/bin64/kmsgrab /tmp/s.png`), `curl`, `jq` | [O] |
| `/tmp` | si svuota al riavvio | [O] |

### 1.3 Superficie di controllo: Akai MPK mini Plus

Dati che servono alla piattaforma; la mappa completa sta in `40-midi-e-controlli.md`.

| Voce | Valore | Etichetta |
|---|---|---|
| USB | `09E8:0054`, class compliant, Full Speed | [M] Plus §13.1 |
| Porte | una scheda ALSA, `midiC<N>D0` con **2 sottodispositivi** per direzione: porta 1 = controller, porta 2 = DIN usato come interfaccia | [M]/[D] Plus §13.2, §13.10 |
| Clock in uscita | **nessuno**: Stame fa da master | [O] Plus §13.7 |
| Alimentazione | solo da USB; il descrittore dichiara 100 mA, assorbimento reale ignoto | [M] descrittore; [V] Plus §18 test 1 |
| Con la Flip come host | il DIN diventa la porta 2: per suonare un synth esterno Stame deve rimandare le note lì | [D] Plus §17.1; [V] Plus §18 test 2 |

---

## 2. Architettura del codice

### 2.1 Moduli

| Modulo | Contenuto | Linguaggio e dipendenze ammesse |
|---|---|---|
| `core` | accordi, voicing, key mode, basso, play style, performance, looper a eventi, tempo e clock, stato dell'interfaccia (viste, overlay, gesti), MIDI logico (mappa MPK → funzioni), parser MIDI, preset e serializzazione | C11 puro |
| `dsp` | motori VA, FM, Reed Piano, basso, effetti, pool di 16 voci, rendering a blocchi di 16 campioni | C11 puro, `float` a 32 bit |
| `ui` | `ui_model_t`: lo stato completo da mostrare, riempito dal nucleo a ogni frame (`30-interfaccia.md`) | C11 puro |
| `gfx` | primitive di disegno su framebuffer software: RGB565 640×480 per la plancia della Flip, 1 bit 128×128 per l'OLED dell'hardware futuro; font bitmap incorporati | C11 puro |
| `ui_flip` | renderer della plancia 640×480 a partire da `ui_model_t` (`30-interfaccia.md`); niente SDL, quindi testabile sul PC con immagini di riferimento | C11 puro |
| `platform/flip` | `main`, audio ALSA, audio SDL (riserva), MIDI rawmidi, input evdev, video SDL KMSDRM caricata con `dlopen`, salvataggi POSIX, thread e priorità | C11 + POSIX + Linux |
| `platform/pc` | simulatore su Windows: audio e video SDL2, tastiera del PC, MIDI WinMM | C11 + SDL2 + Win32 |
| `platform/offline` | render da riga di comando: eventi da file → WAV e immagini del framebuffer | C11 + stdio |

- **PLT-001** `[D]` I moduli `core`, `dsp`, `ui`, `gfx` e `ui_flip` **DEVONO** compilare in C11 senza includere header di SDL, ALSA, POSIX, Linux, Win32 o pthread. Gli header ammessi sono solo: `<stdint.h>`, `<stdbool.h>`, `<stddef.h>`, `<string.h>` (solo `memcpy`, `memmove`, `memset`, `memcmp`), `<math.h>`, `<float.h>`, `<limits.h>`.
- **PLT-002** `[D]` `core`, `dsp`, `ui`, `gfx` e `ui_flip` **NON DEVONO** usare l'heap (`malloc`, `calloc`, `realloc`, `free`), né l'I/O su file, né l'orologio di sistema, né `rand()`. Ogni file di questi moduli **DEVE** includere `stame_base.h`, che contiene `#pragma GCC poison malloc calloc realloc free printf fopen rand time`: un uso vietato blocca la compilazione.
- **PLT-003** `[D]` Le dipendenze **DEVONO** andare in una sola direzione: `platform/*` → tutti i moduli portabili; `ui_flip` → `ui`, `gfx`; `gfx` → nessun altro modulo; `ui` → `core` (riempie `ui_model_t` dallo stato); `core` → `dsp` (per pilotare le voci); `dsp` → nessun altro modulo. Nessun modulo portabile conosce `platform`. Il futuro renderer OLED dell'hardware sarà un modulo fratello di `ui_flip` (`ui_oled` → `ui`, `gfx`).
- **PLT-004** `[D]` Tutto il codice specifico della piattaforma **DEVE** stare sotto `src/platform/<nome>/`. Uno strato futuro `platform/teensy` **DEVE** poter riusare `core`, `dsp`, `ui`, `gfx` e `ui_flip` senza modificarli.

### 2.2 Interfaccia piatta tra nucleo e piattaforma

Il nucleo espone un'API piccola, senza tipi di piattaforma. Schizzo normativo (i nomi possono cambiare, la forma no):

```c
/* src/core/stame.h — nessuna dipendenza di piattaforma */
typedef struct stame stame_t;

typedef struct {
    uint32_t sample_rate;   /* 48000 sulla Flip, 44100 sul Teensy */
    uint32_t max_frames;    /* periodo massimo, multiplo di 16 */
    uint32_t seed;          /* seme del PRNG interno */
} stame_config_t;

typedef struct { size_t fast_bytes, bulk_bytes; } stame_mem_req_t;

/* Memoria fornita dalla piattaforma come array statici; il nucleo la divide solo in stame_init. */
stame_mem_req_t stame_mem_required(const stame_config_t *cfg);
stame_t *stame_init(const stame_config_t *cfg, void *fast, size_t fast_n, void *bulk, size_t bulk_n);

/* Solo dal thread audio (unico proprietario di stame_t). */
void   stame_event(stame_t *s, const stame_event_t *e);            /* tasti, pad, encoder, pulsanti, MIDI */
void   stame_render(stame_t *s, float *l, float *r, uint32_t n);   /* n multiplo di 16 */
size_t stame_midi_out(stame_t *s, stame_midi_msg_t *out, size_t max); /* con offset in campioni */
void   stame_snapshot(const stame_t *s, ui_model_t *v);          /* stato da mostrare (30-interfaccia.md) */
size_t stame_save(const stame_t *s, stame_blob_kind_t k, int slot, uint8_t *buf, size_t max);
int    stame_load(stame_t *s, stame_blob_kind_t k, int slot, const uint8_t *buf, size_t n);

/* ui_flip: dal thread UI, legge solo lo snapshot e disegna la plancia 640×480. */
/* restituisce quanti rettangoli sono cambiati (al massimo max), descritti in dirty[] */
int  ui_flip_render(ui_flip_state_t *st, const ui_model_t *v, uint16_t fb[640 * 480], ui_rect_t *dirty, int max);
```

- **PLT-005** `[D]` La piattaforma **DEVE** parlare con il nucleo solo attraverso questa API e attraverso eventi semantici: `key(nota, velocity)`, `button(id, giù/su)`, `encoder(id, delta)`, `push(id)`, messaggi MIDI già interpretati (3 byte + porta + istante), `battery(percento)`, `device(connesso/perso)`.
- **PLT-006** `[D]` `stame_t` **DEVE** avere un solo proprietario: il thread audio. Gli altri thread **NON DEVONO** leggerlo né scriverlo; ricevono snapshot e blob attraverso le code del §4.
- **PLT-007** `[D]` `stame_render` **DEVE** accettare qualunque `n` multiplo di 16 fino a `max_frames` e lavorare internamente a blocchi di 16 campioni `[D]` (come il DSP di Pistil, vedi `20-suono.md`). Gli eventi ricevuti prima della chiamata si applicano all'inizio del primo blocco.
- **PLT-008** `[D]` L'uscita del nucleo **DEVE** essere stereo, `float` non interlacciato, nominalmente in [−1, +1]. La conversione nel formato dell'hardware (S16, interlacciato) spetta alla piattaforma.

---

## 3. Thread e tempo reale

| Thread | Compito | Priorità proposta | Periodo |
|---|---|---|---|
| **audio** | applica gli eventi, chiama `stame_render`, converte e scrive sul PCM, pubblica snapshot e MIDI out | `SCHED_FIFO` 70 `[V]` T-PLT-06 | un periodo (5,33 ms con 256 frame) |
| **midi-in** | `poll()` sulle porte rawmidi e su un timer per l'hot-plug; parser; marca temporale; coda verso l'audio | `SCHED_FIFO` 60 `[V]` | a eventi |
| **midi-out** | scrive i messaggi in uscita (LED della MPK, clock, DIN) all'istante giusto | `SCHED_FIFO` 55 `[V]` | a eventi, con `clock_nanosleep` |
| **ui** (thread principale) | evdev dei tasti della Flip, `gfx_render`, presentazione SDL, salvataggi su file, registro | normale (`SCHED_OTHER`) | al massimo 60 Hz, e solo se qualcosa è cambiato |

- **PLT-009** `[D]` L'app **DEVE** usare esattamente questi quattro thread (più eventuali thread interni di SDL). Nessun lavoro audio nel thread UI, nessun I/O su file fuori dal thread UI.
- **PLT-010** `[D]` Il thread audio **DEVE** chiedere `SCHED_FIFO` con `pthread_setschedparam`. Se fallisce, **DEVE** continuare in `SCHED_OTHER` con `nice` −10 e scriverlo nel registro.
- **PLT-011** `[D]` All'avvio l'app **DOVREBBE** chiamare `mlockall(MCL_CURRENT | MCL_FUTURE)` e toccare in anticipo lo stack del thread audio (64 KB), per evitare page fault durante il suono.
- **PLT-012** `[D]` L'app **PUÒ** fissare il thread audio sul core 3 (`pthread_setaffinity_np`) e gli altri sui core 0–2. Default: disattivato `[V]` T-PLT-03 (si attiva solo se riduce gli underrun).
- **PLT-013** `[D]` Ogni thread **DEVE** attivare il flush-to-zero dei denormali (bit FZ di FPCR su aarch64, FTZ/DAZ di MXCSR sul PC). Il `dsp` **NON DEVE** dipendere da questa impostazione per la correttezza, solo per le prestazioni.
- **PLT-014** `[D]` Il thread UI **DEVE** ridisegnare solo quando cambia qualcosa: `ui_flip_render` confronta per ogni zona una firma dei campi che usa e restituisce i rettangoli da aggiornare (`30-interfaccia.md` UI-160); la piattaforma carica solo quelli nella texture. Da fermo l'app **DOVREBBE** restare sotto il 5% di un core `[O]`: ridisegnare solo quando serve ha portato un'app nativa della Flip dal 17% al 2,5%.

---

## 4. Comunicazione tra thread

### 4.1 Code

| Coda | Produttore → consumatore | Elemento | Capienza |
|---|---|---|---|
| `q_midi_in` | midi-in → audio | `{porta, status, d1, d2, t_ns}` (16 byte) | 1024 |
| `q_ui_cmd` | ui → audio | evento semantico o comando (`load blob k`, `save slot`, `quit`) | 256 |
| `q_midi_out` | audio → midi-out | `{porta, n, byte[3], t_campione}`; SysEx a parte, in blob | 1024 |
| `q_ui_out` | ui → midi-out | messaggi MIDI dalla UI (LED all'avvio, Identity Request) | 64 |
| `q_blob_to_ui` / `q_blob_to_audio` | audio ↔ ui | indice di un blob del pool | 8 |
| `q_log` | audio → ui | codice e valori numerici (niente testo formattato) | 256 |
| snapshot | audio → ui | `ui_model_t` in **triple buffer** | — |

- **PLT-015** `[D]` Ogni coda **DEVE** essere una coda **SPSC lock-free** (un solo produttore, un solo consumatore) con capienza potenza di 2, elementi di dimensione fissa e indici `_Atomic uint32_t` con ordinamento acquire/release (`<stdatomic.h>`). La coda vive in `src/core/spsc.h`, in C11 puro, ed è riusata sul Teensy tra interrupt audio e `loop()`.
- **PLT-016** `[D]` Se una coda è piena, il produttore **DEVE** scartare l'elemento nuovo e incrementare un contatore atomico di scarti, mostrato nel registro. **NON DEVE** mai bloccarsi o aspettare.
- **PLT-017** `[D]` Lo snapshot per la UI **DEVE** passare in un triple buffer: l'audio scrive sempre in un buffer libero e lo pubblica con uno scambio atomico; la UI legge l'ultimo pubblicato. L'audio **DOVREBBE** pubblicare al massimo a 120 Hz (non a ogni periodo, se lo snapshot supera 1 KB).
- **PLT-018** `[D]` Salvataggi e caricamenti **DEVONO** passare per un **pool statico di blob** (proposta: 4 blob da 4 KB per preset e impostazioni, 2 da 32 KB per i loop `[V]` dimensione reale da `10-accordi-e-performance.md`). La proprietà di un blob passa da un thread all'altro inviandone l'indice in coda. Nel thread audio, `stame_save` e `stame_load` lavorano solo in memoria e in tempo limitato.

### 4.2 Regole del callback audio

- **PLT-019** `[D]` Nel thread audio, tra un'attesa del PCM e la successiva, **NON DEVONO** comparire: `malloc`/`free`, mutex, variabili di condizione, semafori, I/O su file, `printf` o altro testo formattato, chiamate a SDL (tranne il callback SDL stesso nel backend di riserva), `sleep`, syscall diverse dalla scrittura e dall'attesa del PCM.
- **PLT-020** `[D]` Il registro dal thread audio **DEVE** passare da `q_log` con codici numerici; il thread UI li traduce in testo e li scrive su file al massimo una volta al secondo.
- **PLT-021** `[D]` Il thread audio **DEVE** misurare a ogni periodo il tempo di rendering (`clock_gettime(CLOCK_MONOTONIC)`) e tenere massimo, media e numero di underrun, pubblicati nello snapshot per un overlay di debug (attivabile da `piattaforma.txt`, §9).

---

## 5. Audio

### 5.1 Scelta del backend: ALSA diretto, con SDL2 come riserva

**Decisione proposta `[D]`: ALSA diretto sul dispositivo `hw`, tramite le ioctl PCM del kernel (stile tinyalsa, senza alsa-lib), con un backend SDL2 di riserva.**

Motivi:
1. **Latenza.** L'unica configurazione SDL provata sulla Flip è 48 kHz, float, stereo, **1024 campioni** (con 512 ALSA segnalava underrun) `[O]`. Con 1024 campioni a 48 kHz un periodo vale 21,3 ms e il tasto → suono arriva a 40–65 ms: troppo per uno strumento da suonare. Con ALSA diretto si scelgono periodo e numero di periodi.
2. **Priorità.** Con ALSA diretto il thread audio è nostro e lo si mette in `SCHED_FIFO`. Il thread audio di SDL non si controlla altrettanto bene.
3. **Dipendenze.** L'audio non dipende dalla SDL di PyUI, che ha un SONAME non standard e potrebbe cambiare con un aggiornamento di spruce `[O]`.
4. **Portabilità.** Il modello «il thread chiede un periodo, il nucleo lo rende» è lo stesso dell'`update()` dell'Audio Library sul Teensy.
5. **Nessuna dipendenza da alsa-lib.** Si usano le ioctl di `<sound/asound.h>` `[M]` (come già per il MIDI, §6). In alternativa si può includere tinyalsa (licenza BSD) in `third_party/` `[D]`.

Il backend SDL2 resta per: la prima nota (F4, §15), il simulatore su PC e i casi in cui il PCM `hw` non si apre.

- **PLT-022** `[D]` Il backend audio **DEVE** stare dietro un'interfaccia `plat_audio` con due implementazioni: `audio_alsa.c` (default) e `audio_sdl.c` (riserva). La scelta **DEVE** essere configurabile in `piattaforma.txt` (`audio=alsa|sdl`).
- **PLT-023** `[D]` Se l'apertura ALSA fallisce (dispositivo occupato, parametri rifiutati), l'app **DEVE** passare da sola al backend SDL e scriverlo nel registro e in un avviso a schermo di 3 secondi.
- **PLT-024** `[V]` T-PLT-01, T-PLT-02 Il dispositivo di default **DEVE** essere `hw:0,0` (scheda del codec interno, cercata per nome in `/proc/asound/cards` e non per numero fisso). Il valore si può forzare in `piattaforma.txt` (`alsa_device=`).
- **PLT-025** `[V]` T-PLT-05 Stame **DEVE** aprire il PCM in modo esclusivo solo dopo l'uscita di PyUI. Se esiste un `asound.conf` con dmix, si usa comunque `hw` diretto.
- **PLT-026** `[D]` Stame **NON DEVE** toccare il mixer ALSA (`Playback Path`, volumi di sistema): li gestisce spruce, che cambia uscita quando si inseriscono le cuffie `[O]`. Il volume di Stame è digitale, nel nucleo, come sull'Orchid. `[V]` T-PLT-15: il cambio di uscita deve funzionare anche con il PCM `hw` aperto da Stame.

### 5.2 Parametri

| Parametro | Default | Alternative | Etichetta |
|---|---|---|---|
| Sample rate | **48 000 Hz** | 44 100 se il codec lo preferisce | [O] 48 kHz funziona con SDL; [V] T-PLT-02 con ALSA |
| Formato verso l'hardware | **S16_LE** interlacciato stereo | S32_LE o FLOAT_LE se supportati | [V] T-PLT-02 |
| Periodo | **256 frame** (5,33 ms) = 16 blocchi da 16 | 128 se regge, 512 se servono | [V] T-PLT-03 |
| Periodi nel buffer | **2** (buffer 512 frame, 10,7 ms) | 3 | [V] T-PLT-03 |
| `start_threshold` | 1 periodo | — | [D] |
| `avail_min` | 1 periodo | — | [D] |
| Rendering interno | blocchi da 16 campioni | — | [D] da Pistil, vedi `20-suono.md` |

- **PLT-027** `[D]` Sample rate, periodo e numero di periodi **DEVONO** essere letti da `piattaforma.txt` e negoziati con `HW_REFINE`/`HW_PARAMS`. Il valore ottenuto **DEVE** essere scritto nel registro. Il periodo effettivo **DEVE** essere un multiplo di 16; se il driver ne impone uno diverso, la piattaforma rende a blocchi di 16 in un buffer intermedio statico.
- **PLT-028** `[D]` Ciclo del thread audio (pseudocodice):

```
init: hw_params(48000, S16_LE, 2 ch, period=256, periods=2); sw_params; prepare
      scrivi 2 periodi di silenzio; start
loop:
    attendi spazio per 1 periodo (poll sul fd del PCM, POLLOUT)
    svuota q_midi_in e q_ui_cmd → stame_event()
    t0 = now()
    stame_render(s, L, R, 256)
    converti float → S16 interlacciato (clip a ±1; dither TPDF opzionale)
    writei(256)            → se -EPIPE: underrun++, prepare, scrivi 1 periodo di silenzio, riprendi
                           → se -ESTRPIPE: resume (o prepare) finché riesce, poi riprendi
    stame_midi_out() → q_midi_out (con l'istante assoluto del campione)
    ogni ~8 ms: stame_snapshot() → triple buffer
    statistiche: render_ns = now() − t0
```

- **PLT-029** `[D]` Con la configurazione di default, **10 minuti** di esecuzione con 16 voci attive, tutti gli effetti accesi e la UI che ridisegna a 60 Hz **DEVONO** dare **0 underrun** `[V]` T-PLT-03. Se non succede, si passa a 3 periodi, poi a 512 frame, e si aggiorna questo requisito.
- **PLT-030** `[D]` Il backend SDL di riserva **DEVE** aprire 48 kHz, `AUDIO_F32`, stereo, `samples` = 1024 `[O]` (512 dava underrun). Il callback SDL **DEVE** rispettare le stesse regole del §4.2.

### 5.3 Budget di latenza: tasto della MPK → suono

| Tratto | Stima | Etichetta |
|---|---|---|
| Scansione dei tasti della MPK e pacchetto USB | 1–3 ms | [D]; [V] Plus §18 test 27 |
| USB Full Speed (frame da 1 ms), `snd-usb-audio`, rawmidi | 1–2 ms | [D] |
| Thread midi-in: `poll` → parser → coda | < 0,1 ms | [D] |
| Attesa dell'inizio del prossimo periodo | 0–5,3 ms (media 2,7) | [D] con 256 frame |
| Coda nel driver: il periodo appena scritto suona dopo 1–2 periodi | 5,3–10,7 ms | [D] con 2 periodi |
| Codec, filtri, ampli | < 1 ms | [D] |
| **Totale** | **circa 8–22 ms, media circa 13 ms** | [D]; [V] T-PLT-04 |
| Confronto: SDL con 1024 campioni | circa 25–65 ms | [D] |

La latenza dell'Orchid originale è sconosciuta (`Orchid - hardware e distinta per il clone`, tabella delle piattaforme).

- **PLT-031** `[D]` La latenza tasto → suono **DEVE** stare sotto i **25 ms al 95° percentile** e **DOVREBBE** avere una mediana sotto i **15 ms** `[V]` T-PLT-04.
- **PLT-032** `[D]` La piattaforma **DEVE** stimare la latenza interna per ogni Note On: `t_lettura` (marca del thread midi-in) → istante in cui il primo campione della nota esce dal DAC (posizione nel periodo + ritardo riportato da `SNDRV_PCM_IOCTL_DELAY`). L'istogramma va nel registro in modalità debug.
- **PLT-033** `[D]` L'app **PUÒ** applicare gli eventi con un offset in campioni calcolato dalla loro marca temporale (latenza costante, meno jitter, al prezzo di un periodo in più). Default: spento; gli eventi si applicano all'inizio del blocco successivo `[V]` T-PLT-04 (si accende solo se il jitter si sente).

### 5.4 Budget di CPU sulla Flip

- **PLT-034** `[D]` Con 16 voci e tutti gli effetti, il rendering **DEVE** occupare meno del **40%** del tempo di un periodo su un core a 1,8 GHz, e **DOVREBBE** restare sotto il **20%** `[V]` T-PLT-03. Riferimento `[O]`: un'altra app nativa della Flip suona 32 voci con circa il 16% di un core.
- **PLT-035** `[D]` Il thread UI, con un ridisegno a 60 Hz, **DOVREBBE** restare sotto il 15% di un core. Riferimento `[O]`: un'app con grafica pesante usa 9–14 ms per fotogramma su 33 ms.
- **PLT-036** `[O]` L'app **NON DEVE** chiamare `set_smart`; si affida a `set_performance`, già chiamato da `principal.sh` all'avvio delle app.

---

## 6. MIDI

### 6.1 Scelta: ALSA rawmidi, senza alsa-lib

**Decisione proposta `[D]`: rawmidi diretto su `/dev/snd/midiC<N>D<M>` con le ioctl del kernel.** È già provato sulla Flip con una MPK mini IV `[O]`, non richiede `snd-seq` né alsa-lib, e il codice di riferimento per la Plus esiste (guida alla Plus §17.4). Il sequencer ALSA servirebbe solo per far vedere Stame ad altre app sulla Flip, cosa che non serve.

- **PLT-037** `[D]` Il MIDI **DEVE** usare rawmidi in modo non bloccante (`O_RDWR | O_NONBLOCK | O_CLOEXEC`). Senza `O_NONBLOCK` l'`open()` di una porta occupata si blocca `[M]` Plus §13.10.
- **PLT-038** `[M]` Plus §13.10 Per aprire una porta precisa, la piattaforma **DEVE** usare `SNDRV_CTL_IOCTL_RAWMIDI_PREFER_SUBDEVICE` (`_IOW('U', 0x42, int)`) su `/dev/snd/controlC<N>`, tenuto aperto durante l'`open()` del rawmidi, e poi controllare con `SNDRV_RAWMIDI_IOCTL_INFO` (`_IOR('W', 0x01, …)`, 268 byte, campo `stream` impostato prima) quale sottodispositivo si è ottenuto.

### 6.2 Enumerazione delle porte

- **PLT-039** `[D]` All'avvio e a ogni cambiamento (§6.3) la piattaforma **DEVE**:
  1. scorrere `/proc/asound/card0…31`;
  2. per ogni scheda con `/proc/asound/cardN/midi0` (o `midiC N D*` in `/dev/snd`), leggere nome, `usbid` e numero di sottodispositivi;
  3. riconoscere la MPK mini Plus da `usbid` = `09e8:0054` `[M]`;
  4. aprire **tutti** i sottodispositivi in ingresso di tutte le schede MIDI (porta 1 e 2 della Plus, e le porte di altre tastiere). Alcune tastiere mandano controlli diversi su porte diverse `[O]` (la MPK mini IV manda le manopole sulla porta 2);
  5. aprire in uscita la porta 1 della Plus (LED, clock) e la porta 2 (DIN OUT).
- **PLT-040** `[D]` Una tastiera MIDI class compliant diversa dalla Plus **DEVE** essere accettata come «tastiera generica»: le sue note vanno al nucleo come tasti; i controlli seguono la mappa generica di `40-midi-e-controlli.md`.
- **PLT-041** `[D]` Per ogni porta in ingresso il thread midi-in **DEVE** tenere un parser proprio (running status, real time ≥ `F8` accettati anche dentro un SysEx, SysEx fino a 4 KB). Il parser è codice portabile in `core/midi_parse.c`; gira nel thread midi-in, mentre la mappa MPK → funzioni gira nel nucleo (thread audio).
- **PLT-042** `[D]` All'apertura della Plus la piattaforma **DEVE** mandare l'Identity Request `F0 7E 7F 06 01 F7` sulla porta 1 e registrare la risposta (`47 54 00 19` e versione del firmware), poi spegnere i LED del trasporto (`90 73…77 00`) `[D]` Plus §17.4.
- **PLT-043** `[M]` `CLAUDE.md` del progetto: la piattaforma **NON DEVE** mandare SysEx di scrittura dei programmi alla Plus (`F0 47 7F 54 64 …`) senza backup e senza l'ok di Luigi. Il caricamento del programma «STAME» via SysEx resta spento finché non viene approvato.

### 6.3 Hot-plug

- **PLT-044** `[D]` Il thread midi-in **DEVE** rilevare scollegamento e ricollegamento senza riavvio dell'app:
  - scollegamento: `read()` che restituisce `ENODEV`, oppure `POLLERR`/`POLLHUP` → chiudere i fd di quella scheda e mandare al nucleo `device(perso)`;
  - ricollegamento: un `timerfd` a 1 Hz nello stesso `poll()` rilegge `/proc/asound/cards`; una scheda nuova o tornata viene aperta come al §6.2 e il nucleo riceve `device(connesso)`.
- **PLT-045** `[D]` Alla ricezione di `device(perso)` il nucleo **DEVE** rilasciare tutti i tasti e i pad tenuti da quella sorgente (niente note appese). Il looper e il clock continuano.
- **PLT-046** `[V]` Plus §18 test 26 La piattaforma **NON DEVE** dare per scontato che numero di scheda e nomi delle porte restino uguali dopo un ricollegamento: identifica la Plus sempre per `usbid`.
- **PLT-047** `[D]` La piattaforma **PUÒ** usare `inotify` su `/dev/snd` (`IN_CREATE | IN_DELETE`) per reagire prima del timer; il timer a 1 Hz resta come rete di sicurezza.

### 6.4 MIDI in uscita e clock

- **PLT-048** `[D]` Il thread midi-out **DEVE** essere l'**unico** a scrivere sui fd MIDI (così non serve un mutex). Legge `q_midi_out` (dal nucleo) e `q_ui_out` (dalla UI) e scrive ogni messaggio con una sola `write()`.
- **PLT-049** `[D]` Ogni messaggio del nucleo porta l'istante del campione a cui appartiene. Il thread midi-out **DOVREBBE** spedirlo all'istante in cui quel campione esce dal DAC (istante del campione + latenza di uscita stimata), con `clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME)`. Così clock e note in uscita restano allineati al suono. Jitter atteso del clock sotto 1 ms `[V]` T-PLT-04.
- **PLT-050** `[D]` Il clock MIDI (24 PPQN, `FA`/`FC`) **DEVE** essere generato dal nucleo sul tempo dei campioni, non da un timer della piattaforma. Porte e regole stanno in `40-midi-e-controlli.md`.
- **PLT-051** `[M]` `CLAUDE.md` del progetto: se in futuro Stame espone una porta MIDI con un nome (client del sequencer ALSA, gadget USB), il nome **NON DEVE** iniziare con «orchid» e il SysEx **NON DEVE** usare l'ID `00 22 0C`.

---

## 7. Ingressi dai tasti della Flip

- **PLT-052** `[O]` L'input dei tasti **DEVE** essere letto direttamente da evdev. SDL **NON DEVE** inizializzare i sottosistemi joystick e gamecontroller: il gamepad di SDL legge lo stesso dispositivo con un'altra mappatura e, leggendo entrambi, i tasti risultano «già premuti».
- **PLT-053** `[O]` Il dispositivo del pad **DEVE** essere cercato per **nome** («MIYOO Player1», con `EVIOCGNAME` su `/dev/input/event*`), non per numero: un dispositivo USB o Bluetooth con interfaccia HID collegato all'avvio lo sposta da `event5` a `event6` o `event8`.
- **PLT-054** `[O]` I nomi dei tasti nel codice **DEVONO** avere un prefisso proprio (`PAD_*`) e **NON DEVONO** essere `BTN_A`, `BTN_X`, `BTN_LEFT`, `BTN_START` o simili: sono macro di `linux/input.h` con valori diversi, e sulla console i tasti finivano scartati mentre sul PC (senza quell'header) le prove passavano. `input_evdev.c` **DEVE** contenere controlli che bloccano la compilazione, per esempio `_Static_assert(PAD_A == 305, "conflitto di nomi")`.

### 7.1 Mappa dei codici `[O]`

| Nome in Stame | Tipo evdev | Codice | Valori |
|---|---|---|---|
| `PAD_A` | `EV_KEY` | 305 | 1 premuto, 0 rilasciato, 2 ripetizione (da ignorare) |
| `PAD_B` | `EV_KEY` | 304 | idem |
| `PAD_X` | `EV_KEY` | 308 | idem |
| `PAD_Y` | `EV_KEY` | 307 | idem |
| `PAD_L1` | `EV_KEY` | 310 | idem |
| `PAD_R1` | `EV_KEY` | 311 | idem |
| `PAD_SELECT` | `EV_KEY` | 314 | idem |
| `PAD_START` | `EV_KEY` | 315 | idem |
| `PAD_MENU` | `EV_KEY` | 316 | idem |
| `PAD_L3` | `EV_KEY` | 317 | idem |
| `PAD_R3` | `EV_KEY` | 318 | idem |
| croce sinistra/destra | `EV_ABS` | `ABS_HAT0X` | −1, 0, +1 |
| croce su/giù | `EV_ABS` | `ABS_HAT0Y` | −1, 0, +1 |
| `PAD_L2` | `EV_ABS` | `ABS_Z` | 0–255 |
| `PAD_R2` | `EV_ABS` | `ABS_RZ` | 0–255 |
| levetta sinistra | `EV_ABS` | 0 (X), 1 (Y) | limiti da `EVIOCGABS` |
| levetta destra | `EV_ABS` | 3 (X), 4 (Y) | limiti da `EVIOCGABS` |

- **PLT-055** `[D]` L2 e R2 **DEVONO** diventare pulsanti con isteresi: premuto sopra 160, rilasciato sotto 96 `[V]` T-PLT-10. Le levette **DEVONO** usare i limiti letti con `EVIOCGABS` e una zona morta del 20% `[V]` T-PLT-10.
- **PLT-056** `[D]` La piattaforma traduce i tasti in `button(id, giù/su)` e li manda al nucleo. Cosa fanno i tasti (navigazione, encoder virtuali quando la MPK manca) sta in `40-midi-e-controlli.md`.
- **PLT-057** `[D]` Si esce dall'app **solo** da MENU → «Quit Stame» (`40` MIDI-095, `30` UI-129), oltre che con `SIGTERM`/`SIGINT` (PLT-086). Nessuna combinazione di tasti è riservata, perché SELECT e START servono già a Options e BPM. All'uscita si salvano le impostazioni (§9) e si manda All Notes Off sulle porte in uscita.
- **PLT-058** `[V]` T-PLT-10 Tasti del volume, tasto di accensione e coperchio sono gestiti da spruce; Stame **NON DEVE** leggerli per funzioni proprie, ma **DEVE** reagire alle loro conseguenze (sospensione, §12.3).

---

## 8. Video

- **PLT-059** `[O]` Il video **DEVE** usare SDL2 caricata a runtime con `dlopen` da `/mnt/SDCARD/App/PyUI/dll/libSDL2-2.0.so`, con una finestra KMSDRM a schermo intero alla risoluzione corrente e `SDL_RenderSetLogicalSize(640, 480)`.
- **PLT-060** `[D]` Se quel percorso non esiste, la piattaforma **DEVE** provare `libSDL2-2.0.so.0` e `libSDL2.so` nei percorsi di sistema, poi uscire con un messaggio chiaro nel registro.
- **PLT-061** `[D]` SDL **DEVE** essere inizializzata solo con `SDL_INIT_VIDEO` (più `SDL_INIT_AUDIO` se si usa il backend di riserva) e con `SDL_HINT_NO_SIGNAL_HANDLERS = "1"`, così i segnali li gestisce Stame (§12.2).
- **PLT-062** `[D]` Sulla Flip **NON** si emula l'OLED 128×128 dell'Orchid (decisione di Luigi del 13/10/2026: «il display non deve essere clonato da orchid, ma visto che più grande, deve contenere tutto ciò che serve e/o è utile vedere in tempo reale»). `ui_flip` disegna la **plancia nativa** 640×480 descritta in `30-interfaccia.md` su un framebuffer software, che la piattaforma passa a SDL senza scalare (`SDL_HINT_RENDER_SCALE_QUALITY = "0"`).
- **PLT-063** `[D]` Il framebuffer **DEVE** passare a SDL come texture streaming 640×480 aggiornata solo quando cambia, con il caricamento limitato ai rettangoli modificati se il costo si vede (`SDL_UpdateTexture` con `SDL_Rect`); la presentazione **DOVREBBE** usare il vsync e non superare i 60 Hz `[V]` T-PLT-11.

---

## 9. Persistenza

### 9.1 File e cartelle

| Percorso sulla SD | Contenuto | Scritto da |
|---|---|---|
| `/mnt/SDCARD/Saves/stame/impostazioni.txt` | impostazioni globali dello strumento (menu Settings dell'Orchid) | nucleo → blob → thread UI |
| `/mnt/SDCARD/Saves/stame/stato.txt` | stato dell'ultima sessione: preset corrente, tonalità, BPM, viste | nucleo → blob → thread UI |
| `/mnt/SDCARD/Saves/stame/preset/u<NNN>.stp` | preset utente (formato in `20-suono.md`: blocco da 135 byte per motore, con intestazione) | idem |
| `/mnt/SDCARD/Saves/stame/loop/l<NN>.stl` | loop salvati (formato in `10-accordi-e-performance.md`) | idem |
| `/mnt/SDCARD/Saves/stame/piattaforma.txt` | parametri della piattaforma (tabella 9.2), letti solo all'avvio | a mano |
| `/mnt/SDCARD/Saves/spruce/stame.log` | registro | thread UI e `launch.sh` |

- **PLT-064** `[O]` I dati dell'app **DEVONO** stare sotto `Saves/`: gli aggiornamenti di spruce cancellano `spruce/flags`, e `/tmp` si svuota al riavvio.
- **PLT-065** `[D]` I formati dei blob **DEVONO** essere definiti dal nucleo (portabili sul Teensy, dove finiranno su flash o SD). Ogni blob ha un'intestazione: magia di 4 byte (`STM1` impostazioni, `STP1` preset, `STL1` loop), versione a 16 bit, lunghezza, CRC-32 in coda. Campi multibyte in little-endian, scritti byte per byte (niente `struct` copiate in blocco). Il contenuto di `STM1` è lo stesso testo `chiave=valore` di `impostazioni.txt` e `stato.txt` (PLT-066), così un solo lettore serve a tutti e due (**deciso da Luigi il 14/10/2026**).
- **PLT-066** `[D]` I file di testo (`impostazioni.txt`, `stato.txt`, `piattaforma.txt`) **DEVONO** usare righe `chiave=valore` in UTF-8 con fine riga LF; chiavi sconosciute si ignorano, chiavi mancanti prendono il default. Così un file vecchio resta leggibile.
- **PLT-067** `[D]` Ogni scrittura **DEVE** essere atomica per quanto la FAT32 permette: scrittura in `nome.tmp`, `fsync`, `rename` sul nome finale, `fsync` della cartella. Le impostazioni si salvano **al cambiamento**, con un ritardo di 2 s (debounce), oltre che all'uscita. Motivo `[O]`: gli spegnimenti bruschi lasciano file scritti a metà sulla SD.
- **PLT-068** `[D]` Un file corrotto (CRC errato, magia sconosciuta) **DEVE** essere rinominato in `.bad` e sostituito dai default, con un avviso nel registro; l'app **NON DEVE** fermarsi.
- **PLT-069** `[M]` `CONVENZIONI.md` I preset di fabbrica 3.92 sono dati privati: **NON DEVONO** essere nel repo né nel pacchetto dell'app. L'app **DEVE** funzionare senza di essi, con i propri suoni di partenza. **DEVE** caricarli se Luigi li mette lui stesso in `Saves/stame/privato/` sulla SD (**deciso da Luigi il 13/10/2026**). La cartella è fuori dal repo e dal pacchetto, e `deploy.sh` non la tocca mai.

### 9.2 `piattaforma.txt` (default)

```
audio=alsa              # alsa | sdl
alsa_device=auto        # auto = codec interno trovato per nome; oppure hw:C,D
sample_rate=48000
period=256
periods=2
rt_audio=70             # priorità SCHED_FIFO; 0 = niente tempo reale
rt_midi=60
cpu_pin=0               # 1 = thread audio sul core 3
event_offset=0          # 1 = eventi con offset in campioni (PLT-033)
debug_overlay=0         # 1 = CPU, underrun, latenza a schermo
log_level=1
```

---

## 10. Build

### 10.1 Toolchain

- **PLT-070** `[O]` La build per la Flip **DEVE** usare **Zig 0.17** dal PC Windows, senza WSL né toolchain Linux:
  `zig cc -target aarch64-linux-gnu.2.27 -mcpu=cortex_a55`
  con gli header ufficiali di **SDL2 2.32.10** (scaricati con SHA-256 verificato). Percorsi sul PC di lavoro: `D:\dev\toolchain\zig-x86_64-windows-0.17.0\zig.exe` e `D:\dev\toolchain\sdl2\SDL2-2.32.10\include`, passati con le variabili `ZIG` e `SDL_INCLUDE`.
- **PLT-071** `[D]` Opzioni di compilazione comuni: `-std=c11 -O2 -Wall -Wextra -Werror -Wdouble-promotion -Wvla -ffp-contract=off -fno-math-errno`. Per la Flip, in più: link con `-lpthread -ldl -lm`, niente link a SDL (si carica con `dlopen`).
- **PLT-072** `[D]` La build **DEVE** usare uno script POSIX `tools/build.sh` (gira nella Git Bash di Windows), con i target:
  - `flip` → `build/flip/stame` (aarch64);
  - `pc` → `build/pc/stame-sim.exe` (`-target x86_64-windows-gnu`, con l'SDL2 ufficiale per Windows);
  - `test` → compila ed esegue i test del nucleo sul PC, codice di uscita ≠ 0 se un test fallisce;
  - `render` → `build/pc/stame-render.exe`;
  - `portabilita` → controlli del §14.4;
  - `pacchetto` → `build/pacchetto/App/Stame/`.

  Stato del 14/10/2026: `render`, `flip` e `pacchetto` esistono già e costruiscono la **vetrina** (§15.1); `pc` (simulatore con finestra) non ancora. Le variabili sono `ZIG` (zig.exe) e `SDL_INCLUDE` (header di SDL 2.32, solo per `flip`; per default `D:\dev\toolchain\sdl2\SDL2-2.32.10\include`).
- **PLT-073** `[D]` Gli script **DEVONO** essere scritti con l'editor (non generati da heredoc nella shell) e tenuti con fine riga LF (`.gitattributes`: `*.sh text eol=lf`). Motivo `[O]`: nella Git Bash le sequenze `\b`, `\f`, `\t` nei percorsi Windows diventano caratteri di controllo, e uno script CRLF non gira sulla console.

### 10.2 Struttura del repo

```
stame/
  CLAUDE.md
  .gitattributes .gitignore
  docs/specifica/            specifica funzionale (questa)
  docs/disegni/              PDF della plancia e dei controlli, con i sorgenti che lo generano
  src/
    core/                    stame.h, stame_base.h, spsc.h, accordi, performance, looper, tempo,
                             interfaccia (viste), midi_parse, midi_map, blob (serializzazione)
    dsp/                     voci, motori VA/FM/Reed, basso, effetti
    ui/                      ui_model_t e suo riempimento dallo stato del nucleo
    gfx/                     primitive su framebuffer RGB565 e 1 bit, font bitmap
    ui_flip/                 plancia 640×480 della Flip
    ui_oled/                 viste OLED 128×128 (fase 2, hardware)
    platform/
      flip/                  main.c, audio_alsa.c, audio_sdl.c, midi_rawmidi.c, input_evdev.c,
                             video_sdl.c, sdl_loader.c, storage_posix.c, rt.c, log.c
      pc/                    main.c, audio_sdl.c, midi_winmm.c, input_kbd.c, video_sdl.c
      offline/               render.c (eventi → WAV, fotogrammi della plancia → PPM)
  tests/
    unit/                    test del nucleo (accordi, voicing, parser MIDI, code, blob)
    golden/                  script di eventi + hash e WAV di riferimento
    shim/                    header minimi per la compilazione di prova Cortex-M7
  tools/                     build.sh, deploy.sh, flip-ssh.sh, cattura-midi.sh, icona
  app/Stame/                 modello del pacchetto: config.json, launch.sh, icon.png
  third_party/               spleen/ (font bitmap, BSD-2, convertiti in C da tools/bdf2c); eventuale tinyalsa (BSD); ognuno con la sua licenza
  build/                     (ignorata da git)
```

- **PLT-074** `[D]` Header di SDL, binari, `build/`, l'indirizzo della Flip (`tools/flip.ip`) e qualunque file con password **DEVONO** restare fuori da git. I preset di fabbrica non entrano mai nel repo (PLT-069).

---

## 11. Test, render offline e simulatore

- **PLT-075** `[D]` I test unitari del nucleo **DEVONO** girare sul PC con un runner minimo proprio (macro `CHECK`, nessuna libreria esterna) e coprire almeno: tabelle degli accordi e Secret Chords, voicing, key mode, parser MIDI (running status, real time dentro SysEx, SysEx troncati), code SPSC (anche con due thread), serializzazione dei blob (andata e ritorno, CRC errato, versione vecchia).
- **PLT-076** `[D]` `stame-render` **DEVE** leggere uno script di eventi di testo (righe `t_secondi tipo argomenti`, per esempio `0.500 key_on 60 100`) oppure un file MIDI standard (tipo 0 o 1), e scrivere un WAV a 48 kHz (float32 o S16) più, a richiesta, i fotogrammi del framebuffer in PBM. Usa lo stesso `stame_render` dell'app, con periodo 256.
- **PLT-077** `[D]` I test golden **DEVONO** confrontare il render di ogni script con un riferimento: uguaglianza esatta sullo stesso target; tolleranza (massimo scarto assoluto ≤ 1e−4) tra x86_64 e aarch64. `-ffp-contract=off` serve a tenere vicini i risultati.
- **PLT-078** `[D]` Il simulatore su PC **DEVE** mostrare una finestra 640×480 con lo stesso layout della Flip, mappare la tastiera del PC sui tasti della Flip e su una tastiera MIDI virtuale, e **DOVREBBE** leggere la MPK collegata al PC con WinMM, così si suona sul PC con lo stesso controller.
- **PLT-079** `[O]` Nelle build di prova su PC non si apre nessun ingresso audio (microfono) e non si usa la rete.
- **PLT-080** `[D]` Prove sulla console: schermate con `kmsgrab`, tasti premuti da remoto scrivendo strutture `input_event` da 24 byte (`llHHi`) sul dispositivo del pad trovato per nome. Prima di farlo **DEVE** essere chiaro che nessuno sta usando la console (§13).
- **PLT-081** `[O]` Le prove automatiche **NON DEVONO** sostituire l'ascolto: ogni fase che cambia il suono si chiude con un ascolto di Luigi sulla Flip (cuffie e altoparlante).

---

## 12. Packaging, avvio e ciclo di vita

### 12.1 L'app spruceOS

```
/mnt/SDCARD/App/Stame/
  config.json
  launch.sh
  stame            binario aarch64
  icon.png         70×70
  LICENSE  README.md
```

```json
{
  "label": "Stame",
  "icon": "icon.png",
  "launch": "launch.sh",
  "description": "Synth ad accordi, clone dell'Orchid. Collega la MPK mini Plus alla porta USB-C di sopra.",
  "devices": ["MIYOO_FLIP"]
}
```

```sh
#!/bin/sh
# Stame: synth ad accordi per la Miyoo Flip. Sorgenti e specifica nel repo del progetto.
APPDIR="$(cd "$(dirname "$0")" && pwd)"
SAVES=/mnt/SDCARD/Saves/stame
LOG=/mnt/SDCARD/Saves/spruce/stame.log
mkdir -p "$SAVES/preset" "$SAVES/loop"
[ -f "$LOG" ] && [ "$(wc -c < "$LOG")" -gt 1048576 ] && mv "$LOG" "$LOG.1"
cd "$APPDIR" || exit 1
STAME_SAVES="$SAVES" exec ./stame >> "$LOG" 2>&1
```

- **PLT-082** `[O]` L'app **DEVE** essere una cartella `App/Stame` con `config.json` (`label`, `icon`, `launch`, `description`, `devices: ["MIYOO_FLIP"]`) e `launch.sh`, con fine riga LF.
- **PLT-083** `[O]` L'icona **DEVE** essere 70×70, tratto color oro (215, 180, 95) su sfondo trasparente, con un simbolo semplice: a quella misura i dettagli non si leggono. Proposta `[D]`: uno stame stilizzato (filamento verticale e antera ovale), senza testo.
- **PLT-084** `[D]` `launch.sh` **NON DEVE** cambiare il profilo della CPU (`principal.sh` ha già chiamato `set_performance` `[O]`), né toccare `otg_mode`, il mixer o i servizi di spruce. **PUÒ** includere gli script di aiuto di spruce come fanno le altre app native `[V]` T-PLT-12.
- **PLT-085** `[D]` Dall'avvio di `launch.sh` alla prima nota possibile **DOVREBBERO** passare meno di 2 s.

### 12.2 Uscita e segnali

- **PLT-086** `[D]` Alla ricezione di `SIGTERM` o `SIGINT`, e all'uscita da «Quit Stame» (PLT-057), l'app **DEVE**, entro 1 s: mandare `FC` (stop del clock) e All Notes Off (CC 123) sulle porte in uscita, scrivere impostazioni e stato (PLT-067), fermare il PCM (`drop`), chiudere i fd MIDI ed evdev, chiudere SDL. Il gestore del segnale imposta solo un flag atomico; il lavoro lo fa il thread UI `[V]` T-PLT-12 (come spruce chiude le app e quanto aspetta prima di `SIGKILL`).

### 12.3 Sospensione e riattivazione

- **PLT-087** `[D]` L'app **DEVE** sopravvivere a una sospensione (di sistema o con `SIGSTOP`/`SIGCONT`), qualunque sia il modo in cui spruce la fa `[V]` T-PLT-07:
  - PCM: `-ESTRPIPE` → `SNDRV_PCM_IOCTL_RESUME`, oppure `PREPARE` se il resume non è supportato; `-EPIPE` → `PREPARE`;
  - salto di tempo: se tra due periodi passano più di 500 ms, il nucleo riceve un evento `time_jump`: rilascia le note tenute, rimette in fase il clock, manda `FC` e poi `FA` se il trasporto era in moto (regola in `40-midi-e-controlli.md`);
  - USB: al risveglio la MPK può sparire e ricomparire con un altro numero di scheda; la gestisce l'hot-plug (§6.3);
  - evdev: se il fd del pad dà `ENODEV`, lo si riapre cercandolo per nome.
- **PLT-088** `[D]` Prima di una sospensione annunciata (se spruce ne dà notizia `[V]` T-PLT-07) l'app **DOVREBBE** salvare impostazioni e stato.

### 12.4 Alimentazione della MPK

- **PLT-089** `[O]` La MPK si collega alla **porta USB-C di sopra** (OTG), che passa in host da sola e la alimenta. Con un cavo USB-C → USB-B, oppure con un adattatore OTG più un cavo A–B.
- **PLT-090** `[D]` La piattaforma **PUÒ** leggere `/sys/class/power_supply/battery/capacity` e `status` ogni 5 s nel thread UI e mandarli al nucleo (`battery`), per l'indicatore di batteria e per un avviso quando scende sotto il 15% `[V]` T-PLT-09 (percorsi e consumo reale della MPK, Plus §18 test 1).
- **PLT-091** `[O]` Se la Flip non regge la MPK, si usa un **hub USB 2.0 semplice**, senza Power Delivery né ricarica passante (meglio alimentato). Le docking station per portatili non funzionano con la Flip e senza alimentatore l'hanno fatta riavviare.

---

## 13. Deploy via SSH

- **PLT-092** `[O]` Il deploy **DEVE** passare dal Wi-Fi con SSH (dropbear; spruce non offre ADB né altre connessioni USB): Impostazioni → Rete → Attiva SSH; PC e Flip sulla stessa rete, oppure l'hotspot di Windows se la rete isola i dispositivi.
- **PLT-093** `[O]` `tools/flip-ssh.sh` **DEVE**:
  - leggere l'indirizzo da `tools/flip.ip` (cambia da una rete all'altra e anche nella stessa);
  - usare `-o StrictHostKeyChecking=accept-new` (altrimenti con un indirizzo nuovo resta fermo sulla domanda della chiave, invisibile con l'askpass);
  - passare la password con `SSH_ASKPASS` e uno script locale fuori dal repo. Il login con chiave non funziona, perché la home sta sulla FAT32.
  La password **NON DEVE** comparire nel repo né nel vault.
- **PLT-094** `[D]` `tools/deploy.sh` **DEVE**:
  1. controllare con `pidof stame` se l'app è aperta. Se lo è, **fermarsi e chiedere** a Luigi: non chiudere app e non premere tasti da remoto mentre qualcuno usa la console `[O]`. Un binario in esecuzione non si sovrascrive comunque («Text file busy») `[O]`;
  2. copiare `build/pacchetto/App/Stame/` in `/mnt/SDCARD/App/Stame/` (`tar` via `ssh`), scrivendo prima in `stame.new` e poi rinominando;
  3. verificare `md5sum` dei file copiati;
  4. **mai** toccare `otg_mode`, il mixer, i servizi di spruce o la memoria interna.
- **PLT-095** `[O]` Per cercare processi da remoto **DEVE** essere usata la forma `pgrep -f "[s]tame"` o `pidof`: `pgrep -f`/`pkill -f` semplici trovano anche la shell che li lancia e possono chiudere la propria sessione SSH.
- **PLT-096** `[O]` A fine lavoro si rimette «Attiva SSH» su No, soprattutto su reti non proprie: la password predefinita di spruce è pubblica.

---

## 14. Portabilità verso Teensy 4.1

Obiettivo: riusare `core`, `dsp`, `ui`, `gfx` e `ui_flip` sul Teensy 4.1 con Audio Shield senza modificarli, riscrivendo solo lo strato di piattaforma (circa il 10–20% del codice `[D]`, `Orchid - hardware e distinta per il clone` B5).

### 14.1 Dati del bersaglio

| Voce | Teensy 4.1 | Orchid originale (riferimento) | Etichetta |
|---|---|---|---|
| CPU | Cortex-M7 600 MHz, FPU (`float` a singola precisione veloce) | STM32H723, M7 550 MHz | [M] PJRC, ST |
| RAM | 1 MB: **RAM1** 512 KB (ITCM + DTCM, veloce, ci va anche il codice per default) + **RAM2** 512 KB (OCRAM, `DMAMEM`) | 564 KB in blocchi separati, il più grande circa 320 KB | [M] PJRC; [D] Orchid |
| Flash | 8 MB; PSRAM opzionale fino a 16 MB | 1 MB | [M] |
| Audio | Audio Library a 16 bit, 44,1 kHz, blocchi da 128 campioni (riducibili a 64 o 32) | sconosciuto | [M]/[D] |
| Cicli per campione | 13 605 a 44,1 kHz | 11 458 a 48 kHz | [D] |

### 14.2 Regole per il nucleo

- **PLT-097** `[D]` **Niente heap**, in tutto `core`, `dsp`, `ui`, `gfx` e `ui_flip` (non solo nel percorso audio): la memoria arriva dalla piattaforma come due array statici, `fast` e `bulk` (§2.2), e il nucleo la divide solo in `stame_init`. Dopo l'init nessuna allocazione.
- **PLT-098** `[D]` Budget di RAM del nucleo, controllato in compilazione con `_Static_assert` su `stame_mem_required` per la configurazione massima:
  - `fast` ≤ **128 KB** (stato delle voci, accordi, looper, interfaccia, code): sul Teensy va in DTCM;
  - `bulk` ≤ **320 KB** (riverbero, delay, chorus, buffer lunghi): sul Teensy va in RAM2 (`DMAMEM`);
  - totale ≤ **448 KB**, in linea con la stima di 350–400 KB per l'Orchid `[D]`.
  Un delay lungo **DEVE** poter usare campioni a 16 bit (1 s stereo a 48 kHz in float vale 384 KB e non entrerebbe).
- **PLT-099** `[D]` Le tabelle costanti **DEVONO** essere `static const` e marcate con la macro `STAME_ROM` (vuota sulla Flip, `PROGMEM` sul Teensy, dove i dati costanti finiscono altrimenti in RAM1).
- **PLT-100** `[D]` Solo `float` a 32 bit nel percorso audio: niente `double`, costanti con il suffisso `f`, funzioni `sinf`/`expf`/`powf` o tabelle (`-Wdouble-promotion` attivo). Niente VLA, niente ricorsione, stack del rendering ≤ 8 KB.
- **PLT-101** `[D]` Sample rate come parametro (44 100 o 48 000): ogni costante di tempo si calcola all'init o al cambio di parametro, e le tabelle sono dimensionate per 48 kHz.
- **PLT-102** `[D]` Il periodo della piattaforma **DEVE** essere un multiplo di 16 (Flip 256, Teensy 128, 64 o 32): il nucleo rende sempre a blocchi di 16.
- **PLT-103** `[D]` Niente dipendenze dal sistema nel nucleo: casualità da un PRNG interno (xorshift32) con seme dato dalla piattaforma; tempo dal conteggio dei campioni; salvataggi come blob (§9).
- **PLT-104** `[D]` Budget di CPU per il Teensy: con 16 voci ed effetti il `dsp` **DOVREBBE** stare sotto il **50%** della CPU a 600 MHz (circa 6 800 cicli per campione a 44,1 kHz). Si verifica al prototipo P0 (pronto quando: CPU sotto il 60%, nessun buco audio, latenza sotto i 10 ms) `[D]` `Orchid - hardware e distinta per il clone`. Sulla Flip non si misura: lì serve solo come vincolo di progetto.
- **PLT-105** `[D]` Le code SPSC **DEVONO** funzionare anche tra un interrupt e il `loop()` su un solo core (barriere di memoria di `<stdatomic.h>`, nessun lock).

### 14.3 Cosa cambia sul Teensy (fuori da questa specifica)

Callback audio (`AudioStream::update()` con conversione float → int16), driver dell'OLED invece di SDL, scansione di tasti ed encoder, MIDI (USB host per la MPK con `USBHost_t36`, USB device, seriale), salvataggi su flash o SD, aggiornamento.

### 14.4 Controlli automatici di portabilità (`build.sh portabilita`)

- **PLT-106** `[D]` La build **DEVE** fallire se un file di `core`, `dsp` o `gfx` include un header fuori dall'elenco di PLT-001 (controllo con `grep` sugli `#include`), oppure se usa un simbolo avvelenato (PLT-002).
- **PLT-107** `[D]` La build **DOVREBBE** compilare `core`, `dsp`, `ui`, `gfx` e `ui_flip` anche per `-target thumb-freestanding-eabihf -mcpu=cortex_m7` con gli header minimi di `tests/shim/` (solo compilazione, niente link), e stampare la memoria richiesta da `stame_mem_required` `[V]` T-PLT-16 (fattibilità con Zig 0.17).

---

## 15. Piano di sviluppo per la Flip

| Fase | Contenuto | Pronto quando |
|---|---|---|
| **F0 — Repo e toolchain** | struttura del §10.2, `build.sh` (target `test`, `portabilita`), `stame_base.h`, `spsc.h` con test, runner dei test | `build.sh test` e `build.sh portabilita` passano sul PC; un «ciao» aarch64 compilato con Zig |
| **F1 — Nucleo sul PC** | accordi, Secret Chords, nomi, voicing, Split/Octave, key mode, play style, parser MIDI e mappa MPK, blob (sezioni 10 e 40) | tutti i test unitari passano; i comportamenti `[V]` dell'Orchid hanno un default e un test |
| **F2 — Primo suono offline** | pool di voci, un motore (VA) con il basso, `stame-render`, primi test golden | un WAV da uno script di accordi ascoltato da Luigi; golden stabili |
| **F3 — Simulatore su PC** | `ui`, `gfx` e `ui_flip` con la plancia, `platform/pc` (SDL2, tastiera, WinMM con la MPK sul PC) | si suona dal PC con la MPK; plancia uguale alle immagini di riferimento |
| **F4 — Prima nota sulla Flip** | verifiche T-PLT-01, 02, 05, 06, 10 e Plus §18 test 1, 2, 25, 26, 27; backend SDL, poi ALSA diretto con tono di prova; rawmidi con la Plus; una voce | una nota dalla MPK sulla Flip; latenza misurata (T-PLT-04); 10 minuti senza underrun a 256×2 o configurazione aggiornata |
| **F5 — App sulla Flip** | plancia 640×480, tasti della Flip, persistenza, `launch.sh`, icona, `deploy.sh`, hot-plug, sospensione, uscita pulita | l'app parte dal menu di spruce, sopravvive a scollegamento della MPK e a una sospensione, ritrova le impostazioni |
| **F6 — App completa** | tutti i motori, effetti, preset, looper, MIDI out e clock, overlay di debug, ottimizzazioni | requisiti PLT-029, 031, 034 rispettati con 16 voci; ascolto di Luigi in cuffia e all'altoparlante; pacchetto pronto |

- **PLT-108** `[D]` Ogni fase **DEVE** chiudersi con i propri criteri e con il second brain aggiornato; non si passa alla Flip (F4) prima che il nucleo abbia i suoi test sul PC (F1).

### 15.1 La vetrina (14/10/2026)

Luigi ha chiesto di vedere sulla Flip la nuova identità della plancia (`docs/identita/README.md`) prima delle fasi F2–F5. La **vetrina** anticipa una parte di F3 e F5 senza il suono:
- `gfx`, `ui` (modello e `ui_fmt`) e `ui_flip` sono i moduli veri, portabili e con i test (`test_gfx.c`, `test_plancia.c`);
- `src/platform/vetrina/` è un pilota dimostrativo: usa il motore degli accordi (`core/acc`) e lo strato di input (`core/input`) veri, simula suoni, effetti, looper e liste, e dopo 20 s senza ingressi fa partire una demo che passa per tutti gli stati della plancia. Non è `core/ui`: andrà sostituito;
- `src/platform/flip/` apre SDL con `dlopen` (PLT-059..063), legge i tasti da evdev (PLT-052..054), la MPK da rawmidi (§6.1) e la batteria (PLT-090);
- **dal 15/10/2026 la vetrina suona** con il synth vero (`src/dsp`, specifica 20), anticipando F2 e F4: il motore degli accordi manda le note TREBLE al Sound e le BASS al Bass; suono, basso, effetto principale e volumi della vetrina diventano patch e parametri (`vetrina_dsp.c`). Le patch sono quelle di Stame per i 16 suoni e i 6 bassi della vetrina (`tools/patch.py`, banchi in `assets/patch/`). L'audio è il backend SDL di riserva (PLT-022): callback di SDL, periodo `STAME_AUDIO_FRAMES` (default 512, nel `launch.sh`), comandi su una coda SPSC dal thread principale, logo sonoro sommato nell'uscita. Il backend ALSA diretto resta da fare;
- **dal 15/10/2026 suonano anche Perform, Beat, metronomo e looper**: il thread audio fa girare `core/motore` (clock a 96 PPQN, performance, Beat con la batteria, looper a eventi) e la vetrina gli manda BPM, Perform, Beat, transpose e comandi del looper sulla stessa coda; la plancia legge trasporto e looper dallo stato che il motore pubblica a ogni periodo (`mot_snap_t`). La demo automatica registra un loop di quattro battute dopo il count-in e lo fa suonare mentre cambiano suono, effetto e transpose;
- `stame --prova-audio` rende 30 s della demo nel motore in memoria e misura la CPU, senza dispositivo audio: 15/10/2026, solo synth, con il menu di spruce aperto (1,1 GHz), **28,7 % di un core** con al massimo 8 voci; con il motore completo (Beat, Perform e looper), **11,0 % di un core** con al massimo 7 voci e blocco peggiore di 751 µs, isolato e coperto dal periodo di 10,7 ms;
- `stame --prova` fa girare la vetrina in memoria e misura il disegno, senza schermo né tasti: si può lanciare via SSH senza disturbare chi usa la console (15/10/2026, plancia calma: 0,64 ms per fotogramma in media, 1,71 ms per uno schermo intero);
- la plancia è quella calma (30, UI-140, 15/10/2026): L1, R1, croce, A e X aprono la pagina dei comandi, che si chiude 5 s dopo l'ultimo di quei tasti o con B (UI-142a); la demo la apre solo durante la scelta del suono;
- nella vetrina MENU apre il menu della piattaforma (Theme, Linnaeus Tag, Legend, Meters, Demo, Quit Stame); tenere MENU per 2 s esce, come rete di sicurezza della sola vetrina (nell'app vera vale PLT-057);
- `tools/flip-ssh.sh` e `tools/deploy.sh` seguono PLT-093 e PLT-094; l'indirizzo sta in `tools/flip.ip`, fuori da git.
- **PLT-109** `[M]` `CLAUDE.md` del progetto In nessuna fase si forza la porta USB-C OTG in host (`echo host > …/otg_mode`). Se un test richiede di toccare porte, alimentazione o ricarica, prima si spiega il rischio e si chiede l'ok a Luigi.

---

## 16. Test di piattaforma

| ID | Domanda | Come |
|---|---|---|
| T-PLT-01 | Sistema: kernel, CPU, RAM, glibc, schede audio, alsa-lib | `uname -a`, `cat /proc/cpuinfo`, `free -m`, `ls -l /lib/libc.so.6` (o `/lib/ld-linux-aarch64.so.1 --version`), `cat /proc/asound/cards /proc/asound/pcm`, `ls /usr/lib/libasound*` |
| T-PLT-02 | Parametri ammessi dal PCM del codec: formati, rate, periodo e buffer minimi e massimi | programma `stame-probe` (`HW_REFINE` su tutto lo spazio); durante il suono `cat /proc/asound/card0/pcm0p/sub0/hw_params` |
| T-PLT-03 | Underrun e CPU con periodo 128/256/512 × 2/3, con e senza `SCHED_FIFO` e `cpu_pin`, con UI a 60 Hz | 10 minuti per combinazione con carico sintetico (16 voci + effetti); contatori dell'overlay |
| T-PLT-04 | Latenza tasto → suono e jitter del clock in uscita | stima interna (PLT-032) + misura esterna: microfono che registra il clic del tasto e il suono in cuffia; per il clock, registrazione del DIN o di un synth esterno |
| T-PLT-05 | Il PCM `hw` è libero quando PyUI è chiuso? C'è un `asound.conf` con dmix? | apertura da `stame-probe` dopo il lancio da menu; `cat /etc/asound.conf` |
| T-PLT-06 | L'app è root? `SCHED_FIFO` e `mlockall` permessi? | `id`, `ulimit -r`, valore di ritorno di `pthread_setschedparam` nel registro |
| T-PLT-07 | Cosa fa spruce con il tasto di accensione e con il coperchio chiuso (sospensione di sistema, `SIGSTOP`, spegnimento schermo)? Cosa succede a PCM, rawmidi ed evdev al risveglio? | `evtest` su tutti i dispositivi, script di spruce, registro di Stame durante una sospensione |
| T-PLT-08 | Hot-plug della MPK con l'app aperta | = Plus §18 test 26, più controllo dei codici `ENODEV`/`POLLHUP` |
| T-PLT-09 | Consumo della MPK dalla Flip e durata della batteria | = Plus §18 test 1; `current_now` con e senza MPK, pad accesi e spenti |
| T-PLT-10 | Nome del pad, soglie di L2/R2, zone morte delle levette, tasti di volume, accensione e coperchio | `evtest`, `cat /proc/bus/input/devices`, script `button_actions.sh` di spruce |
| T-PLT-11 | Vsync e costo della presentazione SDL KMSDRM; CPU da fermo | misura del tempo per fotogramma, `top` |
| T-PLT-12 | Come spruce chiude un'app (segnale, attesa prima di `SIGKILL`) e cosa includono i `launch.sh` delle app native esistenti | lettura di `principal.sh` e degli script di aiuto sulla SD |
| T-PLT-13 | `snd-seq` presente? (solo informativo) | = Plus §18 test 25 |
| T-PLT-14 | Memoria libera con l'app aperta | `free -m`, `/proc/<pid>/status` (VmRSS, VmLck) |
| T-PLT-15 | Con il PCM `hw` aperto da Stame, inserire e togliere le cuffie cambia ancora l'uscita? | prova a mano con l'app che suona |
| T-PLT-16 | Zig 0.17 compila il nucleo per `thumb-freestanding-eabihf` con header minimi? | `build.sh portabilita` |

---

## 17. Gotcha noti

| Gotcha | Conseguenza | Rimedio | Etichetta |
|---|---|---|---|
| **Porta USB-C OTG forzata in host** (`echo host > …/otg_mode`) | con una dock alimentata collegata, la Flip ha smesso di accettare i caricatori USB-C su tutte e due le porte; un riavvio non basta | **mai forzarla**; se serve toccare porte o alimentazione: spiegare il rischio e chiedere l'ok. Ripristino: `echo otg > /sys/devices/platform/fe8a0000.usb2-phy/otg_mode`; se la ricarica resta bloccata, spegnimento completo dal menu e caricatore attaccato a console spenta | [O] |
| Nomi `BTN_*` nel codice dell'app | tasti scartati sulla console, prove sul PC che passano | prefisso `PAD_*` e `_Static_assert` (PLT-054) | [O] |
| Pad a numero fisso `event5` | con un dispositivo HID collegato all'avvio il pad si sposta e l'app sembra piantata | ricerca per nome (PLT-053) | [O] |
| Input letto sia da SDL sia da evdev | tasti «già premuti» | solo evdev (PLT-052) | [O] |
| SDL di sistema con SONAME standard assente | `dlopen` fallisce | percorso di PyUI e alternative (PLT-059, 060) | [O] |
| SDL audio con 512 campioni | underrun | ALSA diretto; con SDL 1024 (PLT-030) | [O] |
| Altoparlante debole sotto 250–300 Hz | il basso dell'Orchid quasi sparisce all'altoparlante | per suonare: cuffie. Un eventuale esaltatore psicoacustico dei bassi va solo in appendice di `20-suono.md`, spento per default | [O]; rimedio [D] |
| Spegnimento brusco | file scritti a metà, cartelle illeggibili sulla SD | scritture atomiche (PLT-067); spegnere sempre dal menu; in caso di danni `chkdsk /f` dal PC | [O] |
| `spruce/flags` cancellata dagli aggiornamenti, `/tmp` svuotata al riavvio | dati persi | tutto sotto `Saves/` (PLT-064) | [O] |
| «Text file busy» | il binario non si sovrascrive | chiudere l'app prima del deploy (PLT-094) | [O] |
| `pgrep -f`/`pkill -f` via SSH | chiudono la propria sessione | forma `[s]tame` o `pidof` (PLT-095) | [O] |
| Indirizzo della Flip che cambia | SSH fermo sulla chiave dell'host | `flip.ip` e `accept-new` (PLT-093) | [O] |
| Tasti premuti da remoto o app chiuse mentre Luigi usa la console | si interrompe chi sta suonando | chiedere prima, controllare con `pidof` | [O] |
| Docking station per portatili | non si accendono; la Flip si è riavviata | hub USB 2.0 semplice (PLT-091) | [O] |
| Fine riga CRLF negli script; `\b`, `\f`, `\t` nei percorsi negli heredoc | script che non girano sulla console, percorsi rovinati | LF e script scritti con l'editor (PLT-073) | [O] |
| Fuso orario | i programmi lanciati fuori da PyUI possono vedere un'ora sbagliata | nel registro usare il tempo monotono più l'ora UTC; non serve altro | [O]; rimedio [D] |
| Percorsi `/mnt/sdcard` e `/mnt/SDCARD` | stesso file sulla FAT32, stringhe diverse | confrontare i percorsi senza badare alle maiuscole | [O] |
| MPK che manda controlli su più porte | controlli persi se si apre solo la porta 1 | aprire tutte le porte (PLT-039); prima di scrivere la mappa, catturare il traffico reale | [O] |
| SysEx di scrittura sulla Plus | sovrascrive programma e sequenze | mai senza backup e ok di Luigi (PLT-043) | [M] |
| Prove automatiche verdi ma suono sbagliato | un'app musicale «passava» 133 prove e non piaceva | ascolto di Luigi a ogni fase (PLT-081) | [O] |

---

## 18. Questioni aperte

1. **Parametri reali del PCM** (formati, periodo minimo, 44,1 o 48 kHz): default 48 kHz, S16_LE, 256 × 2 `[V]` T-PLT-02, T-PLT-03. Se il driver non regge 256, si ricalcola il budget del §5.3.
2. **Underrun con 512 campioni in SDL**: non si sa se dipendevano dal driver o dallo scheduling di SDL. Lo dice T-PLT-03; se il driver non regge periodi piccoli, la latenza obiettivo (PLT-031) va rivista.
3. **Latenza reale tasto → suono** e jitter: stime soltanto `[V]` T-PLT-04. La latenza dell'Orchid è sconosciuta, quindi non c'è un valore «fedele» da copiare.
4. **Root e `SCHED_FIFO`**: si presume che le app girino come root `[V]` T-PLT-06.
5. **PCM libero e dmix**: si presume che il PCM sia libero dopo l'uscita di PyUI `[V]` T-PLT-05; da verificare anche il cambio di uscita cuffie/altoparlante con il PCM aperto `[V]` T-PLT-15.
6. **Sospensione e coperchio**: comportamento di spruce sconosciuto `[V]` T-PLT-07.
7. ~~Uscita dall'app~~: **decisa il 13/10/2026**, solo MENU → «Quit Stame» (PLT-057).
8. **Chiusura da parte di spruce**: segnale e tempo concesso prima di `SIGKILL` `[V]` T-PLT-12.
9. **RAM, kernel e glibc della Flip**: da leggere `[V]` T-PLT-01. Non cambiano le scelte.
10. **Consumo della MPK** dalla porta OTG e durata della batteria `[V]` Plus §18 test 1, T-PLT-09.
11. **Dimensione dei blob dei loop** (proposta 32 KB) e dei preset: dipende dai formati di `10-accordi-e-performance.md` e `20-suono.md`.
12. ~~Preset di fabbrica privati~~: **decisi il 13/10/2026**, caricati da `Saves/stame/privato/` (PLT-069).
13. **Impostazione «Audio Output» dell'Orchid** (Auto, Headphones, Speakers, Both): sulla Flip l'uscita la sceglie spruce e Stame non tocca il mixer (PLT-026). Proposta: voce mostrata ma senza effetto sulla Flip; da concordare con `30-interfaccia.md`.
14. **Applicazione degli eventi con offset in campioni** (PLT-033): spenta per default; si accende se il jitter si sente.
15. **tinyalsa incluso o ioctl scritte a mano**: da decidere in F4; non cambia l'interfaccia `plat_audio`.
16. **Compilazione di prova Cortex-M7 con Zig** `[V]` T-PLT-16.
17. **Budget di RAM per il Teensy** (128 KB `fast`, 320 KB `bulk`): proposta, da confermare quando `20-suono.md` fissa riverbero e delay.

## 19. Dipendenze da altre sezioni

| Sezione | Cosa serve da lì | Cosa dà questa sezione |
|---|---|---|
| `00-panoramica.md` | glossario, architettura generale | moduli, thread, interfaccia piatta |
| `10-accordi-e-performance.md` | formato dei loop e loro dimensione; comportamento del clock e del looper durante una sospensione | blob, eventi `device(perso)` e `time_jump` |
| `20-suono.md` | numero di voci (16), blocchi da 16, memoria di riverbero e delay, formato dei preset (135 byte per motore), costo di CPU | budget di CPU e RAM (PLT-034, PLT-098), `float` a 32 bit, sample rate come parametro |
| `30-interfaccia.md` | `ui_model_t`, layout della plancia 640×480, font, overlay di debug, indicatore di batteria, voce «Audio Output» | framebuffer 640×480 RGB565, ridisegno solo al cambiamento, `battery` |
| `40-midi-e-controlli.md` | mappa della MPK e della tastiera generica, funzioni dei tasti della Flip, combinazione di uscita, porte e regole del clock in uscita | enumerazione delle porte, hot-plug, parser, istante dei messaggi in uscita, codici evdev |
| `90-questioni-aperte.md` | — | i test T-PLT-01…16 e le questioni del §18 |
