PI=pi@raspberrypi
RUNONPI=ssh $(SSHFLAGS) -q -t $(PI) "mkdir -p rsinstall; cd rsinstall;"

all: bin/pullup.sbin

bin/pullup.sbin: src/pullup.sbin.c
	scp $< $(PI):/tmp
	$(RUNONPI) "cd /tmp; gcc $(notdir $<) -o pullup.out"
	mkdir -p $(dir $@)
	scp $(PI):/tmp/pullup.out $@

