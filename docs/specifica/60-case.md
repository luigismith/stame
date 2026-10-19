# 60 — Case della fase 1 (bozza 5)

> Contenitore che tiene insieme MPK mini IV, macro pad BRIMFORD e Miyoo Flip, con hub e cavi. La bozza 1 (13/10/2026) è nelle pagine 10–11 di `docs/disegni/stame-plancia-e-controlli.pdf`; la bozza 2 (14/10/2026) metteva la Flip su un ponte dietro la MPK mini Plus. La **bozza 3 (15/10/2026)** nasce dalla composizione che Luigi ha scelto e fotografato: la **MK4** al posto della Plus, il **macro pad a destra in linea con i tasti** e la **Flip aperta sopra il pad**, «così lo schermo non copre i tasti del macro pad». La **bozza 4 (17/10/2026)** ha rifatto la costruzione: incastri a linguetta, culla bassa che lascia libere le spalle della Flip, visiera, tasti del pad con le etichette, modello 3D, istruzioni di montaggio e progetti di taglio in PDF. La **bozza 5 (18/10/2026)** tiene la composizione e cambia la forma, su richiesta di Luigi: «deve essere tutto coperto e omogeneo. non mi piace tanto la divisione che hai creato tra mpk e pad, e per il pad vorrei una culla simile a quella che hai fatto per il flip»; e per la mascherina, «falla che si poggia bene con i fori anche per i controlli non utilizzati». L'identità che il case condivide con la plancia è in `docs/identita/README.md`. I pezzi si generano con `hardware/case/genera.py` (istruzioni in `hardware/case/README.md`). Prefisso dei requisiti: `CASE-`.

## 1. Principi
- **CASE-001** [D] Il case NON DEVE modificare gli apparecchi. Niente viti nella MK4, nella Flip o nel pad: entrano interi e si tolgono in un minuto.
- **CASE-002** [D, **composizione decisa da Luigi il 15/10/2026**, forma del 18/10/2026] La disposizione segue le mani (`40` §8.9b, §8.10):
  - MK4 a sinistra, con la sinistra sui pad degli accordi e la destra sulla tastiera; il trasporto (looper) sotto le manopole, a destra;
  - a destra, davanti, il macro pad in linea con i tasti, a un palmo dal trasporto, nella sua culla; dietro, la Flip aperta nella sua culla, con lo schermo rivolto a chi suona;
  - sopra, un piano solo di acrilico nero alla stessa quota da un fianco all'altro; sotto il piano l'hub e i cavi, coperti.
