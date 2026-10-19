"""kits.py — la libreria dei kit di batteria sintetizzati di Stame (specifica 20, SND-540…SND-543).

Ogni kit ha una ricetta per ognuno dei dodici strumenti di ACC-212 (cassa, rimshot, rullante, battimani,
charleston chiuso, tom basso, charleston aperto, tom alto, maracas, conga, campanaccio, piatto), nello
stesso ordine dei tasti, così Beat, loop inventato, tasti e pad suonano qualunque kit. La ricetta è quella
di drum_rec_t in src/dsp/drums.h: un tono (seno, quadra, FM o sei quadre di metallo) con il salto di pitch,
un rumore filtrato, un clic, drive, riduzione di campionamento e di bit. Lo script scrive
  - src/dsp/drum_kits.c: le ricette come tabelle costanti;
  - src/dsp/drum_kits.h: quanti kit e i loro indici (DK_KIT_*).
I guadagni pareggiano i livelli: ogni strumento colpito a 127 arriva al picco di LIVELLO (dBFS, mono, prima
del volume del Beat), dal picco misurato con guadagno 1 da `stame-render --kits` (PICCO_DB, da incollare
qui dopo ogni cambio di una ricetta). Sono kit di Stame, progettati sul carattere del nome.

    python -I tools/kits.py
"""
import math
import os
import re

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

NONE, SINE, SQUARE, FM, METAL = range(5)            # forma del tono (DK_*)
LP, BP, HP = range(3)                               # filtro
HAT808, COWBELL, BELL, CYMB = range(4)              # rapporti del metallo (METAL_R in drums.c)
INST = ['kick', 'rim', 'snare', 'clap', 'chh', 'tom_lo', 'ohh', 'tom_hi', 'maracas', 'conga', 'cowbell', 'cymbal']
PAN = [0.0, -0.15, -0.05, -0.1, 0.25, -0.3, 0.25, 0.3, 0.35, -0.25, 0.2, 0.15]
# picco di ogni strumento a velocity 127 (dBFS, mono): la cassa come i campioni (−1), il resto un po' sotto
LIVELLO = [-1.0, -3.0, -1.5, -2.0, -4.0, -2.0, -4.0, -2.0, -5.0, -2.5, -4.0, -5.0]


def r(osc=NONE, f0=100.0, pa=0.0, tp=0.01, ta=0.1, tone=1.0, r2=1.0, l2=0.0, flt=LP, fc=20000.0, q=0.707,
      tutto=False, tn=0.05, noise=0.0, bursts=0, nhold=0, hold=0, bits=0, click=0.0, drive=0.0, att=0.0,
      dur=None, pan=None):
    if osc == NONE:
        tone = 0.0
    return dict(osc=osc, f0=f0, pa=pa, tp=tp, ta=ta, tone=tone, r2=r2, l2=l2, flt=flt, fc=fc, q=q,
                tutto=tutto, tn=tn, noise=noise, bursts=bursts, nhold=nhold, hold=hold, bits=bits, click=click,
                drive=drive, att=att, dur=dur, pan=pan)


# ---- archetipi: ognuno è una ricetta con i default del suo strumento, da ritoccare per kit ----
def kick(f0=52.0, pa=1.5, tp=0.03, ta=0.25, click=0.1, noise=0.0, fc=1200.0, tn=0.02, **kw):
    return r(SINE, f0=f0, pa=pa, tp=tp, ta=ta, click=click, noise=noise, flt=LP, fc=fc, tn=tn, **kw)


def snare(f0=185.0, r2=1.8, l2=0.5, ta=0.07, tone=0.7, pa=0.2, tp=0.01, flt=HP, fc=1800.0, q=0.7, tn=0.12,
          noise=1.0, **kw):
    return r(SINE, f0=f0, r2=r2, l2=l2, ta=ta, tone=tone, pa=pa, tp=tp, flt=flt, fc=fc, q=q, tn=tn, noise=noise, **kw)


def clap(bursts=4, fc=1100.0, q=1.3, tn=0.12, flt=BP, **kw):
    return r(NONE, bursts=bursts, flt=flt, fc=fc, q=q, tn=tn, noise=1.0, **kw)


def hat(f0=205.3, metal=HAT808, flt=BP, fc=9000.0, q=0.8, ta=0.04, noise=0.15, tn=None, **kw):
    return r(METAL, f0=f0, r2=metal, flt=flt, fc=fc, q=q, ta=ta, noise=noise, tn=ta if tn is None else tn, **kw)


def fruscio(fc=8000.0, flt=HP, q=0.7, tn=0.03, **kw):
    """solo rumore filtrato: charleston dei vecchi preset, shaker, maracas, spazzole"""
    return r(NONE, flt=flt, fc=fc, q=q, tn=tn, noise=1.0, **kw)


def tom(f0=90.0, pa=0.3, tp=0.06, ta=0.22, noise=0.05, fc=900.0, tn=0.03, **kw):
    return r(SINE, f0=f0, pa=pa, tp=tp, ta=ta, noise=noise, flt=LP, fc=fc, tn=tn, **kw)


def cowbell(f0=540.0, fc=1200.0, q=1.2, ta=0.09, **kw):
    return r(METAL, f0=f0, r2=COWBELL, flt=BP, fc=fc, q=q, ta=ta, **kw)


def cymbal(f0=205.3, metal=HAT808, flt=HP, fc=6000.0, q=0.7, ta=1.0, noise=0.4, tn=0.6, **kw):
    return r(METAL, f0=f0, r2=metal, flt=flt, fc=fc, q=q, ta=ta, noise=noise, tn=tn, **kw)


def campana(f0=800.0, metal=BELL, flt=BP, fc=3000.0, q=2.0, ta=0.3, **kw):
    """sei quadre sui modi di una piastra: campane, gong, incudini, lamiere"""
    return r(METAL, f0=f0, r2=metal, flt=flt, fc=fc, q=q, ta=ta, **kw)


def fm(f0=440.0, r2=1.41, l2=0.5, ta=0.1, **kw):
    """seno modulato in fase: legni, campane di vetro, latte, zap"""
    return r(FM, f0=f0, r2=r2, l2=l2, ta=ta, **kw)


def quadra(f0=440.0, ta=0.1, **kw):
    return r(SQUARE, f0=f0, ta=ta, **kw)


def seno(f0=440.0, ta=0.1, **kw):
    return r(SINE, f0=f0, ta=ta, **kw)


def kit(nome, stile, **strumenti):
    assert set(strumenti) == set(INST), (nome, set(INST) ^ set(strumenti))
    return (nome, stile, [strumenti[i] for i in INST])


