RELDIR=$(subst $(TOPDIR),.,$(CURDIR))
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
	@echo dude
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
	$(eval REMOTE_TMP=$(shell ssh $(PI) "mktemp -d"))
	scp $^ $(PI):$(REMOTE_TMP)
	ssh $(PI) "cd $(REMOTE_TMP) && gcc -lpthread $^ -o $@"
	scp $(PI):$(REMOTE_TMP)/$@ $@
	ssh $(PI) "rm -r $(REMOTE_TMP)"
