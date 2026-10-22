/* main.c — runner dei test unitari del nucleo (PLT-075). Codice di uscita 1 se un test fallisce. */
#include "test.h"

int test_checks, test_failures;
const char *test_suite = "";

void test_spsc(void);
void test_acc(void);
void test_midi(void);
void test_input(void);
void test_blob(void);
void test_gfx(void);
void test_plancia(void);
void test_dsp(void);
void test_smp(void);
void test_motore(void);
void test_kits(void);
void test_ambient(void);

int main(void)
{
    test_suite = "spsc";  test_spsc();
    test_suite = "acc";   test_acc();
    test_suite = "midi";  test_midi();
    test_suite = "input"; test_input();
    test_suite = "blob";  test_blob();
    test_suite = "gfx";   test_gfx();
    test_suite = "plancia"; test_plancia();
    test_suite = "dsp";   test_dsp();
    test_suite = "smp";   test_smp();
    test_suite = "motore"; test_motore();
    test_suite = "kits";  test_kits();
    test_suite = "ambient"; test_ambient();
    printf("%d controlli, %d falliti\n", test_checks, test_failures);
    return test_failures ? 1 : 0;
}
