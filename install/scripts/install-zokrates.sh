#!/bin/bash

###########
# PURPOSE #
###########
# Install zokrates
# basic instructions taken from:
# - https://zokrates.github.io/gettingstarted.html
# - https://github.com/Zokrates/ZoKrates/blob/master/Dockerfile

#########
# USAGE #
#########
# Run this script by
# $ ./install-zokrates.sh

###########
# PREPARE #
###########

# Any subsequent commands which fail will cause the shell script to exit immediately
set -e

# determine target directory
BASEDIR=$(dirname "$(readlink -f "$0")")
ZOK="$BASEDIR/../ZoKrates"

# cleanup (if was installed before)
rm -rf "$ZOK"

# create directory
mkdir "$ZOK"
cd "$ZOK"


################
# INSTALL RUST #
################
# Needed to compile zokrates

# set rust version globally
# very specific version to prevent breaking changes
export RUST_TOOLCHAIN=nightly-2019-01-01
export WITH_LIBSNARK=1

# install rustup
# Instructions taken from:
# https://www.rust-lang.org/tools/install
curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain $RUST_TOOLCHAIN

# configure current shell
source $HOME/.cargo/env

cargo --version
rustc --version

###########
# INSTALL #
###########

# clone
git clone https://github.com/ZoKrates/ZoKrates src

# build specific version (indicated by commit hash)
cd src
git checkout 224a7e6
./build_release.sh
cd ..

# create zokrates home directory
mkdir zokrates_home

# copy relevant files
cp -r ./src/target/release/zokrates .
cp -r ./src/zokrates_stdlib/stdlib/* zokrates_home

# cleanup sources
rm -rf src
