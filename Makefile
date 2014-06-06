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
DIRS+=rstem
DIRS+=cellapps
DIRS+=projects
DIRS+=misc

#Putting all here forces it to be the default rule.
all::

clean::
	rm -f install.tar

.PHONY: install.tar
install.tar:
	tar cvf $@ $(shell $(MAKE) --no-print-directory targets)

.PHONY: install
install: install.tar
	scp $< $(PI):
	ssh $(PI) "\
		rm -rf rsinstall; \
		mkdir -p rsinstall; \
		cd rsinstall; \
		tar xvf ../$<; \
		find . -name *.sbin -exec sudo chown root {} \\; ; \
		find . -name *.sbin -exec sudo chmod 4755 {} \\; ; \
		"

.PHONY: check-dev
check-dev:
	ssh $(PI) "cat - > ./test; chmod +x ./test; ./test full; rm ./test" < ./automatedtesting/runtests

include $(POST_MAK)
