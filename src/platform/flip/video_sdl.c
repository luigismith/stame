/* video_sdl.c — SDL2 caricata a runtime (PLT-059..PLT-063): finestra KMSDRM, texture RGB565.
 *
 * Si includono gli header ufficiali di SDL 2.32 solo per tipi e costanti; le funzioni arrivano
 * da dlopen, così il binario non dipende dal SONAME di sistema (quello di PyUI è diverso).
 */
#define _GNU_SOURCE
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "flip.h"
#include "../../gfx/gfx.h"

static void *lib;
static SDL_Window *win;
static SDL_Renderer *ren;
static SDL_Texture *tex;

#define FN(ret, name, args) static ret (*p_##name) args
FN(int, SDL_Init, (Uint32));
FN(void, SDL_Quit, (void));
FN(SDL_bool, SDL_SetHint, (const char *, const char *));
FN(const char *, SDL_GetError, (void));
FN(SDL_Window *, SDL_CreateWindow, (const char *, int, int, int, int, Uint32));
FN(void, SDL_DestroyWindow, (SDL_Window *));
FN(SDL_Renderer *, SDL_CreateRenderer, (SDL_Window *, int, Uint32));
FN(void, SDL_DestroyRenderer, (SDL_Renderer *));
FN(int, SDL_RenderSetLogicalSize, (SDL_Renderer *, int, int));
FN(SDL_Texture *, SDL_CreateTexture, (SDL_Renderer *, Uint32, int, int, int));
FN(void, SDL_DestroyTexture, (SDL_Texture *));
FN(int, SDL_UpdateTexture, (SDL_Texture *, const SDL_Rect *, const void *, int));
FN(int, SDL_RenderCopy, (SDL_Renderer *, SDL_Texture *, const SDL_Rect *, const SDL_Rect *));
FN(void, SDL_RenderPresent, (SDL_Renderer *));
FN(int, SDL_RenderClear, (SDL_Renderer *));
FN(int, SDL_ShowCursor, (int));
FN(int, SDL_PollEvent, (SDL_Event *));
FN(int, SDL_InitSubSystem, (Uint32));
FN(SDL_AudioDeviceID, SDL_OpenAudioDevice, (const char *, int, const SDL_AudioSpec *, SDL_AudioSpec *, int));
FN(int, SDL_QueueAudio, (SDL_AudioDeviceID, const void *, Uint32));
FN(void, SDL_PauseAudioDevice, (SDL_AudioDeviceID, int));
FN(void, SDL_CloseAudioDevice, (SDL_AudioDeviceID));
FN(Uint32, SDL_GetQueuedAudioSize, (SDL_AudioDeviceID));

static const char *const PATHS[] = {
    "/mnt/SDCARD/App/PyUI/dll/libSDL2-2.0.so",      /* PLT-059 */
    "libSDL2-2.0.so.0", "libSDL2.so",               /* PLT-060 */
};

static int load(void)
{
    for (unsigned i = 0; i < sizeof PATHS / sizeof PATHS[0] && !lib; i++) lib = dlopen(PATHS[i], RTLD_NOW);
    if (!lib) { log_msg("SDL2 non trovata: %s", dlerror()); return -1; }
#define LOAD(name) do { *(void **)&p_##name = dlsym(lib, #name); if (!p_##name) { log_msg("SDL2: manca %s", #name); return -1; } } while (0)
    LOAD(SDL_Init); LOAD(SDL_Quit); LOAD(SDL_SetHint); LOAD(SDL_GetError);
    LOAD(SDL_CreateWindow); LOAD(SDL_DestroyWindow); LOAD(SDL_CreateRenderer); LOAD(SDL_DestroyRenderer);
    LOAD(SDL_RenderSetLogicalSize); LOAD(SDL_CreateTexture); LOAD(SDL_DestroyTexture);
    LOAD(SDL_UpdateTexture); LOAD(SDL_RenderCopy); LOAD(SDL_RenderPresent); LOAD(SDL_RenderClear);
    LOAD(SDL_ShowCursor); LOAD(SDL_PollEvent);
    LOAD(SDL_InitSubSystem); LOAD(SDL_OpenAudioDevice); LOAD(SDL_QueueAudio); LOAD(SDL_PauseAudioDevice);
    LOAD(SDL_CloseAudioDevice); LOAD(SDL_GetQueuedAudioSize);
#undef LOAD
    return 0;
}

