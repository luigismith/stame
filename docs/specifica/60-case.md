# 60 — Case della fase 1 (bozza 4)

> Contenitore che tiene insieme MPK mini IV, macro pad BRIMFORD e Miyoo Flip, con hub e cavi. La bozza 1 (13/10/2026) è nelle pagine 10–11 di `docs/disegni/stame-plancia-e-controlli.pdf`; la bozza 2 (14/10/2026) metteva la Flip su un ponte dietro la MPK mini Plus. La **bozza 3 (15/10/2026)** nasce dalla composizione che Luigi ha scelto e fotografato: la **MK4** al posto della Plus, il **macro pad a destra in linea con i tasti** e la **Flip aperta sopra il pad**, «così lo schermo non copre i tasti del macro pad». L'identità che il case condivide con la plancia è in `docs/identita/README.md`. La **bozza 4 (17/10/2026)** tiene la composizione e rifà la costruzione: incastri a linguetta, culla bassa che lascia libere le spalle della Flip, visiera che segue lo schermo, legende della mappa del 17/10/2026, copritasti, e un modello 3D che nasce dalla stessa geometria dei pezzi (`hardware/case/assieme.py`), con le istruzioni di montaggio e i progetti di taglio in PDF (`hardware/case/manuale.py`). I pezzi si generano con `hardware/case/genera.py` (istruzioni in `hardware/case/README.md`). Prefisso dei requisiti: `CASE-`.

## 1. Principi
- **CASE-001** [D] Il case NON DEVE modificare gli apparecchi. Niente viti nella MK4, nella Flip o nel pad: entrano interi e si tolgono in un minuto.
- **CASE-002** [D, **composizione decisa da Luigi il 15/10/2026**] La disposizione segue le mani (`40` §8.9b, §8.10):
  - MK4 a sinistra, con la sinistra sui pad degli accordi e la destra sulla tastiera; il trasporto (looper) sotto le manopole, a destra;
  - a destra la **torre**: davanti il macro pad, in linea con i tasti, a un palmo dal trasporto; dietro la Flip aperta su una mensola, con lo schermo rivolto a chi suona;
  - sotto la mensola il vano dell'hub e dei cavi.
- **CASE-003** [D] Ogni pezzo DEVE stare nella macchina che lo fa, con margine:
  - stampa: piano della Kobra S1 (250 × 250 mm), lato massimo 240 mm;
  - laser: AtomStack S10, lato massimo 390 mm [D].
  I pezzi più lunghi (base, listello del retro) si dividono in due metà; la mascherina della MK4 (341,5 mm) sta in un pezzo solo.
- **CASE-004** [D] Restano accessibili, senza togliere nulla:
  - i connettori posteriori della MK4 (USB-C, MIDI OUT, SUSTAIN), nella zona dei cavi dietro;
  - le due porte USB-C, il jack, l'altoparlante e i tasti del volume della Flip;
  - la porta USB-C del pad, dal suo bordo posteriore;
  - i tasti della Flip e il display.
- **CASE-005** [D] Il case parla la lingua della plancia: stesso marchio, stessi caratteri (Matrice e Spleen incisi), scritte fisse color sabbia su nero (`docs/identita/README.md` §4).
- **CASE-006** [D] **Il case porta i nomi, lo schermo i valori** (plancia calma, 15/10/2026). La funzione di ogni comando della MK4 e del macro pad si legge sull'incisione accanto al comando (mascherina) o davanti al pad (cartellino), non sullo schermo; lo schermo risponde al tocco con il nome e il valore in grande (`30` UI-140, UI-154). Incisioni ed etichette della plancia usano gli stessi termini, abbreviati dove manca spazio (PERF, VOIC, OPT).

