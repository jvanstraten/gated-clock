# JvS: modified from https://github.com/ethernetdan/teensydocker
#    and https://github.com/cruxic/teensy-makefile/blob/master/Makefile

# Based on Karl Lunt's Makefile for Windows.
# Simplified for Linux/Unix by Mike Ditto <ford@omnicron.com>
# Docker-based flashing added by Dan Gillespie <dan@dg.gg>

#########################################################################
# First, describe the cross-compilation environment:

TARGETTYPE = arm-none-eabi

# Source paths
TEENSY_DIR = /teensy/teensy3
PROJ_DIR = .

# Tools paths
CC = $(BINDIR)$(TARGETTYPE)-gcc
CXX = $(BINDIR)$(TARGETTYPE)-g++
AS = $(BINDIR)$(TARGETTYPE)-as
AR = $(BINDIR)$(TARGETTYPE)-ar
LD = $(BINDIR)$(TARGETTYPE)-ld
OBJCOPY = $(BINDIR)$(TARGETTYPE)-objcopy
SIZE = $(BINDIR)$(TARGETTYPE)-size
OBJDUMP = $(BINDIR)$(TARGETTYPE)-objdump

# Shared C/C++ flags
CPPFLAGS = -c -Os -g -Wall -ffunction-sections -fdata-sections -nostdlib -MMD \
 -mthumb -mcpu=cortex-m0plus -fsingle-precision-constant \
 -D__MKL26Z64__ -DTEENSYDUINO=153 -DARDUINO=10809 -DF_CPU=48000000 \
 -DUSB_SERIAL -DLAYOUT_US_ENGLISH -I$(TEENSY_DIR) -I.

# Flags only for C++
CXXFLAGS = -fno-exceptions -felide-constructors -std=gnu++0x -fno-rtti

CORE_C_SOURCES = $(wildcard $(TEENSY_DIR)/*.c)
CORE_CPP_SOURCES = $(wildcard $(TEENSY_DIR)/*.cpp)
CORE_ASM_SOURCES = $(wildcard $(TEENSY_DIR)/*.S)
CORE_OBJS = $(CORE_C_SOURCES:.c=.o) $(CORE_CPP_SOURCES:.cpp=.o) $(CORE_ASM_SOURCES:.S=.o)

PROJ_C_SOURCES = $(wildcard $(PROJ_DIR)/*.c)
PROJ_CPP_SOURCES = $(wildcard $(PROJ_DIR)/*.cpp)
PROJ_OBJS = $(PROJ_C_SOURCES:.c=.o) $(PROJ_CPP_SOURCES:.cpp=.o)

MCU = mkl26z64

PROJECT = gated-clock

.PHONY: deploy
deploy: build
	teensy_loader_cli --mcu=$(MCU) -w -v $(PROJECT).hex

.PHONY: build
build: $(PROJECT).hex $(PROJECT).bin stats dump

$(PROJECT).bin: $(PROJECT).elf
	$(OBJCOPY) -O binary -j .text -j .data $(PROJECT).elf $(PROJECT).bin

$(PROJECT).hex: $(PROJECT).elf
	$(OBJCOPY) -R .stack -O ihex $(PROJECT).elf $(PROJECT).hex

$(PROJECT).elf: $(PROJ_OBJS) teensy3.a
	$(CC) -Os -Wl,--gc-sections,--relax,--defsym=__rtc_localtime=1470636289 "-T$(TEENSY_DIR)/mkl26z64.ld" \
		--specs=nano.specs -mthumb -mcpu=cortex-m0plus -fsingle-precision-constant \
		-o $@ $(PROJ_OBJS) teensy3.a -L$(TEENSY_DIR) -lm

teensy3.a: $(CORE_OBJS)
	rm -f $@
	$(AR) rcs $@ $^

.PHONY: stats
stats: $(PROJECT).elf
	$(SIZE) $(PROJECT).elf

.PHONY: dump
dump: $(PROJECT).elf
	$(OBJDUMP) -h $(PROJECT).elf

