#
# API Makefile
#

DIR=$(notdir $(CURDIR))
TAR=../$(DIR).tar
BINARIES=led_server
PI=pi@raspberrypi

all: $(TAR)

$(TAR): $(PY_FILES) $(BINARIES)
	tar cvf $@  -C .. $(addprefix $(DIR)/,$<)

led_server: led_server.c
	$(eval REMOTE_TMP=$(shell ssh $(PI) "mktemp -d"))
	scp $< $(PI):$(REMOTE_TMP)
	ssh $(PI) "cd $(REMOTE_TMP) && gcc $< -o $@"
	scp $(PI):$(REMOTE_TMP)/$@ $@
	ssh $(PI) "rm -r $(REMOTE_TMP)"
	
