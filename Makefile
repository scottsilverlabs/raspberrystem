PYTHON=python3
SETUP=$(PYTHON) setup.py
PIP=pip-3.2

# install directories
PROJECTSDIR=$$HOME/rstem
CELLSDIR=$$HOME/rstem

PI=pi@raspberrypi
RUNONPI=ssh $(SSHFLAGS) -q -t $(PI) "cd rsinstall;"

OUT=out

# Create version name
DUMMY=$(shell pkg/version.sh)

# Name must be generated the same way as setup.py
RSTEM_NAME:=$(shell cat pkg/NAME)
RSTEM_VER:=$(shell cat pkg/VERSION)
RSTEM_TAR:=$(OUT)/$(RSTEM_NAME)-$(RSTEM_VER).tar.gz

GIT_FILES=$(shell git ls-files)

all: rstem

help:
	@echo "Usage: make <make-target>, where <make-target> is one of:"
	@echo "rstem commands (use to make/install pip packages):"
	@echo "    rstem             setup.py sdist - Create a pip installable source distribution"
	@echo "    rstem-dev       * setup.py develop - Build/install on target for (fast) development"
	@echo "    rstem-undev     * setup.py develop --uninstall - Reverse of make rstem-dev"
	@echo "    rstem-upload      setup.py upload - Upload source distribution to Cheeseshop"
	@echo "    rstem-register    setup.py register - Register user on Cheeseshop"
	@echo "    rstem-doc         HTML API docs, for upload"
	@echo "    rstem-doc-upload  Upload built API doc to <TBD>"
	@echo "    rstem-install   * pip install <tar.gz> - Install from source distribution"
	@echo "    rstem-clean     * Remove all host and target rstem files"
	@echo ""
	@echo "Proj commands (projects are programs that use the rstem API):"
	@echo "    proj              Create projects/cells tarball"
	@echo "    proj-install    * Copy projects/cells to user directory on target"
	@echo "    proj-clean      * Remove all target project/cells directories"
	@echo ""
	@echo "Doc commands (docs are in a separate git repo.  Skips if not found):"
	@echo "    doc               Create PDF docs and HTML lesson plans"
	@echo "    doc-install     * Install lesson plans (from Instructor Manual)"
	@echo "    doc-clean       * Uninstall lesson plans"
	@echo ""
	@echo "IDE commands (IDE is in a separate git repo.  Skips if not found):"
	@echo "    ide               Build IDE."
	@echo "    ide-install     * Install IDE."
	@echo "    ide-clean       * Clean IDE."
	@echo ""
	@echo "Top-level commands:"
	@echo "    [all]             make rstem, proj, doc, ide"
	@echo "    test            * Run tests (TBD)"
	@echo "    push            * Push changes on local computer onto pi"
	@echo "    upload            make *-upload, and upload final binaries"
	@echo "    install         * make *-install"
	@echo "    clean           * make *-clean"
	@echo ""
	@echo " * Requires access to target Raspberry Pi"
	@echo ""
	@echo "Use cases:"
	@echo "    For rstem development"
	@echo "        <edit files>"
	@echo "        Either (fast way):  make rstem-dev"
	@echo "        Or (normal way)  :  make rstem && make install"
	@echo "        <test & repeat>"
	@echo "    X development (where X is in [proj, ide, doc, rstem]:"
	@echo "        <edit files>"
	@echo "        make X && make X-install"
	@echo "        <test & repeat>"
	@echo "    Make and install everything"
	@echo "        make clean #optional"
	@echo "        make && make install"
	@echo "    Release:"
	@echo "        git commit ...   # in each repo to be released"
	@echo "        git tag M.N.P    # in each repo to be released"
	@echo "        make"
	@echo "        make upload"
	@echo ""
	@echo "Final targets:"
	@echo "    RSTEM API (w/ api_docs) (sdist): rstem_vM.N.P.rcX.tar.gz"
	@echo "    Uploadable API doc HTML tarball: rstem_api_docs_vM.N.P.rcX.tar.gz"
	@echo "    Projects/cells programs tarball: rstem_projs_vM.N.P.rcX.tar.gz"
	@echo "    IDE (sdist):                     rstem_ide_vM.N.P.rcX.tar.gz"
	@echo "    Lesson Plans (sdist):            rstem_lessons_vM.N.P.rcX.tar.gz"
	@echo "    Docs (PDF):                      *_vM.N.P.rcX.pdf"
	@echo "Note: sdist is a pip installable tarball creates via setuptools."



./rstem/gpio/pullup.sbin: ./rstem/gpio/pullup.sbin.c
	# compile pullup.sbin
	gcc ./rstem/gpio/pullup.sbin.c -o ./rstem/gpio/pullup.sbin
	# set pullup.sbin as a root program
	sudo chown 0:0 ./rstem/gpio/pullup.sbin
	sudo chmod u+s ./rstem/gpio/pullup.sbin
	
push:
	rsync -azP --delete --exclude-from=.gitignore --exclude=.git ./ $(PI):~/rsinstall

rstem: $(RSTEM_TAR)
$(RSTEM_TAR): $(GIT_FILES)
	$(SETUP) sdist
	mkdir -p $(OUT)
	mv dist/$(notdir $@) $@

rstem-dev: $(GIT_FILES)
	$(MAKE) push
	$(RUNONPI) sudo $(SETUP) develop

rstem-undev: $(GIT_FILES)
	$(RUNONPI) sudo $(SETUP) develop --uninstall

rstem-upload:
	$(SETUP) sdist upload

rstem-register:
	$(SETUP) register

rstem-install:
	scp $(RSTEM_TAR) $(PI):/tmp
	$(RUNONPI) sudo $(PIP) install --upgrade --force-reinstall /tmp/$(notdir $(RSTEM_TAR))

rstem-doc:
	# TBD
	epydoc --html rstem -o doc
	rm -f doc.zip
	cd doc; zip ../doc.zip *; cd ../

proj:
proj-install:
	mkdir -p $(PROJECTSDIR)
	cp -r ./projects $(PROJECTSDIR)
	mkdir -p $(CELLSDIR)
	cp -r ./cells $(CELLSDIR)

