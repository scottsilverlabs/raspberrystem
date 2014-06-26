#include <wiringPi.h>
#include <stdio.h>

long capRead(int send, int rec, long timeout) {
	pinMode(rec, OUTPUT);
	digitalWrite(rec, LOW);
	delay(1);
	pinMode(send, OUTPUT);
	digitalWrite(send, LOW);
	pinMode(rec, INPUT);
	long t = 0;
	digitalWrite(send, HIGH);
	while(!digitalRead(rec) && t < timeout){
		t++;
	}
	digitalWrite(send, LOW);
	return t;
}

int main (void) {
	wiringPiSetup();
		for(;;){
			printf("%i\n", capRead(27,4,10000000));
		}
}
