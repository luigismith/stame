# 30 — Interfaccia

Questa sezione descrive lo schermo OLED 128×128 dell'Orchid e tutto ciò che vi compare (viste, overlay, liste, looper), i gesti degli encoder, i LED, la macchina a stati dell'interfaccia e la resa sulla Miyoo Flip con la Akai MPK mini Plus. Il comportamento musicale (accordi, nomi degli accordi, looper, performance) è nella sezione 10. Qui c'è solo quello che si **vede** e il modo in cui lo si **comanda**. I messaggi MIDI veri e propri della MPK e i codici dei tasti della Flip sono nella sezione 40.

## 0. Convenzioni di questa sezione

### 0.1 Etichette
Le etichette seguono `CONVENZIONI.md`. Le fonti del vault usano un'altra convenzione: lì [V] vuol dire «verificato». La conversione è questa:

| Fonte del vault | Qui |
|---|---|
| figure 1 bit del manuale Coda, testo del manuale v4.1, changelog | `[M]` |
| fotogrammi dei video ufficiali (Quick Start, AMA), foto ufficiali, articolo It's Nice That | `[O]` |
| video e recensioni di terzi (Loopop, Garden Report, Tom Cosm, Molten, Splice, SOS) | `[O]` |
| deduzioni | `[D]` |
| dato mancante, con valore di default scelto qui | `[V]` con il riferimento al test `V-UI-nn` (elenco in §16) |

Per la resa sulla Flip, che sull'originale non esiste, `[D]` indica una **scelta di progetto**. I dati sulla Flip verificati sulla console sono `[O]`.

### 0.2 Sigle delle fonti
- **MAN**: manuale ufficiale Coda v4.1, comprese le figure 1 bit 640×640 (128×128 ingrandito ×5).
- **QS**: Quick Start v3.04 (youtu.be/GKf50ib0tho), con i secondi. **QSb**: Quick Start brevi TZyPDD6IKSw e zOk7zvm69Ec.
- **AMA**: AMA con il prototipo di dicembre 2024 (youtu.be/8AvlFjjgBmk).
- **LP**: Loopop (youtu.be/pnm52ueo_mI). **GR**: Garden Report 03 (youtu.be/VmaFJIkYsNs). **INT**: It's Nice That su Love and Money.
- **FW**: changelog ufficiale del firmware.

### 0.3 Coordinate e tolleranze
- Le coordinate sono in pixel del display: x da 0 a 127 verso destra, y (riga) da 0 a 127 verso il basso. Gli intervalli sono inclusivi: «righe 32..127» comprende sia la 32 che la 127.
- Le misure ricavate dai video hanno una tolleranza di ±1 px (±2 px nelle riprese oblique). I test di accettazione (§15) usano ±2 px per le misure `[O]` e il valore esatto per quelle prese dalle figure del manuale `[M]`.
- Il firmware di riferimento è il **3.92**. Dove le fonti mostrano firmware più vecchi (QS è 3.04), il dato vale solo se il changelog non lo contraddice.

---

## 1. Architettura dell'interfaccia

**UI-001** [D] L'interfaccia DEVE essere divisa in tre strati:

| Strato | Dove | Cosa fa | Dipendenze |
|---|---|---|---|
| `gfx` | nucleo portabile | framebuffer a 1 bit, primitive, font, widget (nome accordo, tastiera, lista, anello) e **disegno delle schermate** a partire da un modello dati | solo C11 |
| `core/ui` | nucleo portabile | macchina a stati della UI, riconoscimento dei gesti, timer, overlay, menu; produce il modello dati per `gfx` | C11, `core` |
| `platform/flip` | piattaforma | porta il framebuffer sullo schermo (SDL2), disegna il pannello virtuale, legge i tasti della Flip, traduce i controlli della MPK in azioni logiche | SDL2, evdev, ALSA |

**UI-002** [D] `gfx` e `core/ui` NON DEVONO includere header di SDL, ALSA, evdev o del sistema operativo, NON DEVONO allocare memoria dinamica e NON DEVONO leggere l'orologio da soli: il tempo arriva come parametro (millisecondi monotoni, `uint32_t now_ms`).

**UI-003** [D] Il disegno di una schermata DEVE essere una funzione pura del modello dati e del tempo: stesso modello e stesso `now_ms` danno lo stesso framebuffer, bit per bit. Così le schermate si provano sul PC con immagini di riferimento (§15).

**UI-004** [D] L'interfaccia NON DEVE mai girare nel thread audio né bloccarlo. Lo scambio con `core` e `dsp` passa da code senza lock e da istantanee del modello (§12.4).

---

## 2. Il modulo `gfx`

### 2.1 Framebuffer

**UI-010** [M] Il display dell'Orchid è di fatto a **1 bit**: testo, barre e riempimenti hanno la stessa luminanza e i grigi sono retini [M figure MAN; O LP 1442-1461]. Il framebuffer di Stame DEVE essere a 1 bit per pixel.

**UI-011** [D] Formato del framebuffer:

```c
typedef struct {
    uint8_t *bits;     /* fornito dal chiamante, nessuna malloc            */
    uint16_t w, h;     /* 128×128 per l'OLED; fino a 320×240 per il pannello */
    uint16_t stride;   /* byte per riga = (w + 7) / 8                       */
    uint8_t  dirty[30];/* una riga sporca = un bit (fino a 240 righe)       */
} gfx_fb_t;

#define GFX_OLED_W 128
#define GFX_OLED_H 128
/* buffer dell'OLED: 128 × 128 / 8 = 2048 byte */
```

- Ordine per righe, 16 byte per riga dell'OLED; nel byte, il bit 7 è il pixel più a sinistra.
- Valore 1 = pixel acceso, 0 = spento.
- `dirty` segna le righe cambiate dall'ultimo invio: la Flip lo usa per decidere se aggiornare la texture, un futuro hardware con controller a pagine (SH1107 è il candidato [D]) per inviare solo le pagine cambiate. La conversione verso le pagine verticali del controller spetta alla piattaforma.

**UI-012** [D] `gfx_fb_t` DEVE accettare dimensioni diverse da 128×128, perché sulla Flip lo stesso codice disegna anche il pannello virtuale a 1 bit (§13.3).

### 2.2 Primitive

**UI-013** [D] `gfx` DEVE offrire almeno queste primitive. Ognuna ha un modo di disegno `GFX_SET`, `GFX_CLR` o `GFX_XOR` e taglia tutto ciò che esce dal framebuffer (clipping), senza errori.

| Funzione | Uso |
|---|---|
| `gfx_clear(fb, val)` | cancella o riempie tutto |
| `gfx_pixel(fb, x, y, mode)` | |
| `gfx_hline`, `gfx_vline`, `gfx_line` (Bresenham) | tracce, separatori, React |
| `gfx_rect`, `gfx_fill_rect` | barre, tasti |
| `gfx_round_rect`, `gfx_fill_round_rect(r)` | anello del looper, pila della batteria |
| `gfx_fill_pattern(rect, pat, mode)` | retini: `PAT_50` (scacchiera 1 px), `PAT_25`, `PAT_75` |
| `gfx_blit(bitmap 1 bit, x, y, mode)` | logo, icone, glifi |
| `gfx_text_*`, `gfx_glyph_fit` | §2.3 |
| `gfx_invert_rect(rect)` | barre di selezione e scritte in negativo |

**UI-014** [O] Il retino al 50% DEVE essere una scacchiera ordinata di 1 px: pixel acceso se `((x + y) & 1) == 0` [O GR 195, LP; fase `[D]`]. Lo usano i tasti premuti (§4.3) e la parte non suonata dell'anello del looper (§8.2).

### 2.3 Font

L'Orchid usa un solo stile grafico in tre usi: testo piccolo per liste ed etichette, una variante sottile per la riga in alto e un font «elastico» per i nomi degli accordi e i numeri grandi [O misure LP, QS, GR]. Il carattere su misura si chiama «Chunky Roll» [O INT]: altezza 14–18 px, **aste verticali di 2 px e orizzontali di 1 px**, per tenere aperti gli occhielli. Il nome commerciale del font a schermo e i glifi completi non sono noti: i glifi di Stame vanno ridisegnati da zero ricalcando i fotogrammi, senza copiare file di font.

**UI-015** [M] **Font piccolo** (`FONT_SMALL`): bitmap proporzionale, per liste, etichette degli overlay e banda delle note.
- Altezza delle maiuscole (cap) **11 px**, discendenti **3 px** [M figura «quant»].
- x-height 8 px (circa il 75% della cap) [O; valore esatto `[V]`, test V-UI-18].
- Minuscole larghe 5–7 px, spaziatura tra lettere **1 px** [O ±1; `[V]` V-UI-18].
- Aste verticali di 2 px e orizzontali di 1 px [O INT].

**UI-016** [O] **Font di testata** (`FONT_HEAD`): bitmap proporzionale sottile, per la tonalità in alto a sinistra e il transpose in alto a destra.
- Cap **9 px** («Trans +3» alle righe 2..10) [O QS 754-770]; la tonalità occupa le righe 0..11, con le discendenti fino alla riga 14 [O QS 730, 770].
- Tratti di 1 px [O «font sottile»].
- Misura di riferimento: «C Major» occupa x 0..45 [O QS 730].

**UI-017** [O] **Font elastico** (`FONT_FIT`): ogni glifo si disegna in un riquadro qualsiasi `(x, y, w, h)` e lo riempie (fit-to-box). Non è una bitmap a misura fissa [O misure LP, QS, GR].
- Stile: grottesco tondo [O].
- Il ♭ è disegnato come una «b» minuscola [O QS 730, 770].
- Il ♯ ha le aste verticali inclinate [O QS 730, 770].
- Il doppio diesis si scrive «x» [M archivio del manuale].

**UI-018** [D] Formato del font elastico. Ogni glifo è uno **scheletro di tratti** in una griglia normalizzata, che `gfx_glyph_fit` rasterizza con uno spessore che dipende dall'altezza del riquadro:

