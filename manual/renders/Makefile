
ifeq (,$(shell which blender-2.91))
BLENDER = blender
else
BLENDER = blender-2.91
endif

.PHONY: all
all: disassembly1.jpg disassembly2.jpg disassembly3.jpg disassembly4.jpg disassembly5.jpg disassembly6.jpg bracket.png

disassembly%.jpg: ../../printed/assembly.blend render-disas.py
	$(BLENDER) -b $< --python render-disas.py --python-exit-code 1 -- $@

bracket.png: bracket.blend render-bracket.py
	$(BLENDER) -b $< --python render-bracket.py --python-exit-code 1 -- $@
