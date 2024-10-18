
ifeq (,$(shell which blender-2.91))
BLENDER = blender
else
BLENDER = blender-2.91
endif

DIRS = $(dir $(shell find . -name '*.verif.blend'))
COMPONENTS = $(join $(DIRS),$(patsubst %/,%.verif.txt,$(DIRS)))

.PHONY: all
all: $(COMPONENTS)

.PHONY: clean
clean:
	find . -name '*.blend1' -or -name '*.verif.txt' -delete

%.verif.txt: %.verif.blend blend-export.py
	$(BLENDER) -b $< --python blend-export.py --python-exit-code 1

