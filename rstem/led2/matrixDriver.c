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
 */

#define F_CPU 8000000
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <stdlib.h>

#define SET(PORT,PIN,VALUE) ((PORT) & ~(1 << (PIN))) | ((VALUE) << (PIN));
#define COL_PORT PORTD
#define ROW0 PORTC0
#define ROW1 PORTC1
#define ROW2 PORTC2
#define ROW3 PORTC3
#define ROW4 PORTC4
#define ROW5 PORTC5
#define ROW6 PORTB0
#define ROW7 PORTB1

volatile unsigned char *store;
volatile unsigned char *show;
volatile unsigned char *swap;
volatile int count = 0;
unsigned char fliped = 1;

//This interrupt fires when the SPDR register is done loading a new byte
ISR(SPI_STC_vect) {
	//Store contents
	store[count] = SPDR;
	//Load data for next matrix
	SPDR = store[(count+1)&31];
	//Reset change variable
	fliped = 0;
	//Increment count and wrap around
	count = (count+1)&31;
}

void delay_us(char del) {
	while(del-->0){
		_delay_us(1);
	}
}

int main(void) {
	//Allocate initial memory
	store = (unsigned char*) malloc((sizeof(unsigned char))*32);
	show = (unsigned char*) malloc((sizeof(unsigned char))*32);
	
	//Set output ports
	DDRB = (1<<PORTB4) | (1<<PORTB1) | (1<<PORTB0)| (1<<PORTB7);
	DDRD = 0xFF;
	DDRC = 0xFF;
	
	//Initialize SPI
	SPCR = (1<<SPE) | (1<<SPIE);   //Enable SPI
	SPCR &= ~((1<<CPOL) | (1<<CPHA));
	
	//Enable global interrupts
	sei();
	
	//Initialize matrix with gradient, will be removed for final version
	for(int i = 0; i < 32; i++){
		show[i] = ((0+i)&31)/4 | ((((0+i)&31)/4) << 4);
	}
	for(int i = 0; i < 32; i++){
		store[i] = 0;
	}
	
	unsigned char one;
	unsigned char two;
	unsigned char three;
	unsigned char four;
	unsigned char iterations = 0;
	
	//Initialize output data
	SPDR = store[count];
	
	//Supposedly faster than a while loop because it is assumed to be true instead of checking each time
	//not sure if I believe it though
	for(;;) {
		//If it has just received data
		if(fliped == 0 && ((PINB & (1 << 2))==0b00000100)) {
			//Show the data in storage, store new data in the old array
			swap = store;
			store = show;
			show = swap;
			fliped = 1;
			} else {
			//Software PWM loop
				for(unsigned char i = 0; i < 8; i++){
					one = show[i*4];
					two = show[i*4 + 1];
					three = show[i*4 + 2];
					four = show[i*4 + 3];
					PORTC = SET(PORTC,PORTC0,0);
					PORTC = SET(PORTC,PORTC1,0);
					PORTC = SET(PORTC,PORTC2,0);
					PORTC = SET(PORTC,PORTC3,0);
					PORTC = SET(PORTC,PORTC4,0);
					PORTC = SET(PORTC,PORTC5,0);
					PORTB = SET(PORTB,PORTB1,0);
					PORTB = SET(PORTB,PORTB0,0);
					COL_PORT = 0xFF;
					
					PORTC = SET(PORTC,PORTC0,(one&0x0F)>iterations);
					PORTC = SET(PORTC,PORTC1,(one>>4)>iterations);
					PORTC = SET(PORTC,PORTC2,(two&0x0F)>iterations);
					PORTC = SET(PORTC,PORTC3,(two>>4)>iterations);
					PORTC = SET(PORTC,PORTC4,(three&0x0F)>iterations);
					PORTC = SET(PORTC,PORTC5,(three>>4)>iterations);
					PORTB = SET(PORTB,PORTB0,(four&0x0F)>iterations);
					PORTB = SET(PORTB,PORTB1,(four>>4)>iterations);
					
					COL_PORT = ~(1 << i);
				}
			iterations = (++iterations)&15;
		}
	}
}