- **CASE-003** [D] Ogni pezzo DEVE stare nella macchina che lo fa, con margine:
  - stampa: piano della Kobra S1 (250 × 250 mm), lato massimo 240 mm;
  - laser: AtomStack S10, lato massimo 390 mm [D].
  I pezzi più lunghi (base, retro e il suo strato d'appoggio) si dividono in due metà; la mascherina (359 × 134 mm) sta in un pezzo solo.
- **CASE-004** [D] Restano accessibili, senza togliere nulla:
  - i connettori posteriori della MK4 (USB-C, MIDI OUT, SUSTAIN), nella zona dei cavi dietro, sotto la mascherina;
  - le due porte USB-C, il jack, l'altoparlante e i tasti del volume della Flip;
  - la porta USB-C del pad, dalla finestra dietro la sua culla;
  - i tasti della Flip e il display.
- **CASE-005** [D] Il case parla la lingua della plancia: stesso marchio, stessi caratteri (Matrice e Spleen incisi), scritte fisse color sabbia su nero (`docs/identita/README.md` §4).
- **CASE-006** [D] **Il case porta i nomi, lo schermo i valori** (plancia calma, 15/10/2026). La funzione di ogni comando della MK4 si legge sull'incisione accanto al comando (mascherina); quella dei tasti del pad sull'etichetta dentro il tasto, quella delle sue manopole sul piano, accanto alla culla. Lo schermo risponde al tocco con il nome e il valore in grande (`30` UI-140, UI-154). Incisioni ed etichette usano gli stessi termini della plancia, abbreviati dove manca spazio (PERF, VOIC, OPT).

## 2. Misure di partenza
| Oggetto | Misure (mm) | Fonte |
|---|---|---|
| MPK mini IV | 347,5 × 192 × 45,7 con le manopole; corpo 37; tasti da 98 mm dal retro, alti ≈ 30 dal tavolo | [M] guida MK4 §1; [D] foto, [V] |
| Controlli della MK4 | centri in `hardware/case/misure.py` (`MK4_CTRL`): ruote 22,9/53,7 × 37,1, pad 87,9…173,3 (passo 28,5) × 18/46,3, cornice 25 mm; display e manopola di navigazione a 214,3; −/+ e SHIFT a 203,7/224,4; manopole 252,3…335,8 (passo 27,8) × 18,3/50, anello rosso 15–17 mm; pulsanti 17,7 × 11,5, trasporto 252,9…334,2 × 74,4 | [D] rimisurati il 17/10/2026 su `mk4_vista_alto.jpg` (scala verificata sui due assi, prospettiva corretta), ±1 mm; prova con la dima |
| Miyoo Flip, chiusa | 84 × 80,35 × 24,5; metà con i tasti 12,25; porta USB-C di sopra OTG; sul bordo davanti jack a −6 e USB-C a +6,3 mm dal centro; tasti sul fianco destro fra 6 e 16 mm dalla cerniera | [O] schede; [D] metà; [D] porte e tasti da due foto (entro 0,5 mm); [V] apertura della cerniera (serve ≥ 115°) |
| Macro pad BRIMFORD | 185 × 75 (77 sul lobo) × 31,5 con le manopole. Corpo 11,5 dal tavolo alla faccia della piastra: fascia scura 6 (distanziali, circuito, fondo), acrilico trasparente 3,5, piastra satinata 2. 15 tasti in 3 file da 5, passo 21,4 × 22,1, primo tasto a (15,5, 12,6). Davanti, dal lato delle manopole, un lobo che sporge 2 mm da 3 mm dopo l'ultima colonna di tasti (x 113) fino in fondo, con l'angolo R 30; gli altri angoli R 5. Manopole m1 (133,5, 18) e m2 (169, 18) ⌀ 20, cappello zigrinato alto 14,5 su un dado da 5; M (151,5, 62) ⌀ 30 con la flangia ⌀ 34; tutte arrivano 20 mm sopra la piastra. Sul retro la USB-C fra m1 e m2, a 148 mm dal bordo dei tasti, centro a 9 dal fondo, con il LED verde accanto; un interruttore a slitta a 78, con la levetta che sporge di circa 1 mm; un altro elemento a 36, che non sporge | [O] metro posato sulla piastra, due foto di Luigi del 19/10/2026 (contorno ±0,5, x di m1 e m2 e della USB-C ±1–2); [D] dieci foto del 18/10/2026 per strati e altezze (±1,5); [V] altezze, quota della USB-C e dell'interruttore, flangia di M |
| Hub USB 2.0 | ≈ 85 × 32 × 15 | [V] dipende dal modello |

## 3. Disposizione
Coordinate in mm: x verso destra dal bordo esterno del fianco sinistro, y dal retro verso il musicista, z dal tavolo.

| Parte | x | y | z | Note |
|---|---|---|---|---|
| Fianchi | 0–16 e 567,5–583,5 | 0–244 | 0–46 | 4 strati di betulla da 4 mm, spigoli in cima arrotondati (r 8); lo strato più interno è d'appoggio |
| Base | 16–566,5 | 0–244 | 0–6 | betulla 6 mm, due metà a coda di rondine (giunta a x = 310) |
| Retro | 16–566,5 | 0–4 | 0–46 | due metà, linguette nelle tacche della base; finestre per alimentazione, audio e pedale |
| Strato d'appoggio del retro | 16–566,5 | 4–8 | 6–42 | incollato davanti al retro, con le stesse finestre |
| Zona dei cavi | 18–365,5 | 8–44 | 6–43 | dietro la MK4, sotto la mascherina: connettori della MK4 |
| MK4 | 18–365,5 | 44–236 | 6–43 (51,7 con le manopole) | |
| Mascherina | 12,2–371,3 | 4,2–138 | 43–46 | acrilico nero 3 mm, un pezzo; appoggia sul pannello della MK4 e sugli strati d'appoggio |
| Costola | 367,5–375,5 | 8–244 | 0–46 | due strati di betulla 4 mm fra la MK4 e la parte destra; dietro, fra y 8 e 44, lascia sotto un passaggio per i cavi alto 24 mm |
| Piano della Flip | 371,7–571,3 | 4,2–156 | 43–46 | acrilico nero 3 mm; porta culla e visiera della Flip e la legenda delle manopole del pad |
| Culla della Flip | 426,9–516,1 | 54–137,3 | 46–53 | vassoio sul piano, bordi di 5 mm, aperto dietro |
| Flip, metà con i tasti | 429,5–513,5 | 54,6–135 | 48–60,3 | in piano nella culla; cerniera dietro |
| Flip, schermo | 429,5–513,5 | da 54,6 verso il retro | fino a ≈ 133 | a 65° dall'orizzontale, inclinato verso il retro |
| Culla del pad | 375,8–567,2 | 156,3–239,7 | 6–53 | stampata, in piedi sulla base, fra costola, fianco e parete davanti |
| Macro pad | 379–564 | 159,5–236,5 | 32–48 la piastra, ≈ 63 i tasti | nella culla, in linea con i tasti della MK4 (144–236) |
| Parete davanti | 375,5–566,5 | 240–244 | 0–46 | betulla 4 mm, linguette nelle asole della base |
| Hub | 428,6–514,4 | 106,3–138,3 | 8–23 | nel suo fermo, sotto il piano della Flip, dietro la culla del pad |

- **CASE-010** [D] La Flip DEVE stare aperta sul piano, nella sua culla, con la metà dei tasti **in piano** e lo schermo a **65° dall'orizzontale**, inclinato verso il retro (apertura della cerniera 115° [V]). Il centro dello schermo sta a circa 96 mm dal tavolo: da 60 cm, con gli occhi 35 cm sopra il tavolo, lo sguardo scende di 23° e arriva a 2° dalla perpendicolare allo schermo. L'altezza massima con lo schermo aperto è 133 mm; lo schermo non sporge dal retro della base.
- **CASE-011** [D] La culla della Flip DEVE essere aperta davanti (jack e USB-C di sotto, per la ricarica), dietro (USB-C di sopra, OTG, verso l'hub) e sui lati (tasti del volume). Jack e USB-C stanno a 12 mm l'uno dall'altra: davanti basta un intaglio solo, da 6,5 mm prima del jack a 7 mm dopo la USB-C; i bordi laterali cominciano 4 mm dopo i tasti (posizioni dalle foto del 15/10/2026). Il piano ha una fessura dietro la culla per l'OTG e una davanti per jack e ricarica.
- **CASE-012** [D] Dietro la MK4 restano 36 mm per i cavi; per l'USB-C della MK4 serve un connettore a 90° [V].
- **CASE-013** [D, bozza 5] **Il telaio e il piano.** Fianchi, retro, costola e parete davanti arrivano tutti a 46 mm, la cima della console. Dentro il telaio c'è un piano solo di acrilico nero, in due pezzi alla stessa quota, che si incontrano sulla costola: a sinistra la mascherina, a destra il piano della Flip. Il piano posa sugli **strati d'appoggio**: lo strato più interno di fianchi, retro e costola è 4 mm più basso dove sopra c'è il piano e porta una striscia di feltro da 1 mm, così il piano sta alla quota del pannello della MK4. Dove il tratto basso arriva sotto lo spigolo arrotondato del fianco, l'arco si ferma sul gradino. Non ci sono più la torre, la mensola, il divisorio e il cartellino della bozza 4.
- **CASE-014** [D] Altezze delle mani: tasti della MK4 a circa 36 mm dal tavolo, manopole della MK4 a 52, mascherina a 46; la piastra del pad a 48 come il fondo della culla della Flip, i suoi tasti a circa 63. Il pad sta più in alto della tastiera di circa 27 mm: è il prezzo della culla come quella della Flip, da provare con le mani [V].

## 4. Integrazione della MK4
- **CASE-030** [D, bozza 5] **Mascherina.** Una piastra di acrilico nero da 3 mm (359 × 134 mm, un pezzo solo) copre il pannello comandi della MK4 e, dietro, la zona dei cavi fino al retro.
  - **appoggia sul pannello della MK4** e ha un foro per ogni controllo, anche per quelli che Stame non usa (Luigi, 18/10/2026): ruote, 8 pad, display, manopola di navigazione, −/+, SHIFT, 8 manopole, i pulsanti del trasporto, OCT−/+, ARP, LATCH, NOTE REPEAT, TAP TEMPO, BANK A/B, PLUGIN/DAW. I pulsanti piccoli stanno 1-2 mm sotto la sua faccia [V: altezza dei pulsanti];
  - il bordo dietro e i lati posano sugli strati d'appoggio di retro, fianco e costola, con il feltro; non servono più piedini;
  - dietro, sulla zona dei cavi, porta la targa: il marchio, STAME e STAMEN HARMONICUM;
  - si toglie sollevandola, ma con i fori anche PLUGIN/DAW (scelta del preset DAW, `40` MIDI-130) e il Global si usano senza toglierla.
- **CASE-031** [D] **Legende della mascherina**, incise:
  - sotto ogni manopola la funzione a punti Matrice: SOUND, PERFORM, FX, KEY / BASS, LOOP, BPM, VOLUME;
  - pad: la fila alta ha DIM, MIN, MAJ, SUS nello spazio fra le due file (Spleen piccolo), la fila bassa 6, m7, M7, 9 a punti Matrice sotto; accanto, in piccolo, la batteria del banco B (`40` MIDI-135): B:CHH, B:OHH, B:TOM, B:CYM sopra, B:KICK, B:SNARE, B:RIM, B:CLAP sotto;
  - sotto i pulsanti del trasporto: UNDO (e S:CLEAR), PAUSE, BEAT (e S:PANIC), LOOP, DUB (`40` MIDI-130); sotto SHIFT: PUSH; sotto − e +: BACK e MENU; sotto la manopola di navigazione: LIST; sotto le ruote BEND e MOD;
  - sotto i controlli della MK4 stessa il loro nome, piccolo: OCT −, OCT +, ARP, LATCH, NOTE RPT, TAP, BANK (con B: DRUMS), DAW (con PRESET).
- **CASE-032** [D] Il fianco sinistro di betulla copre la guancia della MK4; la costola copre quella verso il pad.
- **CASE-033** [D, **deciso da Luigi il 15/10/2026**] I LED dei pad della MK4 in tono con la plancia (accordi acqua, estensioni bianco). Si pilotano dall'host con Note On sul canale 7 (guida MK4 §10.3), senza SysEx; la prima prova si fa con Luigi davanti, reversibile, e poi diventa un'aggiunta di Stame accesa per default [V].

## 5. La Flip e il pad
- **CASE-040** [D, bozza 4] La metà con i tasti della Flip sta in una **culla** stampata: un vassoio sul piano, con fondo da 2 mm e bordi da 5 mm davanti e ai lati, fissato con 4 viti M3 svasate (dadi sotto il piano). È **aperta dietro**: dal 17/10/2026 i tasti della Flip sono sempre vivi (`40` MIDI-137, MIDI-138), spalle comprese (L1, R1 il fuoco, L2 Tap, R2 Fill), e una culla che facesse scendere la Flip nel piano le coprirebbe. Niente legende dei tasti della Flip sul case.
- **CASE-041** [D, bozza 4] Una **visiera** stampata in PETG nero circonda lo schermo aperto su tre lati: due fianchi che seguono lo schermo a 65° (24 mm davanti, 3 mm dietro), un tettuccio sopra il bordo alto e due piedi avvitati al piano accanto alla culla. Non tocca la Flip e lascia libere le spalle [V: angolo dello schermo e ingombro della cerniera]. Arriva a 150 mm dal tavolo. **Deciso da Luigi il 15/10/2026: la visiera c'è.**
- **CASE-042** [tolto nella bozza 5] Il cartellino del pad non c'è più: i nomi dei tasti stanno nelle etichette (CASE-043), quelli delle manopole sul piano (CASE-045).
- **CASE-043** [D, **deciso da Luigi il 15/10/2026, cambiato il 17/10/2026**] **Tasti del macro pad.** I 15 tasti del BRIMFORD si sostituiscono con tasti trasparenti a due strati per Cherry MX (17 × 17 alla base), con sotto il coperchio un'etichetta di carta da 11 × 9 mm. Le etichette (`hardware/case/etichette.py`, `out/etichette_pad.pdf`, A4 al 100 %, tagliate a 10,8 × 8,8) portano il nome della mappa (`40` MIDI-120, MIDI-133), a punti Matrice; LOCK, VIEW e PAGE sono in negativo. Dal 18/10/2026 niente più nota del pad strumento, tolto con le mappe per il solo pad (`40` MIDI-136). Quattro serie chiare e quattro scure (Notte).
- **CASE-044** [D, bozza 5] **Culla del pad**, come quella della Flip (Luigi, 18/10/2026). Stampata in PETG (in piedi, senza supporti), sta sulla base fra costola, fianco destro e parete davanti. Dentro ha la sagoma vera del pad con 0,5 mm di gioco, lobo compreso (foto del 18/10/2026). Il pad poggia su sei costole, con la piastra 2 mm sopra il piano, come il fondo della culla della Flip; il bordo sale 5 mm oltre la piastra. Davanti ha la tacca per la flangia della manopola grande, che sporge dal lobo; dietro la finestra per la spina USB-C del pad (a 148 mm dal bordo dei tasti, fra m1 e m2), a 90°, una finestra per la levetta dell'interruttore (a 78) e un dente che regge il bordo davanti del piano della Flip. La spina arriva sopra la faccia di sotto del piano: nel bordo del piano si apre una tacca, dietro m1 e m2; per questo la legenda delle manopole (CASE-045) sta a sinistra della fessura del jack e della ricarica della Flip [V: altezza del corpo del pad e della presa].
- **CASE-045** [D, bozza 5] **Legenda delle manopole del pad**, incisa sul piano fra le due culle, nella disposizione delle manopole: con la tastiera M CH. VOICING, m1 BASS VOICING, m2 BEAT VOL; con il Lock acceso SOUND, PERFORM, KEY; con DRUMS acceso DENSITY, GROOVE, VARIATION (`40` MIDI-120, MIDI-131, MIDI-135).

## 6. Collegamenti
- **CASE-020** [O] Si usa la porta USB-C **di sopra** della Flip (OTG): con un apparecchio collegato passa da sola in modalità host. Mai forzare `otg_mode` (nota del second brain «Miyoo Flip e spruceOS - app native, SSH e gotcha»).
- **CASE-021** [O] Serve un **hub USB 2.0 semplice, senza PD né ricarica passante**. Le docking station per portatili non si accendono con la Flip.
- **CASE-022** [D] Hub non alimentato per default, sotto il piano della Flip, nel suo fermo: MK4 e pad prendono corrente dalla batteria della Flip, con l'RGB del pad spento. Se il consumo accorcia troppo l'autonomia, si passa a un hub alimentato da un powerbank [V]. Percorsi dei cavi: OTG dalla porta di sopra della Flip, giù dalla fessura del piano dietro la culla; USB-C della MK4 lungo la zona dei cavi e sotto la costola; USB-C del pad dalla finestra dietro la sua culla.
- **CASE-023** [O] La Flip si ricarica dalla porta di sotto, sul bordo davanti, meglio se a console spenta; la culla ha l'intaglio e il piano la fessura. Il case NON DEVE collegare un caricatore alla Flip mentre è in modalità host senza una prova fatta con l'ok di Luigi.
- **CASE-024** [D] Pedale nel jack SUSTAIN della MK4 (retro). Audio dal jack della Flip (bordo davanti, connettore a 90°) verso cuffie o amplificatore: il cavo scende dalla fessura davanti del piano e corre sotto il piano fino all'uscita nel retro. **Deciso da Luigi il 15/10/2026: l'audio esce dal jack della Flip**; un'interfaccia audio USB sull'hub resta una possibilità futura, che il case non prevede.

## 7. Pezzi
L'elenco completo, con quantità, materiali e minuteria, è in `hardware/case/README.md` e nella copertina di `hardware/case/out/istruzioni_montaggio.pdf`. In sintesi:
- laser: mascherina e piano della Flip (acrilico nero 3 mm, una lastra da 369 × 307); retro e strato d'appoggio in due metà, 8 strati dei fianchi, 2 strati della costola, parete davanti (betulla 4 mm, due fogli); base in due metà (betulla 6 mm, due fogli). I fogli impaginati sono in `out/taglio/` (SVG e DXF) e in `progetti_di_taglio.pdf`;
- stampa (PETG): culla della Flip, visiera, culla del pad, fermo dell'hub, 6 squadrette M3. Carta: le etichette dei 15 tasti trasparenti. Da comprare: feltro adesivo da 1 mm, hub, due cavi USB-C a 90°, viti, piedini in gomma.

- **CASE-050** [D] Il modello 3D della console (`out/stame_console.skp` con una scena per passo, `out/stame_console.obj`), le tavole del montaggio e i fogli di taglio DEVONO nascere dalla stessa geometria dei pezzi da tagliare e stampare: un pezzo cambiato in `genera.py` o una misura cambiata in `misure.py` cambiano tutto insieme. Il riferimento del case è sinistrorso, quindi ogni esportazione 3D lo specchia su y: senza, le culle uscirebbero al rovescio. Anche i rendering (`hardware/case/rendering.py`, Blender Cycles, `out/render/`) e la pagina del sito `docs/case.html` nascono da qui. Ogni pezzo inciso DEVE avere, nel mondo vero, il riferimento destrorso con la faccia incisa verso fuori: `genera.py` si ferma altrimenti (17/10/2026: il rendering ha mostrato le scritte dei fianchi esterni a specchio, ora corrette).

Ingombro 583,5 × 244 mm; altezza 46 al telaio, 53 il bordo delle culle, 133 lo schermo aperto, 150 la visiera. Peso stimato con gli apparecchi: circa 2,5 kg [D].

## 7b. La console tutta stampata, per chi non ha il laser
Luigi, 18/10/2026: «crea anche tutto quello che serve per farla tutta stampata 3d (per chi non ha il laser)». La console di betulla e acrilico resta la prima; questa è la stessa console, con gli stessi pezzi, la stessa disposizione e lo stesso montaggio, fatta solo con una stampante. La genera `hardware/case/stampa3d.py` dalla geometria di `genera.py` (CASE-050), in `hardware/case/out/stampa3d/`.
- **CASE-060** [D] Ogni pezzo DEVE stare in 210 × 210 mm, l'area utile di una stampante da 220 × 220 (Ender-3, Bambu Lab, Anycubic Kobra; la Prusa MK4 in y). `stampa3d.py --piatto N` rigenera tutto per un altro piatto.
- **CASE-061** [D] Gli strati incollati del laser diventano un pezzo solo: ogni fianco (quattro strati, 16 mm), ogni metà del retro con il suo strato d'appoggio (8 mm), la costola (8 mm); la base è una lastra sola invece di due metà. Gli strati di uno stesso pezzo si compenetrano di 0,2 mm, così lo slicer li fonde. I fori delle viti delle squadrette nei fianchi scendono 10 mm, per viti autofilettanti da plastica o inserti a caldo.
- **CASE-062** [D] Quello che non sta sul piatto si divide in tasselli, con tagli dritti che passano ad almeno 1,5 mm da fori, tasche e rilievi: la base in sei, la mascherina in due, la metà sinistra del retro in due. Sui tagli ci sono code di rondine (collo 8, testa 12, profondità 7 mm; nella sede 0,15 mm di gioco per lato), da incollare con colla cianoacrilica o epossidica. I pezzi lunghi che entrano in diagonale con almeno 1,5 mm di margine per lato (i fianchi, la costola, la metà destra del retro) escono già ruotati.
- **CASE-063** [D] Ogni STL esce nel verso fisico giusto (specchiato quando il piano del pezzo è sinistrorso nel mondo), con la faccia in vista in alto, e ogni guscio è chiuso: quando i fori sono tanti, `mesh.py` estrude a strisce senza vertici a T.
- **CASE-064** [D] Le incisioni più sottili di 0,7 mm non si stampano con un ugello da 0,4. Sui fianchi il marchio e il nome escono in rilievo di 0,6 mm: con un cambio di filamento alla quota della faccia (16 mm) vengono di un altro colore. La riga «STAMEN HARMONICUM» dei fianchi resta solo sulla console laser.
- **CASE-065** [D] Sulla mascherina e sul piano della Flip ogni gruppo di scritte ha una tasca profonda 0,4 mm, a 0,6 mm almeno dai fori; le scritte si stampano su carta adesiva, 1:1, nere con le lettere chiare come l'incisione (`etichette_mascherina.pdf`, con la mappa delle tasche e una serie di ricambio). Dove fra due fori non c'è posto per la parete (le quattro scritte fra le file dei pad) l'etichetta si posa sulla faccia.
- **CASE-066** [D] Colori: telaio color legno o sabbia, piani e culle neri; circa 1,3 kg di PETG o PLA, stimati in `pezzi.md`. `istruzioni_stampa3d.pdf` raccoglie i pezzi, le impostazioni, i tasselli, le scritte e le differenze dal montaggio della console laser.

## 8. Alternative scartate
- **Flip dietro la MK4 su un ponte (bozza 2):** lo sguardo cadeva lontano dalla destra e dal pad; Luigi l'ha messa sopra il pad, e lì resta.
- **Flip a destra del pad:** allunga la console di 100 mm e porta lo schermo fuori dall'asse della mano che lavora sul pad.
- **Pad dietro la MK4:** la destra dovrebbe scavalcare le manopole per ogni tocco.
- **Flip in piano sul tavolo, senza piano rialzato:** schermo troppo basso (sguardo a 30° dalla perpendicolare) e niente posto per l'hub.
- **Torre con mensola e divisorio (bozza 4):** separava la MK4 dal pad e lasciava il pad in un pozzo; Luigi (18/10/2026) vuole tutto coperto e omogeneo.
- **Mascherina alta sui piedini, che copre i controlli non usati (bozza 4):** Luigi la vuole appoggiata, con un foro per ogni controllo.
- **Tutto stampato al posto del laser:** 583 mm non stanno nel piano da 250, e il legno dà il carattere anni Settanta della console: la prima resta di betulla e acrilico. Dal 18/10/2026 c'è però anche la versione tutta stampata, in tasselli, per chi non ha il laser (§7b).
- **Guscio unico che smonta la MK4:** è il lavoro della fase 2, lo strumento dedicato.

## 9. Prossimi passi
1. Misurare le voci [V] di `hardware/case/misure.py`: altezza del pannello e dei pulsanti piccoli della MK4, corpo del pad e quota della sua presa USB-C, angolo della cerniera della Flip, hub. Basta anche una foto da sopra con il pezzo su un foglio A4 tutto in vista.
2. Stampare la dima della mascherina su carta e provarla sulla MK4.
3. Prova di taglio dei materiali; poi mascherina e piano della Flip.
4. Stampa di prova delle due culle con la Flip e il pad veri; provare con le mani l'altezza del pad (CASE-014).
5. Telaio di betulla.
6. Per la versione stampata (§7b): prima un tassello di prova, per il gioco delle code di rondine sulla stampante che si usa.

## Questioni aperte
- [V] Altezza dei pulsanti piccoli della MK4 e posizione dei connettori sul retro; i controlli sono rimisurati sulle foto (17/10/2026), resta la prova della dima.
- [V] Cerniera e angolo massimo dello schermo della Flip; 65° è una proposta, da provare fra 60° e 70°. Porte e tasti dalle foto [D].
- [V] Consumo di MK4 + pad dalla Flip con un hub non alimentato.
- [V] Altezze del macro pad (corpo 11,5, centro della USB-C a 9 dal fondo, quota dell'interruttore) e flangia della manopola grande. Contorno, USB-C (148 mm dal bordo dei tasti) e interruttore (78) sono stati misurati con il metro il 19/10/2026; le misure del 18/10 erano il 3 % più piccole.
- Decise da Luigi il 15/10/2026 (sera): LED dei pad in tono con la plancia (CASE-033), visiera sì (CASE-041), audio dal jack della Flip (CASE-024); il 17/10/2026 i tasti trasparenti con le etichette (CASE-043); il 18/10/2026 il piano unico, la culla del pad e la mascherina appoggiata (bozza 5).
- Modello 3D, modello SketchUp, tavole e rendering sono della bozza 5 (18/10/2026). Il 18/10/2026 il rendering in qualità piena ha mandato in schermata blu il PC di casa due volte: i rendering pubblicati sono di quella mattina, e `rendering.py` non si rilancia finché la causa non è chiara.

## Dipendenze da altre sezioni
- `40`: mappa dei controlli della MK4 (§8.9b, MIDI-130) e del pad (§8.10, MIDI-131, MIDI-132), collegamento (MIDI-128).
- `50`: porte USB, alimentazione e gotcha della Flip.
- `docs/identita/README.md`: marchio, caratteri e colori.
