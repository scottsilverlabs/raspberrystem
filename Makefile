PYTHON=python3
SETUP=$(PYTHON) setup.py
PIP=pip-3.2

# install directories
PROJECTSDIR=$$HOME/rstem
CELLSDIR=$$HOME/rstem

SSHFLAGS=
PI=pi@raspberrypi
RUNONPI=ssh $(SSHFLAGS) -q -t $(PI) "mkdir -p rsinstall; cd rsinstall;"

OUT=$(abspath out)

# Create version name
DUMMY:=$(shell scripts/version.sh)

# Name must be generated the same way as setup.py
RSTEM_NAME:=$(shell cat NAME)
RSTEM_VER:=$(shell cat VERSION)

# Final targets
RSTEM_TAR:=$(OUT)/$(RSTEM_NAME)-$(RSTEM_VER).tar.gz
PYDOC_TAR:=$(OUT)/$(RSTEM_NAME)_pydocs-$(RSTEM_VER).tar.gz

# Target paths
PYDOC_NAME=pydoc

# Dependency files
GIT_FILES=$(shell git ls-files)

all: rstem ide projects pydoc

$(OUT):
	mkdir -p $(OUT)

# ##################################################
# rstem commands
#

rstem-util:
	$(MAKE) -C util

rstem: $(RSTEM_TAR)
$(RSTEM_TAR): $(GIT_FILES) rstem-pydoc rstem-util | $(OUT)
	@# If there's any files that are untracked in git but that would end up being in
	@# the MANIFEST (via graft of a whole directory) then interactively clean them.
	@# EXCEPT: util/bin includes specific externally built binaries.
	git clean -i $(shell awk '/^graft/{print $$2}' MANIFEST.in | grep -v util/bin)
	$(SETUP) sdist
	mv dist/$(notdir $@) $@

rstem-pydoc: $(PYDOC_TAR)
	rm -rf rstem/$(PYDOC_NAME)
	tar xf $(PYDOC_TAR) -C rstem

rstem-dev: push
	$(RUNONPI) sudo $(SETUP) develop

rstem-undev: push
	$(RUNONPI) sudo $(SETUP) develop --uninstall

rstem-upload:
	$(SETUP) sdist upload

rstem-register:
	$(SETUP) register

rstem-install: rstem-undev
	@if [ ! -e $(RSTEM_TAR) ]; then \
		echo "Rstem package not built.  Did you run 'make' first?"; \
		exit 1; \
	fi
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
$(PYDOC_TAR): $(GIT_FILES) | $(OUT)
	@# A bit circuitous: pydoc is a requirement of rstem (the API docs get
	@# bundled into the package).  However, because pdoc runs on the target only,
	@# we need to have an installed version of rstem on the target.  This a
	@# catch-22.  So, we push a development version of the source to the target
	@# (which doesn't require the API docs in the build via rstem-dev, and we
	@# undev it at the end.
	$(MAKE) rstem-dev
	$(RUNONPI) pdoc --overwrite --html --html-dir $(PYDOC_NAME) rstem
	$(RUNONPI) tar czf $(PYDOC_NAME).tar.gz $(PYDOC_NAME)
	scp $(PI):~/rsinstall/$(PYDOC_NAME).tar.gz $@
	$(MAKE) rstem-undev

pydoc-clean:
	$(RUNONPI) rm -rf $(PYDOC_NAME).tar.gz $(PYDOC_NAME)
	rm -f $(PYDOC_TAR)

pydoc-upload:
	#TBD
	exit 1
	rm -rf build/docs
	mkdir -p build/docs
	cd build/docs && tar xvf $(PYDOC_TAR)
	$(SETUP) upload_docs --upload-dir=build/docs/api/rstem

# ##################################################
# Host commands
#
# Targets that can run on the host without needing the target Pi.
#
host-clean:
	rm NAME VERSION
	rm -rf *.egg-info
	rm -rf $(OUT)

