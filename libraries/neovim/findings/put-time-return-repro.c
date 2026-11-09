#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <time.h>
#define OK 1
#define FAIL 0
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
static void time_to_bytes(time_t t, uint8_t b[8]){for(int i=7;i>=0;i--){b[i]=(uint8_t)t;t>>=8;}}
#include PUT_C /* build.py output */
int main(void){FILE*f=tmpfile();int r=put_time(f,(time_t)1234567890);fflush(f);printf("put_time on a good file returned %s, file size %ld\n",r==OK?"OK":"FAIL",ftell(f));return r!=FAIL;}
