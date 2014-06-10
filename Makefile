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
PROJECTSDIR=$$HOME/rstem/projects
CELLAPPSDIR=$$HOME/rstem/cellapps
BUILDIR=$(CURDIR)/debian/raspberrystem
PROJECT=raspberrystem

#Putting all here forces it to be the default rule.
all::

clean::
	rm -f pi-install.tar
	./setup.py clean
#	$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -rf build/
	find . -name '*.pyc' -delete
	# cleaning up builddeb files...
#	sudo rm -rf ./build
#	sudo rm -rf ./$(PROJECT).egg-info
#	sudo rm -rf 's/$(PROJECT)-(.*)\.orig\.tar\.gz/'

source:
	./setup.py sdist $(COMPILE)

install:
	./setup.py install --root $(DESTDIR) $(COMPILE)

.PHONY: builddeb
builddeb:
	# put project and cellapps into user's home folder
	# TODO: this doesn't work because the user folder won't be same as me...
	sudo mkdir -p $(BUILDIR)$(PROJECTSDIR)
	sudo mkdir -p $(BUILDIR)$(CELLAPPSDIR)
	sudo cp -r ./projects $(BUILDIR)$(PROJECTSDIR)
	sudo cp -r ./cellapps $(BUILDIR)$(CELLAPPSDIR)
	# build the source package in the current directory
	# then rename it to project_version.orig.tar.gz
	sudo ./setup.py sdist --dist-dir=./ 
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ./*
	# build the package
	sudo dpkg-buildpackage -i -I -rfakeroot


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
