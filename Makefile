SHELL = /bin/bash

ifdef ON_PI
  PYTHON=python3  # default python
else
  PYTHON=python3  # default python
endif
PYFLAGS=
DESTDIR=/
# install directories
PROJECTSDIR=$$HOME/rstem
CELLSDIR=$$HOME/rstem
#BUILDIR=$(CURDIR)/debian/raspberrystem
PI=pi@raspberrypi

PYDIR:=$(shell $(PYTHON) $(PYFLAGS) -c "import site; print('site.getsitepackages()[0]')")

# Calculate the base names of the distribution, the location of all source,
NAME:=$(shell $(PYTHON) $(PYFLAGS) ./pkg/setup.py --name)
VER:=$(shell $(PYTHON) $(PYFLAGS) ./pkg/setup.py --version)

PYVER:=$(shell $(PYTHON) $(PYFLAGS) -c "import sys; print('py%d.%d' % sys.version_info[:2])")

# all files to be included in rstem package (all python files plus files included in MANIFEST.in)
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
	$(wildcard debian/*.docs) \
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


COMMANDS=install test source egg zip tar deb dist install-projects install-cells \
    upload-all upload-ppa upload-cheeseshop register

.PHONY: all local-install upload-check help clean push pull doc release  \
    $(COMMANDS) $(addprefix pi-, $(COMMANDS))

help:
#	@echo "make - Compile sources locally"
	@echo "make push - Push changes on local computer onto pi"
	@echo "make pull - Pull changes on pi onto local computer (BE CAREFULL!!!)"
	@echo "make install - Install onto remote Raspberry Pi"
	@echo "make local-install - Install onto local machine"
	@echo "make install-projects - Install projects to home folder"
	@echo "make install-cells - Install cells to home folder"
	@echo "make test - Run tests"
	@echo "make doc - Generate HTML documentation (packages must be installed locally first)"
	@echo "make source - Create source package"
	@echo "make egg - Generate a PyPI egg package"
	@echo "make zip - Generate a source zip package"
	@echo "make tar - Generate a source tar package"
	@echo "make deb - Generate Debian packages (NOT COMPLETED)"
	@echo "make dist - Generate all packages"
	@echo "make clean-pi - Clean all files on the pi"
	@echo "make clean - Get rid of all files locally"
	@echo "make release - Create and tag a new release"
	@echo "make upload-all - Upload the new release to all repositories"
	@echo "make upload-ppa - Upload the new release to ppa"
	@echo "make register - Register raspberry pi to PyPi repository"
	@echo "make upload-cheeseshop - Upload the new release to cheeseshop"

setup.py:
	cp pkg/setup.py ./
	
MANIFEST.in:
	cp pkg/MANIFEST.in ./

./rstem/gpio/pullup.sbin: ./rstem/gpio/pullup.sbin.c
	# compile pullup.sbin
	gcc ./rstem/gpio/pullup.sbin.c -o ./rstem/gpio/pullup.sbin
	# set pullup.sbin as a root program
	sudo chown 0:0 ./rstem/gpio/pullup.sbin
	sudo chmod u+s ./rstem/gpio/pullup.sbin
	
debian:
	cp -r pkg/debian debian

cleanup:
	rm -f ./setup.py
	rm -f ./MANIFEST.in
	rm -rf debian
	rm -f ./rstem/gpio/pullup.sbin


# update files on raspberry pi
push:
	rsync -azP --include-from='pkg/install_include.txt' --exclude='*' ./ $(PI):~/rsinstall


# send changed files on pi back to user
pull:
	rsync -azP $(PI):~/rsinstall/* ./
	$(MAKE) cleanup


# for each command push new files to raspberry pi then run command on the pi
$(COMMANDS)::
	$(MAKE) push
	ssh $(SSHFLAGS) -t $(PI) "cd rsinstall; make pi-$@ PI=$(PI) ON_PI=1"


# on pi commands start with "pi-"

PREVDIR = $(CURDIR)

doc:
	rm -rf doc
	cd; epydoc --html rstem -o $(PREVDIR)/doc; cd $(PREVDIR)

local-install: setup.py MANIFEST.in ./rstem/gpio/pullup.sbin
	# Pretend we are on the pi and install
	sudo $(PYTHON) $(PYFLAGS) ./setup.py install
	$(MAKE) cleanup

pi-install: setup.py MANIFEST.in ./rstem/gpio/pullup.sbin
	sudo $(PYTHON) $(PYFLAGS) ./setup.py install
	$(MAKE) pi-install-projects
	$(MAKE) pi-install-cells
	$(MAKE) cleanup

pi-install-cells:
	mkdir -p $(CELLSDIR)
	cp -r ./cells $(CELLSDIR)

pi-install-projects:
	mkdir -p $(PROJECTSDIR)
	cp -r ./projects $(PROJECTSDIR)

pi-test:
	@echo "There are no test files at this time."

upload-check:
	# Check that we are  in correct branch....
	@if ! git branch | grep -q "* rel/$(VER)"; then \
		echo "Not in the expected branch rel/$(VER)."; \
		echo "Either change your branch to rel/$(VER) or update the version number in ./setup.py"; \
		exit 2; \
	else \
		echo "In correct branch."; \
	fi

pi-upload-all:
	$(MAKE) pi-upload-ppa
	$(MAKE) pi-upload-cheeseshop

pi-upload-ppa: $(DIST_DSC) setup.py MANIFEST.in
	# TODO: change this from raspberrystem-test ppa to an official one
	# (to add this repo on raspberrypi type: sudo add-apt-repository ppa:r-jon-s/ppa)
	$(MAKE) upload-check
	dput ppa:r-jon-s/ppa dist/$(NAME)_$(VER)_source.changes
	$(MAKE) cleanup

pi-upload-cheeseshop: $(PY_SOURCES) setup.py MANIFEST.in
	# update the package's registration on PyPI (in case any metadata's changed)
	# f$(MAKE) upload-check
	$(PYTHON) $(PYFLAGS) setup.py sdist upload
	$(MAKE) cleanup

pi-register: setup.py MANIFEST.in
	$(PYTHON) $(PYFLAGS) setup.py register

release: $(PY_SOURCES) $(DOC_SOURCES)
	$(MAKE) upload-check
	# update the debian changelog with new release information
	dch --newversion $(VER) --controlmaint
	# commit the changes and add a new tag
	git commit debian/changelog -m "Updated changelog for release $(VER)"
	git tag -s release-$(VER) -m "Release $(VER)"

pi-source: $(DIST_TAR) $(DIST_ZIP)

pi-egg: $(DIST_EGG)

pi-zip: $(DIST_ZIP)

pi-tar: $(DIST_TAR)

#pi-deb: $(DIST_DSC) $(DIST_DEB) // uncomment when debian is finished
pi-deb: setup.py MANIFEST.in
	@echo "make deb is currently BETA!!!"
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

pi-dist: $(DIST_EGG) $(DIST_DEB) $(DIST_DSC) $(DIST_TAR) $(DIST_ZIP)

# clean all files from raspberry pi
clean-pi:
	ssh $(SSHFLAGS) -t $(PI) "sudo rm -rf ~/rsinstall; sudo rm -rf ~/rstem"

# clean all files locally
clean: setup.py MANIFEST.in
	sudo $(PYTHON) $(PYFLAGS) setup.py clean
	$(MAKE) -f $(CURDIR)/pkg/debian/rules clean
	sudo rm -rf build dist/
	sudo rm -rf $(NAME).egg-info
	rm -f $(NAME).egg-info
	rm -rf $(NAME)-$(VER).tar.gz
	rm -rf pkg/debian/python3-$(NAME) pkg/debian/python-$(NAME)
	rm -f pkg/debian/python*
	rm -f ../$(NAME)_$(VER).orig.tar.gz ../$(NAME)_$(VER)_armhf.build ../$(NAME)_$(VER)_armhf.changes ../$(NAME)_$(VER)_source.build
	rm -f ../python-$(NAME)_$(VER)_armhf.deb ../python3-$(NAME)_$(VER)_armhf.deb
	rm -f ../$(NAME)_$(VER).dsc ../$(NAME)_$(VER).tar.gz ../$(NAME)_$(VER)_source.changes
	find $(CURDIR) -name '*.pyc' -delete
	rm -f pkg/debian/files
	touch pkg/debian/files
	rm -rf doc
	rm -rf deb_dist
	sudo rm -f ./rstem/gpio/pullup.sbin
	$(MAKE) cleanup

$(DIST_TAR): $(PY_SOURCES) setup.py MANIFEST.in
	$(PYTHON) $(PYFLAGS) setup.py sdist --formats gztar

$(DIST_ZIP): $(PY_SOURCES) setup.py MANIFEST.in
	$(PYTHON) $(PYFLAGS) setup.py sdist --formats zip

$(DIST_EGG): $(PY_SOURCES) setup.py MANIFEST.in
	$(PYTHON) $(PYFLAGS) setup.py bdist_egg

$(DIST_DEB): $(PY_SOURCES) $(DEB_SOURCES) setup.py MANIFEST.in debian
	# build the binary package in the parent directory then rename it to
	# project_version.orig.tar.gz
	$(PYTHON) $(PYFLAGS) setup.py sdist --dist-dir=../
	rename -f 's/$(NAME)-(.*)\.tar\.gz/$(NAME)_$$1\.orig\.tar\.gz/' ../*
	debuild -b -i -I -Idist -Ibuild -Idocs/_build -Icoverage -I__pycache__ -I.coverage -Itags -I*.pyc -I*.vim -I*.xcf -aarmhf -rfakeroot
	mkdir -p dist/
	for f in $(DIST_DEB); do cp ../$${f##*/} dist/; done

$(DIST_DSC): $(PY_SOURCES) $(DEB_SOURCES) setup.py MANIFEST.in debian
	# build the source package in the parent directory then rename it to
	# project_version.orig.tar.gz
	cp -r  pkg/debian debian
	$(PYTHON) $(PYFLAGS) setup.py sdist --dist-dir=../
	rename -f 's/$(NAME)-(.*)\.tar\.gz/$(NAME)_$$1\.orig\.tar\.gz/' ../*
	debuild -S -i -I -Idist -Ibuild -Idocs/_build -Icoverage -I__pycache__ -I.coverage -Itags -I*.pyc -I*.vim -I*.xcf -aarmhf -rfakeroot
	mkdir -p dist/
	for f in $(DIST_DSC); do cp ../$${f##*/} dist/; done