# ---- la libreria: 35 kit dopo i cinque di sempre (Studio, Jazz, 808, Techno a campioni, Chip) ----
KITS = [
    # drum machine analogiche
    kit('808 Boom', 'analog',
        kick=kick(52, pa=1.6, tp=0.035, ta=0.22, click=0.15),
        rim=seno(1700, ta=0.010, r2=0.27, l2=0.6, noise=0.3, flt=HP, fc=2000, tn=0.004),
        snare=snare(180, r2=1.83, l2=0.55, ta=0.06, fc=1500, tn=0.12, noise=0.9),
        clap=clap(4, fc=1100, q=1.4, tn=0.12),
        chh=hat(205.3, ta=0.04),
        tom_lo=tom(85, pa=0.25, tp=0.08, ta=0.22),
        ohh=hat(205.3, ta=0.30),
        tom_hi=tom(140, pa=0.25, tp=0.06, ta=0.18),
        maracas=fruscio(5000, tn=0.022),
        conga=tom(300, pa=0.15, tp=0.02, ta=0.09, noise=0.0),
        cowbell=cowbell(540, fc=1200, ta=0.09),
        cymbal=cymbal(205.3, ta=1.0)),
    kit('808 Trap', 'analog',
        kick=kick(46, pa=2.5, tp=0.05, ta=0.6, click=0.1, drive=1.5),
        rim=seno(2000, ta=0.008, noise=0.4, flt=HP, fc=3000, tn=0.006),
        snare=snare(220, r2=1.75, l2=0.4, ta=0.05, fc=2500, tn=0.09, click=0.2),
        clap=clap(3, fc=1300, q=1.0, tn=0.18),
        chh=hat(250, fc=8500, ta=0.025, noise=0.3),
        tom_lo=tom(100, pa=0.4, ta=0.25),
        ohh=hat(250, fc=8500, ta=0.25, noise=0.3),
        tom_hi=tom(160, pa=0.4, ta=0.2),
        maracas=fruscio(6000, tn=0.03, att=0.008),
        conga=tom(400, pa=0.3, tp=0.02, ta=0.08, noise=0.0),
        cowbell=cowbell(560, fc=1400),
        cymbal=cymbal(320, metal=CYMB, fc=5000, ta=1.2, noise=0.5)),
    kit('909 House', 'analog',
        kick=kick(52, pa=4.0, tp=0.012, ta=0.18, click=0.4, drive=0.5),
        rim=seno(1800, ta=0.012, r2=0.28, l2=0.5, noise=0.3, flt=HP, fc=2500, tn=0.008),
        snare=snare(200, r2=1.8, l2=0.5, pa=0.4, tp=0.015, ta=0.07, tone=0.8, flt=BP, fc=5000, q=0.5, tn=0.16, noise=1.1),
        clap=clap(4, fc=1200, q=1.0, tn=0.15),
        chh=hat(310, metal=CYMB, fc=8000, flt=HP, ta=0.035, noise=0.4),
        tom_lo=tom(95, pa=0.7, tp=0.04, ta=0.2, noise=0.15, tn=0.05),
        ohh=hat(310, metal=CYMB, fc=8000, flt=HP, ta=0.32, noise=0.4),
        tom_hi=tom(150, pa=0.7, tp=0.04, ta=0.17, noise=0.15, tn=0.05),
        maracas=fruscio(6000, tn=0.025),
        conga=tom(360, pa=0.3, tp=0.01, ta=0.07, noise=0.0),
        cowbell=cowbell(587, fc=1600, ta=0.08),
        cymbal=cymbal(450, metal=CYMB, fc=5000, ta=1.2, noise=0.3, tn=0.8)),
    kit('909 Rave', 'analog',
        kick=kick(48, pa=4.0, tp=0.014, ta=0.25, click=0.6, drive=4.0),
        rim=seno(2200, ta=0.01, noise=0.4, flt=HP, fc=3000, tn=0.008, drive=1.0),
        snare=snare(240, r2=1.8, l2=0.5, pa=0.4, ta=0.07, flt=BP, fc=4500, q=0.5, tn=0.2, noise=1.3, drive=2.0),
        clap=clap(5, fc=1200, q=1.0, tn=0.22, drive=1.0),
        chh=hat(330, metal=CYMB, fc=9000, flt=HP, ta=0.03, noise=0.4, drive=1.0),
        tom_lo=tom(110, pa=2.0, tp=0.03, ta=0.2, drive=1.0),
        ohh=hat(330, metal=CYMB, fc=9000, flt=HP, ta=0.4, noise=0.4, drive=1.0),
        tom_hi=tom(170, pa=2.0, tp=0.03, ta=0.17, drive=1.0),
        maracas=fruscio(8000, flt=BP, q=1.0, tn=0.025),
        conga=tom(420, pa=0.5, tp=0.01, ta=0.07, noise=0.0),
        cowbell=cowbell(610, fc=1700, drive=2.0),
        cymbal=cymbal(400, metal=CYMB, fc=4500, ta=1.5, noise=0.6, tn=1.0)),
    kit('CR Rhythm', 'analog',
        kick=kick(60, pa=0.3, tp=0.02, ta=0.12, click=0.0),
        rim=seno(2500, ta=0.025),
        snare=snare(220, l2=0.0, ta=0.04, flt=BP, fc=2500, q=0.8, tn=0.07, noise=0.6),
        clap=clap(3, fc=6500, q=1.0, flt=HP, tn=0.12),
        chh=fruscio(8000, q=1.2, tn=0.02),
        tom_lo=tom(180, pa=0.1, ta=0.07, noise=0.0),
        ohh=fruscio(7000, tn=0.18),
        tom_hi=tom(270, pa=0.1, ta=0.06, noise=0.0),
        maracas=fruscio(5000, tn=0.04, att=0.01),
        conga=tom(210, pa=0.1, ta=0.10, noise=0.0),
        cowbell=cowbell(700, fc=2000, ta=0.05),
        cymbal=cymbal(300, fc=7000, ta=0.6, noise=0.5, tn=0.5)),
    kit('606 Tick', 'analog',
        kick=kick(62, pa=0.8, tp=0.01, ta=0.08, click=0.3),
        rim=seno(2200, ta=0.008),
        snare=snare(240, l2=0.3, ta=0.03, fc=3500, tn=0.07),
        clap=clap(3, fc=1600, tn=0.08),
        chh=hat(260, fc=9500, flt=HP, ta=0.02, noise=0.2),
        tom_lo=tom(130, pa=0.3, ta=0.12, noise=0.0),
        ohh=hat(260, fc=9500, flt=HP, ta=0.2, noise=0.2),
        tom_hi=tom(195, pa=0.3, ta=0.1, noise=0.0),
        maracas=fruscio(7000, tn=0.015),
        conga=tom(380, pa=0.2, ta=0.05, noise=0.0),
        cowbell=cowbell(640, fc=2000, ta=0.04),
        cymbal=cymbal(260, fc=7500, ta=0.5)),
    kit('Hex Toms', 'electronic',
        kick=kick(60, pa=2.0, tp=0.06, ta=0.2, click=0.2, noise=0.3, fc=600, tn=0.05),
        rim=seno(1200, pa=0.5, tp=0.005, ta=0.015, noise=0.5, flt=HP, fc=2500, tn=0.01),
        snare=snare(250, l2=0.0, pa=1.0, tp=0.05, ta=0.12, flt=BP, fc=2000, q=0.7, tn=0.2, noise=0.9),
        clap=clap(4, fc=1000),
        chh=hat(220, fc=8000, flt=HP, ta=0.03),
        tom_lo=tom(80, pa=1.5, tp=0.12, ta=0.35, noise=0.25, tn=0.08),
        ohh=hat(220, fc=8000, flt=HP, ta=0.3),
        tom_hi=tom(150, pa=1.5, tp=0.1, ta=0.3, noise=0.2, tn=0.08),
        maracas=fruscio(6000, tn=0.03),
        conga=tom(115, pa=1.5, tp=0.11, ta=0.32, noise=0.2, tn=0.08),
        cowbell=cowbell(560, fc=1500),
        cymbal=cymbal(380, metal=CYMB, fc=5000, ta=1.2, noise=0.5)),
    kit('Syndrum Disco', 'electronic',
        kick=kick(55, pa=0.6, ta=0.18, click=0.3, noise=0.2, fc=3000),
        rim=seno(900, ta=0.02, r2=2.3, l2=0.4, noise=0.4, flt=BP, fc=3000, q=1.5, tn=0.01),
        snare=snare(180, ta=0.08, flt=BP, fc=2500, q=0.7, tn=0.16),
        clap=clap(4, tn=0.14),
        chh=hat(400, metal=CYMB, fc=8000, flt=HP, ta=0.04, noise=0.6),
        tom_lo=tom(160, pa=2.5, tp=0.15, ta=0.4, noise=0.0),
        ohh=hat(400, metal=CYMB, fc=8000, flt=HP, ta=0.3, noise=0.6),
        tom_hi=tom(260, pa=2.5, tp=0.12, ta=0.35, noise=0.0),
        maracas=fruscio(6000, tn=0.03, att=0.006),
        conga=tom(420, pa=1.8, tp=0.1, ta=0.25, noise=0.0),
        cowbell=cowbell(560, fc=1800, q=1.5, ta=0.12),
        cymbal=cymbal(380, metal=CYMB, fc=4500, ta=1.6, noise=0.6, tn=1.2)),
    kit('Robot Pop', 'electronic',
        kick=kick(70, pa=0.5, tp=0.008, ta=0.07, click=0.4),
        rim=seno(3000, ta=0.004, click=0.5),
        snare=snare(300, l2=0.0, ta=0.03, tone=0.5, flt=BP, fc=1500, q=4.0, tn=0.06),
        clap=clap(2, fc=2500, q=3.0, tn=0.05),
        chh=fruscio(9000, flt=BP, q=4.0, tn=0.02),
        tom_lo=tom(220, pa=0.1, ta=0.08, noise=0.0),
        ohh=fruscio(8000, flt=BP, q=3.0, tn=0.15),
        tom_hi=tom(330, pa=0.1, ta=0.08, noise=0.0),
        maracas=fruscio(6000, flt=BP, q=2.0, tn=0.02),
        conga=tom(500, pa=0.05, ta=0.04, noise=0.0),
        cowbell=fm(800, r2=1.41, l2=0.4, ta=0.1),
        cymbal=fruscio(7000, flt=BP, q=1.5, tn=0.5)),
    kit('Linn Pop', 'eighties',
        kick=kick(58, pa=1.2, tp=0.02, ta=0.14, click=0.6, noise=0.25, fc=2500, tn=0.01, drive=0.5),
        rim=seno(900, ta=0.02, r2=2.3, l2=0.4, noise=0.5, flt=BP, fc=3000, q=2.0, tn=0.01),
        snare=snare(190, r2=1.6, l2=0.5, ta=0.09, flt=BP, fc=4000, q=0.6, tn=0.18, click=0.3),
        clap=clap(3, fc=1500, q=1.2, tn=0.2),
        chh=hat(400, metal=CYMB, fc=9000, flt=HP, q=0.7, ta=0.035, noise=0.6, tone=0.6),
        tom_lo=tom(110, pa=0.5, tp=0.05, ta=0.3, noise=0.2, fc=1500, tn=0.04),
        ohh=hat(400, metal=CYMB, fc=9000, flt=HP, q=0.7, ta=0.35, noise=0.6, tone=0.6),
        tom_hi=tom(165, pa=0.5, tp=0.05, ta=0.25, noise=0.2, fc=1500, tn=0.04),
        maracas=r(METAL, f0=2800, r2=BELL, flt=HP, fc=7000, ta=0.08, tone=0.4, noise=1.0, tn=0.1, bursts=2),
        conga=tom(300, pa=0.2, ta=0.12, noise=0.0),
        cowbell=cowbell(560, fc=1800, q=1.5, ta=0.12),
        cymbal=cymbal(380, metal=CYMB, fc=4500, ta=1.6, noise=0.6, tn=1.2)),
    kit('Gated 80s', 'eighties',
        kick=kick(55, pa=1.0, ta=0.2, click=0.5, drive=1.0),
        rim=seno(900, ta=0.02, r2=2.3, l2=0.4, noise=0.5, flt=BP, fc=3000, q=2.0, tn=0.01),
        snare=snare(200, ta=0.1, flt=BP, fc=3000, q=0.5, tn=0.6, noise=1.2, dur=0.32),
        clap=clap(4, tn=0.5, dur=0.3),
        chh=hat(400, metal=CYMB, fc=8000, flt=HP, ta=0.035, noise=0.6),
        tom_lo=tom(90, pa=0.6, ta=0.6, noise=0.3, fc=1200, tn=0.4, dur=0.45),
        ohh=hat(400, metal=CYMB, fc=8000, flt=HP, ta=0.3, noise=0.6),
        tom_hi=tom(140, pa=0.6, ta=0.6, noise=0.3, fc=1200, tn=0.4, dur=0.4),
        maracas=fruscio(6000, tn=0.03, att=0.006),
        conga=tom(115, pa=0.6, ta=0.6, noise=0.3, fc=1200, tn=0.4, dur=0.42),
        cowbell=cowbell(560, fc=1800),
        cymbal=cymbal(380, metal=CYMB, fc=4500, ta=1.8, noise=0.6, tn=1.4)),
    # techno, house, dub
    kit('Minimal Click', 'techno',
        kick=kick(55, pa=1.5, tp=0.006, ta=0.09, click=0.2),
        rim=seno(1900, ta=0.006),
        snare=snare(400, l2=0.0, ta=0.015, tone=0.5, flt=BP, fc=3500, q=2.0, tn=0.03),
        clap=clap(2, fc=2000, q=2.0, tn=0.04),
        chh=fruscio(10000, tn=0.01),
        tom_lo=tom(160, pa=0.4, tp=0.01, ta=0.04, noise=0.0),
        ohh=fruscio(9000, tn=0.08),
        tom_hi=tom(240, pa=0.4, tp=0.01, ta=0.04, noise=0.0),
        maracas=fruscio(8000, tn=0.008),
        conga=tom(600, pa=0.2, tp=0.005, ta=0.02, noise=0.0),
        cowbell=fm(1200, r2=2.0, l2=0.3, ta=0.03),
        cymbal=cymbal(500, metal=CYMB, fc=8000, ta=0.3, tone=0.3, noise=1.0, tn=0.3)),
    kit('Dub Yard', 'dub',
        kick=kick(48, pa=0.8, tp=0.03, ta=0.28, click=0.05),
        rim=seno(1600, ta=0.03, r2=0.3, l2=0.6),
        snare=snare(160, ta=0.1, flt=BP, fc=1800, q=0.6, tn=0.25, noise=0.8),
        clap=clap(3, fc=900, tn=0.25),
        chh=hat(205.3, fc=6500, flt=HP, ta=0.04, tone=0.4, noise=1.0),
        tom_lo=tom(75, pa=0.3, ta=0.35),
        ohh=hat(205.3, fc=6500, flt=HP, ta=0.35, tone=0.4, noise=1.0),
        tom_hi=tom(110, pa=0.3, ta=0.3),
        maracas=fruscio(4500, flt=BP, q=1.0, tn=0.04, att=0.006),
        conga=tom(200, pa=0.2, ta=0.15, noise=0.0),
        cowbell=fm(520, r2=1.5, l2=0.5, ta=0.15),
        cymbal=cymbal(420, metal=CYMB, fc=4000, ta=1.5, noise=0.5)),
    kit('2-Step', 'garage',
        kick=kick(54, pa=2.2, tp=0.01, ta=0.12, click=0.3, drive=1.0),
        rim=seno(1700, ta=0.012, noise=0.3, flt=HP, fc=3000, tn=0.005),
        snare=snare(230, ta=0.04, fc=2800, tn=0.11, noise=1.1),
        clap=clap(3, fc=1700, tn=0.1),
        chh=hat(420, metal=CYMB, fc=9000, flt=HP, ta=0.02, noise=0.4),
        tom_lo=tom(120, pa=0.5, ta=0.15),
        ohh=hat(420, metal=CYMB, fc=9000, flt=HP, ta=0.18, noise=0.4),
        tom_hi=tom(180, pa=0.5, ta=0.12),
        maracas=fruscio(7000, tn=0.02),
        conga=tom(350, pa=0.3, tp=0.01, ta=0.05, noise=0.0),
        cowbell=fm(1000, r2=1.41, l2=0.5, ta=0.06),
        cymbal=cymbal(460, metal=CYMB, fc=6000, ta=0.8)),
    kit('Jungle', 'breaks',
        kick=kick(60, pa=1.0, ta=0.12, click=0.5, noise=0.3, fc=2500, tn=0.015, drive=1.0, hold=2, bits=512),
        rim=seno(1100, ta=0.02, r2=2.3, l2=0.4, noise=0.5, flt=BP, fc=3500, q=1.5, tn=0.01, hold=2, bits=512),
        snare=snare(260, r2=1.6, l2=0.5, ta=0.07, flt=BP, fc=4500, q=0.6, tn=0.15, click=0.4, drive=0.8, hold=2, bits=512),
        clap=clap(3, fc=1600, tn=0.12, hold=2, bits=512),
        chh=hat(450, metal=CYMB, fc=9000, flt=HP, ta=0.03, noise=0.6, hold=2, bits=512),
        tom_lo=tom(130, pa=0.4, ta=0.2, noise=0.2, hold=2, bits=512),
        ohh=hat(450, metal=CYMB, fc=9000, flt=HP, ta=0.25, noise=0.6, hold=2, bits=512),
        tom_hi=tom(200, pa=0.4, ta=0.16, noise=0.2, hold=2, bits=512),
        maracas=fruscio(6000, tn=0.03, att=0.004, hold=2, bits=512),
        conga=tom(300, pa=0.2, ta=0.08, noise=0.0, hold=2, bits=512),
        cowbell=cowbell(600, fc=1800, hold=2, bits=512),
        cymbal=cymbal(520, metal=CYMB, flt=BP, fc=6500, q=0.7, ta=1.4, noise=0.3, tn=0.9, hold=2, bits=512)),
    # industriale e glitch
    kit('Iron Mill', 'industrial',
        kick=kick(50, pa=3.0, tp=0.02, ta=0.25, click=0.6, noise=0.5, fc=1500, tn=0.05, drive=6.0),
        rim=campana(800, fc=3000, q=3.0, ta=0.03, drive=3.0),
        snare=snare(160, l2=0.0, ta=0.06, tone=0.5, flt=BP, fc=1500, q=0.8, tn=0.18, noise=1.4, drive=5.0, hold=2),
        clap=clap(5, fc=900, q=0.8, tn=0.25, drive=4.0),
        chh=campana(1500, flt=HP, fc=6000, q=0.7, ta=0.04, noise=0.5, tn=0.04, drive=2.0),
        tom_lo=tom(70, pa=2.0, tp=0.05, ta=0.3, noise=0.4, fc=800, tn=0.06, drive=4.0),
        ohh=campana(1300, flt=HP, fc=5000, q=0.7, ta=0.4, noise=0.5, tn=0.3, drive=2.0),
        tom_hi=campana(220, fc=1200, q=2.0, ta=0.35, drive=3.0),
        maracas=fruscio(3000, bursts=3, tn=0.05, drive=2.0),
        conga=fm(300, r2=3.7, l2=1.5, ta=0.15, drive=2.0),
        cowbell=campana(450, fc=2200, q=4.0, ta=0.25, drive=2.0),
        cymbal=campana(600, flt=HP, fc=2500, q=0.7, ta=1.5, noise=1.0, tn=1.2, drive=3.0)),
    kit('Scrap Yard', 'industrial',
        kick=fm(50, r2=1.5, l2=0.8, ta=0.2, pa=1.0, tp=0.02, drive=2.0),
        rim=fm(1300, r2=3.3, l2=1.0, ta=0.02),
        snare=campana(400, fc=2500, q=1.5, ta=0.1, tone=0.6, noise=1.0, tn=0.1),
        clap=clap(4, fc=1800, q=2.0, tn=0.08),
        chh=fm(3000, r2=1.41, l2=2.0, ta=0.02, noise=0.3, flt=HP, fc=5000, tn=0.02),
        tom_lo=fm(120, r2=2.3, l2=0.9, ta=0.3, pa=0.3, tp=0.03),
        ohh=campana(900, flt=HP, fc=5000, q=0.7, ta=0.3),
        tom_hi=fm(200, r2=2.3, l2=0.8, ta=0.25, pa=0.3, tp=0.03),
        maracas=fruscio(5000, flt=BP, q=2.0, bursts=2, tn=0.03),
        conga=fm(330, r2=1.73, l2=0.7, ta=0.12),
        cowbell=campana(600, fc=1800, q=3.0, ta=0.4),
        cymbal=campana(350, flt=HP, fc=2000, q=0.7, ta=2.0, noise=0.3, tn=1.0)),
    kit('Glitch Bits', 'glitch',
        kick=kick(60, pa=3.0, tp=0.01, ta=0.07, click=0.2, drive=2.0, hold=3, bits=16),
        rim=quadra(2500, ta=0.005, hold=2),
        snare=snare(500, l2=0.0, ta=0.01, tone=0.5, flt=BP, fc=3000, q=1.0, tn=0.05, hold=6, bits=6),
        clap=clap(6, fc=2000, q=1.0, tn=0.02, hold=4),
        chh=fruscio(9000, tn=0.008, hold=2, bits=4),
        tom_lo=quadra(200, pa=4.0, tp=0.02, ta=0.08, hold=2),
        ohh=fruscio(7000, tn=0.07, hold=5, bits=5),
        tom_hi=fm(900, r2=1.5, l2=2.0, pa=-0.5, tp=0.05, ta=0.06),
        maracas=fruscio(6000, bursts=3, tn=0.004, hold=3),
        conga=quadra(700, pa=1.0, tp=0.005, ta=0.03, bits=4),
        cowbell=fm(1500, r2=0.5, l2=3.0, ta=0.05, hold=8, bits=3),
        cymbal=fruscio(5000, tn=0.4, att=0.3, hold=8, bits=4, dur=0.62)),
    kit('Data Rot', 'glitch',
        kick=kick(52, pa=6.0, tp=0.004, ta=0.12, click=0.3, drive=3.0, hold=2, bits=24),
        rim=fm(4000, r2=0.7, l2=1.0, ta=0.004),
        snare=r(SQUARE, f0=300, ta=0.03, tone=0.6, flt=LP, fc=2500, tn=0.08, noise=1.0, hold=10, bits=4),
        clap=clap(8, fc=1500, q=2.0, tn=0.015, hold=2),
        chh=fm(7000, r2=1.33, l2=3.0, ta=0.01),
        tom_lo=seno(300, pa=-0.7, tp=0.06, ta=0.1),
        ohh=fm(6000, r2=1.33, l2=3.0, ta=0.15, hold=3),
        tom_hi=quadra(1200, pa=-0.6, tp=0.03, ta=0.05, hold=3),
        maracas=fruscio(3500, flt=BP, q=4.0, bursts=4, tn=0.006),
        conga=fm(220, r2=7.1, l2=1.5, ta=0.08),
        cowbell=quadra(1000, r2=1.06, l2=1.0, ta=0.12, bits=6),
        cymbal=fruscio(3000, tn=0.8, att=0.5, hold=4, dur=1.0)),
    kit('Laser Lab', 'sci-fi',
        kick=kick(60, pa=8.0, tp=0.04, ta=0.15, click=0.1),
        rim=fm(3000, r2=1.5, l2=1.5, pa=2.0, tp=0.01, ta=0.02),
        snare=r(SQUARE, f0=400, pa=4.0, tp=0.03, ta=0.06, tone=0.6, flt=BP, fc=2000, q=2.0, tn=0.12, noise=1.0),
        clap=clap(4, fc=3000, q=3.0, tn=0.04),
        chh=fm(8000, r2=0.71, l2=2.0, ta=0.015),
        tom_lo=seno(120, pa=6.0, tp=0.08, ta=0.25),
        ohh=fruscio(9000, flt=BP, q=4.0, tn=0.2),
        tom_hi=seno(220, pa=-0.6, tp=0.08, ta=0.2),
        maracas=fruscio(7000, flt=BP, q=6.0, bursts=3, tn=0.01),
        conga=fm(400, r2=3.5, l2=2.0, pa=3.0, tp=0.03, ta=0.1),
        cowbell=quadra(1200, r2=1.5, l2=0.8, pa=-0.3, tp=0.05, ta=0.15),
        cymbal=fruscio(2000, tn=0.5, att=0.6, dur=1.0)),
    # lo-fi e chip
    kit('Lo-Fi Dust', 'lo-fi',
        kick=kick(55, pa=1.0, tp=0.02, ta=0.18, click=0.3, noise=0.2, fc=3000, tutto=True, hold=2, bits=256),
        rim=seno(800, ta=0.02, r2=2.1, l2=0.4, noise=0.4, flt=BP, fc=2500, q=1.5, tn=0.01, hold=2, bits=256),
        snare=snare(190, ta=0.08, flt=BP, fc=2200, q=0.5, tn=0.16, hold=2, bits=256),
        clap=clap(3, fc=1300, tn=0.12, hold=2, bits=256),
        chh=hat(420, metal=CYMB, flt=BP, fc=7000, q=0.8, ta=0.03, tone=0.3, noise=1.0, hold=2, bits=256),
        tom_lo=tom(100, pa=0.3, ta=0.2, noise=0.1, hold=2, bits=256),
        ohh=hat(420, metal=CYMB, flt=BP, fc=7000, q=0.8, ta=0.25, tone=0.3, noise=1.0, hold=2, bits=256),
        tom_hi=tom(150, pa=0.3, ta=0.17, noise=0.1, hold=2, bits=256),
        maracas=fruscio(5000, flt=BP, q=0.8, tn=0.03, att=0.006, hold=2, bits=256),
        conga=tom(260, pa=0.15, ta=0.12, noise=0.0, hold=2, bits=256),
        cowbell=fm(560, r2=1.48, l2=0.4, ta=0.08, hold=2, bits=256),
        cymbal=cymbal(420, metal=CYMB, flt=BP, fc=6000, q=0.6, ta=0.9, noise=0.3, tn=0.6, hold=2, bits=256)),
    kit('Tape Crate', 'lo-fi',
        kick=kick(52, pa=1.4, ta=0.22, click=0.4, drive=1.5, hold=3, bits=64),
        rim=seno(750, ta=0.025, r2=2.3, l2=0.4, noise=0.5, flt=BP, fc=2500, q=1.5, tn=0.012, hold=3, bits=64),
        snare=snare(210, ta=0.07, flt=BP, fc=2800, q=0.6, tn=0.14, drive=1.0, hold=3, bits=64),
        clap=clap(4, fc=1200, tn=0.1, hold=3, bits=64),
        chh=fruscio(6000, tn=0.025, hold=3, bits=64),
        tom_lo=tom(95, pa=0.3, ta=0.2, noise=0.1, hold=3, bits=64),
        ohh=fruscio(6000, tn=0.2, hold=3, bits=64),
        tom_hi=tom(145, pa=0.3, ta=0.17, noise=0.1, hold=3, bits=64),
        maracas=fruscio(4500, flt=BP, tn=0.03, att=0.005, hold=3, bits=64),
        conga=tom(240, pa=0.15, ta=0.1, noise=0.0, hold=3, bits=64),
        cowbell=cowbell(540, fc=1300, hold=3, bits=64),
        cymbal=fruscio(4500, tn=0.7, hold=3, bits=64)),
    kit('8-Bit', 'chip',
        kick=quadra(60, pa=4.0, tp=0.015, ta=0.08, bits=8),
        rim=quadra(1500, ta=0.01, bits=8),
        snare=r(SQUARE, f0=220, pa=1.0, tp=0.01, ta=0.02, tone=0.5, flt=HP, fc=200, tn=0.07, noise=1.0, nhold=6, bits=8),
        clap=clap(3, fc=2000, q=0.7, tn=0.03, nhold=4, bits=8),
        chh=fruscio(6000, tn=0.015, bits=8),
        tom_lo=quadra(110, pa=2.0, tp=0.04, ta=0.12, bits=8),
        ohh=fruscio(6000, tn=0.12, bits=8),
        tom_hi=quadra(180, pa=2.0, tp=0.03, ta=0.1, bits=8),
        maracas=fruscio(4000, tn=0.02, nhold=2, bits=8),
        conga=quadra(330, pa=0.5, tp=0.01, ta=0.06, bits=8),
        cowbell=quadra(880, r2=1.5, l2=0.7, ta=0.06, bits=8),
        cymbal=fruscio(3000, tn=0.6, bits=8)),
    kit('Arcade', 'chip',
        kick=quadra(50, pa=6.0, tp=0.02, ta=0.1, bits=16),
        rim=quadra(2000, ta=0.006, bits=16),
        snare=r(SQUARE, f0=200, pa=3.0, tp=0.02, ta=0.04, tone=0.5, flt=HP, fc=300, tn=0.1, noise=1.0, nhold=3, bits=16),
        clap=clap(2, fc=1500, q=0.7, tn=0.05, nhold=2, bits=16),
        chh=fruscio(8000, tn=0.01, bits=16),
        tom_lo=quadra(300, pa=-0.5, tp=0.04, ta=0.1, bits=16),
        ohh=fruscio(7000, tn=0.1, bits=16),
        tom_hi=quadra(500, pa=-0.5, tp=0.04, ta=0.1, bits=16),
        maracas=fruscio(9000, tn=0.006, bits=16),
        conga=quadra(660, r2=2.0, l2=0.5, ta=0.05, bits=16),
        cowbell=quadra(1320, r2=1.335, l2=1.0, ta=0.08, bits=16),
        cymbal=fruscio(4000, tn=0.5, nhold=3, bits=16)),
    # acustici sintetizzati
    kit('Acoustic Room', 'acoustic',
        kick=kick(56, pa=0.7, tp=0.015, ta=0.16, click=0.4, noise=0.4, fc=1200, tn=0.02, r2=1.6, l2=0.15),
        rim=seno(650, ta=0.025, r2=2.7, l2=0.5, noise=0.6, flt=BP, fc=4000, q=1.0, tn=0.015),
        snare=snare(185, r2=1.62, l2=0.6, pa=0.1, ta=0.08, flt=BP, fc=5000, q=0.4, tn=0.2, click=0.4),
        clap=clap(3, fc=1400, q=1.6, tn=0.07),
        chh=hat(480, metal=CYMB, fc=7000, flt=HP, ta=0.03, tone=0.6, noise=0.6),
        tom_lo=tom(95, r2=1.5, l2=0.3, pa=0.15, tp=0.08, ta=0.35, noise=0.2, fc=1000, tn=0.05, click=0.2),
        ohh=hat(480, metal=CYMB, fc=7000, flt=HP, ta=0.6, tone=0.6, noise=0.6, tn=0.5),
        tom_hi=tom(145, r2=1.5, l2=0.3, pa=0.15, tp=0.06, ta=0.3, noise=0.2, fc=1000, tn=0.05, click=0.2),
        maracas=fruscio(6000, flt=BP, q=0.8, tn=0.05, att=0.012),
        conga=tom(120, r2=1.5, l2=0.3, pa=0.15, ta=0.32, noise=0.2, fc=1000, tn=0.05, click=0.2),
        cowbell=cowbell(560, fc=1500, q=1.5, ta=0.1),
        cymbal=cymbal(360, metal=CYMB, fc=3500, ta=1.8, noise=0.6, tn=1.5)),
    kit('Brushes', 'acoustic',
        kick=kick(52, pa=0.3, ta=0.14, click=0.0, noise=0.3, fc=600, tn=0.03),
        rim=seno(700, ta=0.03, r2=2.5, l2=0.4),
        snare=snare(200, l2=0.0, ta=0.03, tone=0.3, flt=BP, fc=4500, q=0.5, tn=0.12, att=0.006),
        clap=fruscio(3500, flt=BP, q=0.6, tn=0.15, att=0.08),
        chh=hat(500, metal=CYMB, fc=6000, flt=HP, ta=0.02, noise=0.3),
        tom_lo=tom(105, pa=0.1, ta=0.3, noise=0.2, fc=2500, tn=0.08),
        ohh=hat(500, metal=CYMB, fc=6000, flt=HP, ta=0.25, noise=0.3),
        tom_hi=tom(150, pa=0.1, ta=0.25, noise=0.2, fc=2500, tn=0.08),
        maracas=fruscio(5000, flt=BP, tn=0.08, att=0.03),
        conga=tom(140, r2=1.5, l2=0.3, pa=0.1, ta=0.3, noise=0.2, fc=2500, tn=0.08),
        cowbell=campana(700, fc=3000, q=2.0, ta=0.5),
        cymbal=cymbal(520, metal=CYMB, flt=BP, fc=6500, q=0.7, ta=1.6, noise=0.25, tn=1.0)),
    kit('Stadium Rock', 'acoustic',
        kick=kick(55, pa=1.0, ta=0.2, click=0.7, noise=0.3, fc=2000, tn=0.02, drive=1.5),
        rim=seno(700, ta=0.03, r2=2.5, l2=0.4, noise=0.5, flt=BP, fc=3500, q=1.2, tn=0.012),
        snare=snare(175, r2=1.6, l2=0.5, ta=0.12, flt=BP, fc=3000, q=0.5, tn=0.3, noise=1.2, drive=1.5, click=0.3),
        clap=clap(4, tn=0.3),
        chh=hat(460, metal=CYMB, fc=7500, flt=HP, ta=0.035, tone=0.7, noise=0.5),
        tom_lo=tom(80, pa=0.5, tp=0.05, ta=0.5, noise=0.3, fc=1500, tn=0.06, drive=1.0, click=0.3),
        ohh=hat(460, metal=CYMB, fc=7500, flt=HP, ta=0.45, tone=0.7, noise=0.5),
        tom_hi=tom(120, pa=0.5, tp=0.05, ta=0.45, noise=0.3, fc=1500, tn=0.06, drive=1.0, click=0.3),
        maracas=r(METAL, f0=2800, r2=BELL, flt=HP, fc=7000, ta=0.08, tone=0.4, noise=1.0, tn=0.1, bursts=2),
        conga=tom(100, pa=0.5, tp=0.05, ta=0.5, noise=0.3, fc=1500, tn=0.06, drive=1.0, click=0.3),
        cowbell=cowbell(560, fc=1800, q=1.5, ta=0.12),
        cymbal=cymbal(360, metal=CYMB, fc=3500, ta=2.0, noise=0.6, tn=1.6)),
    # percussioni del mondo
    kit('Afro Hand', 'world',
        kick=kick(75, pa=0.4, tp=0.02, ta=0.18, click=0.2, noise=0.4, fc=400, tn=0.02),
        rim=seno(600, ta=0.02, tone=0.5, noise=1.0, flt=BP, fc=2000, q=1.5, tn=0.03),
        snare=seno(330, r2=1.6, l2=0.3, ta=0.1, noise=0.3, flt=BP, fc=1500, tn=0.02),
        clap=clap(2, fc=1200, q=1.4, tn=0.05),
        chh=fruscio(6000, flt=BP, q=1.0, bursts=2, tn=0.03, att=0.004),
        tom_lo=tom(65, pa=0.3, ta=0.3, noise=0.3, fc=500),
        ohh=fruscio(5500, flt=BP, q=0.8, bursts=3, tn=0.12, att=0.01),
        tom_hi=tom(110, pa=0.3, ta=0.25, noise=0.3, fc=500),
        maracas=fruscio(4000, tn=0.04, att=0.008),
        conga=tom(160, pa=0.2, ta=0.18, noise=0.2, fc=600),
        cowbell=campana(750, fc=2500, q=3.0, ta=0.3),
        cymbal=fruscio(4500, flt=BP, q=0.5, tn=0.5, att=0.05)),
    kit('Tabla Mist', 'world',
        kick=seno(85, pa=-0.25, tp=0.15, ta=0.35, noise=0.2, flt=LP, fc=300, tn=0.02),
        rim=seno(340, r2=2.0, l2=0.5, ta=0.25, click=0.3),
        snare=seno(680, r2=1.5, l2=0.3, ta=0.12, click=0.3),
        clap=seno(140, ta=0.02, noise=1.0, flt=BP, fc=1200, q=1.0, tn=0.02),
        chh=campana(1800, flt=HP, fc=5000, q=0.7, ta=0.05),
        tom_lo=seno(75, pa=-0.35, tp=0.25, ta=0.5),
        ohh=campana(1800, fc=7000, q=1.5, ta=0.6),
        tom_hi=seno(340, r2=2.0, l2=0.4, ta=0.5),
        maracas=r(METAL, f0=3500, r2=BELL, flt=HP, fc=6000, ta=0.06, tone=0.4, noise=1.0, tn=0.03, bursts=3),
        conga=seno(360, ta=0.04, noise=0.6, flt=BP, fc=3000, tn=0.01),
        cowbell=fm(950, r2=2.76, l2=0.6, ta=0.8),
        cymbal=campana(1100, flt=HP, fc=3000, q=0.7, ta=1.5)),
    kit('Gamelan', 'world',
        kick=kick(90, pa=0.2, ta=0.15, click=0.2, noise=0.3, fc=400),
        rim=seno(500, ta=0.02, noise=1.0, flt=BP, fc=2500, q=1.5, tn=0.02),
        snare=seno(180, pa=0.3, tp=0.02, ta=0.12, noise=0.3, flt=BP, fc=1500, tn=0.03),
        clap=campana(2200, flt=HP, fc=4000, q=0.7, ta=0.12, noise=0.5, tn=0.08, bursts=2),
        chh=campana(2200, flt=HP, fc=4000, q=0.7, ta=0.04, noise=0.5, tn=0.03),
        tom_lo=fm(220, r2=1.48, l2=0.5, ta=1.2),
        ohh=fm(1400, r2=2.76, l2=0.4, ta=0.5),
        tom_hi=fm(520, r2=4.0, l2=0.3, ta=0.8),
        maracas=fruscio(5000, flt=BP, tn=0.04),
        conga=fm(700, r2=3.0, l2=0.4, ta=0.6),
        cowbell=fm(440, r2=2.0, l2=0.5, ta=1.0),
        cymbal=fm(65, r2=2.76, l2=0.8, ta=2.5, dur=5.0)),
    kit('Latin Perc', 'world',
        kick=kick(60, pa=0.3, ta=0.35, click=0.2, noise=0.2, fc=400),
        rim=seno(2500, ta=0.03, r2=2.8, l2=0.1),
        snare=seno(400, r2=1.53, l2=0.5, ta=0.25, noise=0.5, flt=BP, fc=4000, tn=0.04),
        clap=fruscio(3000, flt=BP, q=2.5, bursts=7, tn=0.006),
        chh=fruscio(6000, tn=0.025, att=0.004),
        tom_lo=seno(300, r2=1.5, l2=0.4, ta=0.3),
        ohh=fruscio(5500, flt=BP, tn=0.1, att=0.02),
        tom_hi=seno(420, pa=0.15, ta=0.08),
        maracas=fruscio(5000, tn=0.02, att=0.003),
        conga=seno(240, pa=0.1, ta=0.16, click=0.3),
        cowbell=cowbell(620, fc=1900, ta=0.12),
        cymbal=fm(900, r2=2.76, l2=0.5, ta=0.25)),
    kit('Taiko', 'world',
        kick=kick(45, pa=0.5, tp=0.05, ta=0.6, click=0.3, noise=0.5, fc=300, tn=0.1),
        rim=seno(2200, ta=0.02, r2=2.6, l2=0.5, click=0.6),
        snare=seno(380, pa=0.2, ta=0.08, noise=0.6, flt=BP, fc=2500, tn=0.03),
        clap=clap(3, fc=1300, tn=0.08),
        chh=campana(1600, flt=HP, fc=4000, q=0.7, ta=0.08),
        tom_lo=tom(75, pa=0.4, ta=0.5, noise=0.3, fc=400, tn=0.06),
        ohh=campana(1600, flt=HP, fc=4000, q=0.7, ta=0.6),
        tom_hi=tom(140, pa=0.3, ta=0.3, noise=0.3, fc=600, tn=0.05),
        maracas=fruscio(4000, tn=0.03),
        conga=seno(520, ta=0.06),
        cowbell=campana(1100, fc=3500, q=2.0, ta=0.3),
        cymbal=campana(400, flt=HP, fc=1500, q=0.7, ta=2.0)),
    kit('Darbuka Sand', 'world',
        kick=kick(95, pa=0.15, ta=0.3, click=0.2, noise=0.3, fc=300, tn=0.02),
        rim=seno(900, ta=0.04, r2=2.3, l2=0.4, noise=0.6, flt=BP, fc=4000, q=1.2, tn=0.01, click=0.4),
        snare=seno(750, ta=0.03, noise=0.8, flt=BP, fc=3500, tn=0.012),
        clap=campana(2600, flt=HP, fc=5000, q=0.7, ta=0.15, noise=0.5, tn=0.1, bursts=2),
        chh=campana(2600, flt=HP, fc=5000, q=0.7, ta=0.05, noise=0.5, tn=0.04),
        tom_lo=tom(70, pa=0.2, ta=0.35, noise=0.4, fc=1500, tn=0.2),
        ohh=campana(2600, flt=HP, fc=5000, q=0.7, ta=0.3, noise=0.5, tn=0.2, bursts=3),
        tom_hi=tom(140, pa=0.1, ta=0.25, noise=0.2, fc=1500, tn=0.1),
        maracas=fruscio(5000, tn=0.02),
        conga=seno(400, ta=0.05, noise=0.8, flt=BP, fc=2000, tn=0.03),
        cowbell=campana(2400, fc=6000, q=3.0, ta=0.8),
        cymbal=campana(1800, fc=5000, q=2.0, ta=1.5)),
    kit('Cajon Box', 'acoustic',
        kick=kick(70, pa=0.3, ta=0.15, click=0.2, noise=0.4, fc=800, tn=0.03),
        rim=seno(400, ta=0.02, noise=1.0, flt=BP, fc=3000, tn=0.015),
        snare=seno(300, ta=0.03, tone=0.5, noise=1.0, flt=BP, fc=2500, q=0.6, tn=0.1),
        clap=clap(2, fc=2000, q=1.4, tn=0.04),
        chh=fruscio(7000, flt=BP, tn=0.025, att=0.006),
        tom_lo=tom(85, pa=0.2, ta=0.2, noise=0.2),
        ohh=fruscio(7000, flt=BP, tn=0.08, att=0.02),
        tom_hi=tom(180, pa=0.2, ta=0.12, noise=0.2),
        maracas=fruscio(6000, tn=0.015),
        conga=tom(130, pa=0.2, ta=0.12, noise=0.3, fc=1200),
        cowbell=fm(1100, r2=2.4, l2=0.4, ta=0.05),
        cymbal=cymbal(500, metal=CYMB, fc=4500, ta=0.8)),
    # ambient
    kit('Deep Space', 'ambient',
        kick=kick(50, pa=0.4, ta=0.3, click=0.0, att=0.004),
        rim=fm(1800, r2=2.76, l2=0.3, ta=0.15),
        snare=snare(200, l2=0.0, ta=0.1, tone=0.4, flt=BP, fc=1500, q=0.8, tn=0.35, noise=0.8, att=0.01),
        clap=clap(4, fc=900, tn=0.4, att=0.005),
        chh=fruscio(7000, tn=0.04, att=0.004),
        tom_lo=tom(70, pa=0.2, ta=0.6, noise=0.0, att=0.003),
        ohh=fruscio(6000, flt=BP, tn=0.5, att=0.05),
        tom_hi=tom(105, pa=0.2, ta=0.5, noise=0.0, att=0.003),
        maracas=fruscio(4000, flt=BP, tn=0.08, att=0.04),
        conga=fm(300, r2=2.0, l2=0.3, ta=0.4),
        cowbell=fm(660, r2=2.76, l2=0.5, ta=1.2),
        cymbal=cymbal(420, metal=CYMB, fc=3000, ta=2.0, tone=0.3, noise=1.0, tn=1.0, att=1.0, dur=3.0)),
]

