# JvS: modified from https://github.com/ethernetdan/teensydocker

FROM debian:8

# Adapted from http://www.omnicron.com/~ford/teensy/setup-teensy

RUN PACKAGES="libusb-dev git make curl gcc-arm-none-eabi gcc unzip" && \
    export DEBIAN_FRONTEND=noninteractive && \
    rm /etc/apt/sources.list && \
    echo "deb [trusted=yes] http://archive.debian.org/debian jessie main" | tee -a /etc/apt/sources.list && \
    echo "deb [trusted=yes] http://archive.debian.org/debian-security jessie/updates main" | tee -a /etc/apt/sources.list && \
    echo "Acquire::Check-Valid-Until false;" | tee -a /etc/apt/apt.conf.d/10-nocheckvalid && \
    echo 'Package: *\nPin: origin "archive.debian.org"\nPin-Priority: 500' | tee -a /etc/apt/preferences.d/10-archive-pin && \
    apt-get update && \
    apt-get install -y $PACKAGES && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV COMMIT 605d9dc91102c4fa99c1bd37ff51571e7e672773

# Clone and compile teensy_loader_cli
RUN git clone https://github.com/PaulStoffregen/teensy_loader_cli.git /loader && \
    (cd /loader && git reset $COMMIT --hard  && make) && \
    install -Dm755 /loader/teensy_loader_cli /usr/bin && \
    rm -rf /loader

# Configure device permissions
RUN curl -o /etc/udev/rules.d/49-teensy.rules http://www.pjrc.com/teensy/49-teensy.rules

# Download Teensy core library
RUN git clone https://github.com/PaulStoffregen/cores /teensy && \
    (cd /teensy && git reset 1.53 --hard) && \
    sed -i'' -e 's/#define stricmp[(]a, b[)] strcasecmp[(]a, b[)]/#define stricmp strcasecmp/g' /teensy/teensy3/wiring.h

# Copy code
COPY src /src
WORKDIR /src

# Build
RUN make build -j
