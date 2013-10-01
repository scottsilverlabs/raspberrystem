#
# API Makefile
#

DIR=$(notdir $(CURDIR))
TAR=../$(DIR).tar
PI=pi@raspberrypi
PY_FILES=$(wildcard *.py)

all: $(TAR)

$(TAR): $(PY_FILES)
	tar cvf $@  -C .. $(addprefix $(DIR)/,$^)