## 2. Misure di partenza
| Oggetto | Misure (mm) | Fonte |
|---|---|---|
| MPK mini IV | 347,5 × 192 × 45,7 con le manopole; corpo 37; tasti da 98 mm dal retro, alti ≈ 30 dal tavolo | [M] guida MK4 §1; [D] foto, [V] |
| Controlli della MK4 | centri in `hardware/case/misure.py` (`MK4_CTRL`): ruote 22,9/53,7 × 37,1, pad 87,9…173,3 (passo 28,5) × 18/46,3, cornice 25 mm; display e manopola di navigazione a 214,3; −/+ e SHIFT a 203,7/224,4; manopole 252,3…335,8 (passo 27,8) × 18,3/50, anello rosso 15–17 mm; pulsanti 17,7 × 11,5, trasporto 252,9…334,2 × 74,4 | [D] rimisurati il 17/10/2026 su `mk4_vista_alto.jpg` (scala verificata sui due assi, prospettiva corretta), ±1 mm; prova con la dima |
| Miyoo Flip, chiusa | 84 × 80,35 × 24,5; metà con i tasti 12,25; porta USB-C di sopra OTG; sul bordo davanti jack a −6 e USB-C a +6,3 mm dal centro; tasti sul fianco destro fra 6 e 16 mm dalla cerniera | [O] schede; [D] metà; [D] porte e tasti da due foto (entro 0,5 mm); [V] apertura della cerniera (serve ≥ 115°) |
| Macro pad BRIMFORD | ≈ 158 × 70 × 32; 15 tasti in 3 file da 5, passo ≈ 18,2 × 19,5, primo tasto a (12, 11); manopole m1 (117,5, 13) e m2 (150, 13) ⌀ 20, M (135, 53) ⌀ 30; USB-C sul retro verso le manopole | [D] foto; [V] tutto, con il calibro |
| Hub USB 2.0 | ≈ 85 × 32 × 15 | [V] dipende dal modello |

## 3. Disposizione
Coordinate in mm: x verso destra dal bordo esterno del fianco sinistro, y dal retro verso il musicista, z dal tavolo.

| Parte | x | y | z | Note |
|---|---|---|---|---|
| Fianchi | 0–16 e 553,5–569,5 | 0–244 | 0–54 dietro, 40 davanti | 4 strati di betulla da 4 mm |
| Base | 16–553,5 | 0–244 | 0–6 | betulla 6 mm, due metà a coda di rondine (giunta a x = 310) |
| Listello del retro | 16–553,5 | 0–4 | 6–36 | chiude la zona dei cavi; uscite per alimentazione, audio e pedale; due linguette per metà nelle tacche della base |
| Zona dei cavi | 18–551,5 | 4–44 | | dietro MK4 e torre: connettori della MK4, cavo OTG |
| MK4 | 18–365,5 | 44–236 | 6–43 (51,7 con le manopole) | |
| Mascherina | sopra la MK4 | 47–138 | +4 mm sul pannello | acrilico nero 3 mm, un pezzo |
| Divisorio | 367,5–371,5 | 44–236 | 6–46 | copre il fianco della MK4; due linguette nelle asole della base; passaggio dei cavi dietro |
| Torre: piano della mensola | 373,5–551,5 | 41–151 | 40–46 | betulla 6 mm; sporge 3 mm oltre le pareti, che entrano nelle sue asole; sotto il vano dell'hub (34 mm) |
| Torre: pareti dietro e davanti | 373,5–551,5 | 44–48 e 144–148 | 6–40 | linguette in basso nella base e in alto nel piano |
| Cartellino | 375,5–527,5 | 148–151 | 6–39 | la mappa del pad, incollato sulla parete davanti; a destra il passaggio del cavo del pad |
| Culla | 417,9–507,1 | 54–137,4 | 46–53 | vassoio sul piano, bordi di 5 mm, aperto dietro |
| Flip, metà con i tasti | 420,5–504,5 | 54,6–135 | 48–60 | in piano nella culla; cerniera dietro |
| Flip, schermo | 420,5–504,5 | da 50,6 a ≈ 17 | fino a ≈ 133 | a 65° dall'orizzontale, inclinato verso il retro |
| Macro pad | 383,5–541,5 | 157–227 | 6–38 | sulla base, dentro la cornice stampata; in linea con i tasti della MK4 (142–236) |

