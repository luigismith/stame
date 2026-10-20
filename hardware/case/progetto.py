"""progetto.py — il lavoro per Anycubic Slicer Next: i pezzi a più colori impaginati sui piatti della Kobra S1.

Luigi, 20/10/2026: «puoi creare tu il lavoro per la mia anycubic slicer next?»

Uso: python -I hardware/case/progetto.py       scrive hardware/case/out/stampa3d_nes/stame_kobra_s1.3mf
     (lo rifà anche multicolore.py --nes, ogni volta che rifà la cartella)

Un progetto 3MF come quelli che salva lo slicer (il formato di Bambu Studio 2.0, su cui è fatto Anycubic Slicer
Next 2.0): i pezzi di out/stampa3d_nes/ con le loro parti e i filamenti già assegnati, sei piatti (PIATTI), su ognuno
la torre di spurgo dove non tocca niente. Stampante, ugello e profilo della stampa vengono da un progetto salvato da
Luigi con il suo slicer (kobra_s1.json: Anycubic Kobra S1, ugello 0,4 d'acciaio, 0,20 mm High Quality); i
filamenti sono i tre PETG di multicolore.SCHEMI['nes'], tutti col profilo Anycubic PETG, e la stampa ha le
impostazioni di pezzi.md: 3 perimetri, 4 strati pieni sopra e sotto, riempimento giroide al 20 %. La visiera ha i
supporti, solo dal piatto; gli altri pezzi no. La prova di giunta non c'è: Luigi l'ha già stampata. Le anteprime
dei piatti le rifà lo slicer quando si affetta.
"""
import json
import math
import os
import struct
import sys
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import multicolore as MC             # noqa: E402

CARTELLA = os.path.join(QUI, 'out', MC.SCHEMI['nes']['cartella'])
USCITA = os.path.join(CARTELLA, 'stame_kobra_s1.3mf')
PIATTO = 250.0                       # il piano della Kobra S1; lo slicer mette i piatti a 1,2 volte la sua misura
PASSO = PIATTO * 1.2
# i piatti: nome, pezzi con l'angolo davanti a sinistra (mm sul piatto), angolo della torre di spurgo
PIATTI = [
    ('vasca sinistra', [('vasca_sx', (1.0, 5.0))], (214.0, 40.0)),
    ('vasca di centro', [('vasca_centro', (1.0, 5.0))], (214.0, 40.0)),
    ('vasca destra', [('vasca_dx', (1.0, 5.0))], (214.0, 40.0)),
    ('mascherina sinistra e culla della Flip', [('mascherina_1', (5.0, 119.0)), ('culla_flip', (5.0, 10.0))], (180.0, 30.0)),
    ('mascherina destra e visiera', [('mascherina_2', (5.0, 119.0)), ('visiera', (5.0, 30.0))], (180.0, 30.0)),
    ('piano della Flip', [('piano_flip', (5.0, 105.0))], (180.0, 30.0)),
]
CON_SUPPORTI = {'visiera'}
# pezzi.md: 3 perimetri, 4 strati pieni sopra e sotto, giroide al 20 %; la torre con un bordo di 3 mm, così accanto
# alle vasche larghe 208 ci sta
STAMPA = {'wall_loops': '3', 'top_shell_layers': '4', 'bottom_shell_layers': '4', 'sparse_infill_density': '20%',
          'sparse_infill_pattern': 'gyroid', 'enable_prime_tower': '1', 'prime_tower_brim_width': '3'}
# quanto si spurga passando da un filamento all'altro (mm³): dal grigio scuro al crema chiaro serve di più
SPURGO = {(1, 2): 400, (1, 3): 250, (2, 1): 150, (2, 3): 200, (3, 1): 150, (3, 2): 450}


def leggi_stl(path):
    """i triangoli di un STL binario"""
    with open(path, 'rb') as f:
        dati = f.read()
    n = struct.unpack_from('<I', dati, 80)[0]
    out = []
    for k in range(n):
        v = struct.unpack_from('<12f', dati, 84 + 50 * k)
        out.append((v[3:6], v[6:9], v[9:12]))
    return out


def colonne(n):
    """le colonne dei piatti, come le conta lo slicer: la radice arrotondata, una in più se la radice è più grande"""
    r = math.sqrt(n)
    return round(r) + 1 if r > round(r) else round(r)


