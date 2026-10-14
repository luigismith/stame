/* main.c — runner dei test unitari del nucleo (PLT-075). Codice di uscita 1 se un test fallisce. */
#include "test.h"

int test_checks, test_failures;
const char *test_suite = "";

void test_spsc(void);
void test_acc(void);
void test_midi(void);
void test_input(void);
void test_blob(void);

int main(void)
{
    test_suite = "spsc";  test_spsc();
    test_suite = "acc";   test_acc();
    test_suite = "midi";  test_midi();
    test_suite = "input"; test_input();
    test_suite = "blob";  test_blob();
    printf("%d controlli, %d falliti\n", test_checks, test_failures);
    return test_failures ? 1 : 0;
}
