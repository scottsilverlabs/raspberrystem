#
# API Makefile
#

DIR=$(notdir $(CURDIR))
TAR=$(DIR).tar
BINARIES=led_server accel_server pullup
PI=pi@raspberrypi
PY_FILES=$(wildcard *.py)

all: $(TAR)

$(TAR): $(PY_FILES) $(BINARIES)
	tar cvf $@  -C .. $(addprefix $(DIR)/,$^)

clean:
	rm -f $(TAR)

led_server: led_server.c
	$(eval REMOTE_TMP=$(shell ssh $(PI) "mktemp -d"))
	scp $^ $(PI):$(REMOTE_TMP)
	ssh $(PI) "cd $(REMOTE_TMP) && gcc -lpthread $^ -o $@"
	scp $(PI):$(REMOTE_TMP)/$@ $@
	ssh $(PI) "rm -r $(REMOTE_TMP)"
	
accel_server: accel_server.c
	$(eval REMOTE_TMP=$(shell ssh $(PI) "mktemp -d"))
	scp $^ $(PI):$(REMOTE_TMP)
	ssh $(PI) "cd $(REMOTE_TMP) && gcc $^ -o $@"
	scp $(PI):$(REMOTE_TMP)/$@ $@
	ssh $(PI) "rm -r $(REMOTE_TMP)"
	
pullup: pullup.c
	$(eval REMOTE_TMP=$(shell ssh $(PI) "mktemp -d"))
	scp $^ $(PI):$(REMOTE_TMP)
	ssh $(PI) "cd $(REMOTE_TMP) && gcc $^ -o $@"
	scp $(PI):$(REMOTE_TMP)/$@ $@
	ssh $(PI) "rm -r $(REMOTE_TMP)"
