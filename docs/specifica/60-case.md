# 60 — Case della fase 1 (bozza)

> Contenitore che tiene insieme MPK mini Plus, macro pad BRIMFORD e Miyoo Flip, con hub e cavi. Bozza del 13/10/2026, chiesta da Luigi: «progetta anche una bozza di case nel quale far stare tutto dentro». I disegni (vista dall'alto in scala, sezione, cablaggio) sono nelle pagine 10–11 di `docs/disegni/stame-plancia-e-controlli.pdf`. Prefisso dei requisiti: `CASE-`.

## 1. Principi
- **CASE-001** [D] Il case NON DEVE modificare gli apparecchi. Niente viti nella MPK, nella Flip o nel pad: entrano interi e si tolgono in un minuto.
- **CASE-002** [D] La disposizione segue la mappa dei controlli (`40` §8.5 e §8.10):
  - MPK davanti, con la sinistra sui pad degli accordi e la destra sulla tastiera;
  - macro pad a destra, dove sull'Orchid stanno le manopole del voicing, accanto alla mano che suona i tasti;
  - Flip dietro, come schermo.
- **CASE-003** [D] Ogni parte stampata DEVE stare nel piano della Kobra S1 di Luigi (250 × 250 × 250 mm), con 10 mm di margine: lato massimo 240 mm. La base, più grande, è un pannello di legno.
- **CASE-004** [D] Restano accessibili, senza togliere nulla:
  - tutti i connettori posteriori della MPK (USB-B, SUSTAIN, CV, CLOCK, MIDI);
  - le due porte USB-C, il jack e l'altoparlante della Flip;
  - la porta USB-C del pad;
  - i tasti della Flip.

## 2. Misure di partenza
| Oggetto | Misure (mm) | Fonte |
|---|---|---|
| MPK mini Plus | 451,1 × 180 × 52, 1,26 kg; connettori nella metà destra del retro (x ≈ 272–420 dal bordo sinistro) | [M] manuale; [D] guida alla Plus §14.13 |
| Miyoo Flip, chiusa | 84 × 80,35 × 24,5, 165 g | [O] schede dei negozi |
| Macro pad BRIMFORD | ≈ 115 × 100 × 35, stimato dalla confezione (165 × 127 × 47) | [V] da misurare |
| Hub USB 2.0 | ≈ 85 × 32 × 15 | [V] dipende dal modello |
| Powerbank (facoltativo) | ≈ 110 × 68 × 25 | [V] |

## 3. Disposizione
Coordinate in mm, origine nell'angolo posteriore sinistro della base: x verso destra, y verso il musicista.

| Zona | x | y | Note |
|---|---|---|---|
| Base | 0–610 | 0–300 | compensato di betulla 6 mm (o MDF), angoli raggiati, piedini in gomma |
| Vano MPK | 8–461 | 112–292 | bordo alto 16 mm in 4 pezzi; spessori in TPU per il gioco |
| Dorso posteriore | 8–461 | 8–104 | 3 moduli; alto 52 → 62 mm verso il retro |
| Canale dei cavi | 8–461 | 78–104 | sotto un coperchio a scatto, con uscite verso il retro |
| Culla della Flip | 150–250 | 14–100 | inclinata di 15°, dietro ai pad e lontana dai connettori della MPK |
| Vano del pad | 469–602 | 182–292 | piattaforma rialzata di circa 10 mm, così i tasti stanno all'altezza del piano della MPK [V] |
| Vano hub e powerbank | 469–602 | 8–174 | coperchio con feritoie |

- **CASE-010** [D] La Flip DEVE stare aperta, con la metà inferiore inclinata di 15° (retro più alto) e lo schermo a circa 70° dall'orizzontale, cioè circa 20° all'indietro rispetto alla verticale. Così, da 50–70 cm, lo sguardo arriva quasi perpendicolare allo schermo. Lo schermo sporge di circa 10 mm dal retro della base.
- **CASE-011** [D] La culla della Flip DEVE avere aperture per le due porte USB-C, il jack delle cuffie e l'altoparlante. Le posizioni vanno misurate sulla console [V].
- **CASE-012** [D] Il canale dei cavi DEVE essere profondo almeno 26 mm dietro la MPK. Per il cavo USB-B conviene un connettore ad angolo di 90° [V].

## 4. Collegamenti
- **CASE-020** [O] Si usa la porta USB-C **di sopra** della Flip (OTG): con un apparecchio collegato passa da sola in modalità host. Mai forzare `otg_mode` (nota del second brain «Miyoo Flip e spruceOS - app native, SSH e gotcha»).
- **CASE-021** [O] Serve un **hub USB 2.0 semplice, senza PD né ricarica passante**. Le docking station per portatili non si accendono con la Flip.
- **CASE-022** [D] Hub non alimentato per default: MPK e pad prendono corrente dalla batteria della Flip, con l'RGB del pad spento. Se il consumo accorcia troppo l'autonomia, si passa a un hub USB-A alimentato da un powerbank nel vano, con un adattatore OTG USB-C → USB-A [V].
- **CASE-023** [O] La Flip si ricarica dalla porta di sotto, meglio se a console spenta. Il case NON DEVE collegare un caricatore alla Flip mentre è in modalità host senza una prova fatta con l'ok di Luigi.
- **CASE-024** [D] Pedale nel jack SUSTAIN della MPK. Audio dal jack della Flip verso cuffie o amplificatore.

## 5. Parti
| Parte | Materiale | Misure (mm) | Pezzi |
|---|---|---|---|
| Base | compensato 6 mm | 610 × 300 | 1 |
| Bordo del vano MPK | PETG | ≤ 240, alto 16 | 4 |
| Dorso posteriore | PETG, incastri a coda di rondine | ≈ 150 × 96 × 58 | 3 |
| Coperchi del canale cavi | PETG | ≈ 150 × 24 | 3 |
| Culla della Flip | PETG + appoggi in TPU | 100 × 90 | 1 |
| Piattaforma del pad | PETG | 133 × 110 × 10 | 1 |
| Vano hub e coperchio | PETG | 133 × 166 | 2 |
| Minuteria | viti M3 × 8 e inserti a caldo | — | ≈ 24 + 24 |

Filamento stimato: 600–800 g di PETG [D]. Peso totale con gli apparecchi: circa 2,8 kg [D].

## 6. Alternative scartate
- **Tutto stampato:** 610 mm non stanno nel piano da 250 mm. Servirebbero 6–8 pezzi incollati, e la base sarebbe meno rigida.
- **Guscio unico che smonta la MPK:** è il lavoro della fase 2, lo strumento dedicato.
- **Pad a sinistra:** comodo per «tasto + manopola» con due mani, ma la manopola grande del voicing finirebbe lontano dalla mano che suona i tasti.

## 7. Prossimi passi
1. Misurare il pad (ingombro, posizione delle manopole, porta) e la Flip (porte, jack, altoparlante, tasti).
2. Modello parametrico in OpenSCAD in `hardware/case/`, con tutte le misure in un solo file.
3. Stampa di prova della culla della Flip e della piattaforma del pad, le parti più incerte; poi i moduli del dorso.

## Questioni aperte
- [V] Misure del pad e posizione delle manopole.
- [V] Posizione di porte, jack e altoparlante della Flip.
- [V] Consumo di MPK + pad dalla Flip con un hub non alimentato.
- [V] Un hub USB 2.0 semplice funziona con la Flip insieme a MPK e pad (non ancora provato).
- Decisione di Luigi: legno + stampa (proposta) oppure tutto stampato.

## Dipendenze da altre sezioni
- `40`: mappa dei controlli e collegamento del pad (§8.10).
- `50`: porte USB, alimentazione e gotcha della Flip.
