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

# Final targets
RSTEM_TAR:=$(OUT)/$(RSTEM_NAME)-$(RSTEM_VER).tar.gz
RSTEM_PROJ:=$(OUT)/$(RSTEM_NAME)_projs-$(RSTEM_VER).tar.gz
PYDOC_TAR:=$(OUT)/$(RSTEM_NAME)_api_docs-$(RSTEM_VER).tar.gz

# Dependency files
RSTEM_GIT_FILES=$(shell git ls-files | grep -v ^projects/)
PROJ_GIT_FILES=$(shell git ls-files | grep ^projects/)

all: rstem

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
	@echo "Proj commands (projects are programs that use the rstem API):"
	@echo "    proj              Create projects/cells tarball"
	@echo "    proj-install    * Copy projects/cells to user directory on target"
	@echo "    proj-clean      * Remove all target project/cells directories"
	@echo ""
	@echo "Doc commands (docs are in a separate git repo.  Skip if not found):"
	@echo "    doc               Create PDF docs and HTML lesson plans"
	@echo "    doc-install     * Install lesson plans (from Instructor Manual)"
	@echo "    doc-clean       * Uninstall lesson plans"
	@echo ""
	@echo "IDE commands (IDE is in a separate git repo.  Skip if not found):"
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
	@echo "        Or (normal way)  :  make rstem && make rstem-install"
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
	@echo "    RSTEM API (w/ api_docs) (sdist): $(RSTEM_TAR)"
	@echo "    Projects/cells programs tarball: $(RSTEM_PROJ)"
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

# ##################################################
# rstem commands
#

rstem: $(RSTEM_TAR)
$(RSTEM_TAR): $(RSTEM_GIT_FILES)
	$(SETUP) sdist
	mkdir -p $(OUT)
	mv dist/$(notdir $@) $@

rstem-dev: $(RSTEM_GIT_FILES)
	$(MAKE) push
	$(RUNONPI) sudo $(SETUP) develop

rstem-undev: $(RSTEM_GIT_FILES)
	$(RUNONPI) sudo $(SETUP) develop --uninstall

rstem-upload:
	$(SETUP) sdist upload

rstem-register:
	$(SETUP) register

rstem-install:
	scp $(RSTEM_TAR) $(PI):/tmp
	$(RUNONPI) sudo $(PIP) install --upgrade --force-reinstall /tmp/$(notdir $(RSTEM_TAR))

rstem-clean:
	rm -rf dist build
	rm -f $(RSTEM_TAR)

# ##################################################
# Pydoc commands
#

pydoc: $(PYDOC_TAR)
$(PYDOC_TAR): $(RSTEM_GIT_FILES)
	$(MAKE) push
	$(RUNONPI) epydoc --html rstem -o doc
	$(RUNONPI) tar cvzf doc.tar.gz doc
	scp $(PI):~/rsinstall/doc.tar.gz $@

pydoc-clean:
	$(RUNONPI) rm -rf doc.tar.gz doc
	rm -f $(PYDOC_TAR)

# ##################################################
# Proj commands
#

proj: $(PROJ_TAR)
$(PROJ_TAR): $(PROJ_GIT_FILES)
	git archive --format tar.gz -o $@ HEAD projects

proj-install:
	scp $(PROJ_TAR) $(PI):/tmp
	$(RUNONPI) /tmp/$(notdir $(PROJ_TAR))

proj-clean:
	rm -f $(PROJ_TAR)

# ##################################################
# External Repo commands
#
# External repo makefiles can support any target rules they want, but must
# include at least these targets:
#	all - builds primary targets
#	targets - echoes the list of targets built by 'make all'
# If the external repo does not exist, it will be ignored with a warning.
#

doc_REPO=../raspberrystem-doc
ide_REPO=../raspberrystem-ide

.PHONY: ide doc
ide: ide-all
doc: doc-all
ide-% doc-%:
	@# Ugly eval to compute the value in the variable "$(reponame_REPO)"
	$(eval REPO=$($(subst -$*,,$@)_REPO))
	@if [ ! -d $(REPO) ]; then \
		echo "Warning: Skipping build of '$@'.  Git repo $(REPO) not found"; \
	else \
		echo "MAKE $@ (from external repo)"; \
		$(MAKE) -C $(REPO) $*; \
		$(eval TARGETS=$(shell $(MAKE) -C $(REPO) targets)) \
		cp $(addprefix $(REPO)/,$(TARGETS)) $(OUT); \
	fi


# ##################################################
# Top-level commands
#

push:
	rsync -azP --delete --exclude-from=.gitignore --exclude=.git ./ $(PI):~/rsinstall
