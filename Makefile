#
# Makefile
#
# Builds all tools needed on target (api, apps, ide, etc).  Optionally installs them.
#

PI=pi@raspberrypi

TARGET_DIRS=
TARGET_DIRS+=api
TARGET_DIRS+=apps
#TARGET_DIRS+=ide
#TARGET_DIRS+=etc

TARGET_TARBALLS=$(foreach t,$(TARGET_DIRS),$(t)/$(t).tar)

SETUID_FILES=api/pullup

.PHONY: $(TARGET_DIRS)
all: $(TARGET_DIRS)

$(TARGET_DIRS):
	make -C $@

clean:
	for t in $(TARGET_DIRS); do make -C $$t clean; done

.PHONY: install
install: $(TARGET_TARBALLS)
	for i in $^; do \
		scp $$i $(PI): ;\
		ssh $(PI) tar xvf `basename $$i` ;\
	done
	for i in $(SETUID_FILES); do \
		ssh $(PI) sudo chown root $$i; \
		ssh $(PI) sudo chmod 4755 $$i; \
	done
