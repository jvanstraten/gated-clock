
ifeq (,$(shell which blender-2.91))
BLENDER = blender
else
BLENDER = blender-2.91
endif

DIRS = $(shell echo */)
COMPONENTS = $(join $(DIRS),$(patsubst %/,%.blend.data,$(DIRS)))

.PHONY: all
all: $(COMPONENTS)

%.blend.data: %.blend blend-export.py
	$(BLENDER) -b $< --python blend-export.py --python-exit-code 1
