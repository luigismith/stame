# 60 — Case della fase 1 (bozza 2)

> Contenitore che tiene insieme MPK mini Plus, macro pad BRIMFORD e Miyoo Flip, con hub e cavi. La bozza 1 (13/10/2026) è nelle pagine 10–11 di `docs/disegni/stame-plancia-e-controlli.pdf`. La bozza 2 (14/10/2026) nasce dalla richiesta di Luigi: «lavoriamo sull'estetica del display e sul case, vorrei che fosse sinergico e che la tastiera MPK mini Plus sia più integrata possibile; ho a disposizione taglio laser e stampante 3D». L'identità che il case condivide con la plancia è in `docs/identita/README.md`. I pezzi si generano con `hardware/case/genera.py` (istruzioni in `hardware/case/README.md`). Prefisso dei requisiti: `CASE-`.

## 1. Principi
- **CASE-001** [D] Il case NON DEVE modificare gli apparecchi. Niente viti nella MPK, nella Flip o nel pad: entrano interi e si tolgono in un minuto.
- **CASE-002** [D] La disposizione segue la mappa dei controlli (`40` §8.5 e §8.10):
  - MPK davanti, con la sinistra sui pad degli accordi e la destra sulla tastiera;
  - macro pad a destra, accanto alla mano che suona i tasti;
  - Flip dietro i pad, come schermo.
- **CASE-003** [D] Ogni pezzo DEVE stare nella macchina che lo fa, con margine:
  - stampa: piano della Kobra S1 (250 × 250 mm), lato massimo 240 mm;
  - laser: AtomStack S10, lato massimo 390 mm [D].
  I pezzi più lunghi si dividono in due metà (base, piano, fronte e retro del ponte, mascherina).
- **CASE-004** [D] Restano accessibili, senza togliere nulla:
  - tutti i connettori posteriori della MPK (USB-B, SUSTAIN, CV, CLOCK, MIDI), attraverso la bocca nel fronte del ponte;
  - le due porte USB-C, il jack e l'altoparlante della Flip;
  - la porta USB-C del pad;
  - i tasti della Flip.
- **CASE-005** [D] Il case parla la lingua della plancia: stesso marchio, stessi caratteri (Matrice e Spleen incisi), scritte fisse color sabbia su nero (`docs/identita/README.md` §4).
- **CASE-006** [D] **Il case porta i nomi, lo schermo i valori** (plancia calma, 15/10/2026). La funzione di ogni comando della MPK e del macro pad si legge sull'incisione accanto al comando, non sullo schermo; lo schermo risponde al tocco con il nome e il valore in grande (30, UI-140 e UI-154). Per questo incisioni ed etichette della plancia usano gli stessi termini, abbreviati sulla mascherina dove manca spazio (PERF, VOIC, OPT).

## 2. Misure di partenza
| Oggetto | Misure (mm) | Fonte |
|---|---|---|
| MPK mini Plus | 451,1 × 180 × 52, profilo a cuneo 37,5 dietro e 28,5 davanti senza manopole | [M] manuale; [D] guida alla Plus §14.13 |
| Controlli della MPK | centri in `hardware/case/misure.py` (`MPK_CTRL`) | [D] guida alla Plus §14.15.2 |
| Miyoo Flip, chiusa | 84 × 80,35 × 24,5 | [O] schede dei negozi |
| Macro pad BRIMFORD | ≈ 115 × 100 × 35 | [V] da misurare |
| Hub USB 2.0 | ≈ 85 × 32 × 15 | [V] dipende dal modello |

## 3. Disposizione
Coordinate in mm: x verso destra dal bordo esterno del fianco sinistro, y dal retro verso il musicista, z dal tavolo.

| Parte | x | y | z | Note |
|---|---|---|---|---|
| Fianchi | 0–16 e 603–619 | 0–288 | 0–80 | 4 strati di betulla da 4 mm |
| Base | 16–603 | 0–288 | 0–6 | betulla 6 mm, due metà a coda di rondine |
| Ponte | 16–603 | 0–98 | 6–78 | scatola di betulla, piano a 15° |
| Tasca della Flip | 159–251 | nel piano del ponte | — | centro a x = 205, dietro i pad |
| MPK | 18–469 | 100–280 | 6–52 | |
| Mascherina | sopra la MPK | 103–189 | +4 mm sul pannello | acrilico nero 3 mm, due metà |
| Divisorio | 469–473 | 100–284 | 6–52 | |
| Vano del macro pad | 473–601 | 100–280 | | cartellino dietro, pad davanti su un vassoio |

- **CASE-010** [D] La Flip DEVE stare aperta, con la metà dei tasti inclinata di 15° nella culla e lo schermo a circa 70° dall'orizzontale. Da 50–70 cm lo sguardo arriva quasi perpendicolare allo schermo. Lo schermo sporge di circa 21 mm dal retro del case; l'altezza massima con lo schermo aperto è 150 mm.
- **CASE-011** [D] La culla della Flip DEVE essere aperta dietro (porta USB-C di sopra) e sui lati (tasti del volume). Le posizioni vanno misurate sulla console [V].
- **CASE-012** [D] Dietro la MPK il ponte lascia 94 mm per i cavi; per il cavo USB-B conviene un connettore ad angolo di 90° [V].