def parti(nome, righe):
    """le parti di un pezzo con il loro filamento, dall'elenco di multicolore.py: [(parte, triangoli, filamento)]"""
    riga = next(r for r in righe if r['nome'] == nome)
    if len(riga['parti']) == 1:
        return [(nome, leggi_stl(os.path.join(CARTELLA, f'{nome}.stl')), riga['parti'][0][1])]
    return [(p, leggi_stl(os.path.join(CARTELLA, f'{nome}_{p}.stl')), f) for p, f in riga['parti']]


def mesh_xml(oid, uuid, tris, centro):
    idx, vert, facce = {}, [], []
    for t in tris:
        ii = []
        for v in t:
            k = tuple(round(c - o, 4) for c, o in zip(v, centro))
            if k not in idx:
                idx[k] = len(vert)
                vert.append(k)
            ii.append(idx[k])
        if len(set(ii)) == 3:
            facce.append(ii)
    vs = '\n'.join(f'     <vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in vert)
    ts = '\n'.join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in facce)
    return (f'  <object id="{oid}" p:UUID="{uuid}" type="model">\n   <mesh>\n    <vertices>\n{vs}\n    </vertices>\n'
            f'    <triangles>\n{ts}\n    </triangles>\n   </mesh>\n  </object>\n')


TESTA = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
         'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
         'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
         ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n')


def impostazioni():
    """kobra_s1.json con i tre filamenti di SCHEMI['nes'] e la stampa di pezzi.md"""
    with open(os.path.join(QUI, 'kobra_s1.json'), encoding='utf-8') as f:
        c = json.load(f)
    sc = MC.SCHEMI['nes']
    n = len(sc['nomi'])
    vecchi = len(c['filament_settings_id'])
    petg = c['filament_type'].index('PETG')
    for k, v in list(c.items()):                 # le liste dei filamenti: il profilo del PETG per tutti
        if isinstance(v, list) and len(v) == vecchi and k != 'printable_area':
            c[k] = [v[petg]] * n
    c['filament_colour'] = ['#%02X%02X%02X' % sc['tinta'][k] for k in sorted(sc['nomi'])]
    c['default_filament_colour'] = [''] * n
    c['filament_map'] = ['1'] * n
    c['inherits_group'] = c['inherits_group'][:1] + [''] * n + c['inherits_group'][-1:]
    c['flush_volumes_matrix'] = [str(SPURGO.get((a, b), 0)) for a in range(1, n + 1) for b in range(1, n + 1)]
    c['flush_volumes_vector'] = ['140'] * (2 * n)
    c['wipe_tower_x'] = [f'{t[0]:g}' for _, _, t in PIATTI]
    c['wipe_tower_y'] = [f'{t[1]:g}' for _, _, t in PIATTI]
    c.update(STAMPA)
    return c


def main():
    MC.genera(schema='nes')                     # rifà la cartella e, alla fine, il progetto (scrivi)


