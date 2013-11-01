/*
 * led_server.c
 *
 * Copyright (c) 2013  Brian Silverman <bri@blueacresembedded.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License.
 *
 * This LED server writes to up a fixed number (MAX_MATRICIES) of MAX7221 LED
 * drivers at a fixed rate (1/DISPLAY_PERIOD).
 *
 * Data is written to the server via stdin.  This server is intended to be
 * launched by a front end python script via Popen() and fed data through that
 * pipe - however, it can also be command via the command line using FIFO.  To
 * do so, launch the server with:
 *
 *      mkfifo fifo
 *      tail -f fifo | ./led_server &
 *
 * and then send commands to the server with:
 *
 *      echo -n <command> > fifo
 *
 * As the server is expetced to be called from a known front-end, no sanity
 * checking is performed on the stdin data.
 *
 * The server keeps an internal framebuffer for each LED matrix.  The server
 * supports remapping the order of all rows / columns, to facilitate hooking up
 * an matrix in the easiest possible physical layout.
 *
 * Commands are character strings of the format:
 *      CNNDDDDD...
 *  where
 *      C       is a one character code of the command
 *      NN      is the hex number of data bytes to follow
 *      DD...   is the data bytes for the command
 *
 *  Supported commands:
 *      n       Set the number of connected LED matrices.  Currently not used.
 *              data format: ascii integer
 *      o       Set the order mapping for a specific matrix
 *              data format: "Mabcdefgh,ABCDEFGH", where:
 *                  M           is the matrix index (0-7)
 *                  abcdefgh    are the col indexes for the mapping
 *                  ABCDEFGH    are the row indexes for the mapping
 *              For example, if c = 0, then to write to the third col, you'd
 *              write to the 0th register (which is MAX7221 register 0x01).
 *              Each number a-h should be unique.
 *      m       Write data to the framebuffer for a specific matrix
 *              data format: "Maabbccddeeffgghh", where:
 *                  M           is the matrix index (0-7)
 *                  aa          is the data for row 0
 *                  ...
 *                  hh          is the data for row 7
 *              For each row, the MSB is the first col.
 */

#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <fcntl.h>
#include <pthread.h> 
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

#define SPI_DEV "/dev/spidev0.0"
#define SPI_HZ 5000000

#define REG_NOOP            0x00
#define REG_DIGIT0          0x01
#define REG_DIGIT1          0x02
#define REG_DIGIT2          0x03
#define REG_DIGIT3          0x04
#define REG_DIGIT4          0x05
#define REG_DIGIT5          0x06
#define REG_DIGIT6          0x07
#define REG_DIGIT7          0x08
#define REG_DECODE_MODE     0x09
#define REG_INTENSITY       0x0a
#define REG_SCAN_LIMIT      0x0b
#define REG_SHUTDOWN        0x0c
    #define REG_SHUTDOWN_MODE_SHUTDOWN      0x00
    #define REG_SHUTDOWN_MODE_NORMAL        0x01
#define REG_DISPLAY_TEST    0x0f
    #define REG_DISPLAY_TEST_MODE_NORMAL    0x00
    #define REG_DISPLAY_TEST_MODE_TEST      0x01

#define DEFAULT_INTENSITY   0x08

#define DISPLAY_PERIOD      20000

#define MAX_MATRICIES   8
#define MATRIX_COLS     8
#define MATRIX_ROWS     8

#define FIRST_ROW_BIT_SET (1<<(MATRIX_ROWS-1))

int fb[MAX_MATRICIES][MATRIX_COLS][MATRIX_ROWS];

char colmap[MAX_MATRICIES][MATRIX_COLS];
char rowmap[MAX_MATRICIES][MATRIX_ROWS];
int num_matrixes = 1;

static int spi_write_reg_on_all_matrices(int fd, uint8_t reg, uint8_t vals[MAX_MATRICIES])
{
	int ret;
	uint8_t tx[MAX_MATRICIES*2];
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)tx,
		.len = ARRAY_SIZE(tx),
	};
    int i;

    for (i = 0; i < MAX_MATRICIES; i++) {
        tx[2*i] = reg;
        tx[2*i+1] = vals[MAX_MATRICIES - i - 1];
    }
	ret = ioctl(fd, SPI_IOC_MESSAGE(1), &tr);

    return ret;
}

