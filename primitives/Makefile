
ifeq (,$(shell which blender-2.91))
BLENDER = blender
else
BLENDER = blender-2.91
endif

DIRS = $(shell echo */)
COMPONENTS = $(join $(DIRS),$(patsubst %/,%.blend.txt,$(DIRS)))

.PHONY: all
all: $(COMPONENTS)

.PHONY: clean
clean:
	find . -name '*.blend1' -or -name '*.blend.txt' -delete

%.blend.txt: %.blend blend-export.py
	$(BLENDER) -b $< --python blend-export.py --python-exit-code 1