## 4. Integrazione della MPK
- **CASE-030** [D] **Mascherina.** Una piastra di acrilico nero da 3 mm copre il pannello comandi della MPK, dalla parte posteriore fino ai tasti, in due metà (giunta fra i pad e BANK).
  - ha un foro per ogni comando che Stame usa: ruote, joystick, 8 pad, 8 manopole, encoder e display della MPK, BANK, SHIFT, PROG SELECT, « » STOP PLAY REC;
  - copre i comandi che Stame non usa (ARP, TAP, NOTE REPEAT, FULL LEVEL, OCT, SCALES, CHORDS, HOME, SEQ): lì sta il marchio;
  - poggia su 14 piedini da 4 mm incollati sotto, in zone piane del pannello: così non preme nessun pulsante [V: altezza dei pulsanti];
  - si toglie sollevandola: serve per le impostazioni della MPK (SHIFT + STOP per Trpt).
- **CASE-031** [D] **Legende della mascherina**, incise:
  - sotto ogni manopola la funzione a punti Matrice: SOUND, PERFORM, FX, KEY / BASS, LOOP, BPM, VOLUME;
  - sopra la fila alta dei pad DIM, MIN, MAJ, SUS e sotto la fila bassa 6, m7, M7, 9, a punti Matrice; accanto, in piccolo, la funzione del banco B (LOOP, BPM, OPT, PUSH / KEY, BASS, PERF, VOIC);
  - sotto i pulsanti del trasporto: « » TURN, PAUSE, BEAT, LOOP; sotto le ruote BEND e MOD; sotto il joystick FOCUS.
- **CASE-032** [D] I fianchi di betulla coprono le guance rosse della MPK; il divisorio copre quella verso il macro pad.
- **CASE-033** [D] Proposta, da decidere con Luigi: colori dei pad nel programma STAME in tono con la plancia (accordi acqua, estensioni bianco, banco B ambra). Cambiare il programma richiede il SysEx: prima il backup e l'ok di Luigi (`CLAUDE.md`).

## 5. La Flip come display della console
- **CASE-040** [D] La metà dei tasti sta in una culla stampata che scende nella tasca del piano del ponte. Sul piano, ai lati della tasca, sono incise le funzioni dei tasti della Flip (L1 R1 FOCUS, ✚ TURN, A PRESS, B BACK, X PUSH, Y BS.VOIC, SEL OPTIONS, START BPM, MENU).
- **CASE-041** [D] Una **visiera** stampata in PETG nero circonda lo schermo aperto su tre lati: lo ripara dalla luce e lo fa sembrare il display della console. Si avvita al ponte, non tocca la Flip [V: angolo dello schermo e ingombro della cerniera].

## 6. Collegamenti
- **CASE-020** [O] Si usa la porta USB-C **di sopra** della Flip (OTG): con un apparecchio collegato passa da sola in modalità host. Mai forzare `otg_mode` (nota del second brain «Miyoo Flip e spruceOS - app native, SSH e gotcha»).
- **CASE-021** [O] Serve un **hub USB 2.0 semplice, senza PD né ricarica passante**. Le docking station per portatili non si accendono con la Flip.
- **CASE-022** [D] Hub non alimentato per default, nel vano sotto il cartellino: MPK e pad prendono corrente dalla batteria della Flip, con l'RGB del pad spento. Se il consumo accorcia troppo l'autonomia, si passa a un hub alimentato da un powerbank [V].
- **CASE-023** [O] La Flip si ricarica dalla porta di sotto, meglio se a console spenta. Il case NON DEVE collegare un caricatore alla Flip mentre è in modalità host senza una prova fatta con l'ok di Luigi.
- **CASE-024** [D] Pedale nel jack SUSTAIN della MPK. Audio dal jack della Flip verso cuffie o amplificatore; le uscite dei cavi sono nel retro del ponte.

## 7. Pezzi
L'elenco completo, con quantità e materiali, è in `hardware/case/README.md`. In sintesi:
- laser: 2 mezze mascherine e il cartellino (acrilico nero 3 mm); piano, fronte e retro del ponte in due metà, 3 centine, 8 strati dei fianchi, divisorio (betulla 4 mm); base in due metà (betulla 6 mm);
- stampa (PETG): culla della Flip, visiera, vassoio del macro pad, 14 piedini (meglio TPU), 12 squadrette M3, fermo dell'hub, 4 colonnine.

Peso stimato con gli apparecchi: circa 3 kg [D].

## 8. Alternative scartate
- **Tutto stampato:** 619 mm non stanno nel piano da 250 mm; servirebbero molti pezzi incollati e il legno dà il carattere anni Settanta della console.
- **Mascherina appoggiata sul pannello:** preme i pulsanti piccoli. Va sollevata sui piedini.
- **Guscio unico che smonta la MPK:** è il lavoro della fase 2, lo strumento dedicato.
- **Pad a sinistra:** la manopola grande del voicing finirebbe lontano dalla mano che suona i tasti.

## 9. Prossimi passi
1. Misurare le voci [V] di `hardware/case/misure.py`.
2. Stampare la dima della mascherina su carta e provarla sulla MPK.
3. Prova di taglio dei materiali; poi mascherina e cartellino.
4. Stampa di prova della culla e della visiera con la Flip vera.
5. Telaio di betulla.

## Questioni aperte
- [V] Posizioni e misure dei controlli della MPK e altezza dei pulsanti piccoli.
- [V] Misure del macro pad, posizione di tasti e manopole.
- [V] Porte, tasti del volume, cerniera e angolo massimo dello schermo della Flip.
- [V] Consumo di MPK + pad dalla Flip con un hub non alimentato.
- Decisione di Luigi: colori dei pad (CASE-033); tasti del macro pad stampati in sabbia con le legende.

## Dipendenze da altre sezioni
- `40`: mappa dei controlli e collegamento del pad (§8.5, §8.10).
- `50`: porte USB, alimentazione e gotcha della Flip.
- `docs/identita/README.md`: marchio, caratteri e colori.
