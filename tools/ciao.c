/* ciao.c — prova della toolchain per la Flip (fase F0): programma minimo compilato per
 * aarch64-linux-gnu.2.27 con Zig dal PC Windows (PLT-070). Tocca pthread, dl e libm
 * perché il link con -lpthread -ldl -lm (PLT-071) venga provato davvero.
 * Sulla Flip: scp build/flip/ciao root@<ip>:/tmp/ && ssh root@<ip> /tmp/ciao */
#include <stdio.h>
#include <pthread.h>
#include <dlfcn.h>
#include <math.h>

int main(void)
{
    pthread_t me = pthread_self();
    void *sdl = dlopen("libSDL2-2.0.so.0", RTLD_NOW);
    printf("ciao dalla Flip: thread %lu, sqrtf(2) = %.4f, SDL2 %s\n",
           (unsigned long)me, (double)sqrtf(2.0f), sdl ? "trovata" : "non trovata");
    if (sdl) dlclose(sdl);
    return 0;
}
