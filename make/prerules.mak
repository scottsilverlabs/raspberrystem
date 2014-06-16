RELDIR=$(subst $(TOPDIR),.,$(CURDIR))
COMPILEONPI=1 # set to 1 if you want to compile on pi instead
PI=pi@192.168.1.11
# ssh password on raspberrypi
PIPASSWORD=raspberry

#TODO: get proper cflags from Joe
# Flags to compile c python wrappers

CFLAGSTEMP=
CFLAGS2=-shared -I/usr/include/python2.3/ -lpython2.3
CFLAGS3=-shared -I/usr/include/python3/ -lpython3

#
# Directory rules
#
%.dir: %
	make -C $^

%.targets: %
	@make -C $^ targets

%.cleandir: %
	make -C $^ clean

#
# Per file clean rules
#
%.py.clean: %.py
	@#Do nothing

%.c.clean: %.c
	rm -f $*

%.clean:
	rm -f $*

#
# Per file target echo rules
#
%.c.target: %.c
	@echo $(RELDIR)/$*

%.target:
	@echo $(RELDIR)/$*


#
# Per file build rules
#
%: %.c
	scp $^ $(PI):/tmp
	ssh $(PI) "\
		mkdir -p /tmp/rs; \
		cd /tmp/rs; \
		mv ../$^ .; \
		gcc $(CFLAGSTEMP) $^ -o $@; \
		mv $@ ..; \
		cd ..; \
		rm -r /tmp/rs; \
		"
	sshpass -p '$(PIPASSWORD)' scp $(PI):/tmp/$@ $@
