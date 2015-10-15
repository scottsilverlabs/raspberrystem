/*
 * pullup.c
 *
 * Copyright (c) 2013  Brian Silverman <bri@blueacresembedded.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License.
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/mman.h>


#define MAP_ADDR_RPI1   0x20200000
#define MAP_ADDR_RPI2   0x3f200000
#define MAP_SIZE        0x1000
#define FIRST_RPI2_REV  0x1000

#define GPPUD       (0x94/4)
#define GPPUDCLK0   (0x98/4)

int main(int argc, char *argv[])
{
    int fd;
    unsigned long * map_base;
    unsigned long pin;
    unsigned long pullup;
    int rpi2;
    off_t map_addr;

    if (argc < 3) {
        perror("argument error");
        exit(1);
    }

    pin = atoi(argv[1]);
    pullup = atoi(argv[2]);
    rpi2 = 1;
    if (argc >= 3 && atoi(argv[3]) < FIRST_RPI2_REV) {
        rpi2 = 0;
    }

    if((fd = open("/dev/mem", O_RDWR | O_SYNC)) == -1) {
        perror("open");
        exit(1);
    }

    /* Map one page */
    map_addr = rpi2 ? MAP_ADDR_RPI2 : MAP_ADDR_RPI1;
    map_base = mmap(0, MAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, map_addr);
    if(map_base == (void *) -1) {
        perror("mmap");
        exit(1);
    }

    map_base[GPPUD] = pullup;
    usleep(1000);
    map_base[GPPUDCLK0] = 1 << pin;
    usleep(1000);
    map_base[GPPUD] = 0;
    usleep(1000);
    map_base[GPPUDCLK0] = 0;
    usleep(1000);

    if(munmap(map_base, MAP_SIZE) == -1) {
        perror("munmap");
    }

    close(fd);
    return 0;
}
