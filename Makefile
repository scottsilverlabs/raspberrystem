#
# Master Makefile
#
# Builds all software needed on target.  Optionally installs them.
#
SHELL = /bin/bash
export PRE_MAK=$(CURDIR)/make/prerules.mak
export POST_MAK=$(CURDIR)/make/postrules.mak
include $(PRE_MAK)

export TOPDIR=$(CURDIR)

DIRS=
DIRS+=rstem
DIRS+=cellapps
DIRS+=projects
DIRS+=misc

PYTHON=python
PYFLAGS=
DESTDIR=/
PROJECTSDIR=$$HOME/rstem/projects
CELLAPPSDIR=$$HOME/rstem/cellapps
#BUILDIR=$(CURDIR)/debian/raspberrystem

# Calculate the base names of the distribution, the location of all source,
NAME:=$(shell $(PYTHON) $(PYFLAGS) setup.py --name)
VER:=$(shell $(PYTHON) $(PYFLAGS) setup.py --version)


PYVER:=$(shell $(PYTHON) $(PYFLAGS) -c "import sys; print('py%d.%d' % sys.version_info[:2])")
PY_SOURCES:=$(shell \
	$(PYTHON) $(PYFLAGS) setup.py egg_info >/dev/null 2>&1 && \
	grep -v "\.egg-info" $(NAME).egg-info/SOURCES.txt)
DEB_SOURCES:=debian/changelog \
	debian/control \
	debian/copyright \
	debian/rules \
#	debian/docs \
	$(wildcard debian/*.init) \
	$(wildcard debian/*.default) \
	$(wildcard debian/*.manpages) \
#	$(wildcard debian/*.docs) \
	$(wildcard debian/*.doc-base) \
	$(wildcard debian/*.desktop)
DOC_SOURCES:=docs/conf.py \
	$(wildcard docs/*.png) \
	$(wildcard docs/*.svg) \
	$(wildcard docs/*.rst) \
	$(wildcard docs/*.pdf)

# Types of dist files all located in dist folder
DIST_EGG=dist/$(NAME)-$(VER)-$(PYVER).egg
DIST_TAR=dist/$(NAME)-$(VER).tar.gz
DIST_ZIP=dist/$(NAME)-$(VER).zip
DIST_DEB=dist/python-$(NAME)_$(VER)_armhf.deb \
	dist/python3-$(NAME)_$(VER)_armhf.deb
#	dist/python-$(NAME)-docs_$(VER)-1$(DEB_SUFFIX)_all.deb
DIST_DSC=dist/$(NAME)_$(VER).tar.gz \
	dist/$(NAME)_$(VER).dsc \
	dist/$(NAME)_$(VER)_source.changes

.PHONY: all install test doc source egg zip tar deb dist clean release upload-all upload-ppa upload-cheeseshop pi-install projects cellapps upload-check

all:
	@echo "make install - Install on local system"
	@echo "TODO: make pi-install - Install onto remote Raspberry Pi"
	@echo "make projects - Install projects to home folder"
	@echo "make cellapps - Install cellapps to home folder"
#	@echo "make test - Run tests"
#	@echo "make doc - Generate HTML and PDF documentation"
	@echo "make source - Create source package"
	@echo "make egg - Generate a PyPI egg package"
	@echo "make zip - Generate a source zip package"
	@echo "make tar - Generate a source tar package"
	@echo "make deb - Generate Debian packages"
	@echo "make dist - Generate all packages"
	@echo "make clean - Get rid of all generated files"
	@echo "make release - Create and tag a new release"
	@echo "make upload-all - Upload the new release to all repositories"
	@echo "make upload-ppa - Upload the new release to ppa"
	@echo "make upload-cheeseshop - Upload the new release to cheeseshop"
	


install:
	sudo $(PYTHON) $(PYFLAGS) ./setup.py install --root $(DESTDIR)
	$(MAKE) projects
	$(MAKE) cellapps
	
projects:
	mkdir -p $(PROJECTSDIR)
	cp -r ./projects $(PROJECTSDIR)

cellapps:
	mkdir -p $(CELLAPPSDIR)
	cp -r ./cellapps $(CELLAPPSDIR)

test:
    # TODO
    
upload-check:
	# Check that we are in correct branch....
	@if ! git branch | grep -q "* rel/$(VER)"; then \
		echo "Not in the expected branch rel/$(VER)."; \
		echo "Either change your branch to rel/$(VER) or update the version number in ./setup.py"; \
		exit 2; \
	else \
		echo "In correct branch."; \
	fi 
    
upload-all:
	$(MAKE) upload-ppa
	$(MAKE) upload-cheeseshop
	
upload-ppa: $(DIST_DSC)
	# TODO: change this from raspberrystem-test ppa to an official one
	# (to add this repo on raspberrypi type: sudo add-apt-repository ppa:r-jon-s/ppa)
	$(MAKE) upload-check
	dput ppa:r-jon-s/ppa dist/$(NAME)_$(VER)_source.changes

upload-cheeseshop: $(PY_SOURCES)
	# update the package's registration on PyPI (in case any metadata's changed)
	$(MAKE) upload-check
	$(PYTHON) $(PYFLAGS) setup.py register
    
source: $(DIST_TAR) $(DIST_ZIP)

egg: $(DIST_EGG)

zip: $(DIST_ZIP)

tar: $(DIST_TAR)

deb: $(DIST_DSC) $(DIST_DEB)

dist: $(DIST_EGG) $(DIST_DEB) $(DIST_DSC) $(DIST_TAR) $(DIST_ZIP)

clean:
	$(PYTHON) $(PYFLAGS) setup.py clean
	$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -rf build/ dist/ $(NAME).egg-info/ $(NAME)-$(VER) 
	rm -rf debian/python3-$(NAME) debian/python-$(NAME) 
	rm -f debian/python*
	rm -f ../$(NAME)_$(VER).orig.tar.gz ../$(NAME)_$(VER)_armhf.build ../$(NAME)_$(VER)_armhf.changes ../$(NAME)_$(VER)_source.build
	rm -f ../python-$(NAME)_$(VER)_armhf.deb ../python3-$(NAME)_$(VER)_armhf.deb
	rm -f ../$(NAME)_$(VER).dsc ../$(NAME)_$(VER).tar.gz ../$(NAME)_$(VER)_source.changes
	find $(CURDIR) -name '*.pyc' -delete
	rm -f debian/files
	touch debian/files


$(DIST_TAR): $(PY_SOURCES)
	$(PYTHON) $(PYFLAGS) setup.py sdist --formats gztar

$(DIST_ZIP): $(PY_SOURCES)
	$(PYTHON) $(PYFLAGS) setup.py sdist --formats zip

$(DIST_EGG): $(PY_SOURCES)
	$(PYTHON) $(PYFLAGS) setup.py bdist_egg

$(DIST_DEB): $(PY_SOURCES) $(DEB_SOURCES)
	# build the binary package in the parent directory then rename it to
	# project_version.orig.tar.gz
	$(PYTHON) $(PYFLAGS) setup.py sdist --dist-dir=../
	rename -f 's/$(NAME)-(.*)\.tar\.gz/$(NAME)_$$1\.orig\.tar\.gz/' ../*
	debuild -b -i -I -Idist -Ibuild -Idocs/_build -Icoverage -I__pycache__ -I.coverage -Itags -I*.pyc -I*.vim -I*.xcf -aarmhf -rfakeroot
#	debuild -b -i -I -aarmhf -rfakeroot
	mkdir -p dist/
	for f in $(DIST_DEB); do cp ../$${f##*/} dist/; done

