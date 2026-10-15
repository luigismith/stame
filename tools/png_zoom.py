"""png_zoom.py — ritaglia e ingrandisce un PNG (per controllare i pixel della plancia).

Uso: python -I tools/png_zoom.py in.png out.png x y w h fattore
Legge PNG RGB/RGBA a 8 bit non interlacciati (anche quelli di stame-render); solo libreria standard.
"""
import struct
import sys
import zlib


def leggi(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos, idat, w = 8, b'', 0
    while pos < len(data):
        n, = struct.unpack('>I', data[pos:pos + 4])
        tipo = data[pos + 4:pos + 8]
        corpo = data[pos + 8:pos + 8 + n]
        if tipo == b'IHDR':
            w, h, bit, col = struct.unpack('>IIBB', corpo[:10])
            assert bit == 8 and col in (2, 6)
            bpp = 3 if col == 2 else 4
        elif tipo == b'IDAT':
            idat += corpo
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * bpp
    righe, prec = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        r = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = r[i - bpp] if i >= bpp else 0
            b = prec[i]
            c = prec[i - bpp] if i >= bpp else 0
            if f == 1:
                r[i] = (r[i] + a) & 255
            elif f == 2:
                r[i] = (r[i] + b) & 255
            elif f == 3:
                r[i] = (r[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                r[i] = (r[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        righe.append(bytes(r))
        prec = r
    return w, h, bpp, righe


def scrivi(path, w, h, righe):
    raw = b''.join(b'\x00' + r for r in righe)

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    out = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(out)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    x, y, w, h, k = (int(v) for v in sys.argv[3:8])
    W, H, bpp, righe = leggi(src)
    out = []
    for yy in range(y, y + h):
        r = righe[min(yy, H - 1)]
        riga = bytearray()
        for xx in range(x, x + w):
            p = r[min(xx, W - 1) * bpp:min(xx, W - 1) * bpp + bpp]
            if bpp == 4:                      # trasparenza: si compone su un fondo scuro
                a = p[3]
                p = bytes((c * a + 32 * (255 - a)) // 255 for c in p[:3])
            riga += bytes(p[:3]) * k
        for _ in range(k):
            out.append(bytes(riga))
    scrivi(dst, w * k, h * k, out)


if __name__ == '__main__':
    main()
