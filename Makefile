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

.PHONY: $(TARGET_DIRS)
all: $(TARGET_DIRS)

$(TARGET_DIRS):
	make -C $@

.PHONY: install
install: $(TARGET_DIRS:=.tar)
	for i in $^; do \
		scp $$i $(PI): ;\
		ssh $(PI) tar xvf $$i ;\
	done