# ##################################################
# External Repo commands
#
# External repo makefiles can support any target rules they want, but must
# include at least these targets:
#	all - builds primary targets
#	targets - echoes the list of targets built by 'make all'
# If the external repo does not exist, it will be ignored with a warning.
#
# If we need to add any more external repos, this should probably switched to
# an define/call/eval - but being that those are so painfully ugly, I'm
# avoiding that for now.

#
# Projects repo
#
DOC_REPO=../raspberrystem-projects

ifeq ($(wildcard $(DOC_REPO)),)
projects projects-%:
	@echo "Warning: Skipping build of $@.  Git repo not found."
else
DOC_TARGETS=$(shell $(MAKE) -C $(DOC_REPO) targets)
.PHONY: projects
projects: projects-all | $(OUT)
	cp $(DOC_TARGETS) $(OUT)

projects-%:
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
IDE_TARGETS=$(shell $(MAKE) -C $(IDE_REPO) targets)
.PHONY: ide
ide: ide-all | $(OUT)
	cp $(IDE_TARGETS) $(OUT)

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
	@echo "    - Base NOOBS install"
	@echo "        - Format SD"
	@echo "            - See also: https://github.com/raspberrypi/noobs"
	@echo "            - For Mac: Use SDFormmatter."
	@echo "        - NOOBS install (tested with v1.3.11):"
	@echo "            - Extract zip file, copy all to SD card"
	@echo "           - Boot target with SD card"
	@echo "            - Install Raspbian (i) - takes a while"
	@echo "    - Wifi setup"
	@echo "         - Use startx, Wifi Config (from menu)"
	@echo "         - Or use wpa_supplicant commands to edit conf file (untested)."
	@echo "             sudo sh -c 'wpa_passphrase SSID PASS >> /etc/wpa_supplicant/wpa_supplicant.conf'"
	@echo "                 where SSID/PASS are the actual SSID and password of the Wifi network."
	@echo "             sudo reboot"
	@echo "             Use ifconfig to show IP."
	@echo "    - Note: first few ssh commands will request password"
	@echo "    - Note: if first ssh fails, its likely because of a strict key checking "
	@echo "        issue.  Run 'ssh-keygen -R <IP>' to remove the offending key."
	@read -p "Ready?  Enter to continue, Ctrl-C to cancel> "
	$(RUNONPI) "mkdir -p ~/.ssh"
	scp ~/.ssh/id_rsa.pub  $(PI):.ssh/authorized_keys
	$(RUNONPI) sudo sed -i '/XKBLAYOUT/s/\".*\"/\"us\"/' /etc/default/keyboard
	$(RUNONPI) sudo apt-get update -y
	$(RUNONPI) sudo apt-get install -y python3-pip
	$(RUNONPI) sudo apt-get install -y libi2c-dev
	$(RUNONPI) sudo apt-get install -y sox
	$(RUNONPI) sudo apt-get install -y libsox-fmt-mp3
	$(RUNONPI) sudo apt-get install -y espeak
	$(RUNONPI) sudo $(PIP) install pdoc

CLEAN_TARGETS=rstem pydoc ide projects host test
INSTALL_TARGETS=rstem ide projects
UPLOAD_TARGETS=rstem ide projects

clean: $(addsuffix -clean,$(CLEAN_TARGETS))
	$(RUNONPI) "cd ~; sudo rm -rf ~/rsinstall"

install: $(addsuffix -install,$(INSTALL_TARGETS))

upload: $(addsuffix -upload,$(UPLOAD_TARGETS))

run: ide-run

dev: rstem-dev

test:
	@echo "What do you want to test?"
	@for FULLFILE in rstem/tests/test_*.py; do \
		BASENAME=`basename "$$FULLFILE"`; \
		WITHOUT_EXTENSION="$${BASENAME%.*}"; \
		TESTNAME="$${WITHOUT_EXTENSION##test_}"; \
		echo "    make test-$$TESTNAME"; \
	done
	@echo "Or, replace 'test-' with:"
	@echo "    'auto-' to run only automatic tests"
	@echo "    'manu-' to run only manual tests"
	@echo "    'help-' to get help on a specific test"

