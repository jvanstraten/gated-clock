#ARDUINO = /data/opt/arduino/arduino-1.8.9

#ARDUINO_TOOLS = $(ARDUINO)/hardware/teensy/../tools

PROJECT = gated-clock
IMAGE = jvanstraten/gated-clock

.PHONY: all
all: program

.PHONY: build
build: $(PROJECT).hex loader/teensy_loader_cli

.PHONY: program
program: build
	-stty -F /dev/serial/by-id/usb-Teensyduino_USB_Serial* -drain 134 # this is Teensy magic to reboot the board
	loader/teensy_loader_cli --mcu=TEENSYLC -w -v $(PROJECT).hex

$(PROJECT).hex: Dockerfile src
	docker build -t $(IMAGE) .
	id=`docker create $(IMAGE)` && (docker cp $$id:/src/$(PROJECT).hex $(PROJECT).hex ; docker rm -v $$id)

loader/teensy_loader_cli:
	rm -rf loader
	git clone https://github.com/PaulStoffregen/teensy_loader_cli.git loader
	cd loader && git reset 0a9ad5f --hard && make -j

.PHONY: clean
clean:
	-docker image rm $(IMAGE)
	$(RM) -f $(PROJECT).hex
