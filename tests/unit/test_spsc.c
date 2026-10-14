/* test_spsc.c — coda SPSC: base, saturazione, avvolgimento degli indici, due thread. */
#include "test.h"
#include "core/spsc.h"

#ifdef _WIN32
#include <windows.h>
#else
#include <pthread.h>
#endif

typedef struct { uint32_t seq; uint32_t chk; } item_t;

#define N_ITEMS 200000u

static item_t buf[256];
static spsc_t q;
static uint32_t retries;   /* push falliti a coda piena: devono coincidere con dropped */

static void produce(void)
{
    for (uint32_t i = 0; i < N_ITEMS; ) {
        item_t it = { i, ~i };
        if (spsc_push(&q, &it)) i++; else retries++;
    }
}

#ifdef _WIN32
static DWORD WINAPI produce_thread(LPVOID p) { (void)p; produce(); return 0; }
#else
static void *produce_thread(void *p) { (void)p; produce(); return NULL; }
#endif

void test_spsc(void)
{
    item_t it = { 0, 0 }, out;

    CHECK(!spsc_init(&q, buf, sizeof buf[0], 100));     /* non è una potenza di 2 */
    CHECK(!spsc_init(&q, buf, sizeof buf[0], 0));
    CHECK(spsc_init(&q, buf, sizeof buf[0], 256));
    CHECK(!spsc_pop(&q, &out));
    CHECK_EQ(spsc_count(&q), 0);

    /* riempimento, saturazione e svuotamento in ordine */
    for (uint32_t i = 0; i < 256; i++) { it.seq = i; it.chk = ~i; CHECK(spsc_push(&q, &it)); }
    it.seq = 999; CHECK(!spsc_push(&q, &it));
    CHECK_EQ(spsc_dropped(&q), 1);
    CHECK_EQ(spsc_count(&q), 256);
    for (uint32_t i = 0; i < 256; i++) {
        CHECK(spsc_pop(&q, &out));
        CHECK(out.seq == i && out.chk == ~i);
    }
    CHECK(!spsc_pop(&q, &out));

    /* avvolgimento degli indici a 32 bit */
    atomic_store(&q.head, 0xFFFFFF80u);
    atomic_store(&q.tail, 0xFFFFFF80u);
    bool ok = true;
    for (uint32_t i = 0; i < 1000; i++) {
        it.seq = i; it.chk = ~i;
        if (!spsc_push(&q, &it) || !spsc_pop(&q, &out) || out.seq != i) ok = false;
    }
    CHECK(ok);
    CHECK_EQ(spsc_count(&q), 0);

    /* due thread: il consumatore deve vedere tutto, nell'ordine, senza corruzione */
    CHECK(spsc_init(&q, buf, sizeof buf[0], 256));
#ifdef _WIN32
    HANDLE th = CreateThread(NULL, 0, produce_thread, NULL, 0, NULL);
    CHECK(th != NULL);
#else
    pthread_t th;
    CHECK(pthread_create(&th, NULL, produce_thread, NULL) == 0);
#endif
    uint32_t expected = 0; int errors = 0;
    while (expected < N_ITEMS) {
        if (!spsc_pop(&q, &out)) continue;
        if (out.seq != expected || out.chk != ~expected) errors++;
        expected++;
    }
#ifdef _WIN32
    WaitForSingleObject(th, INFINITE);
    CloseHandle(th);
#else
    pthread_join(th, NULL);
#endif
    CHECK_EQ(errors, 0);
    CHECK_EQ(spsc_dropped(&q), retries);
    CHECK(!spsc_pop(&q, &out));
}