static int spi_write_reg(int fd, uint8_t reg, uint8_t val)
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
    const char *device = SPI_DEV;
    uint8_t mode = 0;
    uint8_t bits = 8;
    uint32_t speed = SPI_HZ;
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

	err = spi_write_reg(spi, REG_DECODE_MODE, 0x00);
	if (err < 0)
		goto out;
	err = spi_write_reg(spi, REG_INTENSITY, DEFAULT_INTENSITY);
	if (err < 0)
		goto out;
	err = spi_write_reg(spi, REG_SCAN_LIMIT, 0x07);
	if (err < 0)
		goto out;
	err = spi_write_reg(spi, REG_SHUTDOWN, REG_SHUTDOWN_MODE_NORMAL);
	if (err < 0)
		goto out;
	err = spi_write_reg(spi, REG_DISPLAY_TEST, 0x00);
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
    char * rowdata;
    char * coldata;

    m = data[0] - '0';
    coldata = &data[1];
    for (i = 0; i < MATRIX_COLS; i++) {
        colmap[m][i] = coldata[i] - '0';
    }
    rowdata = &data[1+MATRIX_COLS+1];
    for (i = 0; i < MATRIX_ROWS; i++) {
        rowmap[m][i] = rowdata[i] - '0';
    }
}

int hex2bin(char * hex)
{
    char s[3];
    s[0] = hex[0];
    s[1] = hex[1];
    s[2] = 0;
    return strtoul(s, NULL, 16);
}

void write_fb(char * data)
{
    int m;
    int col;
    int row;

    //
    // data format: "Maabbccddeeffgghh", where:
    //      M               is the matrix index ('0' - '7')
    //      aa through hh   is the hex value of column
    //          
    m = data[0] - '0';
    for (col = 0; col < MATRIX_COLS; col++) {
        int rowval = hex2bin(&data[1+col*2]);
        for (row = 0; row < MATRIX_ROWS; row++) {
            fb[m][col][row] = rowval & (FIRST_ROW_BIT_SET>>row);
        }
    }
}

#ifdef DEBUG
void debug_display_fb()
{
    int m;
    int col;
    int row;

    for (row = MATRIX_ROWS - 1; row >= 0; row--) {
        for (m = 0; m < MAX_MATRICIES; m++) {
            for (col = 0; col < MATRIX_COLS; col++) {
                printf("%c", fb[m][col][row] ? '#' : 'x');
            }
            printf(" ");
        }
        printf("\n");
    }
}
#else
void debug_display_fb() {}
#endif

void display_matrix(int spi)
{
    int m;
    int col;
    int row;
    uint8_t shadow[MATRIX_COLS][MAX_MATRICIES];

    debug_display_fb();

    memset(shadow, 0, sizeof(shadow));
    for (m = 0; m < MAX_MATRICIES; m++) {
        for (col = 0; col < MATRIX_COLS; col++) {
            int digit = 0;
            for (row = 0; row < MATRIX_ROWS; row++) {
                if (fb[m][col][row])
                    digit |= FIRST_ROW_BIT_SET >> rowmap[m][row];
            }
            shadow[colmap[m][col]][m] = digit;
        }
    }
    for (col = 0; col < MATRIX_COLS; col++) {
        spi_write_reg_on_all_matrices(spi, col + 1, shadow[col]);
    }
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
            write_fb(get_data(fifo));
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
    int m;
    
    //
    // Set defaults for col/row map
    //
    for (m = 0; m < MAX_MATRICIES; m++) {
        for (i = 0; i < MATRIX_COLS; i++) {
            colmap[m][i] = i;
        }
        for (i = 0; i < MATRIX_ROWS; i++) {
            rowmap[m][i] = i;
        }
    }

    spi = open_spi();

    fifo = 0; // stdin

    void *f1(int *x){
        for (;;) {
            usleep(DISPLAY_PERIOD);
            display_matrix(*x);
        }
    }
    pthread_t f1_thread; 
    pthread_create(&f1_thread,NULL,f1,&spi);

    for (;;) {
        process_cmd(fifo, spi);
    }

    close(fifo);
    close(spi);

    return 0;
}


