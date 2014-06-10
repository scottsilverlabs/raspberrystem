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

DESTDIR=/
BUILDIR=$(CURDIR)/debian/raspberrystem
PROJECT=raspberrystem
VERSION=0.0.1

#Putting all here forces it to be the default rule.
all::

clean::
	rm -f pi-install.tar
	./setup.py clean
	$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -rf build/ MANIFEST
	find . -name '*.pyc' -delete

source:
	./setup.py sdist $(COMPILE)

install:
	./setup.py install --root $(DESTDIR) $(COMPILE)

.PHONY: builddeb
builddeb:
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=../ 
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*
	# build the package
	dpkg-buildpackage -i -I -rfakeroot

# create .deb file
#.PHONY: deb
#deb:
#	@read -p "Enter Version Number (M.N.0):" version; \
#	rm -r ./raspberrystem_$$version; \
#	mkdir -p ./raspberrystem_$$version; \
#	cp -r ./* ./raspberrystem_$$version/; \
#	cd ./raspberrystem_$$version; \
#	./setup.py sdist --dist-dir=/
#	dpkg-buildpackage -b
	
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
