PYTHON=python3
SETUP=$(PYTHON) setup.py
PIP=pip-3.2

# install directories
PROJECTSDIR=$$HOME/rstem
CELLSDIR=$$HOME/rstem

PI=pi@raspberrypi
RUNONPI=ssh $(SSHFLAGS) -q -t $(PI) "mkdir -p rsinstall; cd rsinstall;"

OUT=out

# Create version name
DUMMY:=$(shell scripts/version.sh)

# Name must be generated the same way as setup.py
RSTEM_NAME:=$(shell cat NAME)
RSTEM_VER:=$(shell cat VERSION)

# Final targets
RSTEM_TAR:=$(OUT)/$(RSTEM_NAME)-$(RSTEM_VER).tar.gz
PYDOC_TAR:=$(OUT)/$(RSTEM_NAME)_api_docs-$(RSTEM_VER).tar.gz

# Dependency files
GIT_FILES=$(shell git ls-files)

#all: rstem ide doc pydoc
all: rstem ide pydoc

help:
	@echo "Usage: make <make-target>, where <make-target> is one of:"
	@echo "rstem commands (use to make/install pip packages):"
	@echo "    rstem             setup.py sdist - Create a pip installable source distribution"
	@echo "    rstem-dev       * setup.py develop - Build/install on target for (fast) development"
	@echo "    rstem-undev     * setup.py develop --uninstall - Reverse of make rstem-dev"
	@echo "    rstem-register    setup.py register - One-time user register/login on Cheeseshop"
	@echo "    rstem-upload      setup.py upload - Upload source distribution to Cheeseshop"
	@echo "    rstem-install   * pip install <tar.gz> - Install from source distribution"
	@echo "    rstem-clean     * Remove all host and target rstem files"
	@echo ""
	@echo "Pydoc commands (HTML API documentation generated from source):"
	@echo "    pydoc           * HTML API docs, for upload"
	@echo "    pydoc-upload      Upload built API doc to <TBD>"
	@echo "    pydoc-install   * pip install <tar.gz> - Install from source distribution"
	@echo "    pydoc-clean     * Remove all host and target rstem files"
	@echo ""
	@echo "Doc commands (docs are in a separate git repo.  Skip if not found):"
	@echo "    doc               Create PDF docs and HTML lesson plans"
	@echo "    doc-install     * Install lesson plans (from Instructor Manual)"
	@echo "    doc-clean       * Uninstall lesson plans"
	@echo ""
	@echo "IDE commands (IDE is in a separate git repo.  Skip if not found):"
	@echo "    ide               Build IDE."
	@echo "    ide-upload      * Upload IDE."
	@echo "    ide-install     * Install IDE."
	@echo "    ide-clean       * Clean IDE."
	@echo ""
	@echo "Top-level commands:"
	@echo "    [all]             make rstem, doc, ide"
	@echo "    pi-setup        * One-time setup required on clean Raspbian install."
	@echo "    test            * Run tests (TBD)"
	@echo "    push            * Push changes on local computer onto pi"
	@echo "    pull            * Pull changes on pi back to local onto pi (BE CARFEULL!!)"
	@echo "    upload            make *-upload, and upload final binaries to <TBD>"
	@echo "    install         * make *-install"
	@echo "    clean           * make *-clean"
	@echo ""
	@echo " * Requires access to target Raspberry Pi"
	@echo ""
	@echo "Use cases:"
	@echo "    For rstem development"
	@echo "        Either (fast way):"
	@echo "            make rstem-dev"
	@echo "            <edit files>"
	@echo "            make push"
	@echo "            <test & repeat>"
	@echo "            make rstem-undev"
	@echo "        Or (normal way):"
	@echo "            <edit files>"
	@echo "            make rstem && make rstem-install"
	@echo "            <test & repeat>"
	@echo "    X development (where X is in [ide, doc, rstem]:"
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
	@echo "    Install from PyPI"
	@echo "        From target, to install ide:"
	@echo "            pip install raspberrystem"
	@echo "            pip install raspberrystem-ide"
	@echo ""
	@echo "Final targets:"
	@echo "    RSTEM API (w/ api_docs) (sdist): $(RSTEM_TAR)"
	@echo "    Uploadable API doc HTML tarball: $(PYDOC_TAR)"
	@echo "    IDE (sdist):                     rstem_ide_VERSION.tar.gz"
	@echo "    Lesson Plans (sdist):            rstem_lessons_VERSION.tar.gz"
	@echo "    Docs (PDF):                      *_VERSION.pdf"
	@echo "Note: sdist is a pip installable tarball creates via setuptools."

./rstem/gpio/pullup.sbin: ./rstem/gpio/pullup.sbin.c
	# compile pullup.sbin
	gcc ./rstem/gpio/pullup.sbin.c -o ./rstem/gpio/pullup.sbin
	# set pullup.sbin as a root program
	sudo chown 0:0 ./rstem/gpio/pullup.sbin
	sudo chmod u+s ./rstem/gpio/pullup.sbin

