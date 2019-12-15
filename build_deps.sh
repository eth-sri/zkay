#!/bin/bash
# Build grammar
ANTLR_VERSION="4.7.2"

# Download antlr if not installed
if $(command -v antlr4); then # && [ "$(antlr4 | head -n 1)" == "*${ANTLR_VERSION}" ]; then
	ANTLR_CMD='antlr4'
else
	ANTLR_CMD='java -jar antlr4.jar'
	wget -N -O zkay/solidity_parser/antlr4.jar "https://www.antlr.org/download/antlr-${ANTLR_VERSION}-complete.jar"
fi

# Build grammar
cd zkay/solidity_parser && eval "${ANTLR_CMD} -o generated -visitor -Dlanguage=Python3 Solidity.g4" && cd ../../

if command -v sudo; then
	if command -v apt-get; then
		sudo apt-get update && \
		sudo apt-get install default-openjdk-headless git build-essential cmake libgmp-dev pkg-config libssl-dev libboost-dev libboost-program-options-dev
	elif command -v pacman; then
		sudo pacman -Sy && sudo pacman -S --needed jdk-openjdk cmake pkgconf openssl gmp boost
	fi
fi

# Clone libsnark
if [ ! -d libsnark ]; then
	git clone --recursive git@gitlab.inf.ethz.ch:OU-VECHEV/zkay-libsnark.git libsnark
fi

# Build libsnark
cd libsnark && git pull && ./build.sh $(grep -c ^processor /proc/cpuinfo) && cd ../
cp libsnark/build/libsnark/zkay_interface/run_snark zkay/jsnark_interface/run_snark
