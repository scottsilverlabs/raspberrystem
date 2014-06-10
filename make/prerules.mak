RELDIR=$(subst $(TOPDIR),.,$(CURDIR))
COMPILEONPI=0 # set to 1 if you want to compile on pi instead
PI=pi@raspberrypi

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
ifeq ($(COMPILEONPI), 1)
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
else
	gcc $(CFLAGS) $^ -o $@
endif
