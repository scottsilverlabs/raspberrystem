RELDIR=$(subst $(TOPDIR),.,$(CURDIR))
PI=pi@raspberrypi

# proper CFLAGS if need to compile c manually
ifeq ($(PYTHON),python3)
	CFLAGS=-shared -I/usr/include/python3.2mu/ -lpython3.2mu
else
	CFLAGS=-shared -I/usr/include/python2.7/ -lpython2.7
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
	# Do nothing because the extensions are installed through setup.py
