.PHONY: all
all:
	cd primitives && $(MAKE)
	rm -rf output
	mkdir -p output
	python3 generator/compose.py
