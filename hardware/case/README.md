# Case di Stame — la console

Bozza 3, 15/10/2026. Specifica: `docs/specifica/60-case.md`. Identità: `docs/identita/README.md`.

Un telaio di betulla tiene insieme la MPK mini IV, il macro pad BRIMFORD e la Miyoo Flip, nella composizione scelta da Luigi: MK4 a sinistra; a destra la **torre**, con il pad davanti in linea con i tasti e la Flip aperta dietro, su una mensola che nasconde l'hub. Nessun apparecchio viene modificato (CASE-001): si posano e si tolgono in un minuto.

Il modello 3D `out/stame_console.skp` e l'immagine `docs/identita/img/case_3d.png` sono ancora della bozza 2 (Flip dietro la Plus): si rifanno dopo le misure con il calibro.

## Come si generano i pezzi

```
python -I hardware/case/genera.py
```

Tutte le misure stanno in `misure.py`, ognuna con la sua fonte: [M] manuale, [O] osservato, [D] dedotto, [V] da verificare. Cambiata una misura, si rigenera tutto. Il generatore stampa l'elenco dei pezzi, controlla che stiano nei piani delle macchine e che i pezzi stampati siano gusci chiusi, e toglie da `out/` i pezzi della bozza precedente.

Escono in `hardware/case/out/`:
- **SVG per il laser**, in scala 1:1 e in millimetri. In LightBurn il rosso è taglio, il nero pieno è incisione, il blu è un segno leggero (posizioni, aree);
- **STL da stampare**;
- `dima_mascherina.svg`, da stampare su carta al 100%;
- `tavola_insieme.svg`, vista dall'alto e di fianco (non si taglia).

## Prima di tagliare

1. **Misurare** con il calibro le voci [V] di `misure.py`, soprattutto:
   - posizione e misura dei controlli della MK4 (`MK4_CTRL`, `FORO`) e altezza dei pulsanti piccoli: la mascherina sta 4 mm sopra (`piede_h`);
   - ingombro del macro pad, passo dei tasti, posizione delle manopole e della presa USB-C (`PAD`, `PAD_KNOB`, `PAD_USB_X`);
   - porte, tasti del volume e angolo di apertura della Flip (serve almeno 115°).
2. **Stampare la dima** su carta al 100% e controllare il righello di 100 mm. Ritagliarla e posarla sulla MK4: i fori devono cadere sui controlli, i rettangoli blu sui pulsanti coperti, i cerchi blu dei piedini su zone piane senza pulsanti.
3. **Prova di taglio** di un ritaglio di acrilico e di compensato per tarare potenza, velocità e passate (il laser a diodo taglia l'acrilico nero, non quello trasparente).

## Pezzi

### Laser

| File | Materiale | Quanti | Note |
|---|---|---|---|
| `mascherina.svg` | acrilico nero 3 mm | 1 | un pezzo solo (343,5 × 93); incisione chiara: le legende di Stame; si può ripassare con colore sabbia |
| `cartellino_pad.svg` | acrilico nero 3 mm | 1 | la mappa del macro pad, sulla parete davanti della mensola |
| `retro_sx.svg`, `retro_dx.svg` | betulla 4 mm | 1 + 1 | listello del retro, alto 30: chiude la zona dei cavi, con le uscite |
| `fianco_sx_esterno.svg`, `fianco_dx_esterno.svg` | betulla 4 mm | 1 + 1 | strato esterno con marchio e nome |
| `fianco_interno.svg` | betulla 4 mm | 6 | tre strati interni per fianco, incollati all'esterno: 16 mm |
| `base_sx.svg`, `base_dx.svg` | betulla 6 mm | 1 + 1 | si incastrano a coda di rondine; segni per la posa di MK4, divisorio, torre, pad e hub |
| `divisorio.svg` | betulla 4 mm | 1 | fra MK4 e torre; copre il fianco della MK4 e regge la mensola; passaggio dei cavi dietro |
| `torre_piano.svg` | betulla 6 mm | 1 | piano della mensola con la tasca della culla |
| `torre_fronte.svg`, `torre_retro.svg` | betulla 4 mm | 1 + 1 | pareti del vano dell'hub: davanti porta il cartellino e l'intaglio del cavo del pad, dietro il passaggio dei cavi |

### Stampa 3D (Kobra S1, PETG)

| File | Quanti | Note |
|---|---|---|
| `culla_flip.stl` | 1 | scende nella tasca della mensola; aperta davanti (jack e USB-C di ricarica), dietro (USB-C OTG) e ai lati (tasti del volume) [V] |
| `cornice_pad.stl` | 1 | tiene fermo il pad sulla base, con l'intaglio per il cavo |
| `visiera.stl` | 1 | cappa attorno allo schermo aperto; si avvita alla mensola. Facoltativa |
| `piedino_mascherina.stl` | 11 | meglio in TPU; si incollano sotto la mascherina dove indica la dima |
| `squadretta_m3.stl` | 16 | uniscono base, fianchi, retro, divisorio e torre |
| `fermo_hub.stl` | 1 | tiene l'hub USB nel vano sotto la mensola |

Minuteria: viti M3×8 per legno o autofilettanti (fori da 2,5 mm nel compensato), colla vinilica per i fianchi a strati, piedini in gomma da 12 mm sotto la base.

## Montaggio

1. Incollare i fianchi: tre strati interni e l'esterno, allineati sul profilo.
2. Unire le due metà della base (coda di rondine e colla) e del listello del retro.
3. Retro, fianchi e divisorio sulla base con le squadrette.
4. Torre: pareti davanti e dietro sulla base, poi il piano della mensola sopra pareti, divisorio e fianco destro; hub nel suo fermo, nel vano.
5. Culla nella tasca della mensola, visiera dietro la culla se la si vuole; cartellino avvitato sulla parete davanti; cornice del pad sulla base.
6. MK4 nel suo vano, mascherina sopra con i piedini; pad nella cornice; Flip nella culla, aperta.

## Misure principali

| | mm |
|---|---|
| ingombro | 569,5 × 244 |
| altezza dei fianchi | 54 dietro, 40 davanti |
| mensola della Flip | piano a 46; vano sotto 40 |
| altezza con lo schermo aperto | 133 (schermo a 65°, centro a 96 dal tavolo) |
| tasti del pad / tasti della MK4 | 38 / ≈ 36 dal tavolo |