def scrivi(righe):
    """il progetto, dai file appena scritti in CARTELLA e dall'elenco delle parti con i filamenti (multicolore.genera)"""
    cols = colonne(len(PIATTI))
    file_mod, oggetti, articoli, impost, piatti, rels = {}, [], [], [], [], []
    oid = 0
    for i, (_, pezzi, _) in enumerate(PIATTI):
        ox, oy = (i % cols) * PASSO, -(i // cols) * PASSO
        istanze = []
        for nome, (x0, y0) in pezzi:
            pp = parti(nome, righe)
            pts = [v for _, tris, _ in pp for t in tris for v in t]
            lo = [min(p[k] for p in pts) for k in range(3)]
            hi = [max(p[k] for p in pts) for k in range(3)]
            centro = [(a + b) / 2 for a, b in zip(lo, hi)]
            assert x0 + hi[0] - lo[0] <= PIATTO and y0 + hi[1] - lo[1] <= PIATTO, f'{nome} non sta nel piatto'
            ids = []
            corpo = ''
            for parte, tris, fil in pp:
                oid += 1
                ids.append((oid, parte, fil))
                corpo += mesh_xml(oid, f'{oid:04x}0000-81cb-4c03-9d28-80fed5dfa1dc', tris, centro)
            percorso = f'/3D/Objects/{nome}_{oid}.model'
            file_mod[percorso[1:]] = TESTA + f' <resources>\n{corpo} </resources>\n <build/>\n</model>\n'
            rels.append(percorso)
            oid += 1
            comp = ''.join(f'    <component p:path="{percorso}" objectid="{k}" p:UUID="{k:04x}0000-b206-40ff-9872-83e8017abed1" '
                           'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n' for k, _, _ in ids)
            oggetti.append(f'  <object id="{oid}" p:UUID="{oid:08x}-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n'
                           f'   <components>\n{comp}   </components>\n  </object>\n')
            tx, ty, tz = ox + x0 + (hi[0] - lo[0]) / 2, oy + y0 + (hi[1] - lo[1]) / 2, (hi[2] - lo[2]) / 2
            articoli.append(f'  <item objectid="{oid}" p:UUID="{oid:08x}-b1ec-4553-aec9-835e5b724bb4" '
                            f'transform="1 0 0 0 1 0 0 0 1 {tx:.4f} {ty:.4f} {tz:.4f}" printable="1"/>\n')
            extra = ('    <metadata key="enable_support" value="1"/>\n    <metadata key="support_type" value="tree(auto)"/>\n'
                     if nome in CON_SUPPORTI else '')
            parti_xml = ''.join(
                f'    <part id="{k}" subtype="normal_part">\n      <metadata key="name" value="{parte}"/>\n'
                '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                f'      <metadata key="extruder" value="{fil}"/>\n'
                '      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                '    </part>\n' for k, parte, fil in ids)
            impost.append(f'  <object id="{oid}">\n    <metadata key="name" value="{nome}"/>\n'
                          f'    <metadata key="extruder" value="{ids[0][2]}"/>\n{extra}{parti_xml}  </object>\n')
            istanze.append(f'    <model_instance>\n      <metadata key="object_id" value="{oid}"/>\n'
                           f'      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{1000 + oid}"/>\n'
                           '    </model_instance>\n')
        # il nome del piatto resta vuoto: con un nome lo slicer, dalla riga di comando, si ferma (20/10/2026, 2.0.0.3);
        # i piatti sono elencati in pezzi.md
        piatti.append(f'  <plate>\n    <metadata key="plater_id" value="{i + 1}"/>\n    <metadata key="plater_name" value=""/>\n'
                      '    <metadata key="locked" value="false"/>\n    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
                      f'    <metadata key="filament_maps" value="{" ".join(["1"] * len(MC.SCHEMI["nes"]["nomi"]))}"/>\n'
                      + ''.join(istanze) + '  </plate>\n')
    modello = (TESTA.replace(' <metadata name="BambuStudio:3mfVersion">1</metadata>\n',
                             ' <metadata name="Application">BambuStudio-2.0.0.3</metadata>\n'
                             ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
                             ' <metadata name="Title">Stame, la console nei colori del NES</metadata>\n')
               + ' <resources>\n' + ''.join(oggetti) + ' </resources>\n <build>\n' + ''.join(articoli) + ' </build>\n</model>\n')
    config = '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + ''.join(impost) + ''.join(piatti) + '</config>\n'
    tipi = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
            ' <Default Extension="png" ContentType="image/png"/>\n'
            ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
    radice = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
              ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
              '</Relationships>\n')
    rel_mod = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
               + ''.join(f' <Relationship Target="{p}" Id="rel-{k}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                         for k, p in enumerate(rels, 1)) + '</Relationships>\n')
    info = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n'
            '    <header_item key="X-ACNext-Client-Type" value="slicer"/>\n'
            '    <header_item key="X-ACNext-Client-Version" value="2.0.0.3 20260904033713"/>\n  </header>\n</config>\n')
    voci = [('[Content_Types].xml', tipi), ('_rels/.rels', radice), ('3D/3dmodel.model', modello),
            ('3D/_rels/3dmodel.model.rels', rel_mod)] + sorted(file_mod.items()) + [
            ('Metadata/project_settings.config', json.dumps(impostazioni(), indent=4, ensure_ascii=False) + '\n'),
            ('Metadata/model_settings.config', config), ('Metadata/slice_info.config', info)]
    with zipfile.ZipFile(USCITA, 'w', zipfile.ZIP_DEFLATED) as z:
        for nome, testo in voci:
            zi = zipfile.ZipInfo(nome, date_time=(2026, 1, 1, 0, 0, 0))   # data fissa: lo stesso progetto dà lo stesso file
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, testo)
    print(f'{USCITA}: {len(PIATTI)} piatti, {sum(len(p) for _, p, _ in PIATTI)} pezzi')


if __name__ == '__main__':
    main()
