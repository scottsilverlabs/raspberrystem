/*
 * pullup.c
 *
 * Copyright (c) 2014, Scott Silver Labs, LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License. 
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/mman.h>

 
#define MAP_ADDR    0x20200000
#define MAP_SIZE    0x1000

#define GPPUD       (0x94/4)
#define GPPUDCLK0   (0x98/4)
 
int main(int argc, char *argv[])
{
    int fd;
    unsigned long * map_base;
    unsigned long pin;
    unsigned long pullup;
 
    if((fd = open("/dev/mem", O_RDWR | O_SYNC)) == -1) {
        perror("open");
        exit(1);
    }
 
    /* Map one page */
    map_base = mmap(0, MAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, MAP_ADDR);
    if(map_base == (void *) -1) {
        perror("mmap");
        exit(1);
    }
 
    pin = atoi(argv[1]);
    pullup = atoi(argv[2]);
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