```c
typedef enum { ST_VSTEM, ST_HBAR, ST_ARC, ST_DIAG } gfx_stroke_kind_t;
typedef struct {
    uint8_t kind;              /* gfx_stroke_kind_t                          */
    uint8_t x0, y0, x1, y1;    /* in 1/64 della larghezza e dell'altezza del riquadro */
    uint8_t quadrant;          /* per ST_ARC: 0..3, raggio dato dal rettangolo */
} gfx_stroke_t;

/* spessori: contrasto 2:1 come Chunky Roll                                  */
tv = max(2, round(h / 8.0));   /* aste verticali e diagonali   [V] V-UI-18   */
th = max(1, round(h / 16.0));  /* tratti orizzontali           [V] V-UI-18   */
r  = round(min(w, h) * 0.30);  /* raggio delle curve           [V] V-UI-18   */
```

- Ogni glifo ha anche un **rapporto naturale** `aspect = w/h`, usato dall'impaginazione (§4.2).
- Set minimo: `0–9`, `A–Z`, `a–z`, `+ - / ( ) ♯ ♭ x °`, più le lettere degli apici `J A Z W T F M`.
- Sotto i 16 px di altezza `gfx_glyph_fit` DOVREBBE usare `FONT_SMALL`, perché gli scheletri a quelle misure si leggono male [D].

**UI-019** [D] Le stringhe arrivano a `gfx` in UTF-8. Oltre all'ASCII stampabile DEVONO essere riconosciuti `♯` (U+266F), `♭` (U+266D), `✓` (U+2713), `●` (U+25CF) e `°` (U+00B0). Un carattere sconosciuto diventa `?`. I testi a schermo restano **in inglese** come sull'Orchid, quindi i font non devono avere lettere accentate.

---

## 3. Modello dati della UI

**UI-020** [D] `core/ui` DEVE consegnare a `gfx` un'istantanea `ui_model_t`, copiata per valore, con almeno questi campi. Li riempie `core`; i contenuti musicali (nomi, note, ortografia enarmonica) li decide la sezione 10.

| Campo | Contenuto |
|---|---|
| `view` | vista attiva: `VIEW_REACT`, `VIEW_CHORD`, `VIEW_KEYBOARD`, `VIEW_CHORD_KBD`, `VIEW_NOTES`, `VIEW_GEEK` |
| `key_on`, `key_root`, `key_acc`, `key_minor` | Key mode e tonalità |
| `transpose` | −12..+12 semitoni (gamma: sezione 10) |
| `chord_label` | nome dell'accordo da disegnare (§4.2), oppure vuoto |
| `chord_visible_until_ms` | fine della persistenza dopo il rilascio (§4.5) |
| `sounding_notes[]`, `n_sounding` | note dell'accordo che suona, dalla più grave alla più acuta, con nome già scritto («Eb», «F♯») |
| `pc_mask_sounding` | classi di altezza che suonano (12 bit) |
| `pc_mask_in_key` | classi di altezza della tonalità (12 bit), per i marker |
| `single_notes_mode`, `split_pc` | Split o Octave, punto di split (`W mod 12`) |
| `looper` | stato del looper, battute, progresso 0..65535, voci del menu, voce selezionata |
| `overlay` | overlay attivo (§6), con valori e scadenza |
| `list` | lista o menu aperto (§7), con voci, selezione e proprietario |
| `leds` | stato dei LED dell'originale (§11) |
| `battery_pct`, `charging` | batteria (sulla Flip: quella della console) |
| `scope` | puntatore in sola lettura al buffer dell'oscilloscopio (§5.1) |

---

## 4. Elementi comuni della schermata di gioco

### 4.1 Riga di testata

**UI-030** [O] **Tonalità** in alto a sinistra, con `FONT_HEAD`, a x = 0 e con la cap alle righe 1..10 (riga 0..11 con gli accenti, discendenti fino alla 14) [O QS 730, 770].
- Formato: radice, alterazione ed eventuale nome del modo, per esempio «C Major», «F♯ Minor».
- «Major» è osservato [O QS 730]; «Minor» è `[V]` (V-UI-19).
- Con la Key mode spenta la testata a sinistra resta vuota [O QS 754-770, firmware 3.04]. Se il 3.92 vi scriva «Off» è `[V]` (V-UI-19); default: vuota.

**UI-031** [O] **Transpose** in alto a destra, con `FONT_HEAD`, nella forma «Trans +3» / «Trans -2», allineato a destra con il bordo a x = 124, righe 2..10 [O QS 754-770]. Compare solo se `transpose ≠ 0`. Il nome dell'accordo tiene già conto del transpose [M FW 3.60].

**UI-032** [D] La testata (UI-030, UI-031) compare in tutte le viste tranne React, che ha solo la traccia (§5.1, `[V]` V-UI-17).

### 4.2 Il nome dell'accordo (impaginazione elastica)

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

**UI-034** [O] Regole di impaginazione nel riquadro `B = (bx, by, bw, bh)`:

| Parte | Altezza | Allineamento | Fonte |
|---|---|---|---|
| fondamentale | `bh` (tutta) | in basso; **si allarga in orizzontale** per riempire lo spazio libero | [O QS 730, 770] |
| alterazione | `round(2/3 · bh)` | in alto, subito a destra della fondamentale; può sovrapporsi fino a 3 px | [O QS 730, 770] |
| qualità minuscola | `round(0.70 · bh)` | sulla linea di base della fondamentale | [O LP 1220; rapporto `[V]` V-UI-18] |
| apice | `round(1/2 · bh)` | in alto; bordo destro a `bx + bw − 3` (x 124–126 a tutta larghezza) | [O QS 730, 770; LP 161-178] |
| «/» e basso | `bh` | dopo la qualità; l'alterazione del basso alta 2/3 | [O LP 1220] |

Ordine da sinistra: fondamentale, alterazione, qualità, apice, «/», basso.

**UI-035** [D] Algoritmo di impaginazione:

```
per ogni parte p: wn[p] = round(altezza[p] · aspect(glifi di p)) + gap   // gap = 2 px, tranne
                                                                         // alterazione dopo la radice: −3
W  = bw ; tot = Σ wn[p]
se tot ≤ W:
    w[root] = wn[root] + (W − tot)           // la fondamentale prende tutto lo spazio libero
    le altre parti restano alla larghezza naturale
altrimenti:                                   // nome troppo lungo: si stringe tutto
    w[p] = floor(wn[p] · W / tot)  per ogni p
    (larghezza minima di un glifo: 4 px)
x = bx ; per ogni p in ordine: disegna p in (x, y[p], w[p], altezza[p]) ; x += w[p]
l'apice, se c'è, si allinea a destra su bx + bw − 3; la differenza va alla fondamentale
```

