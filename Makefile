#
# Master Makefile
#
# Builds all software needed on target.  Optionally installs them.
#
export PRE_MAK=$(CURDIR)/make/prerules.mak
export POST_MAK=$(CURDIR)/make/postrules.mak
include $(PRE_MAK)

export TOPDIR=$(CURDIR)

DIRS=
DIRS+=rs
DIRS+=cellapps
DIRS+=projects
DIRS+=misc

#Putting all here forces it to be the default rule.
all::

.PHONY: install
install: 
	for i in $^; do \
		scp $$i $(PI): ;\
		ssh $(PI) tar xvf `basename $$i` ;\
	done
	for i in $(SETUID_FILES); do \
		ssh $(PI) sudo chown root $$i; \
		ssh $(PI) sudo chmod 4755 $$i; \
	done

include $(POST_MAK)
