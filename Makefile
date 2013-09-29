#
# Makefile
#
# Builds all tools needed on target (api, apps, ide, etc).  Optionally installs them.
#

TARGET_DIRS=
TARGET_DIRS+=api
#TARGET_DIRS+=ide
#TARGET_DIRS+=apps
#TARGET_DIRS+=etc

.PHONY: $(TARGET_DIRS)
all: $(TARGET_DIRS)

$(TARGET_DIRS):
	make -C $@

.PHONY: install
install:
	scp api.tar pi@raspberrypi:
	ssh pi@raspberrypi tar xvf api.tar