/* ---- audio di SDL con callback: il backend di riserva di PLT-022 (PLT-030), usato da audio.c ---- */
static SDL_AudioDeviceID adev;

int sdl_audio_open(int rate, int frames, void (*cb)(void *, uint8_t *, int), int *got_rate, int *got_frames)
{
    if (p_SDL_InitSubSystem(SDL_INIT_AUDIO) != 0) { log_msg("audio: %s", p_SDL_GetError()); return -1; }
    SDL_AudioSpec want, have;
    memset(&want, 0, sizeof want);
    want.freq = rate;
    want.format = AUDIO_F32SYS;
    want.channels = 2;
    want.samples = (Uint16)frames;
    want.callback = (SDL_AudioCallback)cb;
    adev = p_SDL_OpenAudioDevice(NULL, 0, &want, &have, 0);     /* formato diverso: converte SDL */
    if (!adev) { log_msg("audio: %s", p_SDL_GetError()); return -1; }
    *got_rate = have.freq;
    *got_frames = have.samples;
    p_SDL_PauseAudioDevice(adev, 0);
    return 0;
}

void sdl_audio_close(void)
{
    if (adev) { p_SDL_CloseAudioDevice(adev); adev = 0; }
}

int video_open(void)
{
    if (load()) return -1;
    p_SDL_SetHint(SDL_HINT_NO_SIGNAL_HANDLERS, "1");            /* PLT-061 */
    p_SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");          /* PLT-062 */
    if (p_SDL_Init(SDL_INIT_VIDEO) != 0) { log_msg("SDL_Init: %s", p_SDL_GetError()); return -1; }
    win = p_SDL_CreateWindow("Stame", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 640, 480,
                             SDL_WINDOW_FULLSCREEN_DESKTOP | SDL_WINDOW_SHOWN);
    if (!win) { log_msg("SDL_CreateWindow: %s", p_SDL_GetError()); return -1; }
    ren = p_SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!ren) ren = p_SDL_CreateRenderer(win, -1, 0);
    if (!ren) { log_msg("SDL_CreateRenderer: %s", p_SDL_GetError()); return -1; }
    p_SDL_RenderSetLogicalSize(ren, 640, 480);
    tex = p_SDL_CreateTexture(ren, SDL_PIXELFORMAT_RGB565, SDL_TEXTUREACCESS_STREAMING, 640, 480);
    if (!tex) { log_msg("SDL_CreateTexture: %s", p_SDL_GetError()); return -1; }
    p_SDL_ShowCursor(0);
    return 0;
}

void video_present(const uint16_t *px, const void *rects, int n_rects)
{
    const gfx_rect_t *r = (const gfx_rect_t *)rects;
    for (int i = 0; i < n_rects; i++) {
        SDL_Rect sr = { r[i].x, r[i].y, r[i].w, r[i].h };
        p_SDL_UpdateTexture(tex, &sr, px + (size_t)r[i].y * 640 + r[i].x, 640 * 2);
    }
    /* KMSDRM non manda eventi utili, ma la coda va svuotata */
    SDL_Event ev;
    while (p_SDL_PollEvent(&ev)) {}
    p_SDL_RenderClear(ren);
    p_SDL_RenderCopy(ren, tex, NULL, NULL);
    p_SDL_RenderPresent(ren);
}

void video_close(void)
{
    sdl_audio_close();
    if (tex) p_SDL_DestroyTexture(tex);
    if (ren) p_SDL_DestroyRenderer(ren);
    if (win) p_SDL_DestroyWindow(win);
    if (lib) p_SDL_Quit();
    tex = NULL; ren = NULL; win = NULL;
}
