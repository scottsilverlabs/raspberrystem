PI=pi@raspberrypi
RUNONPI=ssh $(SSHFLAGS) -q -t $(PI) "mkdir -p rsinstall; cd rsinstall;"

all: bin/pullup.sbin bin/rstem_mixer

bin/pullup.sbin: src/pullup.sbin.c
	scp $< $(PI):/tmp
	$(RUNONPI) "cd /tmp; gcc $(notdir $<) -o bin.out"
	mkdir -p $(dir $@)
	scp $(PI):/tmp/bin.out $@

bin/rstem_mixer: src/mixer.c
	scp $< $(PI):/tmp
	$(RUNONPI) "cd /tmp; gcc $(notdir $<) -lpthread -lasound -o bin.out"
	mkdir -p $(dir $@)
	scp $(PI):/tmp/bin.out $@

