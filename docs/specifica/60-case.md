# 60 — Case della fase 1 (bozza 3)

> Contenitore che tiene insieme MPK mini IV, macro pad BRIMFORD e Miyoo Flip, con hub e cavi. La bozza 1 (13/10/2026) è nelle pagine 10–11 di `docs/disegni/stame-plancia-e-controlli.pdf`; la bozza 2 (14/10/2026) metteva la Flip su un ponte dietro la MPK mini Plus. La **bozza 3 (15/10/2026)** nasce dalla composizione che Luigi ha scelto e fotografato: la **MK4** al posto della Plus, il **macro pad a destra in linea con i tasti** e la **Flip aperta sopra il pad**, «così lo schermo non copre i tasti del macro pad». L'identità che il case condivide con la plancia è in `docs/identita/README.md`. I pezzi si generano con `hardware/case/genera.py` (istruzioni in `hardware/case/README.md`). Prefisso dei requisiti: `CASE-`.

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
| Controlli della MK4 | centri in `hardware/case/misure.py` (`MK4_CTRL`): ruote 24/52, pad 88…170 × 17/46 (25 mm), display e manopola di navigazione a 212, −/+ e SHIFT a 202/222, manopole 249…335 × 15/46, trasporto 250…332 × 75 | [D] foto del 15/10/2026 in rapporto alla larghezza; [V] con la dima |
| Miyoo Flip, chiusa | 84 × 80,35 × 24,5; metà con i tasti 12,25; porta USB-C di sopra OTG, porta di sotto e jack sul bordo davanti | [O] schede; [O] foto; [D] metà; [V] posizioni, tasti del volume, apertura della cerniera (serve ≥ 115°) |
| Macro pad BRIMFORD | ≈ 158 × 70 × 32; 15 tasti in 3 file da 5, passo ≈ 18,2 × 19,5, primo tasto a (12, 11); manopole m1 (117,5, 13) e m2 (150, 13) ⌀ 20, M (135, 53) ⌀ 30; USB-C sul retro verso le manopole | [D] foto; [V] tutto, con il calibro |
| Hub USB 2.0 | ≈ 85 × 32 × 15 | [V] dipende dal modello |

## 3. Disposizione
Coordinate in mm: x verso destra dal bordo esterno del fianco sinistro, y dal retro verso il musicista, z dal tavolo.

| Parte | x | y | z | Note |
|---|---|---|---|---|
| Fianchi | 0–16 e 553,5–569,5 | 0–244 | 0–54 dietro, 40 davanti | 4 strati di betulla da 4 mm |
| Base | 16–553,5 | 0–244 | 0–6 | betulla 6 mm, due metà a coda di rondine (giunta a x = 310) |
| Listello del retro | 16–553,5 | 0–4 | 6–36 | chiude la zona dei cavi; uscite per alimentazione, audio e pedale |
| Zona dei cavi | 18–551,5 | 4–44 | | dietro MK4 e torre: connettori della MK4, cavo OTG |
| MK4 | 18–365,5 | 44–236 | 6–43 (51,7 con le manopole) | |
| Mascherina | sopra la MK4 | 47–138 | +4 mm sul pannello | acrilico nero 3 mm, un pezzo |
| Divisorio | 367,5–371,5 | 44–236 | 6–46 | copre il fianco della MK4, regge la mensola; passaggio dei cavi dietro |
| Torre: mensola | 373,5–551,5 | 44–144 | piano a 46 | betulla 6 mm con la tasca della culla; sotto il vano dell'hub (40 mm) |
| Torre: parete davanti e cartellino | 373,5–551,5 | 144–148 (+3 di acrilico) | 6–46 | la mappa del pad, rivolta a chi suona |
| Flip, metà con i tasti | 420,5–504,5 | 50,6–131 | 48–60 | in piano nella culla; cerniera dietro |
| Flip, schermo | 420,5–504,5 | da 50,6 a ≈ 17 | fino a ≈ 133 | a 65° dall'orizzontale, inclinato verso il retro |
| Macro pad | 383,5–541,5 | 157–227 | 6–38 | sulla base, dentro la cornice stampata; in linea con i tasti della MK4 (142–236) |

