RELDIR=$(subst $(TOPDIR),.,$(CURDIR))
COMPILEONPI=1 # set to 1 if you want to compile on pi instead
PI=pi@192.168.1.11
SSHPASS=sshpass -p 'raspberry'  # comment this line out if you don't want to use sshpass
SSHFLAGS= -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null


ifeq ($(PYTHON),python3)
	CFLAGS=-shared -I/usr/include/python3.2mu/ -lpython3.2mu
else
	CFLAGS=-shared -I/usr/include/python2.7/ -lpython2.7
endif

#
# Directory rules
#
%.dir: %
	@echo "In $@"
	make -C $^

%.targets: %
	@echo "In $@"
	@make -C $^ targets

%.cleandir: %
	@echo "In $@"
	make -C $^ clean

#
# Per file clean rules
#
%.py.clean: %.py
	@echo "In $@"
	@#Do nothing

%.c.clean: %.c
	@echo "In $@"
	rm -f $*

%.clean:
	@echo "In $@"
	rm -f $*

#
# Per file target echo rules
#
%.c.target: %.c
	@echo "In $@"
	@echo $(RELDIR)/$*

%.target:
	@echo "In $@"
	@echo $(RELDIR)/$*


#
# Per file build rules
#
%: %.c
	@echo "In $@"
	gcc $(CFLAGS) $^ -o $@.so
#	$(SSHPASS) scp $(SSHFLAGS) $^ $(PI):/tmp
#	$(SSHPASS) ssh $(SSHFLAGS) $(PI) "\
#		mkdir -p /tmp/rs; \
#		cd /tmp/rs; \
#		mv ../$^ .; \
#		gcc $(CFLAGS) $^ -o $@; \
#		mv $@ ..; \
#		cd ..; \
#		rm -r /tmp/rs; \
#		"
#	$(SSHPASS) scp $(SSHFLAGS) $(PI):/tmp/$@ $@