$(DIST_DSC): $(PY_SOURCES) $(DEB_SOURCES)
	# build the source package in the parent directory then rename it to
	# project_version.orig.tar.gz
	$(PYTHON) $(PYFLAGS) setup.py sdist --dist-dir=../
	rename -f 's/$(NAME)-(.*)\.tar\.gz/$(NAME)_$$1\.orig\.tar\.gz/' ../*
	debuild -S -i -I -Idist -Ibuild -Idocs/_build -Icoverage -I__pycache__ -I.coverage -Itags -I*.pyc -I*.vim -I*.xcf -aarmhf -rfakeroot
#	debuild -S -i -I -aarmhf -rfakeroot
	mkdir -p dist/
	for f in $(DIST_DSC); do cp ../$${f##*/} dist/; done

release: $(PY_SOURCES) $(DOC_SOURCES)
	$(MAKE) clean
	# make sure we are on a master branch
	test -z "$(shell git branch | grep -q '* master')"
	# create release branch
#	git branch rel/$(VER)
	# checkout release branch
#	git checkout rel/$(VER)
	# update the debian changelog with new release information
	dch --newversion $(VER) --controlmaint
	# commit the changes and add a new tag
#	git commit debian/changelog -m "Updated changelog for release $(VER)"
#	git tag -s release-$(VER) -m "Release $(VER)"

#.PHONY: builddeb
#builddeb:

#	# build the source package in the current directory
#	# then rename it to project_version.orig.tar.gz
#	sudo ./setup.py sdist --dist-dir=./ 
#	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ./*
#	# build the package
#	sudo dpkg-buildpackage -i -I -rfakeroot


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
	

pi-install.tar: 
	tar cvf $@ $(shell $(MAKE) targets)
	

# had to rename from "install" for deb package installer
pi-install: pi-install.tar
	scp $< $(PI):
	sshpass -p '$(PIPASSWORD)' ssh $(PI) "\
		rm -rf rsinstall; \
		mkdir -p rsinstall; \
		cd rsinstall; \
		tar xvf ../$<; \
		find . -name *.sbin -exec sudo chown root {} \\; ; \
		find . -name *.sbin -exec sudo chmod 4755 {} \\; ; \
		"

#include $(POST_MAK)
