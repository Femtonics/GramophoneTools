@echo off
gcc -m64 -c perlin.c
gcc -shared -o perlin64.dll perlin.o -Wl,--out-implib,perlin.a
del perlin.a
del perlin.o
echo Done compiling perlin64.dll

gcc -c perlin.c
gcc -shared -o perlin32.dll perlin.o
del perlin.o
echo Done compiling perlin32.dll
