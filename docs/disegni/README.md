# Disegni

- `stame-plancia-e-controlli.pdf` — come appare la plancia sulla Miyoo Flip, come funzionano i controlli (MPK mini Plus, macro pad BRIMFORD, tasti della Flip), ricette d’uso e case. Bozza 4, 15/10/2026, 13 pagine: la plancia calma è fatta di fotogrammi veri del renderer, il case è la bozza 2 di `60-case.md`.
- `stame-plancia-e-controlli.html` — la stessa cosa in HTML.
- `sorgenti/` — gli script Python che generano l'HTML; il PDF si stampa con Chrome:

```
cd docs/disegni/sorgenti
python documento.py ../stame-plancia-e-controlli.html
chrome --headless=new --no-pdf-header-footer --print-to-pdf=../stame-plancia-e-controlli.pdf ../stame-plancia-e-controlli.html
```

La plancia (`plancia.py`) segue `docs/specifica/30-interfaccia.md` §4: se cambia la specifica, va aggiornato anche il disegno.
