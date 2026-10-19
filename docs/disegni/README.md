# Disegni

- `stame-plancia-e-controlli.pdf` — come appare la plancia sulla Miyoo Flip, come funzionano i controlli (MPK mini Plus, macro pad BRIMFORD, tasti della Flip), ricette d’uso e case. Bozza 4, 15/10/2026, 13 pagine: la plancia calma è fatta di fotogrammi veri del renderer, il case è la bozza 2 di `60-case.md`. Il 18/10/2026 i fotogrammi sono stati rifatti nel tema Giorno, il default (`stame-render --scene`); le pagine dei controlli e del case sono ancora quelle del 15/10 (MPK mini Plus, bozza 2): per la mappa di oggi valgono il manuale e il prontuario.
- `stame-plancia-e-controlli.html` — la stessa cosa in HTML.
- `sorgenti/hardware.py` — i disegni dei comandi hardware del manuale e del prontuario (`docs/manuale/img/{postazione,mk4,pad,flip}.svg`): la MPK mini IV con la mappa del preset DAW, il macro pad con le sue etichette, i tasti della Flip e la postazione vista dall'alto. Misure da `hardware/case/misure.py`, nomi dal manuale: `python -I docs/disegni/sorgenti/hardware.py` (19/10/2026).
- `sorgenti/` — gli script Python che generano l'HTML; il PDF si stampa con Chrome:

```
cd docs/disegni/sorgenti
python documento.py ../stame-plancia-e-controlli.html
chrome --headless=new --no-pdf-header-footer --print-to-pdf=../stame-plancia-e-controlli.pdf ../stame-plancia-e-controlli.html
```

La plancia (`plancia.py`) segue `docs/specifica/30-interfaccia.md` §4: se cambia la specifica, va aggiornato anche il disegno.
