"""pad_ascolta.py — registra cosa manda il macro pad (Windows, Raw Input), per le verifiche VP della specifica 40.

Ascolta tastiera, mouse e tasti multimediali di tutti i dispositivi, ma scrive solo gli eventi del
dispositivo indicato (per default il pad BRIMFORD, 1189:8840). Non blocca nulla: i tasti arrivano
comunque alla finestra in primo piano, quindi conviene tenere aperto un Blocco note.

    python -I tools/pad_ascolta.py [secondi] [file.jsonl] [VID_xxxx&PID_yyyy]
"""
import ctypes
import ctypes.wintypes as wt
import json
import sys
import time

FILTRO = sys.argv[3].upper() if len(sys.argv) > 3 else 'VID_1189&PID_8840'
DURATA = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
USCITA = sys.argv[2] if len(sys.argv) > 2 else None

user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)

WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIDI_DEVICENAME = 0x20000007
RIM_TYPEMOUSE, RIM_TYPEKEYBOARD, RIM_TYPEHID = 0, 1, 2
PM_REMOVE = 1


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [('usUsagePage', wt.USHORT), ('usUsage', wt.USHORT), ('dwFlags', wt.DWORD), ('hwndTarget', wt.HWND)]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [('dwType', wt.DWORD), ('dwSize', wt.DWORD), ('hDevice', wt.HANDLE), ('wParam', wt.WPARAM)]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [('MakeCode', wt.USHORT), ('Flags', wt.USHORT), ('Reserved', wt.USHORT), ('VKey', wt.USHORT),
                ('Message', wt.UINT), ('ExtraInformation', wt.ULONG)]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [('usFlags', wt.USHORT), ('_pad', wt.USHORT), ('usButtonFlags', wt.USHORT),
                ('usButtonData', wt.USHORT), ('ulRawButtons', wt.ULONG), ('lLastX', wt.LONG), ('lLastY', wt.LONG),
                ('ulExtraInformation', wt.ULONG)]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [('style', wt.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', ctypes.c_int),
                ('cbWndExtra', ctypes.c_int), ('hInstance', wt.HINSTANCE), ('hIcon', wt.HICON),
                ('hCursor', wt.HANDLE), ('hbrBackground', wt.HBRUSH), ('lpszMenuName', wt.LPCWSTR),
                ('lpszClassName', wt.LPCWSTR)]


user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.GetRawInputData.argtypes = [wt.HANDLE, wt.UINT, ctypes.c_void_p, ctypes.POINTER(wt.UINT), wt.UINT]
user32.GetRawInputDeviceInfoW.argtypes = [wt.HANDLE, wt.UINT, ctypes.c_void_p, ctypes.POINTER(wt.UINT)]
user32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
user32.CreateWindowExW.restype = wt.HWND
user32.PeekMessageW.argtypes = [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT, wt.UINT]

# nomi dei tasti virtuali più probabili su un macro pad
VK = {0x08: 'BACKSPACE', 0x09: 'TAB', 0x0D: 'ENTER', 0x10: 'SHIFT', 0x11: 'CTRL', 0x12: 'ALT', 0x13: 'PAUSE',
      0x14: 'CAPSLOCK', 0x1B: 'ESC', 0x20: 'SPACE', 0x21: 'PGUP', 0x22: 'PGDN', 0x23: 'END', 0x24: 'HOME',
      0x25: 'LEFT', 0x26: 'UP', 0x27: 'RIGHT', 0x28: 'DOWN', 0x2C: 'PRINTSCREEN', 0x2D: 'INSERT', 0x2E: 'DELETE',
      0x5B: 'LWIN', 0x5C: 'RWIN', 0x5D: 'MENU', 0x60: 'KP0', 0x61: 'KP1', 0x62: 'KP2', 0x63: 'KP3', 0x64: 'KP4',
      0x65: 'KP5', 0x66: 'KP6', 0x67: 'KP7', 0x68: 'KP8', 0x69: 'KP9', 0x6A: 'KP*', 0x6B: 'KP+', 0x6D: 'KP-',
      0x6E: 'KP.', 0x6F: 'KP/', 0x90: 'NUMLOCK', 0x91: 'SCROLLLOCK', 0xA0: 'LSHIFT', 0xA1: 'RSHIFT',
      0xA2: 'LCTRL', 0xA3: 'RCTRL', 0xA4: 'LALT', 0xA5: 'RALT', 0xAD: 'VOL_MUTE', 0xAE: 'VOL_DOWN',
      0xAF: 'VOL_UP', 0xB0: 'NEXT', 0xB1: 'PREV', 0xB2: 'STOP', 0xB3: 'PLAY_PAUSE', 0xBA: ';', 0xBB: '=',
      0xBC: ',', 0xBD: '-', 0xBE: '.', 0xBF: '/', 0xC0: '`', 0xDB: '[', 0xDC: 'BACKSLASH', 0xDD: ']', 0xDE: "'"}
for i in range(26):
    VK[0x41 + i] = chr(0x41 + i)
for i in range(10):
    VK[0x30 + i] = str(i)
for i in range(24):
    VK[0x70 + i] = 'F%d' % (i + 1)
CONSUMER = {0xE9: 'VOL_UP', 0xEA: 'VOL_DOWN', 0xE2: 'MUTE', 0xCD: 'PLAY_PAUSE', 0xB5: 'NEXT', 0xB6: 'PREV',
            0xB7: 'STOP', 0x6F: 'BRIGHT_UP', 0x70: 'BRIGHT_DOWN', 0x192: 'CALC', 0x223: 'WWW_HOME'}

nomi = {}
t0 = time.monotonic()
righe = []


def nome_dispositivo(h):
    if h in nomi:
        return nomi[h]
    n = wt.UINT(0)
    user32.GetRawInputDeviceInfoW(h, RIDI_DEVICENAME, None, ctypes.byref(n))
    buf = ctypes.create_unicode_buffer(n.value + 1)
    user32.GetRawInputDeviceInfoW(h, RIDI_DEVICENAME, buf, ctypes.byref(n))
    nomi[h] = buf.value
    return buf.value


def collezione(nome):
    u = nome.upper()
    for c in ('COL01', 'COL02', 'COL03', 'COL04', 'COL05'):
        if c in u:
            return c.lower()
    return 'mi_' + (u.split('MI_')[1][:2] if 'MI_' in u else '?')


def scrivi(ev):
    righe.append(ev)
    t = ev['t']
    if ev['tipo'] == 'tasto':
        print('%7.3f  %-5s tasto %-10s %-4s make=0x%02X%s vk=0x%02X' % (
            t, ev['col'], ev['nome'], ev['verso'], ev['make'], ' E0' if ev['e0'] else '', ev['vk']), flush=True)
    elif ev['tipo'] == 'mouse':
        print('%7.3f  %-5s mouse tasti=0x%04X rotella=%d dx=%d dy=%d' % (
            t, ev['col'], ev['tasti'], ev['rotella'], ev['dx'], ev['dy']), flush=True)
    else:
        print('%7.3f  %-5s hid   %s %s' % (t, ev['col'], ev['byte'], ev.get('nome', '')), flush=True)


@WNDPROC
def wndproc(hwnd, msg, wparam, lparam):
    if msg == WM_INPUT:
        size = wt.UINT(0)
        user32.GetRawInputData(lparam, RID_INPUT, None, ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER))
        buf = ctypes.create_string_buffer(size.value)
        if user32.GetRawInputData(lparam, RID_INPUT, buf, ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER)) == size.value:
            hdr = RAWINPUTHEADER.from_buffer_copy(buf)
            nome = nome_dispositivo(hdr.hDevice) if hdr.hDevice else ''
            if FILTRO in nome.upper():
                off = ctypes.sizeof(RAWINPUTHEADER)
                t = round(time.monotonic() - t0, 3)
                col = collezione(nome)
                if hdr.dwType == RIM_TYPEKEYBOARD:
                    k = RAWKEYBOARD.from_buffer_copy(buf, off)
                    scrivi({'t': t, 'col': col, 'tipo': 'tasto', 'vk': k.VKey, 'nome': VK.get(k.VKey, '?'),
                            'make': k.MakeCode, 'e0': bool(k.Flags & 2), 'verso': 'su' if k.Flags & 1 else 'giu'})
                elif hdr.dwType == RIM_TYPEMOUSE:
                    m = RAWMOUSE.from_buffer_copy(buf, off)
                    rot = ctypes.c_short(m.usButtonData).value if m.usButtonFlags & 0x0400 else 0
                    scrivi({'t': t, 'col': col, 'tipo': 'mouse', 'tasti': m.usButtonFlags, 'rotella': rot,
                            'dx': m.lLastX, 'dy': m.lLastY})
                else:
                    sz = int.from_bytes(buf.raw[off:off + 4], 'little')
                    cnt = int.from_bytes(buf.raw[off + 4:off + 8], 'little')
                    dati = buf.raw[off + 8:off + 8 + sz * cnt]
                    ev = {'t': t, 'col': col, 'tipo': 'hid', 'byte': dati.hex(' ')}
                    if len(dati) >= 3:
                        u = dati[1] | dati[2] << 8
                        if u:
                            ev['nome'] = CONSUMER.get(u, 'usage 0x%03X' % u)
                    scrivi(ev)
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def main():
    hinst = kernel32.GetModuleHandleW(None)
    wc = WNDCLASSW()
    wc.lpfnWndProc = wndproc
    wc.hInstance = hinst
    wc.lpszClassName = 'StamePadAscolta'
    user32.RegisterClassW(ctypes.byref(wc))
    hwnd = user32.CreateWindowExW(0, wc.lpszClassName, 'pad', 0, 0, 0, 0, 0, wt.HWND(-3), None, hinst, None)
    usi = [(0x01, 0x06), (0x01, 0x02), (0x0C, 0x01), (0x01, 0x80), (0xFF00, 0x01)]
    arr = (RAWINPUTDEVICE * len(usi))(*[RAWINPUTDEVICE(p, u, RIDEV_INPUTSINK, hwnd) for p, u in usi])
    if not user32.RegisterRawInputDevices(arr, len(usi), ctypes.sizeof(RAWINPUTDEVICE)):
        print('RegisterRawInputDevices: errore', ctypes.get_last_error())
        return 1
    print('in ascolto per %.0f s, dispositivo %s' % (DURATA, FILTRO), flush=True)
    msg = wt.MSG()
    while time.monotonic() - t0 < DURATA:
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        time.sleep(0.003)
    if USCITA:
        with open(USCITA, 'w', encoding='utf-8') as f:
            for r in righe:
                f.write(json.dumps(r) + '\n')
    print('fine: %d eventi' % len(righe), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
