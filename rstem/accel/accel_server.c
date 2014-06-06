/*
 * accel_server.c
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
 *
 * This code originally used the SPI testing utility included with Linux as a
 * reference.
 */

#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

#define SPI_DEV "/dev/spidev0.1"
#define SPI_HZ 500000

static int transfer(int fd, uint8_t reg, uint8_t val)
{
	int ret;
	uint8_t tx[2];
	uint8_t rx[2];
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)tx,
		.rx_buf = (unsigned long)rx,
		.len = ARRAY_SIZE(tx),
	};

	tx[0] = reg;
	tx[1] = val;
	ret = ioctl(fd, SPI_IOC_MESSAGE(1), &tr);
    if (ret != 2) {
        return (ret < 0) ? ret : -1;
    }

    return rx[0] << 8 | rx[1];
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

out:
    if (err < 0 && spi > 0)
        close(spi);
    
	return spi;
}

int main(int argc, char *argv[])
{
	int ret = 0;
	int spi;
    unsigned long reg, val;
    int c;
    int i;
    
    spi = open_spi();

    for (;;) {
        char s[64];
        int ret;
        int tx;
        int rx;

        ret = read(0, s, 4);
        if (ret != 4) break;
        s[5] = 0;

        tx = strtoul(s, NULL, 16);
        rx = transfer(spi, tx >> 8, tx & 0xFF);
        rx = rx & 0x3FF;

        sprintf(s, "%04X", rx & 0xFFFF);
        ret = write(1, s, 4);
        if (ret != 4) break;
    }

    close(spi);

    return 0;
}


