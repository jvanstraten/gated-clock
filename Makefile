ifeq (,$(shell which blender-2.91))
BLENDER = blender
else
BLENDER = blender-2.91
endif

.PHONY: all
all: generate blend

.PHONY: generate
generate:
	cd primitives && $(MAKE)
	#rm -rf output
	mkdir -p output
	#python3 generator/compose_mainboard.py
	python3 generator/compose_support_board.py
	python3 generator/post.py

.PHONY: blend
blend:
	cd render && $(BLENDER) -b --python blend-import-support-board-parts.py --python-exit-code 1
	cd render && $(BLENDER) -b --python blend-import-support-board.py --python-exit-code 1
# 	cd render && $(BLENDER) -b --python blend-import-mainboard-parts.py --python-exit-code 1
# 	cd render && $(BLENDER) -b --python blend-import-mainboard.py --python-exit-code 1
# 	cd render && $(BLENDER) -b --python blend-import-front.py --python-exit-code 1
# 	cd render && $(BLENDER) -b --python blend-import-display.py --python-exit-code 1
# 	cd render && $(BLENDER) -b --python blend-import-highlight.py --python-exit-code 1