# Picchi misurati con guadagno 1 (stame-render --kits): dBFS mono a velocity 127, uno per strumento
PICCO_DB = {
    '808 Boom': (0.16, 4.00, 5.85, -9.17, -5.11, -0.19, -5.10, -0.14, 2.18, -0.07, -0.29, -1.49),
    '808 Trap': (-0.01, 3.06, 6.45, -7.73, -4.64, -0.14, -4.64, -0.09, -2.02, -0.05, -0.60, -1.66),
    '909 House': (-0.34, 3.08, 5.34, -7.39, -5.38, -0.09, -4.10, -0.03, 2.22, -0.07, -0.83, -3.04),
    '909 Rave': (0.00, -0.00, -0.00, -2.62, -1.43, -0.14, -1.24, -0.14, -0.79, -0.05, -0.00, -0.90),
    'CR Rhythm': (-0.23, -0.05, -1.06, 3.27, 3.61, -0.16, 2.39, -0.12, -0.58, -0.09, -1.02, -2.29),
    '606 Tick': (0.05, -0.19, 5.53, -7.90, -7.64, -0.11, -7.64, -0.09, 1.08, -0.10, -1.32, -4.40),
    'Hex Toms': (0.09, 3.52, 1.13, -8.67, -6.26, 0.01, -6.26, 0.19, 2.36, 0.38, -0.73, -1.82),
    'Syndrum Disco': (0.39, 2.67, 2.72, -8.63, -2.65, -0.01, -2.01, -0.01, -0.89, -0.01, -2.20, -0.18),
    'Robot Pop': (0.13, 2.59, -4.25, -9.78, -5.17, -0.11, -2.34, -0.07, -3.69, -0.10, -0.05, -0.90),
    'Linn Pop': (-0.49, 2.65, 4.28, -6.86, -3.95, 0.13, -3.38, 0.20, 3.07, -0.05, -2.20, -0.18),
    'Gated 80s': (-0.09, 2.65, 5.01, -7.90, -2.72, 0.36, -2.01, 0.41, -0.89, 0.47, -0.98, -0.13),
    'Minimal Click': (0.12, -0.21, -1.74, -8.43, -0.11, -0.24, 0.59, -0.16, -0.36, -0.16, -0.06, 1.45),
    'Dub Yard': (-0.06, 3.26, 1.33, -8.42, 2.87, -0.17, 3.34, -0.13, -4.45, -0.06, -0.02, 0.40),
    '2-Step': (-0.09, 2.04, 6.59, -7.19, -4.33, -0.14, -3.92, -0.12, 1.44, -0.10, -0.14, -1.90),
    'Jungle': (-0.14, 3.07, -0.00, -7.50, -3.16, -0.07, -0.93, 0.27, -0.22, -0.09, -0.91, -2.82),
    'Iron Mill': (0.00, -1.03, 0.00, -0.02, -0.00, 0.00, -0.00, -0.23, 0.00, -0.00, -2.89, 0.00),
    'Scrap Yard': (0.00, -0.07, -4.71, -8.60, 2.05, -0.03, 0.87, -0.01, -6.44, -0.04, -8.88, 2.23),
    'Glitch Bits': (0.00, -0.07, -1.58, -4.96, -0.00, -0.00, 1.58, -0.03, 0.30, -0.00, 0.00, -3.23),
    'Data Rot': (0.00, -0.47, -0.00, -10.17, -0.14, -0.23, -0.10, -0.01, -11.16, -0.03, 6.02, -2.38),
    'Laser Lab': (0.23, -0.10, -0.98, -9.23, -0.06, -0.02, -4.22, -0.12, -8.56, -0.03, 5.10, -6.05),
    'Lo-Fi Dust': (0.23, 1.97, 2.96, -9.08, -1.64, -0.17, -0.42, -0.14, -4.88, -0.07, -0.07, -2.10),
    'Tape Crate': (0.00, 2.15, -0.00, -9.28, 2.26, -0.28, 2.96, -0.14, -3.71, -0.14, -0.56, 2.96),
    '8-Bit': (0.00, 0.00, 4.22, 0.00, 1.94, 0.00, 2.77, 0.00, 1.94, -0.00, 4.86, 2.77),
    'Arcade': (0.00, 0.00, 4.86, -4.08, -0.00, 0.00, 2.36, 0.00, -0.56, 3.52, 6.02, 3.88),
    'Acoustic Room': (0.57, 3.81, 5.61, -9.88, -0.88, 1.91, -0.21, 2.07, -2.28, 1.87, -2.04, 0.51),
    'Brushes': (-0.08, 2.41, 1.23, -5.95, -4.55, 0.07, -4.12, 0.22, -4.23, 1.70, -7.83, -1.91),
    'Stadium Rock': (-0.01, 2.83, -0.00, -8.16, -3.33, -0.10, -1.91, -0.10, 3.07, -0.11, -2.20, 0.55),
    'Afro Hand': (-0.09, -2.64, 2.19, -9.30, -1.48, -0.33, -1.67, -0.16, -0.16, -0.22, -10.23, -0.50),
    'Tabla Mist': (-0.12, 3.01, 2.98, 1.37, -0.53, -0.09, -5.34, 1.68, 2.76, 2.26, -0.01, 1.46),
    'Gamelan': (-0.38, 1.67, 0.50, 2.02, 2.49, -0.00, -0.01, -0.00, -0.51, -0.02, -0.01, -0.01),
    'Latin Perc': (-0.13, 0.54, 4.30, -9.29, -0.47, 2.49, -3.05, -0.06, 0.50, 0.95, -0.83, -0.04),
    'Taiko': (-0.04, 3.97, 2.04, -8.86, 1.19, 0.04, 1.46, -0.07, 2.05, -0.07, -7.35, 2.80),
    'Darbuka Sand': (-0.22, 4.07, 2.21, 3.36, 3.97, 0.28, 3.53, -0.03, 2.08, 2.60, -9.36, -7.22),
    'Cajon Box': (-0.28, 3.65, -0.11, -7.23, -4.43, -0.04, -2.38, -0.24, 1.64, -0.17, -0.12, -2.05),
    'Deep Space': (-0.22, -0.01, -2.10, -7.91, 0.08, -0.04, -0.93, -0.10, -5.45, -0.00, -0.01, -4.85),
}


