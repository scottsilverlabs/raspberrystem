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
	rm -f pi-install.tar
	
# create .deb file
.PHONY: deb
deb:
	@read -p "Enter Version Number (M.N.0):" version; \
	rm -r ./raspberrystem-$$version; \
	mkdir -p ./raspberrystem-$$version; \
	cp -r ./* ./raspberrystem-$$version/; \
	cd ./raspberrystem-$$version; \
	dpkg-buildpackage -b
	
.PHONY: build
build:
	./setup.py install

pi-install.tar: 
	tar cvf $@ $(shell $(MAKE) targets)
	

# had to rename from "install" for deb package installer
.PHONY: pi-install
pi-install: pi-install.tar
	scp $< $(PI):
	ssh $(PI) "\
		rm -rf rsinstall; \
		mkdir -p rsinstall; \
		cd rsinstall; \
		tar xvf ../$<; \
		find . -name *.sbin -exec sudo chown root {} \\; ; \
		find . -name *.sbin -exec sudo chmod 4755 {} \\; ; \
		"

include $(POST_MAK)
