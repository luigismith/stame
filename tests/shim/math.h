/* math.h minimo per la compilazione di prova freestanding Cortex-M7 (PLT-107).
 * Solo funzioni a singola precisione (PLT-100). */
#ifndef STAME_SHIM_MATH_H
#define STAME_SHIM_MATH_H

float sinf(float x);
float cosf(float x);
float tanf(float x);
float expf(float x);
float logf(float x);
float log2f(float x);
float powf(float x, float y);
float sqrtf(float x);
float fabsf(float x);
float floorf(float x);
float ceilf(float x);
float fmodf(float x, float y);
float atanf(float x);
float tanhf(float x);

#endif
