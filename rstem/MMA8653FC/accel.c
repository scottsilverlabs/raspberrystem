//#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#define STATUS 0x00
#define OUT_X_MSB 0x01
#define XYZ_DATA_CFG 0x0E
#define CTRL_REG1 0x2A
#define CTRL_REG2 0x2B
#define CTRL_REG3 0x2C
#define CTRL_REG4 0x2D
#define CTRL_REG5 0x2E
#define FF_MT_CFG 0x15
#define FF_MT_SRC 0x16
#define FF_MT_THS 0x17
#define FF_MT_COUNT 0x18

int adapter_number = 0;
int addr = 0x1D;
char rawData[7];
int accelData[3];
int file;
char int_enable = 0x00;
char int_pins = 0x00;

int init_i2c(){
	adapter_number = adapter_number;
	char filename[20];
	snprintf(filename, 19, "/dev/i2c-%d", adapter_number);
	file = open(filename, O_RDWR);
	return file;
}

int set_slave(){
	return ioctl(file, I2C_SLAVE, addr);
}

int write_command(char reg, char value){
	return i2c_smbus_write_byte_data(file, reg, value);
}

void init_accel() {
	init_i2c();
	set_slave();
	write_command(CTRL_REG1, 0x00);
	write_command(XYZ_DATA_CFG, 0x01);
	write_command(CTRL_REG1, 0x01);
}

//Mode is 0 for free fall, 1 for motion detect
void enable_freefall_motion(int mode, int pin){
	int_enable |= (1 << 2);
	write_command(CTRL_REG1, 0x00);
	write_command(CTRL_REG3, 2);
	write_command(CTRL_REG4, int_enable);
	char config = (1 << 5) | (1 << 4) | (1 << 3);
	if(pin == 1){
		int_pins |= (1 << 2);
	} else {
		int_pins &= ~(1 << 2);
	}
	write_command(CTRL_REG5, int_pins);
	if(mode == 0){
		write_command(FF_MT_CFG, config);
	} else {
		write_command(FF_MT_CFG, config | (1 << 6));
	}
	write_command(CTRL_REG1, 0x01);
}

void set_freefall_motion_threshold(char debounce_mode, char thresh){
	write_command(CTRL_REG1, 0x00);
	write_command(FF_MT_THS, ((debounce_mode & 0x01) << 8) | (thresh & 0x7F));
	write_command(CTRL_REG1, 0x01);
}

void set_freefall_motion_debounce(char counts){
	write_command(FF_MT_COUNT, counts);
}

int update_data(){
	usleep(1000);
	i2c_smbus_read_i2c_block_data(file, 0x00, 7, rawData);
	int i;
	for(i = 0; i < 3; i++){
		accelData[i] = (rawData[2*i+1] << 2) | ((rawData[2*i+2] >> 6) & 0x03);
		if(accelData[i] > 1024/2) {
			accelData[i] -= 1025;
		}
	}
}

int main(){
	init_accel();
	usleep(1000);
	enable_freefall_motion(1, 1);
	set_freefall_motion_threshold(0, 20);
	int count = 0;
	while(count < 10){
		update_data();
		printf("X: %d\tY: %d\tZ: %d\n", accelData[0], accelData[1], accelData[2]);
//		printf("%d\n", i2c_smbus_read_byte(file));
		fflush(stdout);
		usleep(100000);
		count++;
	}
	return 0;
}
