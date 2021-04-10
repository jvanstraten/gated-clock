
ifeq (,$(shell which blender-2.91))
BLENDER = blender
else
BLENDER = blender-2.91
endif

FRONT_THICKNESS = 3.0
DISPLAY_THICKNESS = 3.0
HIGHLIGHT_THICKNESS = 5.0

.PHONY: all
all: assembly.blend assembly.py led-bender.blend led-bender.py
	rm -rf stl
	mkdir -p stl/black stl/white stl/any
	FRONT_THICKNESS=$(FRONT_THICKNESS)              \
	DISPLAY_THICKNESS=$(DISPLAY_THICKNESS)          \
	HIGHLIGHT_THICKNESS=$(HIGHLIGHT_THICKNESS)      \
	$(BLENDER) -b assembly.blend --python assembly.py --python-exit-code 1
	$(BLENDER) -b led-bender.blend --python led-bender.py --python-exit-code 1