- **CASE-010** [D] La Flip DEVE stare aperta sulla mensola, con la metà dei tasti **in piano** e lo schermo a **65° dall'orizzontale**, inclinato verso il retro (apertura della cerniera 115° [V]). Il centro dello schermo sta a circa 96 mm dal tavolo: da 60 cm, con gli occhi 35 cm sopra il tavolo, lo sguardo scende di 23° e arriva a 2° dalla perpendicolare allo schermo. L'altezza massima con lo schermo aperto è 133 mm; lo schermo non sporge dal retro della base.
- **CASE-011** [D] La culla della Flip DEVE essere aperta davanti (jack e USB-C di sotto, per la ricarica), dietro (USB-C di sopra, OTG, verso l'hub) e sui lati (tasti del volume). Jack e USB-C stanno a 12 mm l'uno dall'altra: davanti basta un intaglio solo, da 6,5 mm prima del jack a 7 mm dopo la USB-C; i bordi laterali cominciano 4 mm dopo i tasti (posizioni dalle foto del 15/10/2026).
- **CASE-012** [D] Dietro gli apparecchi restano 40 mm per i cavi; per l'USB-C della MK4 conviene un connettore a 90° [V].
- **CASE-013** [D, bozza 4] **La torre.** Piano di betulla da 6 mm (z 40–46) appoggiato su due pareti da 4 mm, dietro e davanti, che stanno sotto di lui e si incastrano a linguetta nella base e nel piano; il piano sporge di 3 mm oltre le pareti, così le asole restano chiuse. Sotto, un vano di circa 170 × 96 × 34 mm per l'hub e la riserva dei cavi; la parete dietro ha la finestra dei cavi, quella davanti il passaggio del cavo del pad, a destra del cartellino. Il pad sta sulla base, in piano, dentro una cornice stampata alta 8 mm che si incolla. Nella bozza 3 le pareti arrivavano alla quota del piano e le viti del piano cadevano fuori dalle pareti: la bozza 4 lo corregge.
- **CASE-014** [D] Altezze delle mani: tasti del pad a 38 mm dal tavolo, tasti della MK4 a circa 36, manopole della MK4 a 52, mascherina a 47–50 [V]. La destra passa dai tasti al pad senza salire.

## 4. Integrazione della MK4
- **CASE-030** [D] **Mascherina.** Una piastra di acrilico nero da 3 mm copre il pannello comandi della MK4, dal retro ai tasti (y 3–94 nel riferimento della MK4), in un pezzo solo (341,5 × 91 mm).
  - ha un foro per ogni comando che Stame usa: ruote, 8 pad, display, manopola di navigazione, −/+, SHIFT, 8 manopole, i 5 pulsanti del trasporto;
  - copre i comandi che Stame non usa (OCT−/+, ARP, LATCH, NOTE REPEAT, TAP TEMPO, BANK A/B, PLUGIN/DAW): sopra OCT sta il marchio;
  - poggia su 11 piedini da 4 mm incollati sotto, in zone piane del pannello: così non preme nessun pulsante [V: altezza dei pulsanti];
  - si toglie sollevandola: serve per PLUGIN/DAW (scelta del preset DAW, `40` MIDI-130) e per il Global.
- **CASE-031** [D] **Legende della mascherina**, incise:
  - sotto ogni manopola la funzione a punti Matrice: SOUND, PERFORM, FX, KEY / BASS, LOOP, BPM, VOLUME;
  - pad: la fila alta ha DIM, MIN, MAJ, SUS nello spazio fra le due file (Spleen piccolo), la fila bassa 6, m7, M7, 9 a punti Matrice sotto; accanto, in piccolo, la batteria del banco B (`40` MIDI-135, bozza 4): B:CHH, B:OHH, B:TOM, B:CYM sopra, B:KICK, B:SNARE, B:RIM, B:CLAP sotto;
  - sotto i pulsanti del trasporto: UNDO (e S:CLEAR), PAUSE, BEAT (e S:PANIC), LOOP, DUB (`40` MIDI-130); sotto SHIFT: PUSH; sotto − e +: BACK e MENU; sotto la manopola di navigazione: LIST; sotto le ruote BEND e MOD.
- **CASE-032** [D] Il fianco sinistro di betulla copre la guancia della MK4; il divisorio copre quella verso la torre.
- **CASE-033** [D, **deciso da Luigi il 15/10/2026**] I LED dei pad della MK4 in tono con la plancia (accordi acqua, estensioni bianco). Si pilotano dall'host con Note On sul canale 7 (guida MK4 §10.3), senza SysEx; la prima prova si fa con Luigi davanti, reversibile, e poi diventa un'aggiunta di Stame accesa per default [V].

## 5. La Flip sopra il pad
- **CASE-040** [D, bozza 4] La metà con i tasti sta in una **culla** stampata: un vassoio sul piano della mensola, con fondo da 2 mm e bordi da 5 mm davanti e ai lati, fissato con 4 viti M3 svasate (dadi sotto il piano). È **aperta dietro**: dal 17/10/2026 i tasti della Flip sono sempre vivi (`40` MIDI-137, MIDI-138), spalle comprese (L1, R1 il fuoco, L2 Tap, R2 Fill), e la culla della bozza 3, che faceva scendere la Flip di 12 mm nel piano, le avrebbe coperte. Niente legende dei tasti della Flip sul legno.
- **CASE-041** [D, bozza 4] Una **visiera** stampata in PETG nero circonda lo schermo aperto su tre lati: due fianchi che seguono lo schermo a 65° (24 mm davanti, 3 mm dietro), un tettuccio sopra il bordo alto e due piedi avvitati al piano accanto alla culla. Non tocca la Flip e lascia libere le spalle [V: angolo dello schermo e ingombro della cerniera]. Arriva a 150 mm dal tavolo. **Deciso da Luigi il 15/10/2026: la visiera c'è** (la composizione funzionerebbe anche senza, ma così lo schermo è il display della console).
- **CASE-042** [D, bozza 4] **Cartellino del pad.** Una striscia di acrilico nero (152 × 33 mm) incollata sulla parete davanti della mensola, proprio dietro il pad, porta la mappa dei 15 tasti nello stesso ordine in cui stanno sul pad, con la mappa del 16-17/10/2026 (`40` MIDI-120, MIDI-133): T1 HOLD, T2 TAP, T3 METRO, T4 FILL, T13 LOCK / T5–T8 SCENE 1–4, T14 VIEW / T9 OPTIONS, T10 SAVE LP, T11 DRUMS, T12 PANIC, T15 PAGE. In ogni casella dei tasti T1–T12 c'è anche, in piccolo, la nota del pad strumento (C … B, `40` MIDI-136). Le tre manopole sono disposte come sul pad, con il mestiere con la tastiera (m1 BASS VOIC, m2 BEAT VOL, M CHORD VOIC), quello del pad strumento (EXT, FOCUS, TYPE) e, in alto, quello con il Lock acceso (SOUND, PERFORM, KEY). Le tre aggiunte di Stame (T13–T15) hanno un segno sotto il nome.
- **CASE-043** [D, **deciso da Luigi il 15/10/2026**; bozza 4] **Tasti del macro pad.** I 15 tasti del BRIMFORD si coprono con copritasti stampati in PETG sabbia (`copritasti.stl`, tutti e 15 in un pezzo da stampare): sopra il nome della mappa con la tastiera, a punti Matrice in rilievo di 0,5 mm (neri, con il cambio di filamento), e in basso a destra, più piccola, la nota del pad strumento. Stelo a croce tipo MX [V]: le misure dello stelo e del passo vanno prese sul pad prima di stamparne quindici.

## 6. Collegamenti
- **CASE-020** [O] Si usa la porta USB-C **di sopra** della Flip (OTG): con un apparecchio collegato passa da sola in modalità host. Mai forzare `otg_mode` (nota del second brain «Miyoo Flip e spruceOS - app native, SSH e gotcha»).
- **CASE-021** [O] Serve un **hub USB 2.0 semplice, senza PD né ricarica passante**. Le docking station per portatili non si accendono con la Flip.
- **CASE-022** [D] Hub non alimentato per default, nel vano sotto la mensola, nel suo fermo: MK4 e pad prendono corrente dalla batteria della Flip, con l'RGB del pad spento. Se il consumo accorcia troppo l'autonomia, si passa a un hub alimentato da un powerbank [V]. Percorsi dei cavi: OTG dalla porta di sopra della Flip, giù dietro la mensola e dentro il vano dalla finestra della parete dietro; USB-C della MK4 lungo la zona dei cavi e dentro il vano dal passaggio nel divisorio; USB-C del pad dall'intaglio della parete davanti.
- **CASE-023** [O] La Flip si ricarica dalla porta di sotto, sul bordo davanti, meglio se a console spenta; la culla ha l'intaglio. Il case NON DEVE collegare un caricatore alla Flip mentre è in modalità host senza una prova fatta con l'ok di Luigi.
- **CASE-024** [D] Pedale nel jack SUSTAIN della MK4 (retro). Audio dal jack della Flip (bordo davanti, connettore a 90°) verso cuffie o amplificatore: il cavo corre sotto il cartellino, lungo la parete davanti, fino al fianco destro e all'uscita nel listello del retro. **Deciso da Luigi il 15/10/2026: l'audio esce dal jack della Flip**; un'interfaccia audio USB sull'hub resta una possibilità futura, che il case non prevede.

## 7. Pezzi
L'elenco completo, con quantità, materiali e minuteria, è in `hardware/case/README.md` e nella copertina di `hardware/case/out/istruzioni_montaggio.pdf`. In sintesi:
- laser: mascherina e cartellino (acrilico nero 3 mm, un foglio); listello del retro in due metà, 8 strati dei fianchi, divisorio, pareti davanti e dietro della mensola (betulla 4 mm, due fogli); base in due metà e piano della mensola (betulla 6 mm, due fogli). I fogli impaginati sono in `out/taglio/` (SVG e DXF) e in `progetti_di_taglio.pdf`;
- stampa (PETG): culla della Flip, cornice del pad, visiera, 11 piedini (meglio TPU), 6 squadrette M3, fermo dell'hub, 15 copritasti.

- **CASE-050** [D, bozza 4] Il modello 3D della console (`out/stame_console.skp` con una scena per passo, `out/stame_console.obj`), le tavole del montaggio e i fogli di taglio DEVONO nascere dalla stessa geometria dei pezzi da tagliare e stampare: un pezzo cambiato in `genera.py` o una misura cambiata in `misure.py` cambiano tutto insieme. Il riferimento del case è sinistrorso, quindi ogni esportazione 3D lo specchia su y: senza, la culla e la cornice uscirebbero al rovescio.

Ingombro 569,5 × 244 mm; altezza 54 ai fianchi, 133 lo schermo aperto, 150 la visiera. Peso stimato con gli apparecchi: circa 2,5 kg [D].

## 8. Alternative scartate
- **Flip dietro la MK4 su un ponte (bozza 2):** lo sguardo cadeva lontano dalla destra e dal pad; Luigi l'ha messa sopra il pad, e lì resta.
- **Flip a destra del pad:** allunga la console di 100 mm e porta lo schermo fuori dall'asse della mano che lavora sul pad.
- **Pad dietro la MK4:** la destra dovrebbe scavalcare le manopole per ogni tocco.
- **Flip in piano sul tavolo, senza mensola:** schermo troppo basso (sguardo a 30° dalla perpendicolare) e niente posto per l'hub; la mensola la alza di 40 mm e nasconde i cavi.
- **Mascherina appoggiata sul pannello:** preme i pulsanti piccoli. Va sollevata sui piedini.
- **Tutto stampato:** 570 mm non stanno nel piano da 250; il legno dà il carattere anni Settanta della console.
- **Guscio unico che smonta la MK4:** è il lavoro della fase 2, lo strumento dedicato.

## 9. Prossimi passi
1. Misurare le voci [V] di `hardware/case/misure.py`: pad (ingombro, passo dei tasti, manopole, presa USB), MK4 (altezza dei pulsanti, connettori sul retro), Flip (angolo della cerniera), hub. Basta anche una foto da sopra con il pezzo su un foglio A4 tutto in vista.
2. Stampare la dima della mascherina su carta e provarla sulla MK4.
3. Prova di taglio dei materiali; poi mascherina e cartellino.
4. Stampa di prova della culla e della cornice con la Flip e il pad veri.
5. Telaio di betulla e torre.

## Questioni aperte
- [V] Altezza dei pulsanti piccoli della MK4 e posizione dei connettori sul retro; i controlli sono rimisurati sulle foto (17/10/2026), resta la prova della dima.
- [V] Misure del macro pad e della sua presa USB-C.
- [V] Cerniera e angolo massimo dello schermo della Flip; 65° è una proposta, da provare fra 60° e 70°. Porte e tasti dalle foto [D].
- [V] Consumo di MK4 + pad dalla Flip con un hub non alimentato.
- [V] Stelo e passo dei tasti del macro pad, per i copritasti (CASE-043).
- Decise da Luigi il 15/10/2026 (sera): LED dei pad in tono con la plancia (CASE-033), visiera sì (CASE-041), audio dal jack della Flip (CASE-024), tasti del macro pad in sabbia con le legende incise (CASE-043).
- Modello 3D, modello SketchUp e immagine `docs/identita/img/case_3d.png` sono della bozza 4 (17/10/2026); si rigenerano da `misure.py` quando le misure [V] saranno confermate.

## Dipendenze da altre sezioni
- `40`: mappa dei controlli della MK4 (§8.9b, MIDI-130) e del pad (§8.10, MIDI-131, MIDI-132), collegamento (MIDI-128).
- `50`: porte USB, alimentazione e gotcha della Flip.
- `docs/identita/README.md`: marchio, caratteri e colori.