$(OUT):
	mkdir -p $(OUT)

# ##################################################
# rstem commands
#

rstem: $(RSTEM_TAR)
$(RSTEM_TAR): $(GIT_FILES) $(OUT)
	@# If there's any files that are not in git but that would end up being in
	@# the MANIFEST (via graft of a whole directory) then inteactively clean them.
	git clean -i $(shell awk '/^graft/{print $2}' MANIFEST.in)
	$(SETUP) sdist
	mv dist/$(notdir $@) $@

rstem-dev: push
	$(RUNONPI) sudo $(SETUP) develop

rstem-undev: push
	$(RUNONPI) sudo $(SETUP) develop --uninstall

rstem-upload:
	$(SETUP) sdist upload

rstem-register:
	$(SETUP) register

rstem-install: rstem-undev
	scp $(RSTEM_TAR) $(PI):/tmp
	-$(RUNONPI) sudo $(PIP) uninstall -y $(RSTEM_NAME)
	$(RUNONPI) sudo $(PIP) install /tmp/$(notdir $(RSTEM_TAR))

rstem-clean:
	rm -rf dist build
	rm -f $(RSTEM_TAR)

# ##################################################
# Pydoc commands
#

pydoc: $(PYDOC_TAR)
$(PYDOC_TAR): $(GIT_FILES)
	$(MAKE) push
	$(RUNONPI) pdoc --html --html-dir doc rstem
	$(RUNONPI) tar cvzf doc.tar.gz doc
	scp $(PI):~/rsinstall/doc.tar.gz $@

pydoc-clean:
	$(RUNONPI) rm -rf doc.tar.gz doc
	rm -f $(PYDOC_TAR)

# ##################################################
# External Repo commands
#
# External repo makefiles can support any target rules they want, but must
# include at least these targets:
#	all - builds primary targets
#	targets - echoes the list of targets built by 'make all'
# If the external repo does not exist, it will be ignored with a warning.
#

#
# doc repo
#
DOC_REPO=../raspberrystem-doc

ifeq ($(wildcard $(DOC_REPO)),)
doc doc-%:
	@echo "Warning: Skipping build of $@.  Git repo not found."
else
TARGETS=$(addprefix $(DOC_REPO)/,$(shell $(MAKE) -C $(DOC_REPO) targets))
.PHONY: doc
doc: doc-all $(OUT)
	cp $(TARGETS) $(OUT)

doc-%:
	$(MAKE) -C $(DOC_REPO) $*
endif

#
# IDE repo
#
IDE_REPO=../raspberrystem-ide

ifeq ($(wildcard $(IDE_REPO)),)
ide ide-%:
	@echo "Warning: Skipping build of $@.  Git repo not found."
else
TARGETS=$(addprefix $(IDE_REPO)/,$(shell $(MAKE) -C $(IDE_REPO) targets))
.PHONY: ide
ide: ide-all $(OUT)
	cp $(TARGETS) $(OUT)

ide-%:
	$(MAKE) -C $(IDE_REPO) $*
endif

# ##################################################
# Top-level commands
#

push:
	rsync -azP --delete --include=NAME --include=VERSION --exclude-from=.gitignore --exclude=.git ./ $(PI):~/rsinstall

pull:
	rsync -azP "$(PI):~/rsinstall/*" ./

pi-setup:
	@echo "Required for this setup sequence to work:"
	@echo "		- Base NOOBS install"
	@echo "		- Wifi or ethernet setup (/etc/network/interface)"
	@echo "		- ssh setup for user 'pi'"
	$(RUNONPI) sudo sed -i '/XKBLAYOUT/s/\".*\"/\"us\"/' /etc/default/keyboard
	$(RUNONPI) sudo apt-get update -y
	$(RUNONPI) sudo apt-get install -y python3-pip
	# Should this be a dependency?
	$(RUNONPI) sudo apt-get install -y libi2c-dev
	# pytest no longer required?
	$(RUNONPI) sudo $(PIP) install pytest
	$(RUNONPI) sudo $(PIP) install pdoc

ALL_GROUPS=rstem pydoc ide doc
UPLOAD_GROUPS=rstem pydoc ide

clean: $(addsuffix -clean,$(ALL_GROUPS))
	rm NAME VERSION
	rm -rf *.egg-info
	$(RUNONPI) "cd ~; sudo rm -rf ~/rsinstall"

install: $(addsuffix -install,$(ALL_GROUPS))

upload: $(addsuffix -upload,$(UPLOAD_GROUPS))

TEST_FILES=$(wildcard rstem/tests/test_*.py)
test: $(foreach test,$(TEST_FILES),test-$(subst test_,,$(basename $(notdir $(test)))))

test-%: push
	$(RUNONPI) "cd rstem/tests; $(PYTHON) -m testing $*"