- **CASE-010** [D] La Flip DEVE stare aperta sulla mensola, con la metà dei tasti **in piano** e lo schermo a **65° dall'orizzontale**, inclinato verso il retro (apertura della cerniera 115° [V]). Il centro dello schermo sta a circa 96 mm dal tavolo: da 60 cm, con gli occhi 35 cm sopra il tavolo, lo sguardo scende di 23° e arriva a 2° dalla perpendicolare allo schermo. L'altezza massima con lo schermo aperto è 133 mm; lo schermo non sporge dal retro della base.
- **CASE-011** [D] La culla della Flip DEVE essere aperta davanti (jack e USB-C di sotto, per la ricarica), dietro (USB-C di sopra, OTG, verso l'hub) e sui lati (tasti del volume). Le posizioni vanno misurate sulla console [V].
- **CASE-012** [D] Dietro gli apparecchi restano 40 mm per i cavi; per l'USB-C della MK4 conviene un connettore a 90° [V].
- **CASE-013** [D] **La torre.** Mensola di betulla a 46 mm con la tasca per la culla; sotto, un vano di circa 170 × 92 × 40 mm per l'hub e la riserva dei cavi, chiuso davanti dalla parete con il cartellino e dietro da una parete con il passaggio dei cavi. Il pad sta sulla base, in piano, dentro una cornice stampata alta 8 mm che lo tiene fermo e lascia un intaglio per il suo cavo, che entra nel vano da un intaglio nella parete davanti.
- **CASE-014** [D] Altezze delle mani: tasti del pad a 38 mm dal tavolo, tasti della MK4 a circa 36, manopole della MK4 a 52, mascherina a 47–50 [V]. La destra passa dai tasti al pad senza salire.

## 4. Integrazione della MK4
- **CASE-030** [D] **Mascherina.** Una piastra di acrilico nero da 3 mm copre il pannello comandi della MK4, dal retro ai tasti (y 3–94 nel riferimento della MK4), in un pezzo solo (341,5 × 91 mm).
  - ha un foro per ogni comando che Stame usa: ruote, 8 pad, display, manopola di navigazione, −/+, SHIFT, 8 manopole, i 5 pulsanti del trasporto;
  - copre i comandi che Stame non usa (OCT−/+, ARP, LATCH, NOTE REPEAT, TAP TEMPO, BANK A/B, PLUGIN/DAW): sopra OCT sta il marchio;
  - poggia su 11 piedini da 4 mm incollati sotto, in zone piane del pannello: così non preme nessun pulsante [V: altezza dei pulsanti];
  - si toglie sollevandola: serve per PLUGIN/DAW (scelta del preset DAW, `40` MIDI-130) e per il Global.
- **CASE-031** [D] **Legende della mascherina**, incise:
  - sotto ogni manopola la funzione a punti Matrice: SOUND, PERFORM, FX, KEY / BASS, LOOP, BPM, VOLUME;
  - pad: la fila alta ha DIM, MIN, MAJ, SUS nello spazio fra le due file (3 mm: Spleen piccolo), la fila bassa 6, m7, M7, 9 a punti Matrice sotto, con accanto in piccolo la riserva del banco B (B:KEY, B:BASS, B:PERF, B:VOIC);
  - sotto i pulsanti del trasporto: UNDO, PAUSE, BEAT, LOOP, DUB (`40` MIDI-130); sotto SHIFT: PUSH; sotto − e +: BACK e MENU; sotto la manopola di navigazione: LIST; sotto le ruote BEND e MOD.
- **CASE-032** [D] Il fianco sinistro di betulla copre la guancia della MK4; il divisorio copre quella verso la torre.
- **CASE-033** [D] Proposta, da decidere con Luigi: colori dei pad in tono con la plancia (accordi acqua, estensioni bianco). Sulla MK4 i LED dei pad si pilotano dall'host con Note On sul canale 7 (guida MK4 §10.3), senza SysEx: resta comunque da provare con il suo ok.

## 5. La Flip sopra il pad
- **CASE-040** [D] La metà con i tasti sta in una **culla** stampata che scende nella tasca del piano della mensola; la Flip chiusa entra di 12 mm, aperta la metà con i tasti resta nella culla. Niente legende dei tasti della Flip sul legno: dal 15/10/2026 la plancia non le mostra più (`30` UI-155) e i tasti servono solo a liste e pagina dei comandi, che il macro pad apre con T15.
- **CASE-041** [D] Una **visiera** stampata in PETG nero circonda lo schermo aperto su tre lati: lo ripara dalla luce e lo fa sembrare il display della console. Si avvita al piano della mensola dietro la culla, non tocca la Flip [V: angolo dello schermo e ingombro della cerniera]. È facoltativa: la composizione funziona anche senza.
- **CASE-042** [D] **Cartellino del pad.** Una striscia di acrilico nero (174 × 36 mm) avvitata sulla parete davanti della mensola, proprio dietro il pad, porta la mappa dei 15 tasti nello stesso ordine in cui stanno sul pad (T1 SOUND … T4 KEY, T13 LOCK / T5 BASS … T8 VOLUME, T14 VIEW / T9 OPTIONS … T12 PANIC, T15 PAGE) e le tre manopole disposte come sul pad (m1 BASS VOIC, m2 LIST, M CHORD VOIC) con il mestiere che hanno con il Lock acceso (SOUND, PERFORM, KEY; `40` MIDI-131, MIDI-132). Le tre aggiunte di Stame (T13–T15) hanno un segno sotto il nome.

## 6. Collegamenti
- **CASE-020** [O] Si usa la porta USB-C **di sopra** della Flip (OTG): con un apparecchio collegato passa da sola in modalità host. Mai forzare `otg_mode` (nota del second brain «Miyoo Flip e spruceOS - app native, SSH e gotcha»).
- **CASE-021** [O] Serve un **hub USB 2.0 semplice, senza PD né ricarica passante**. Le docking station per portatili non si accendono con la Flip.
- **CASE-022** [D] Hub non alimentato per default, nel vano sotto la mensola, nel suo fermo: MK4 e pad prendono corrente dalla batteria della Flip, con l'RGB del pad spento. Se il consumo accorcia troppo l'autonomia, si passa a un hub alimentato da un powerbank [V]. Percorsi dei cavi: OTG dalla porta di sopra della Flip, giù dietro la mensola e dentro il vano dalla finestra della parete dietro; USB-C della MK4 lungo la zona dei cavi e dentro il vano dal passaggio nel divisorio; USB-C del pad dall'intaglio della parete davanti.
- **CASE-023** [O] La Flip si ricarica dalla porta di sotto, sul bordo davanti, meglio se a console spenta; la culla ha l'intaglio. Il case NON DEVE collegare un caricatore alla Flip mentre è in modalità host senza una prova fatta con l'ok di Luigi.
- **CASE-024** [D] Pedale nel jack SUSTAIN della MK4 (retro). Audio dal jack della Flip (bordo davanti, connettore a 90°) verso cuffie o amplificatore: il cavo corre sotto il cartellino, lungo la parete davanti, fino al fianco destro e all'uscita nel listello del retro. In alternativa un'interfaccia audio USB sull'hub, che lascia libero il bordo davanti della Flip [V].

## 7. Pezzi
L'elenco completo, con quantità e materiali, è in `hardware/case/README.md`. In sintesi:
- laser: mascherina e cartellino (acrilico nero 3 mm); listello del retro in due metà, 8 strati dei fianchi, divisorio, pareti davanti e dietro della mensola (betulla 4 mm); base in due metà e piano della mensola (betulla 6 mm);
- stampa (PETG): culla della Flip, cornice del pad, visiera (facoltativa), 11 piedini (meglio TPU), 16 squadrette M3, fermo dell'hub.

Ingombro 569,5 × 244 mm; altezza 54 ai fianchi, 133 con lo schermo aperto. Peso stimato con gli apparecchi: circa 2,5 kg [D].

## 8. Alternative scartate
- **Flip dietro la MK4 su un ponte (bozza 2):** lo sguardo cadeva lontano dalla destra e dal pad; Luigi l'ha messa sopra il pad, e lì resta.
- **Flip a destra del pad:** allunga la console di 100 mm e porta lo schermo fuori dall'asse della mano che lavora sul pad.
- **Pad dietro la MK4:** la destra dovrebbe scavalcare le manopole per ogni tocco.
- **Flip in piano sul tavolo, senza mensola:** schermo troppo basso (sguardo a 30° dalla perpendicolare) e niente posto per l'hub; la mensola la alza di 40 mm e nasconde i cavi.
- **Mascherina appoggiata sul pannello:** preme i pulsanti piccoli. Va sollevata sui piedini.
- **Tutto stampato:** 570 mm non stanno nel piano da 250; il legno dà il carattere anni Settanta della console.
- **Guscio unico che smonta la MK4:** è il lavoro della fase 2, lo strumento dedicato.

## 9. Prossimi passi
1. Misurare con il calibro le voci [V] di `hardware/case/misure.py`: pad (ingombro, passo dei tasti, manopole, presa USB), MK4 (altezza dei pulsanti, connettori sul retro), Flip (porte, tasti del volume, angolo della cerniera).
2. Stampare la dima della mascherina su carta e provarla sulla MK4.
3. Prova di taglio dei materiali; poi mascherina e cartellino.
4. Stampa di prova della culla e della cornice con la Flip e il pad veri.
5. Telaio di betulla e torre.

## Questioni aperte
- [V] Posizioni e misure dei controlli della MK4, altezza dei pulsanti piccoli, posizione dei connettori sul retro.
- [V] Misure del macro pad e della sua presa USB-C.
- [V] Porte, tasti del volume, cerniera e angolo massimo dello schermo della Flip; 65° è una proposta, da provare fra 60° e 70°.
- [V] Consumo di MK4 + pad dalla Flip con un hub non alimentato.
- Decisioni di Luigi: colori dei pad (CASE-033); visiera sì o no (CASE-041); audio dal jack della Flip o da un'interfaccia USB sull'hub (CASE-024); tasti del macro pad stampati in sabbia con le legende.
- Il modello 3D `hardware/case/out/stame_console.skp` e l'immagine `docs/identita/img/case_3d.png` sono ancora della bozza 2: da rifare quando le misure [V] saranno confermate.

## Dipendenze da altre sezioni
- `40`: mappa dei controlli della MK4 (§8.9b, MIDI-130) e del pad (§8.10, MIDI-131, MIDI-132), collegamento (MIDI-128).
- `50`: porte USB, alimentazione e gotcha della Flip.
- `docs/identita/README.md`: marchio, caratteri e colori.