def durata(p):
    """fino a −60 dB dell'inviluppo più lungo, più l'attacco e i colpi del battimani; al più 6 s"""
    t = 0.0
    if p['tone'] > 0.0:
        t = max(t, 6.9 * p['ta'])
    if p['noise'] > 0.0:
        t = max(t, 6.9 * p['tn'] + max(0, p['bursts'] - 1) * 0.0095)
    if p['click'] > 0.0:
        t = max(t, 0.01)
    return min(6.0, max(0.03, t + p['att'] + 0.004))


def cf(x):
    s = '%.7g' % x
    if '.' not in s and 'e' not in s:
        s += '.0'
    return s + 'f'


def ricetta_c(p, i, gain):
    flags = '0' if not p['tutto'] else 'DK_ALL'
    osc = ['DK_NONE', 'DK_SINE', 'DK_SQUARE', 'DK_FM', 'DK_METAL'][p['osc']]
    flt = ['DK_LP', 'DK_BP', 'DK_HP'][p['flt']]
    dur = p['dur'] if p['dur'] is not None else durata(p)
    pan = p['pan'] if p['pan'] is not None else PAN[i]
    v = [p['f0'], p['pa'], p['tp'], p['ta'], p['tone'], p['r2'], p['l2'], p['fc'], p['q'], p['tn'], p['noise'],
         p['click'], p['drive'], p['att'], dur, pan, gain]
    return '{ %s, %s, %s, %d, %d, %d, %d, %s },' % (osc, flt, flags, p['bursts'], p['hold'], p['nhold'], p['bits'],
                                                    ', '.join(cf(x) for x in v))


