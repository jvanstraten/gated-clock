ifeq (,$(shell which blender-2.91))
BLENDER = blender
else
BLENDER = blender-2.91
endif

# NOTE: I'm too lazy to make proper recipies with proper dependencies. Just
# manually comment out what you don't need when you're experimenting; some
# steps take forever.

.PHONY: all
all:
	cd primitives && $(MAKE)
	cd parts && $(MAKE)
	rm -rf output
	mkdir -p output
	python3 generator/compose_mainboard.py
	python3 generator/compose_support_board.py
	python3 generator/post.py
	python3 generator/orderlist.py
	convert output/mainboard.normal.svg output/mainboard.normal.png
	convert output/mainboard.front.traces.svg output/mainboard.front.traces.png
	convert output/mainboard.back.traces.svg output/mainboard.back.traces.png
	convert output/support_board.front.traces.svg output/support_board.front.traces.png
	convert output/support_board.back.traces.svg output/support_board.back.traces.png
	cd render && $(BLENDER) -b --python blend-import-support-board-parts.py --python-exit-code 1
	cd render && $(BLENDER) -b --python blend-import-support-board.py --python-exit-code 1
	cd render && $(BLENDER) -b --python blend-import-mainboard-parts.py --python-exit-code 1
	cd render && $(BLENDER) -b --python blend-import-mainboard.py --python-exit-code 1
	cd render && $(BLENDER) -b --python blend-import-front.py --python-exit-code 1
	cd render && $(BLENDER) -b --python blend-import-display.py --python-exit-code 1
	cd render && $(BLENDER) -b --python blend-import-highlight.py --python-exit-code 1
	rm -f output/mainboard.zip
	cd output && 7z a -tzip mainboard.zip  \
		mainboard.PCB.GM1 \
		mainboard.PCB.TXT \
		mainboard.PCB.GTO \
		mainboard.PCB.GTS \
		mainboard.PCB.GTL \
		mainboard.PCB.G1  \
		mainboard.PCB.G2  \
		mainboard.PCB.GBL \
		mainboard.PCB.GBS \
		mainboard.PCB.GBO
	rm -f output/support_board.zip
	cd output && 7z a -tzip support_board.zip  \
		support_board.PCB.GM1 \
		support_board.PCB.TXT \
		support_board.PCB.GTO \
		support_board.PCB.GTS \
		support_board.PCB.GTL \
		support_board.PCB.G1  \
		support_board.PCB.G2  \
		support_board.PCB.GBL \
		support_board.PCB.GBS \
		support_board.PCB.GBO
