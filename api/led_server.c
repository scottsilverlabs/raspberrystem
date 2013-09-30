/*
 * SPI testing utility (using spidev driver)
 *
 * Copyright (c) 2007  MontaVista Software, Inc.
 * Copyright (c) 2007  Anton Vorontsov <avorontsov@ru.mvista.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License.
 *
 * Cross-compile with cross-gcc -I/path/to/cross-kernel/include
 */

#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

#define MAX_MATRICIES 8

char rowmap[MAX_MATRICIES][8];
char colmap[MAX_MATRICIES][8];
int num_matrixes = 1;

static int transfer(int fd, uint8_t reg, uint8_t val)
{
	int ret;
	uint8_t tx[2];
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)tx,
		.len = ARRAY_SIZE(tx),
	};

	tx[0] = reg;
	tx[1] = val;
	ret = ioctl(fd, SPI_IOC_MESSAGE(1), &tr);

    return ret;
}

int open_spi()
{
    const char *device = "/dev/spidev0.0";
    uint8_t mode = 0;
    uint8_t bits = 8;
    uint32_t speed = 10000000;
    int spi = 0;
    int err = -1;

	spi = open(device, O_RDWR);
	if (spi < 0)
		goto out;

	/*
	 * spi mode
	 */
	err = ioctl(spi, SPI_IOC_WR_MODE, &mode);
	if (err < 0)
		goto out;

	err = ioctl(spi, SPI_IOC_RD_MODE, &mode);
	if (err < 0)
		goto out;

	/*
	 * bits per word
	 */
	err = ioctl(spi, SPI_IOC_WR_BITS_PER_WORD, &bits);
	if (err < 0)
		goto out;

	/*
	 * max speed hz
	 */
	err = ioctl(spi, SPI_IOC_WR_MAX_SPEED_HZ, &speed);
	if (err < 0)
		goto out;

	err = transfer(spi, 0x09, 0x00);
	if (err < 0)
		goto out;
	err = transfer(spi, 0x0A, 0x08);
	if (err < 0)
		goto out;
	err = transfer(spi, 0x0B, 0x07);
	if (err < 0)
		goto out;
	err = transfer(spi, 0x0C, 0x01);
	if (err < 0)
		goto out;

out:
    if (err < 0 && spi > 0)
        close(spi);
    
	return spi;
}

char * get_data(int fifo)
{
    static char s[256];
    int ret;
    int len;

    ret = read(fifo, s, 2);
    if (ret != 2) return NULL;
    s[2] = 0;
    len = strtoul(s, NULL, 16);

    ret = read(fifo, s, len);
    if (ret != len) return NULL;
    s[len] = 0;

    return s;
}

void set_order(char * data)
{
    int m;
    int i;
    int j;

    for (m = 0; m < num_matrixes; m++) {
        for (i = 0; i < 2; i++) {
            for (j = 0; j < 8; j++) {
                int mapping = data[m*16+i*8+j] - '0';
                if (i) {
                    colmap[m][j] = mapping;
                } else {
                    rowmap[m][j] = mapping;
                }
            }
        }
    }
}

void display_matrix(int spi, char * data)
{
    int m;
    int row;
    int col;
    char s[3];

    for (m = 0; m < num_matrixes; m++) {
        for (row = 0; row < 8; row++) {
            char * digit_str = &data[m*16+row*2];
            int digit;
            int remapped_digit;
            s[0] = digit_str[0];
            s[1] = digit_str[1];
            s[2] = 0;
            digit = strtoul(s, NULL, 16);
            remapped_digit = 0;
            for (col = 0; col < 8; col++) {
                if (digit & (1<<col)) 
                    remapped_digit |= 1 << colmap[m][col] - 1;
            }
            transfer(spi, rowmap[m][row], remapped_digit);
        }
    }
#if 0
    for(;;) {
        int i;
        for (i = 0; i < 256; i++) {
            transfer(spi, rowmap[0][0], i & 1 ? 0xff : 0);
            transfer(spi, rowmap[0][1], i & 2 ? 0xff : 0);
            transfer(spi, rowmap[0][2], i & 3 ? 0xff : 0);
            transfer(spi, rowmap[0][3], i & 4 ? 0xff : 0);
            transfer(spi, rowmap[0][4], i & 5 ? 0xff : 0);
            transfer(spi, rowmap[0][5], i & 6 ? 0xff : 0);
            transfer(spi, rowmap[0][6], i & 7 ? 0xff : 0);
            transfer(spi, rowmap[0][7], i & 8 ? 0xff : 0);
            usleep(16000);
        }
    }
#endif
}

void process_cmd(int fifo, int spi)
{
    char cmd;
    int ret;
    ret = read(fifo, &cmd, 1);
    if (ret != 1) return;
    switch (cmd) {
        case 'n':
            num_matrixes = atoi(get_data(fifo));
            break;
        case 'o':
            set_order(get_data(fifo));
            break;
        case 'm':
            display_matrix(spi, get_data(fifo));
            break;
        default:
            break;
    }
}

int main(int argc, char *argv[])
{
	int ret = 0;
	int spi;
    unsigned long reg, val;
    int fifo;
    int c;
    int i;
    
    spi = open_spi();

    //fifo = open("fifo", O_RDONLY);
    fifo = 0;

    for (;;) {
        process_cmd(fifo, spi);
    }

    close(fifo);
    close(spi);

    return 0;
}