test-% auto-% manu-% help-%: push
	$(RUNONPI) "cd rstem/tests; $(PYTHON) -m testing $@ $*"

test-clean:
	$(RUNONPI) rm -rf "~/rstem_logs"


# ##################################################
# help
#

help:
	@echo "Usage: make <make-target>, where <make-target> is one of:"
	@echo "rstem commands (use to make/install pip packages):"
	@echo "    rstem               setup.py sdist - Create a pip installable source distribution"
	@echo "    rstem-dev         * setup.py develop - Build/install on target for (fast) dev"
	@echo "    rstem-undev       * setup.py develop --uninstall - Reverse of make rstem-dev"
	@echo "    rstem-pydoc         Extract the pydocs into the rstem package"
	@echo "    rstem-register      setup.py register - One-time user register/login on PyPI"
	@echo "    rstem-upload        setup.py upload - Upload source distribution to PyPI"
	@echo "    rstem-install     * pip install <tar.gz> - Install from source distribution"
	@echo "    rstem-clean       * Remove all host and target rstem files"
	@echo ""
	@echo "Doc commands (docs are in a separate git repo.  Skip if not found):"
	@echo "    projects            Create HTML projects"
	@echo "    projects-register   setup.py register - One-time user register/login on PyPI"
	@echo "    projects-upload     setup.py upload - Upload source distribution to PyPI"
	@echo "    projects-install  * Install projects (from Instructor Manual)"
	@echo "    projects-clean    * Uninstall projects"
	@echo ""
	@echo "IDE commands (IDE is in a separate git repo.  Skip if not found):"
	@echo "    ide                 Build IDE."
	@echo "    ide-register        setup.py register - One-time user register/login on PyPI"
	@echo "    ide-upload          setup.py upload - Upload source distribution to PyPI"
	@echo "    ide-install       * Install IDE."
	@echo "    ide-run           * Start IDE server."
	@echo "    ide-clean         * Clean IDE."
	@echo ""
	@echo "Top-level commands:"
	@echo "    [all]               make rstem, projects, ide"
	@echo "    pi-setup          * One-time setup required on clean Raspbian install."
	@echo "    test              * Run tests (TBD)"
	@echo "    push              * Push changes on local computer onto pi"
	@echo "    pull              * Pull changes on pi back to local onto pi (BE CARFEULL!!)"
	@echo "    upload              make *-upload, and upload final binaries to <TBD>"
	@echo "    install           * make *-install"
	@echo "    clean             * make *-clean"
	@echo "    run               * make ide-run"
	@echo "    dev               * make rstem-dev"
	@echo ""
	@echo " * Requires access to target Raspberry Pi"
	@echo ""
	@echo "Use cases:"
	@echo "    For rstem development"
	@echo "        <first time>:"
	@echo "            make && make install # Required for post-install steps"
	@echo "            sudo reboot"
	@echo "        <repeat>:"
	@echo "            make rstem-dev (only required once at start unless editing C files)"
	@echo "            <edit files>"
	@echo "            make test-<test_suite>"
	@echo "        make rstem-undev"
	@echo "    Make, install and run IDE remotely:"
	@echo "        make ide"
	@echo "        make ide-install"
	@echo "        make ide-run"
	@echo "        <On host, open browser and point to raspberrypi>"
	@echo "    X development (where X is in [ide, projects, rstem]:"
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
	@echo "            pip install raspberrystem-projects"
	@echo ""
	@echo "Final targets (copied to 'out' dir):"
	@echo "    RSTEM API (w/ api_docs) (sdist): $(notdir $(RSTEM_TAR))"
	@echo "    IDE (sdist):                     $(notdir $(IDE_TARGETS))"
	@echo "    Projects (sdist):                $(notdir $(DOC_TARGETS))"
	@echo "    Docs (PDF):                      TBD"
	@echo "Note: sdist is a pip installable tarball creates via setuptools."
