RELDIR=$(subst $(TOPDIR),.,$(CURDIR))
COMPILEONPI=1 # set to 1 if you want to compile on pi instead
PI=pi@192.168.1.11

#TODO: get proper cflags from Joe
# Flags to compile c python wrappers

ifeq ($(PYTHON),python3)
	CFLAGS=-shared -I/usr/include/python3/ -lpython3
else
	CFLAGS=-shared -I/usr/include/python2.3/ -lpython2.3
endif

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
		gcc $(CFLAGS) $^ -o $@; \
		mv $@ ..; \
		cd ..; \
		rm -r /tmp/rs; \
		"
	scp $(PI):/tmp/$@ $@