Il restringimento dei nomi lunghi corrisponde alla critica dei recensori sui «nomi lunghi schiacciati» [O SOS, FM]; il modo esatto (stringere tutto o solo l'apice) è `[V]` (V-UI-18).

**UI-036** [O] Misure di riferimento per i test (§15):

| Caso | Riquadro | Misure |
|---|---|---|
| G♯ᴹ⁷, vista Chord | x 0..127, righe 32..127 | G x 1..66 (righe 32..127); ♯ x 67..92, righe 32..96; M x 92..106 e 7 x 109..124, righe 32..80 [O QS 730] |
| E♭ᴹ⁷, vista Chord | idem | E x 0..70; ♭ x 67..90, righe 34..96; M7 x 92..124, righe 32..80 [O QS 770] |
| C⁹, Geek Out senza tonalità | righe 2..52 | C x 0..100; 9 x 102..125, righe 4..27 [O GR/LP] |
| Dm/A, Geek Out | righe 18..54 | D x 0..38; m x 40..77, righe 30..54; / x 79..103; A x 104..127 [O LP 1220] |
| C^JAZZ | righe 2..52 | C x 1..85; J 89..96, A 99..105, Z 109..116, Z 119..126, righe 2..26 [O LP 161-178] |
| C^WTF | righe 2..52 | C x 1..82; W 87..98, T 101..113, F 116..127 [O LP 161-178] |

**UI-037** [V] Nota singola (Play Style Advanced o Free, oppure tasto senza tipo con la Key mode spenta): il riquadro del nome mostra solo la nota, con le regole della fondamentale [V V-UI-07]. L'indicatore di nota singola introdotto nel 3.60 [M FW] non ha immagini: default, nessun segno in più oltre al nome.

### 4.3 Widget tastiera

**UI-038** [O] La tastiera è un'ottava da Do a Si, disegnata nel riquadro righe `yt..127`. Geometria orizzontale (uguale in tutte le viste [O GR 176-195, LP 1450-1453; D per le viste diverse da Geek Out]):

| Elemento | Geometria |
|---|---|
| tasti bianchi | **accesi**, passo 18 px, larghezza totale x 0..125 |
| separatori dei bianchi | colonne spente di 1 px a x 17, 35, 53, 71, 89, 107 |
| separatore orizzontale | riga spenta `yt − 1` |
| tasti neri | **spenti**, centrati sui confini: C♯ x 13..24, D♯ 31..41, F♯ 67..78, G♯ 86..97, A♯ 104..114 |
| altezza dei neri | da `yt + 1` a `yk = yt + round(0.58 · (128 − yt))` (Geek Out: righe 79..107) |
| marker «in tonalità» sui bianchi | barretta **spenta** di 10 px × 4 righe, centrata nel tasto, righe 122..125 |
| marker «in tonalità» sui neri | barretta **accesa** di 10 px × 4 righe, centrata, righe `yk − 4 .. yk − 1` (Geek Out: 103..106) |
| tasti che suonano | riempiti con il retino al 50% (UI-014), marker compresi |

- Le misure di altre riprese differiscono di 1–2 px per la calibrazione [O].
- I marker delle note in tonalità esistono dal 3.04 [M FW] e compaiono solo con la Key mode attiva [D].
- Il disegno dei tasti neri «premuti» si vede poco: è una critica degli utenti [O], da non correggere.

**UI-039** [V] I tasti a retino sono le **classi di altezza dell'accordo che suona** (`pc_mask_sounding`), ripiegate in un'ottava, e non solo il tasto premuto [V V-UI-06]. Il basso non è compreso [V V-UI-06].

**UI-040** [V] **Grafica dello split** (dal 3.84 [M FW], nessuna immagine): in modalità Split, una linea verticale tratteggiata (un pixel sì e uno no) sul bordo sinistro del tasto `split_pc`, per tutta l'altezza della tastiera [V V-UI-07]. In modalità Octave non si disegna nulla.

### 4.4 Banda delle note

**UI-041** [O] Banda piena (accesa) alle righe 59..76, con i nomi delle note **spenti** (in negativo), separatore spento alla riga 77 [O GR 176-195, LP 1450-1453].
- Testo con `FONT_SMALL`, cap alle righe 64..74 (misurate 65..74, `[V]` V-UI-18), primo carattere a x = 3.
- I nomi sono le `sounding_notes` **dalla più grave alla più acuta**, separati da uno spazio: «F A D» è un Re minore in primo rivolto [O GR, LP]; esempi «F A D», «G C Eb», con le cap a x 3, 15, 28.
- Le alterazioni nella banda si scrivono «b» e «#» in ASCII come nell'esempio «Eb» [O]; il diesis è `[V]` (V-UI-28).
- Senza note che suonano la banda resta accesa e vuota [O QS 960].

### 4.5 Persistenza del nome

**UI-042** [M] Dal 3.90 il nome dell'accordo resta visibile un attimo dopo il rilascio [M FW 3.90]. Default: **1000 ms** dal rilascio dell'ultimo tasto, poi si cancella il riquadro del nome [V V-UI-02]. Prima del 3.90 restava solo la tonalità [O LP 1459-1461].

**UI-043** [D] Un nuovo accordo durante la persistenza sostituisce subito il nome vecchio. Tastiera e banda delle note seguono il suono e non la persistenza: si spengono al rilascio [D].

---

## 5. Le sei viste

Si scelgono da Options > System > View; la vista attiva ha la spunta [M MAN; O QS 950-975, LP 1441-1458]. La vista «Bliss Out» del prototipo del dicembre 2024 [O AMA 26-34] non esiste nel firmware di serie e NON DEVE essere implementata.

**UI-050** [V] La vista di fabbrica è **Chord** [V V-UI-29]. La vista scelta DEVE essere salvata tra un avvio e l'altro (formato: sezione 50).

**UI-051** [M] Le viste compaiono nello stato `PLAY` (§12) quando non c'è il looper attivo e nessun overlay, lista o menu le copre.

### 5.1 React

**UI-052** [O] Oscilloscopio dell'audio in uscita: traccia di 1 px su tutta la larghezza (x 0..127), centrata sulla riga 64. Da fermo è una linea piatta; con un accordo a volume medio oscilla di circa ±10 px. Il campionamento è libero, non agganciato al periodo [O AMA 29.7-30.7; D sul trigger]. Nasce dall'oscilloscopio con cui Parker disegnava un fiore con l'audio [O INT].

**UI-053** [V] Parametri della traccia:
- sorgente: somma mono `(L + R) / 2` dopo il volume master [V V-UI-17];
- finestra: gli ultimi 256 campioni a 48 kHz (5,3 ms), uno ogni 2, quindi 128 punti [V V-UI-17];
- ampiezza: `y = 64 − round(s · 40)`, tagliata a 0..127 (±1,0 di fondo scala = ±40 px) [V V-UI-17];
- tra due punti consecutivi si traccia una linea (`gfx_line`), così la traccia resta continua;
- nessuna testata [V V-UI-17].

**UI-054** [D] Il buffer dell'oscilloscopio lo scrive il thread audio (anello di almeno 1024 campioni `int16_t`, indice di scrittura atomico); la UI lo legge senza lock e accetta di vedere ogni tanto un campione strappato. React si ridisegna a 30 fps (§12.5).

### 5.2 Chord

**UI-055** [O] Testata (§4.1) e nome dell'accordo nel riquadro **x 0..127, righe 32..127** [O QS 730, 770]. Al rilascio, dopo la persistenza, resta solo la testata [O LP 1459-1461]. Il riquadro del nome non cambia se la testata è vuota [O QS 754-770].

```
C Major.................Trans+3.   righe 0..11   (1 carattere = 4×4 px)
................................
#########.....###...#####.######   righe 32..80: apici M e 7
##.....##....#.#.#..##.##.....##
##..........######..##.#.#...##.
##...####....#.#.#..##...#..##..
##.....##....#.#.#..............   riga 96: fine del ♯
#########.......................   la G arriva alla riga 127
```

### 5.3 Keyboard

**UI-056** [O] Testata e tastiera in basso, senza nome [O QS 2, 7]. L'altezza della tastiera non è misurata: default `yt = 56`, cioè tastiera alle righe 56..127 [V V-UI-05].

### 5.4 Chord & Keyboard

**UI-057** [O] Testata, nome nel riquadro **x 0..127, righe 17..71**, tastiera con `yt = 74` (righe 74..127) [O QSb TZyPDD6IKSw 10.5-12; ±3 px]. Niente banda delle note [D]. Nella lista View si chiama «Chord + Keyboard» [O QS] (nel manuale «Chord & Keyboard» [M]).

### 5.5 Notes

**UI-058** [V] Il manuale dice «nome ed elenco delle note» [M]; non esiste un fotogramma. Default [V V-UI-04]:
- testata alle righe 0..11;
- nome nel riquadro x 0..127, righe 17..64;
- banda accesa alle righe 72..127 con le `sounding_notes` **spenti**, scritte con `FONT_FIT` alte 36 px (righe 82..117), separate da 6 px, centrate; se non stanno in 120 px si stringono come in UI-035.

### 5.6 Geek Out

**UI-059** [O] La vista consigliata per vedere cosa fa il voicing [M]. Righe dall'alto [O LP 1220, 1450-1453; GR 176-195; QS 960-1111]:

| Righe | Contenuto |
|---|---|
| 0..11 | testata |
| 18..54 | nome (con la tonalità); **2..52** senza tonalità |
| 59..76 | banda delle note (§4.4) |
| 77 | separatore spento |
| 78..127 | tastiera con `yt = 78` (neri alle righe 79..107) |

A riposo restano solo testata, banda vuota e tastiera [O QS 960].

```
C Major.........................   0..11
.....#######......#....#........   18..54 nome
....##.....##.....#..#####......
....##.........######..#........
################################   59..76 banda
##.G##C##Eb#####################      (testo spento)
................................   77 separatore
###.##.####.##.##.####.##.##.###   78..127 neri spenti 79..107
#######.#######.#######.#######.
#:::.####.####.####.:::.####.###   suonano = retino
#.#.#..#.#.#.#.#..#.#.#.#.#..###   marker in tonalità 122..125
```

---

## 6. Overlay

Gli overlay sono schermate temporanee a **tutto schermo** che coprono la vista quando si gira o si preme un encoder.

### 6.1 Schema comune

**UI-060** [M] Schema numero + etichetta [M MAN; O QS]:
- **numero grande** con `FONT_FIT` alle righe **1..108**;
- **etichetta** centrata con `FONT_SMALL`, cap alle righe **114..124**.

**UI-061** [O] Impaginazione del numero, `n` = numero di caratteri:
- di norma 2 cifre con lo zero davanti («04», «07»); 3 se servono [M MAN; O QS];
- celle uguali: `c = (128 − 2·(n − 1)) / n`, carattere `i` a `x = i·(c + 2)`;
- 2 cifre: x 0..62 e 65..127; 3 cifre: circa x 0..42, 44..84, 86..125 [O QS 738, 863].

**UI-062** [O] Valore zero dei parametri che a zero si spengono: al posto di «00» compare la parola **«OFF»** (O x 1..41, F x 43..84, F x 90..116) [O QS 662.5, 754]. Vale per gli effetti, la quantità di Perform e il transpose. Per i volumi a zero il default è «00» [V V-UI-11].

**UI-063** [M] **Funzioni secondarie** (quelle che si ottengono premendo e girando: Transpose, Beat Volume, Bass Volume): l'etichetta sta in una **barra piena alle righe 111..126**, x 0..127, con il testo in negativo [M figure trans/bpm; O QS 754; D per Bass Volume].

**UI-064** [M] **Volumi** (Volume, Bass Volume, Beat Volume): numero 0–99 ed etichetta, più un riempimento di livello in **XOR** dietro il numero, così le cifre si invertono dove si sovrappongono [M figura «Volume»]. Default della geometria: rettangolo da x 0 a `round(v · 128 / 99) − 1`, righe 0..109 [V V-UI-08]. Per Beat Volume si presume lo stesso [D].

```
.######....######.
##....##..##....##     righe 1..108
##....##........##     (cifre adattate alla cella)
##....##......###.
.######...########
..................
.....Volume.......     righe 114..124
```

### 6.2 Tabella degli overlay

**UI-065** I contenuti degli overlay sono questi. Le gamme dei valori e gli elenchi dei nomi sono delle sezioni 10 e 20.

| Gesto | Numero | Etichetta | Note | Fonte |
|---|---|---|---|---|
| Volume, ruotare | 00–99 | «Volume» | riempimento XOR | [M] |
| Volume, premere e ruotare | 00–99 | «Bass Volume» in barra | riempimento XOR | [M MAN] |
| Volume, premere | — | — | schermata batteria (§9.2) | [M] |
| Sound, ruotare | «07»; Sound utente «U05» | «Sound» | | [O QS] |
| Perform, ruotare | quantità o numero del pattern; 0 → «OFF» | nome breve del modo | etichette in UI-066 | [O QS 444-520, AMA] |
| Perform, ruotare (Arpeggiate) | due righe | «Arpeggiate» | §6.3 | [O QS 452, 486, 659.5] |
| FX, ruotare | 01–10; 0 → «OFF» | nome dell'effetto principale | «04 Reverb», «OFF Chorus» | [O QS 653-664] |
| Key, ruotare | lettera della tonalità | «Key» | §6.4 | [O GR 186-192, QS 700] |
| Key, premere | tonalità oppure «Off» | «Key» | default `[V]` V-UI-09 | [M; V] |
| Key, premere e ruotare | «+3», «-2»; 0 → «OFF» | «Transpose» in barra | formato `[V]` V-UI-10 | [O QS 754] |
| BPM, ruotare | «96», «117» | «BPM» | testo dell'etichetta `[V]` V-UI-09 | [O QS 863] |
| BPM, premere e ruotare | 00–99 | «Beat Volume» in barra | riempimento XOR | [M] |
| Bass, ruotare | «03» | «Bass Sound» | | [O QS 810-842] |
| Bass, premere | acceso: «03» / spento: «OFF» | «Bass Sound» / «Bass» | default `[V]` V-UI-09 | [V] |
| Chord Voicing, ruotare | **sempre 3 cifre**, «032» | «Voicing» | | [O QS 738] |
| Bass Voicing, ruotare | «07» | «Bass Voicing» | | [O QS 810-842] |
| Chord Voicing, premere | «Split» / «Octave» | «Single Notes» | parola con `FONT_FIT`, righe 1..108; default `[V]` V-UI-07 | [V] |
| Perform o FX, tenere premuto (Lock) | **nessun overlay** | — | si accende solo il LED | [O QS 653-683] |
| BPM, premere (Beat o metronomo) | nessun overlay | — | default `[V]` V-UI-09 | [V] |
| count-in del looper | «04» … «01», righe 2..109 | «Counting in», righe 116..126 | §8 | [O LP 1398; QS] |

**UI-066** [O] Etichette brevi dei modi di Perform negli overlay: «Strum», «Strum 2 Oct», «Slop», «Arpeggiate», «Pattern», «Harp» [O QS 444-520, AMA]. «Arp 2 Oct» per Arpeggiate 2 Octaves e l'etichetta di Perform a zero («OFF» + nome del modo) sono `[V]` (V-UI-25).

### 6.3 Overlay di Arpeggiate

**UI-067** [O] Due righe con `FONT_FIT`, ognuna adattata alla larghezza [O QS 452, 486, 659.5]:
- riga 1, la velocità: «16» o «08», righe 0..53;
- riga 2, la direzione: «UP», «DOWN», «UP/DOWN», righe 55..110;
- etichetta «Arpeggiate» con `FONT_SMALL`, righe 114..127 (comprese le discendenti di p e g), circa x 30..98.

### 6.4 Overlay di Key

**UI-068** [O] Impaginazione [O GR VmaFJIkYsNs 186-192; QS 700]:
- **maggiore senza alterazione**: la lettera a tutta larghezza, x 0..127, righe 2..102 [O QS 700 «C»];
- **con alterazione o minore**: fondamentale x 0..62, righe 2..102; colonna destra divisa: alterazione in alto (x 64..125, righe 2..48), «m» in basso (righe 54..102). Una tonalità minore senza alterazione lascia vuota la parte alta, una maggiore con alterazione la parte bassa [D];
- **Key Off**: la parola «Off» con `FONT_FIT`, righe 2..102 [M dal 3.90; impaginazione D];
- etichetta «Key», righe 114..124, x 53..80.

Garden Report mostra anche un «F♭», che il recensore segnala come errore [O GR 324]: l'elenco delle tonalità valide è della sezione 10.

```
######......#.#.....   righe 2..48: ♯
##.........######...
#####.......#.#.....
##..................   righe 54..102: m
##.........###.##...
##.........#.##.#...
.......Key..........   114..124
```

### 6.5 Tempi

**UI-069** [V] Un overlay resta a schermo **3400 ms** dall'ultima azione che lo ha aggiornato [D da QS; V V-UI-01]. Ogni nuova rotazione dello stesso encoder riparte da zero.

**UI-070** [D] Un overlay nuovo sostituisce subito quello vecchio, anche se di un altro encoder. Alla scadenza si torna alla schermata sotto (vista, looper, lista o menu). Il tasto B della Flip chiude subito l'overlay (§14).

---

## 7. Liste e menu

### 7.1 Widget lista

**UI-071** [M] Geometria, misurata sulla figura 1 bit del manuale [M fig. «quant» bl-XmlINMmhrh; O QS 937-1136, LP]:
- **5 righe da 24 px**; la riga `i` (0..4) ha la cap alle righe `24·i + 6 .. 24·i + 16` (cap a 6, 30, 54, 78, 102) e le discendenti fino a `+3`;
- la voce selezionata è **sempre nella riga centrale**: barra piena alle righe **48..71**, x **0..126** (la colonna 127 resta spenta), testo in negativo;
- testo con `FONT_SMALL` a **x = 4**;
- la lista scorre sotto la barra; agli estremi le righe senza voce restano vuote, così la prima voce può stare al centro.

```
................................   0..5
.Exit...........................   cap 6..16
................................
.Battery........................   cap 30..40
###############################.   48..71 barra
#.View##########################   testo in negativo
###############################.
.Audio Output...................   cap 78..88
.MIDI Channels..................   cap 102..112
```

**UI-072** [O] Marcatori a destra:
- **valori** allineati a destra con il bordo a x = 124 [O];
- **spunta ✓** sulla scelta corrente, allineata a destra a x = 124; dentro la barra è spenta [O];
- **pallino ●** pieno di circa 11 px, x 114..124, allineato alle cap, sul modo Perform attivo [O QS 444-520];
- Arpeggiate mostra l'indice del tipo al posto del pallino: «Arpeggiate 03» [O QS 444-520].

**UI-073** [M] Struttura: la radice di ogni lista ha **«Exit»** in cima, ogni sottomenu ha **«Back»** in cima [O QS 937-1136]. La lista NON DEVE ricominciare dall'inizio dopo l'ultima voce [D; V V-UI-23].

**UI-074** [D] Rotazione e pressione: girando in senso orario (+1) la selezione scende alla voce successiva. Premere sceglie: entra in un sottomenu, applica una scelta (la ✓ si sposta subito) oppure, su Exit e Back, risale di un livello. Una scelta applicata lascia la lista aperta, salvo dove indicato.

**UI-075** [V] Voci numeriche (per esempio Volumes > Master): premere entra in modifica, il valore a destra lampeggia (500 ms acceso, 250 spento), girando cambia, premendo di nuovo si conferma [V V-UI-16].

**UI-076** [V] Chiusura:
- Exit o Back alla radice;
- **liste aperte da un encoder** (Sound, Perform, FX, Bass, Beats, Save): dopo **10 s** senza azioni [V V-UI-16];
- **Options**: nessun timeout [V V-UI-16];
- girare o premere un **altro** encoder chiude la lista o il menu ed esegue l'azione di quell'encoder [V V-UI-16];
- il tasto B della Flip equivale a Back (§14).

Il manuale dice che si esce anche «ripremendo Options» [M]; dato che premere Options conferma la voce selezionata, il conflitto resta aperto (V-UI-16) e per ora vale la conferma.

### 7.2 Liste degli encoder

**UI-077** I contenuti di queste liste sono:

| Lista | Si apre con | Voci | Marcatore | Fonte |
|---|---|---|---|---|
| Sound | premere Sound | Exit, «01 Orchid EP» … «70 …», poi «U01» … «U30» (solo gli slot occupati) | ✓ sul suono attivo | [O QS, LP; M FW 3.60] |
| Perform | premere Perform | Exit, Strum, Strum 2 Octaves, Slop, Arpeggiate, Arp 2 Octaves, Pattern, Harp | ● sul modo attivo; indice per Arpeggiate | [O QS 444-520] |
| FX | premere FX | Exit, poi gli slot del suono (Reverb, FX1, FX2, Filter) con il nome dell'effetto e il valore a destra («Off» o 1–10) | valore | [O QS 653-664] |
| Bass | tenere Bass 1 s | Exit, Chords Only, Unison, Bass Single Notes, Solo | ✓ | [M MAN; O QS 810-842, LP 1356] |
| Beats | tenere BPM 1 s | Exit, 2/4, 3/4, 4/4, 6/8, poi i Beat «01 Nome» … | ✓ | [M MAN; impaginazione V V-UI-20] |
| Save Sound | tenere Sound | Exit, Save, Save As, Delete | — | [M MAN; V V-UI-13] |
| Save Loop | tenere Loop 2 s | Exit, Save As Loop XX, Save As, Load Loop, Delete Loop | — | [M MAN; V V-UI-12] |

- Nella lista Sound i nomi sono in maiuscole e minuscole («NN Nome»); quelli di fabbrica sono nella sezione 20.
- Nella lista Perform, dopo la scelta di un modo, girare regola il suo parametro con l'overlay di §6.2 [M MAN].
- Nella lista FX, premendo una voce e girando si regola la sua intensità [M MAN].
- Le voci di Bass sono quelle del manuale 3.90; nel 3.04 erano «With chords only, Unison, Bass single notes, Solo» [O QS]. Maiuscole esatte `[V]` (V-UI-20).

**UI-078** [V] Save As (Sound e Loop) apre una seconda lista di slot: «U01» … «U30» oppure «Loop 01» … «Loop 10», con ● sugli slot occupati; salvare su uno slot occupato lo sovrascrive [M MAN]. Dopo un salvataggio compare la conferma «Saved» con lo slot sotto come etichetta («U05», «Loop 03»), per la durata di un overlay [V V-UI-12, V-UI-13].

### 7.3 Menu Options

**UI-079** [M] Albero del menu Options del firmware 3.90 e successivi [M MAN, supporto]. Profondità massima 3 livelli.

```
Options                         (radice: Exit in cima)
├─ Exit
├─ System
│  ├─ Back
│  ├─ View              Back / React / Chord / Keyboard / Chord + Keyboard / Notes / Geek Out   (✓)
│  ├─ Battery           → schermata batteria (§9.2)
│  ├─ Auto Power Off    Back / 10 min / 30 min / Never   (✓)
│  └─ Version           → schermata versione (§9.5)
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
- Audio Output agisce su altoparlante e jack della Flip (sezione 50);
- Auto Power Off, alla scadenza, salva lo stato e chiude l'app tornando a spruceOS; non scatta durante la carica [M per la regola della carica; D per la chiusura].

**UI-081** [D] «Upgrade Firmware» NON DEVE comparire sulla Flip: l'aggiornamento di Stame passa da spruceOS. Le schermate «Ready for Firmware» e «Select USB Mode / Enable USB MIDI» dell'originale [M MAN] non si replicano, perché la Flip non fa da dispositivo USB MIDI.

---

## 8. Looper

Il comportamento del looper (stati, battute, overdub, undo, salvataggio) è nella sezione 10. Qui c'è la sua schermata, che **sostituisce la vista** finché il looper è attivo.

### 8.1 Anello

**UI-082** [O] Anello spesso 17 px lungo i quattro lati [O LP 1338-1406; QS 851-934]:
- righe 1..17 e 111..127, colonne 1..16 e 111..127; riga 0 e colonna 0 spente;
- interno libero: x 17..110, righe 18..110;
- angoli esterni arrotondati con raggio circa 12; angoli interni quasi vivi.

**UI-083** [O] **Fessure delle battute**: con N battute, N fessure radiali larghe 2–3 px agli angoli `k · 360° / N`, a partire da ore 12 e in senso orario. Con 8 battute ci sono anche le diagonali degli angoli. In Free l'anello è continuo [O LP; QS].

**UI-084** [O] **Progresso**: la parte già suonata è piena, il resto è a scacchiera di 1 px (UI-014). Il riempimento avanza in senso orario da ore 12 e riparte da zero a ogni giro [O QS 870-934; LP 1338-1406].

**UI-085** [D] Algoritmo dell'anello, con una tabella degli angoli calcolata una volta all'avvio (127 × 127 valori `uint16_t`, circa 32 KB; si può anche generare alla compilazione):

```
centro c = (63.5, 63.5)
ang(x,y) = atan2(x − 63.5, 63.5 − y) portato in [0, 65536)     // 0 = ore 12, senso orario
per ogni (x,y) nella maschera dell'anello:
    fessura = esiste k < N tale che
              |proiezione perpendicolare di (x,y) − c sulla semiretta a k·65536/N| ≤ 1.0
              e il punto sta dalla parte della semiretta
    se fessura:                 spento
    altrimenti se ang(x,y) < progresso:  acceso                 // progresso 0..65535
    altrimenti:                 acceso se ((x + y) & 1) == 0    // scacchiera
```

**UI-086** [V] Registrazione in Free: finché il loop non è chiuso la lunghezza non si conosce; default: anello tutto a scacchiera, che si riempie dal primo giro dopo la chiusura [V V-UI-21].

### 8.2 Waiting Room

**UI-087** [O] Si entra premendo o girando Loop [M MAN]. Anello (con le fessure della scelta selezionata, UI-083) e, al centro, la lista **Exit / Free / 1 Bar / 2 Bars / 4 Bars / 8 Bars / 16 Bars** [O QS 851-870].
- Barra di selezione larga x 20..105, alta 24 px [O; bordo destro 105–107].
- Tre righe visibili: righe 26..49, 50..73, 74..97, con la selezione fissa al centro (50..73) e il testo centrato [D; V V-UI-21].

### 8.3 Menu a tre voci

**UI-088** [O] Durante registrazione e riproduzione l'interno dell'anello mostra un menu di tre voci alle righe 26..49, 50..73 e 74..97, testo centrato con `FONT_SMALL`. Qui la barra **si sposta** sulla voce selezionata (non è fissa al centro) [O QS 870-934; LP 1338-1406].

| Stato del looper (sezione 10) | Voci | Fonte |
|---|---|---|
| registrazione | Rec / Play / Back (Rec selezionato) | [O QS] |
| riproduzione dopo la registrazione | Overdub / Pause / Clear | [O QS, LP] |
| overdub | Stop / Play / Clear | [O QS] |
| riproduzione dopo un overdub | Overdub / Pause / Undo | [O QS] |
| riproduzione dopo un undo | Overdub / Pause / Clear | [O QS] |
| pausa | Overdub / Play / Clear | [V V-UI-26] |

**UI-089** [O] Count-in: overlay «04» … «01» a tutta larghezza alle righe 2..109, con «Counting in» centrato alle righe 116..126 [O LP 1398; QS]. In un tempo diverso da 4/4 il conto parte dal numero di movimenti della battuta («03» in 3/4) [V V-UI-27].

**UI-090** [V] Con il looper attivo i nomi degli accordi suonati non si vedono; gli overlay degli encoder (Volume, Sound…) compaiono sopra la schermata del looper [V V-UI-21].

---

## 9. Altre schermate

### 9.1 Avvio

**UI-091** [O] Logo per circa 4 s, poi la schermata di gioco [O QS 112-118]. Stame NON DEVE usare il logo né il marchio di Telepathic Instruments: serve un logo proprio, monocromo, in una bitmap 1 bit da 128×128 [D].

**UI-092** [D] Sulla Flip il logo copre l'inizializzazione di audio e MIDI. Resta al massimo 4 s; finita l'inizializzazione, un tasto qualsiasi lo salta. Sull'Orchid toccare i tasti durante il logo può creare problemi [O supporto], sulla Flip no.

**UI-093** [M] Se il transpose salvato è diverso da zero, dopo l'avvio compare in testata (UI-031) [M FW 3.04].

### 9.2 Batteria

**UI-094** [O] Premendo Volume compare la sagoma della pila con la barra di carica (dal 3.32) e, senza caricatore, la scritta «No cable detected» [O QS 168-172, 940; M MAN]. Geometria di default [V V-UI-14]:
- pila: contorno arrotondato (raggio 3) x 24..99, righe 28..68; polo x 100..103, righe 42..54;
- barra interna: x 28 .. `28 + round(68 · pct / 100) − 1`, righe 32..64;
- percentuale «NN%» con `FONT_HEAD`, centrata, cap alle righe 80..88;
- «No cable detected» oppure «Charging» con `FONT_SMALL`, centrata, cap alle righe 104..114.

La schermata dura quanto un overlay (UI-069).

**UI-095** [V] Batteria bassa: avviso al 10% [M MAN] con la schermata di UI-094 e la scritta «Low Battery» al posto di «No cable detected», per la durata di un overlay; si ripete al 5% [V V-UI-14]. Sulla Flip, al livello critico, Stame salva lo stato prima che spruceOS spenga la console (sezione 50).

### 9.3 Scelta rapida della tonalità

**UI-096** [M] Tenendo premuto Key compare la richiesta «select key»; si preme la tonica sulla tastiera, tenendo il tipo **Min** per la minore (dal 3.84; dal 3.90 senza ottava nel prompt) [M MAN, FW]. Impaginazione di default: «Select Key» con `FONT_SMALL`, centrata, cap alle righe 58..68 [V V-UI-15]. La richiesta resta finché non si preme un tasto, finché non scade la durata di un overlay o finché non si tocca un altro encoder; dopo la scelta compare l'overlay Key (UI-068) [V V-UI-15].

### 9.4 Batteria da suonare

**UI-097** [O] Bass Voicing tenuto + BPM attiva la batteria da suonare sulla tastiera [O, guida corretta il 13/10/2026; comportamento nella sezione 10]. Sullo schermo, default: overlay «Drums» con `FONT_FIT` e l'etichetta «On» / «Off» [V V-UI-09].

### 9.5 Versione

**UI-098** [D] System > Version mostra «Stame» con `FONT_HEAD` e la versione («1.0.0») con `FONT_SMALL`, centrati, finché non si preme o gira Options.

### 9.6 Salvaspazio schermo

**UI-099** [V] L'Orchid non ha uno screensaver documentato; l'occhio in pixel art delle foto ufficiali potrebbe essere solo marketing [O INT; D]. Stame NON DEVE avere uno screensaver [V V-UI-24].

---

## 10. Gesti

### 10.1 Controlli dell'originale

L'Orchid ha 9 encoder infiniti e premibili (Sound, Perform, FX, Key, Bass, Loop, BPM, Volume, Options) e 2 manopole di voicing (Chord Voicing premibile, Bass Voicing premibile e usato come modificatore). Non c'è un tasto SHIFT [M MAN].

```c
typedef enum {
    ENC_SOUND, ENC_PERFORM, ENC_FX, ENC_KEY, ENC_BASS, ENC_LOOP,
    ENC_BPM, ENC_VOLUME, ENC_OPTIONS, ENC_CHORD_VOICING, ENC_BASS_VOICING,
    ENC_COUNT   /* 11 */
} ui_enc_t;
```

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

**UI-102** Soglie della pressione lunga:

| Encoder | Soglia | Fonte |
|---|---|---|
| BPM | 1000 ms | [M] |
| Bass | 1000 ms | [M] |
| Loop | 2000 ms | [M] |
| Perform, FX (Lock) | 1000 ms | [V V-UI-03] (osservato 1–2 s, QS 671-683) |
| Sound (Save) | 1000 ms | [V V-UI-03] |
| Key (scelta rapida) | 1000 ms | [V V-UI-03] |

**UI-103** [D] Riconoscimento dei gesti, uguale per tutti gli encoder e indipendente dalla sorgente (MPK, tasti della Flip, un futuro encoder vero). Ingressi: `ENC_DOWN(k)`, `ENC_UP(k)`, `ENC_ROT(k, d)` con `d` in scatti logici (la conversione da CC relativi è nella sezione 40), più `tick(now_ms)`.

```
per ogni encoder k:  stato IDLE | DOWN { t0, rotated, long_fired }

ENC_DOWN(k):  s = DOWN { t0 = now, rotated = false, long_fired = false }
              emit PRESS_START(k)                       // serve ai modificatori (UI-104)
ENC_ROT(k,d): se s == DOWN e !long_fired e has_press_turn(k):
                  rotated = true ; emit PRESS_ROT(k, d)  // funzione secondaria
              altrimenti se s == DOWN e !long_fired:
                  rotated = true ; emit ROT(k, d)        // nessuna funzione secondaria: vale come rotazione
              altrimenti:
                  emit ROT(k, d)                         // anche dopo LONG: va alla lista appena aperta
tick(now):    se s == DOWN e !rotated e !long_fired e has_long(k) e now − t0 ≥ T_long[k]:
                  long_fired = true ; emit LONG(k)       // scatta mentre si tiene premuto
ENC_UP(k):    se s == DOWN e !rotated e !long_fired: emit TAP(k)
              emit PRESS_END(k) ; s = IDLE
```

- Il tap scatta **al rilascio**, così Key premuto e girato fa il transpose senza cambiare la Key mode [D da M MAN].
- La pressione lunga scatta **alla soglia**, senza aspettare il rilascio [O QS 653-683, il LED del Lock si accende con il tasto ancora premuto].
- Un encoder senza pressione lunga dà sempre un tap, qualunque sia la durata.

**UI-104** [M] Combinazioni con Bass Voicing tenuto (il «Shift» nascosto del changelog [M FW 3.84]):

| Combinazione | Effetto | Fonte |
|---|---|---|
| Bass Voicing tenuto + tap Loop | **uscita forzata** dal looper (perde il loop non salvato) | [M MAN, FW 3.84] |
| Bass Voicing tenuto + tap BPM | batteria da suonare (§9.4) | [O] |
| Bass Voicing tenuto + tap Bass | basso on/off | [O] |

Con Bass Voicing tenuto il tap dell'altro encoder NON DEVE eseguire la sua funzione normale.

**UI-105** [M] Altre combinazioni:
- durante la scelta rapida della tonalità (UI-096), un tasto della tastiera imposta la tonica e il tipo **Min** tenuto la rende minore [M MAN];
- Power tenuto 1 s (on/off), Power 10 s (riavvio forzato) e accensione con Bass premuto (bootloader) [M] **non** si replicano: sulla Flip li gestisce spruceOS [D].

---

## 11. LED e indicatori

**UI-106** [O] LED dell'originale, bianchi e piccoli, in alto a destra del loro encoder [O QS 653-683; QSb zOk7zvm69Ec 30-33; LP 1441-1461]:

| LED | Acceso quando | Fonte |
|---|---|---|
| Key | Key mode attiva | [M; O] |
| Bass | basso attivo | [O] |
| Perform | Lock di Perform | [M; O] |
| FX | Lock di FX | [M; O] |
| vicino a Volume | alimentazione e batteria; lampeggia sempre più in fretta mentre la batteria scende | [M MAN] |

Sono monocolore [D].

**UI-107** [V] Lampeggio del LED di Volume: fisso sopra il 25%; sotto, periodo che scende in modo lineare da 1600 ms (al 25%) a 200 ms (al 5% e sotto), con il 50% di tempo acceso [V V-UI-22].

**UI-108** [D] Sulla Flip i LED si disegnano sul pannello virtuale (§13.3) come pallini di 6×6 px, colore del pixel OLED acceso, in alto a destra della manopola. Se il pannello è nascosto, i LED accesi si elencano nella barra di stato. Quando i LED del trasporto della MPK si possono comandare (verifica della sezione 40), DOVREBBERO riprendere i LED dell'originale secondo la tabella di §14.2.

---

## 12. Macchina a stati e aggiornamento dello schermo

### 12.1 Stati

**UI-109** [D] La UI ha uno **stato di base** e una **pila di livelli** sopra. Si disegna la base, poi i livelli dal basso verso l'alto; ogni livello copre tutto lo schermo.

| Livello | Stati | Esce con |
|---|---|---|
| base | `BOOT` → `PLAY(view)` oppure `LOOPER(sub)` | — |
| 1 | `LIST(owner, items, sel)`, `OPTIONS(stack)` | Exit/Back, timeout, altro encoder (UI-076) |
| 2 | `PROMPT_KEY` (scelta rapida), `CONFIRM` (salvato) | tasto della tastiera, timeout |
| 3 | `OVERLAY(kind, value, expire_ms)`, `BATTERY` | timeout (UI-069), B della Flip |
| 4 | `WARN_LOWBATT` | timeout |
| 5 | `PLATFORM_MENU` (solo Flip, §13.6) | MENU o Back |

`LOOPER(sub)` ha i sottostati `WAITING_ROOM`, `COUNT_IN`, `REC`, `PLAY`, `OVERDUB`, `PAUSE`, copiati dallo stato del looper di `core` (sezione 10): la UI non li decide, li mostra.

### 12.2 Transizioni principali

```
BOOT        --init finita e (4 s trascorsi o tasto)-->  PLAY(view salvata)
PLAY        --core.looper != IDLE-->                     LOOPER(core.looper)
LOOPER      --core.looper == IDLE (Exit, uscita forzata)--> PLAY
qualsiasi   --ROT/PRESS_ROT/TAP che ha un overlay-->     push/sostituisci OVERLAY
qualsiasi   --TAP(SOUND|PERFORM|FX)-->                   apri LIST(owner)
qualsiasi   --LONG(BASS|BPM|SOUND|LOOP)-->               apri LIST(owner)
qualsiasi   --LONG(KEY)-->                               PROMPT_KEY
qualsiasi   --LONG(PERFORM|FX)-->                        cambia il Lock (nessun livello nuovo)
PLAY/LOOPER --TAP(OPTIONS)-->                            OPTIONS(radice)
LIST/OPTIONS --evento di un encoder diverso dal proprietario--> chiudi, poi esegui l'evento
OVERLAY     --now ≥ expire_ms-->                         pop
batteria ≤ 10% (una volta) e ≤ 5% (una volta) -->        WARN_LOWBATT
MENU (Flip) -->                                          PLATFORM_MENU  (le note continuano a suonare)
```

**UI-110** [D] Gli eventi musicali (tasti, pad degli accordi, pedale) NON DEVONO passare dalla macchina a stati della UI: vanno direttamente a `core` e suonano in qualunque stato, anche con un menu aperto. La UI ne vede solo l'effetto attraverso `ui_model_t`.

**UI-111** [D] Lo stato da salvare tra un avvio e l'altro comprende vista, tema e opzioni della piattaforma (§13). Overlay, liste aperte e selezioni non si salvano.

### 12.3 Timer

**UI-112** [D] Tutti i tempi della UI (overlay, persistenza, pressioni lunghe, timeout delle liste, lampeggi) si calcolano su `now_ms` passato da fuori. `core/ui` DEVE esporre `ui_next_deadline_ms()`, cioè il primo istante in cui qualcosa cambierà a schermo, così la piattaforma può dormire fino ad allora.

### 12.4 Thread

**UI-113** [D] Sulla Flip la UI gira nel **thread principale** (quello di SDL), separato dal thread audio e da quello che legge il MIDI:
- MIDI e tasti → coda di eventi senza lock → `core` / `core/ui`;
- `core` → istantanea `ui_model_t` con doppio buffer e indice atomico (il lettore non blocca mai lo scrittore);
- thread audio → anello dell'oscilloscopio (UI-054).

La disposizione dei thread e la proprietà di `core` sono della sezione 50.

### 12.5 Frequenza di aggiornamento

**UI-114** [O] Sull'Orchid si vedono aggiornamenti parziali a bande (tearing) [O QS 964, 1073; GR 187]; ne si deduce circa 30 fps con scrittura per pagine [D]. Stame NON DEVE simulare il tearing [D].

**UI-115** [D] Regole di aggiornamento:
- il framebuffer si ridisegna **solo quando cambia** il modello o scade un timer (`dirty`); a riposo la UI non consuma CPU (sulla Flip, ridisegnare solo quando serve ha portato un'app simile dal 17% al 2,5% di CPU [O nota Flip]);
- le schermate animate (React, anello del looper in moto, LED che lampeggiano) si ridisegnano a **30 fps**;
- la presentazione sulla Flip segue il vsync a 60 Hz;
- latenza dall'azione allo schermo: al massimo 50 ms (obiettivo: un fotogramma più il tempo di disegno) [D].

---

## 13. Resa sulla Flip

### 13.1 Schermo

**UI-116** [O] Lo schermo della Miyoo Flip è **640×480**. Le app native aprono una finestra KMSDRM a schermo intero con dimensione logica 640×480 (`SDL_RenderSetLogicalSize(640, 480)`) [O nota Flip].

**UI-117** [D] Il 128×128 DEVE essere ingrandito di un fattore **intero ×3** (384×384) con nearest-neighbour, senza filtri (`SDL_HINT_RENDER_SCALE_QUALITY = "0"`), e posizionato con l'origine a **(128, 48)**: margini di 128 px a sinistra e a destra, 48 px sopra e sotto. ×4 (512 px) non sta nei 480 px di altezza. Se la risoluzione fisica non fosse 640×480, la piattaforma DEVE comunque garantire un fattore intero in pixel fisici (`SDL_RenderSetIntegerScale`).

**UI-118** [D] Percorso di disegno: framebuffer 1 bit → texture 128×128 in streaming, aggiornata solo se `dirty` → copia nel rettangolo (128, 48, 384, 384). Il pannello ha una sua texture, ridisegnata solo quando cambia.

### 13.2 Colore dell'OLED simulato

**UI-119** [O] Il pixel acceso dell'Orchid è bianco freddo; l'azzurrino dei video è il bilanciamento della videocamera [O foto ufficiali, GR; D]. Colori di Stame:

| Nome | Acceso | Note |
|---|---|---|
| Cold White | `#E8F0FF` | **default** [D dalla nota] |
| White | `#FFFFFF` | |
| Video Blue | `#BFE3FF` | come appare nei video |
| Amber | `#FFB000` | |
| Green | `#33FF66` | |

Il pixel spento è sempre `#000000`.

**UI-120** [D] Opzione «Pixel Grid», spenta di default: ogni pixel ingrandito diventa 2×2 acceso più una riga e una colonna di 1 px spente, per imitare la trama del pannello. L'Orchid non ha regolazione di luminosità [O]; Stame non ne aggiunge, quella della console resta a spruceOS.

### 13.3 Disposizione dello schermo

**UI-121** [D] Zone dello schermo 640×480:

| Zona | Rettangolo (x, y, w, h) | Contenuto |
|---|---|---|
| barra di stato | 0, 0, 640, 48 | stato della MPK, attività MIDI, batteria della Flip (§13.4) |
| colonna sinistra | 0, 48, 128, 384 | 4 manopole: **Sound, Perform, FX, Key** (96 px ciascuna) |
| OLED | 128, 48, 384, 384 | il 128×128 ×3 |
| colonna destra | 512, 48, 128, 384 | 4 manopole: **Bass, Loop, BPM, Volume** |
| banda inferiore | 0, 432, 640, 48 | a sinistra Options (128 px); al centro gli 8 tasti degli accordi (8 × 48 px, sotto l'OLED); a destra Chord Voicing e Bass Voicing (128 px) |

L'ordine riprende l'originale: Sound, Perform e FX in fila a sinistra, il display tra Key e Bass [O QSb TZyPDD6IKSw; M MAN §13.1].

**UI-122** [D] Il pannello si disegna con lo stesso `gfx` su un framebuffer a 1 bit di **320×240**, ingrandito ×2 e colorato con i colori del tema; LED, evidenziazione del fuoco e cappucci colorati si aggiungono sopra come rettangoli pieni. Il testo del pannello usa `FONT_SMALL` (che ×2 diventa cap 22 px). In coordinate del pannello l'OLED occupa (64, 24, 192, 192).

**UI-123** [D] Ogni cella di manopola (128×96) contiene:
- la manopola, un cerchio di 48 px di diametro con il colore del cappuccio dell'originale: **giallo** Sound, Perform, FX; **nero** Key; **rosso-arancio** Bass; nero gli altri; **fumé** i due voicing [O guida §16.1];
- una tacca che gira di 15° a ogni scatto (gli encoder sono infiniti, la tacca non indica un valore);
- la manopola disegnata «affondata» (anello interno più scuro) mentre è premuta;
- il LED (UI-108) in alto a destra;
- il nome sotto, con `FONT_SMALL` ×2;
- in piccolo, il controllo della MPK che la comanda («K3 · B3»), se l'opzione «Legends» è attiva (default: attiva).

I valori dei parametri NON DEVONO comparire sul pannello: sull'Orchid si vedono solo negli overlay.

**UI-124** [D] Gli 8 tasti degli accordi nella banda inferiore, nell'ordine **Dim, Min, Maj, Sus, 6, m7, M7, 9**, sono celle 48×48 con il nome; una cella si inverte mentre il tasto corrispondente (pad della MPK) è premuto.

**UI-125** [D] Il pannello si può nascondere (opzione «Panel: Off»): restano l'OLED e la barra di stato, il resto è nero.

### 13.4 Barra di stato e stato della MPK

**UI-126** [D] La barra di stato mostra, con `FONT_SMALL` ×2:
- a sinistra: «MPK» con lo stato: «ready» (collegata e aperta), «no MPK» (nessuna tastiera trovata, lampeggia ogni secondo), «error» (porta aperta ma muta o in errore);
- accanto, due pallini di attività: MIDI in dalla MPK e MIDI out verso il DIN, accesi 50 ms a ogni messaggio;
- a destra: batteria della Flip in percentuale, con una saetta durante la carica;
- se il pannello è nascosto: il nome dell'encoder con il fuoco (§14.3) e i LED accesi.

Le informazioni della piattaforma NON DEVONO mai comparire dentro il 128×128, tranne nel menu della piattaforma (§13.6).

**UI-127** [D] Collegamento e scollegamento della MPK a caldo: la UI lo segnala solo nella barra di stato. Il riconoscimento della tastiera è della sezione 40.

### 13.5 Temi

**UI-128** [D] Due temi; i colori sono token che la piattaforma legge da una tabella:

| Token | Orchid (default) | Dark |
|---|---|---|
| sfondo del pannello | `#EFEDE6` | `#000000` |
| grafica e testo | `#191919` | `#8A8A8A` |
| accento (fuoco, «ready») | `#22D504` | `#22D504` |
| cornice dell'OLED | `#000000`, 6 px attorno al display | nessuna |
| avviso («no MPK») | `#191919` lampeggiante | `#E0451B` lampeggiante |

I colori del tema Orchid vengono dal pannello e dalle grafiche ufficiali [O]. Il tema riprende il linguaggio visivo dell'originale (pannello crema, grafica nera grottesca, un solo accento verde fluo, display bianco su nero [O INT]) senza logo né marchio.

### 13.6 Menu della piattaforma

**UI-129** [D] Il tasto MENU della Flip apre un menu con lo stesso widget lista (§7.1), disegnato dentro il 128×128. Voci, in inglese come il resto:

```
Back
Theme          Orchid / Dark                                   (✓)
OLED Color     Cold White / White / Video Blue / Amber / Green (✓)
Pixel Grid     Off / On                                        (✓)
Panel          On / Off                                        (✓)
Legends        On / Off                                        (✓)
MPK Status     → schermata: porte aperte, ultimo messaggio ricevuto, programma atteso «STAME»
Quit Stame     → salva lo stato ed esce verso spruceOS
```

Le migliorie musicali (latch, clock in…) non stanno qui: sono nell'appendice delle opzioni, spente di default.

---

## 14. Da dove arrivano le azioni

Questa è la mappa **logica**: azioni della UI → controlli fisici. I numeri di CC, i canali, le porte e i codici evdev sono nella sezione 40. Il programma «STAME» della MPK è descritto lì.

### 14.1 Azioni logiche

**UI-130** [D] La piattaforma traduce ogni controllo in una di queste azioni, uguali per tutte le sorgenti:

| Azione | Significato |
|---|---|
| `ENC_ROT(k, d)` | rotazione dell'encoder `k` di `d` scatti |
| `ENC_DOWN(k)`, `ENC_UP(k)` | pressione e rilascio dell'encoder `k` |
| `NAV(d)` | scorre la lista o il menu aperto (come la rotazione del suo proprietario) |
| `NAV_OK` | pressione del proprietario della lista aperta |
| `NAV_BACK` | Back; senza lista, chiude l'overlay |
| `FOCUS(d)` | sposta il fuoco del pannello (solo Flip) |
| `PLATFORM_MENU` | apre o chiude il menu della piattaforma |

`NAV` senza nessuna lista aperta non fa nulla.

### 14.2 MPK mini Plus

**UI-131** [D] Mappa proposta (le 8 manopole sono gli encoder più usati; i pad del banco B sono le loro pressioni):

| Controllo della MPK | Azione | Note |
|---|---|---|
| K1 … K8 | `ENC_ROT` di Chord Voicing, Bass Voicing, Sound, Perform, FX, Key, BPM, Volume | manopole in modo relativo |
| pad B1 … B8 | `ENC_DOWN` / `ENC_UP` degli stessi 8 encoder | tap, pressione lunga e pad tenuto + manopola = premere e ruotare, come un encoder vero |
| Rec | `ENC_DOWN` / `ENC_UP` di **Loop** | serve anche il rilascio |
| « / » | `ENC_ROT(LOOP, −1 / +1)` | Waiting Room e menu del looper |
| Stop | `ENC_DOWN` / `ENC_UP` di **Options** | |
| Play | `ENC_DOWN` / `ENC_UP` di **Bass** | |
| joystick su / giù | `NAV(−1 / +1)` con ripetizione | qualunque lista aperta, compreso Options |
| joystick sinistra / destra | `ENC_ROT(BASS, −1 / +1)` con ripetizione | suono di basso |
| pad del banco A, tasti, rotelle, pedale | eventi musicali, non UI | sezioni 10 e 40 |

- Combinazioni: B2 (Bass Voicing) tenuto + Rec = uscita forzata dal looper; B2 tenuto + B7 = batteria da suonare; B2 tenuto + Play = basso on/off (UI-104). B6 (Key) tenuto 1 s + un tasto, con il pad Min tenuto per la minore = scelta rapida (UI-096).
- Ripetizione del joystick: primo passo subito, poi dopo 400 ms uno ogni 120 ms [D].
- LED del trasporto, se comandabili: **Rec** acceso in registrazione e overdub, **Play** acceso con il basso attivo (come il LED di Bass), **Stop** acceso con il menu Options aperto.
- Bass, Loop e Options non hanno una manopola propria sulla MPK: la loro rotazione passa da joystick e « », la pressione dai tasti di trasporto. Tutti e tre restano raggiungibili anche dalla Flip (§14.3).

### 14.3 Tasti della Flip

**UI-132** [D] Con i soli tasti della Flip si DEVE poter raggiungere **tutta** l'interfaccia, anche senza la MPK: c'è un **fuoco** su una delle 11 manopole del pannello, evidenziato con il colore d'accento.

| Tasto della Flip | Azione |
|---|---|
| L1 / R1 | `FOCUS(−1 / +1)` nell'ordine Sound, Perform, FX, Key, Bass, Loop, BPM, Volume, Options, Chord Voicing, Bass Voicing (ciclico) |
| croce su / giù | lista aperta: `NAV(−1 / +1)`; altrimenti `ENC_ROT(fuoco, +1 / −1)` |
| croce destra / sinistra | `ENC_ROT(fuoco, +1 / −1)` |
| A | lista aperta: `NAV_OK`; altrimenti `ENC_DOWN` / `ENC_UP` dell'encoder con il fuoco. A tenuto + croce = premere e ruotare; A tenuto da solo = pressione lunga |
| B | `NAV_BACK` |
| Y tenuto | `ENC_DOWN` / `ENC_UP` di **Bass Voicing**, il modificatore (Y + A su Loop = uscita forzata) |
| SELECT | `ENC_DOWN` / `ENC_UP` di **Options** |
| START | `ENC_DOWN` / `ENC_UP` di **BPM** (Beat o metronomo) |
| MENU | `PLATFORM_MENU` |
| X, L2, R2, levette, L3, R3 | liberi, riservati |

- Ripetizione della croce come il joystick: dopo 400 ms, un passo ogni 120 ms.
- All'avvio il fuoco è su Sound.
- Volume e accensione della Flip restano a spruceOS.

---

## 15. Test di accettazione

**UI-133** [D] Ogni schermata DEVE avere un test sul PC che costruisce un `ui_model_t`, disegna il framebuffer e lo confronta con le misure della specifica (riquadri di ingombro dei pixel accesi) e con un'immagine PBM di riferimento salvata nel repository. Misure con tolleranza ±2 px per i dati `[O]`, esatte per i dati `[M]` e per le scelte `[D]`/`[V]` di Stame.

| Test | Verifica |
|---|---|
| T-UI-01 | Lista Options: barra alle righe 48..71, x 0..126, colonna 127 spenta; cap alle righe 6, 30, 54, 78, 102; testo a x = 4 |
| T-UI-02 | Vista Chord con G♯ᴹ⁷ e E♭ᴹ⁷: ingombri di UI-036 |
| T-UI-03 | Geek Out con Dm/A, C⁹, C^JAZZ, C^WTF: ingombri di UI-036; tasti neri, separatori e marker di UI-038 |
| T-UI-04 | Overlay «07 Sound», «117» BPM, «032 Voicing», «OFF Chorus»: celle di UI-061/062, etichetta alle righe 114..124 |
| T-UI-05 | Overlay Volume a 50: XOR del riempimento sulle cifre (UI-064) |
| T-UI-06 | Overlay Transpose: barra 111..126 con testo in negativo |
| T-UI-07 | Overlay Key per C, F♯m, Cm, G♭m: geometria di UI-068 |
| T-UI-08 | Anello del looper con 1, 2, 4, 8, 16 battute e Free; progresso 0%, 25%, 50%, 99%: fessure, scacchiera, angoli |
| T-UI-09 | Riconoscimento dei gesti: tap, pressione lunga alla soglia, premere e ruotare, rotazione dopo la pressione lunga, Bass Voicing + Loop, con tempi simulati |
| T-UI-10 | Overlay: scadenza a 3400 ms, ripartenza a ogni rotazione, sostituzione |
| T-UI-11 | Persistenza del nome: 1000 ms, sostituzione con un nuovo accordo |
| T-UI-12 | Flip: l'OLED in (128, 48, 384, 384), ogni pixel logico diventa un quadrato 3×3 dello stesso colore |
| T-UI-13 | Flip: navigazione completa di Options con i soli tasti della Flip, e con i soli controlli della MPK |
| T-UI-14 | A riposo (nessun timer attivo) la UI non ridisegna e `ui_next_deadline_ms()` restituisce «nessuna scadenza» |

---

## 16. Questioni aperte

### 16.1 Da verificare su un Orchid vero

| Test | Cosa verificare | Default scelto |
|---|---|---|
| V-UI-01 | Durata di un overlay (girare Volume, cronometrare la scomparsa; ripetere con BPM e Sound) | 3400 ms |
| V-UI-02 | Persistenza del nome dopo il rilascio (3.90+) | 1000 ms |
| V-UI-03 | Soglie della pressione lunga di Perform, FX, Sound, Key | 1000 ms |
| V-UI-04 | Impaginazione della vista Notes | UI-058 |
| V-UI-05 | Altezza della tastiera nella vista Keyboard | righe 56..127 |
| V-UI-06 | Tasti a retino: note dell'accordo o tasto premuto; basso compreso o no | note dell'accordo, senza basso |
| V-UI-07 | Indicatore Split/Octave (3.60), grafica dello split (3.84), nota singola | overlay «Split»/«Octave», linea tratteggiata, solo il nome |
| V-UI-08 | Verso e area del riempimento dei volumi; aspetto di Beat e Bass Volume | da sinistra, righe 0..109 |
| V-UI-09 | Overlay per Key premuto, Bass on/off, BPM premuto, batteria da suonare; testo dell'etichetta BPM | UI-065, UI-097 |
| V-UI-10 | Formato del transpose («+3» o «+03») e gamma | «+3» |
| V-UI-11 | Volume a zero: «00» o «OFF» | «00» |
| V-UI-12 | Schermate Save / Load / Delete del looper e conferma | liste di UI-077/078, «Saved» |
| V-UI-13 | Schermate Save / Save As / Delete dei Sound e conferma (3.84) | idem |
| V-UI-14 | Misure della pila, testo dell'avviso di batteria bassa, ripetizione al 5% | UI-094/095 |
| V-UI-15 | Impaginazione e fine della richiesta «select key» | UI-096 |
| V-UI-16 | Timeout di liste e Options; «ripremere Options» per uscire; effetto degli altri encoder con un menu aperto; modifica delle voci numeriche | 10 s / nessuno / chiude ed esegue |
| V-UI-17 | React: finestra, ampiezza, sorgente, testata | 256 campioni, ±40 px, dopo il master, nessuna testata |
| V-UI-18 | Spessori e forme del font elastico; rapporto della qualità minuscola; restringimento dei nomi lunghi; x-height e spaziatura del font piccolo; cap della banda delle note | UI-015, UI-018, UI-034, UI-035 |
| V-UI-19 | Testata in minore («A Minor»?) e con la Key mode spenta nel 3.92 («Off» o vuota) | «Minor», vuota |
| V-UI-20 | Nomi e maiuscole esatte delle voci dei sottomenu 3.90, lista Bass e Beats | testi di UI-077/079 |
| V-UI-21 | Looper: selezione della Waiting Room, anello in registrazione Free, accordi e overlay sopra il looper | UI-086, UI-087, UI-090 |
| V-UI-22 | Ritmo del lampeggio del LED di Volume | UI-107 |
| V-UI-23 | Liste cicliche o no; Options girato a menu chiuso | non cicliche; nulla |
| V-UI-24 | Esistenza di uno screensaver | nessuno |
| V-UI-25 | Etichette di Arp 2 Octaves e di Perform a zero | «Arp 2 Oct», «OFF» + modo |
| V-UI-26 | Menu del looper in pausa | Overdub / Play / Clear |
| V-UI-27 | Count-in in 3/4 e 6/8 | parte dal numero di movimenti |
| V-UI-28 | Banda delle note: grafia del diesis, basso compreso, contenuto con una nota singola | «#», senza basso |
| V-UI-29 | Vista di fabbrica | Chord |

### 16.2 Altre questioni
- **Font**: va disegnato da zero ricalcando i fotogrammi (QS 730, 770, 863, 662.5; LP 161-178, 1220; GR 186-192). Serve una sessione dedicata con i fotogrammi a piena risoluzione.
- **Logo di Stame**: da disegnare (bitmap 128×128 a 1 bit, monocroma, senza richiami al logo TI).
- **LED del trasporto della MPK**: se l'host li possa accendere su Linux non è verificato (sezione 40, verifiche sulla MPK). Senza, il pannello virtuale resta l'unico indicatore.
- **Mappa della MPK**: la proposta di §14.2 lascia la pressione lunga di Bass (lista dei modi) solo a Play tenuto e la rotazione di Options solo al joystick. Va provata con le mani prima di fissare il programma «STAME».
- **Tema**: il pannello superiore dell'Orchid è nero lucido, la scocca crema; il tema «Orchid» usa il crema per lo sfondo e una cornice nera attorno al display. Da rivedere su una foto dello strumento.
- **Testi in inglese**: anche il menu della piattaforma è in inglese, per non dover aggiungere le lettere accentate ai font. Da confermare con Luigi.
- **Pressione e rotazione con la croce della Flip**: A tenuto + croce = premere e ruotare (UI-132). Va provato se è comodo con una mano sola.

---

## 17. Dipendenze da altre sezioni

| Sezione | Cosa serve da lì |
|---|---|
| `00-panoramica.md` | conferma della posizione di `core/ui` nel nucleo e del glossario (encoder, overlay, vista) |
| `10-accordi-e-performance.md` | `chord_label_t` (nomenclatura, «JAZZ», «WTF», Secret Chords, slash chord, enarmonie), note che suonano e loro nomi, Key mode e tonalità valide, transpose, Split/Octave e `W`, Play Style, modi e parametri di Perform, stati e menu del looper, BPM, Beats e tempi in chiave, batteria da suonare |
| `20-suono.md` | nomi e numeri dei 70 Sound, dei 12 bassi e degli User Sound, slot degli effetti e «effetto principale», gamme 0–10 degli effetti, volumi, uscita audio per React |
| `40-midi-e-controlli.md` | traduzione dei messaggi della MPK (CC relativi → scatti, pad, trasporto, joystick) e dei codici evdev della Flip nelle azioni di §14; LED del trasporto; canali MIDI del menu Options |
| `50-piattaforma-flip.md` | thread e code, finestra SDL e texture, salvataggio delle impostazioni, batteria e carica della Flip, Audio Output, chiusura dell'app (Auto Power Off, Quit, batteria critica) |
| `90-questioni-aperte.md` | raccoglie i test V-UI-01 … V-UI-29 e le questioni di §16.2 |
