@echo off
gcc -m64 -c perlin.c
gcc -shared -o perlin.dll perlin.o -Wl,--out-implib,perlin.a
del perlin.a
del perlin.o
echo Done compiling perlin.dll