def ident(nome):
    return 'DK_KIT_' + re.sub(r'[^A-Z0-9]+', '_', nome.upper()).strip('_')


def main():
    nomi = [k[0] for k in KITS]
    assert len(set(nomi)) == len(nomi)
    c = ['/* drum_kits.c — la libreria dei kit di batteria sintetizzati (specifica 20, SND-540…SND-543).',
         ' * Generato da tools/kits.py: non modificare a mano. Ricette di Stame, progettate sul carattere del nome. */',
         '#include "drums.h"', '',
         '/* { tono, filtro, flag, colpi, hold, hold del rumore, bits, f0, pa, tp, ta, tone, r2, l2, fc, q, tn, noise,',
         ' *   click, drive, att, dur, pan, gain } */',
         'const drum_kit_t drum_kits[DRUM_SYNTH_KITS] STAME_ROM = {']
    mancano = 0
    for nome, stile, ricette in KITS:
        c.append('    { "%s", "%s", {' % (nome, stile))
        picchi = PICCO_DB.get(nome)
        for i, p in enumerate(ricette):
            if picchi:
                gain = 10.0 ** ((LIVELLO[i] - picchi[i]) / 20.0)
            else:
                gain = 1.0
                mancano += 1
            c.append('        /* %-7s */ %s' % (INST[i], ricetta_c(p, i, gain)))
        c.append('    } },')
    c += ['};', '']
    open(os.path.join(RADICE, 'src', 'dsp', 'drum_kits.c'), 'w', encoding='utf-8', newline='\n').write('\n'.join(c))
    h = ['/* drum_kits.h — quanti kit sintetizzati ha la libreria e i loro indici in drum_kits[] (SND-541).',
         ' * Generato da tools/kits.py: non modificare a mano. */',
         '#ifndef STAME_DRUM_KITS_H', '#define STAME_DRUM_KITS_H', '',
         '#define DRUM_SYNTH_KITS %d' % len(KITS), '', 'enum {']
    h += ['    %s,%s' % (ident(n), '' if i else '   /* il primo: 0 */') for i, n in enumerate(nomi)]
    h += ['};', '', '#endif', '']
    open(os.path.join(RADICE, 'src', 'dsp', 'drum_kits.h'), 'w', encoding='utf-8', newline='\n').write('\n'.join(h))
    print('kit: %d sintetizzati, %d strumenti%s' % (len(KITS), len(KITS) * len(INST),
          '' if not mancano else ' (%d senza picco misurato: stame-render --kits)' % mancano))


if __name__ == '__main__':
    main()
