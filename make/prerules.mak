RELDIR=$(subst $(TOPDIR),.,$(CURDIR))
PI=pi@$USER-raspberrypi

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
