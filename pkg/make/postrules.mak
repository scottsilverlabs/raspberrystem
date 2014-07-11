.PHONY: all clean targets

all:: $(DIRS:=.dir) $(TARGETS)
	@#This comment suppressed "Nothing to be done..."

clean:: $(DIRS:=.cleandir) $(TARGETS:=.clean)
	@echo 'Cleaning directory "$(RELDIR)"'
	@rm -f *.o
	@rm -f *.pyc

targets:: $(DIRS:=.targets) $(TARGETS:=.target)
	@#This comment suppressed "Nothing to be done..."
