FROM debian:latest AS helper
# Helper image to install
# - zokrates

#######################
# BASIC PREREQUISITES #
#######################
# Needed for download/compilation/...
# To install on host:
# - install packages listed below

# -qq: quiet installation
RUN apt-get update \
	&& apt-get install -y \
		curl \
		build-essential \
		git \
	&& rm -rf /var/lib/apt/lists/*

####################
# INSTALL ZOKRATES #
####################
# To install on host:
# - install packages listed below
# $ ./scripts/install-zokrates.sh

# libsnark (prerequisite)
# Instructions taken from:
# https://github.com/Zokrates/ZoKrates/blob/master/scripts/install_libsnark_prerequisites.sh
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential \
		cmake \
		libboost-dev \
		libboost-program-options-dev \
		libgmp3-dev \
		libprocps-dev \
		libssl-dev \
		pkg-config \
		python-markdown \
	&& rm -rf /var/lib/apt/lists/*

# prepare scripts
WORKDIR /scripts
COPY scripts/install-zokrates.sh install-zokrates.sh
# run installation script
RUN ./install-zokrates.sh


FROM continuumio/miniconda3
# Image to be distributed
# - starts from image containing conda
# - conda allows to keep the installation within docker and on host consistent

###################
# PREPARE SCRIPTS #
###################
# To install on host:
# - No action necessary

# prepare scripts directory
ENV SCRIPTS /scripts
RUN mkdir -p $SCRIPTS

#####################
# CONDA ENVIRONMENT #
#####################
# To install on host:
# - install conda
# $ source ./scripts/prepare-conda.sh

# deactivate warnings for outdated conda
RUN conda config --set notify_outdated_conda false
RUN conda init bash

# import conda environment to root (avoids having to activate the resulting environment)
COPY scripts/environment.yml $SCRIPTS/environment.yml
RUN conda env update -n root --file $SCRIPTS/environment.yml \
	&& conda clean --all

#########################
# ENVIRONMENT VARIABLES #
#########################
# To install on host:
# - No action necessary

# zokrates
ENV WITH_LIBSNARK 1
ENV ZOKRATES_ROOT /zokrates
ENV ZOKRATES_HOME $ZOKRATES_ROOT/zokrates_home

# ZKAY
ENV ZKAYDIR /zkay
ENV ZKAYSRC $ZKAYDIR/src
ENV PYTHONPATH $ZKAYSRC

##########################
# INSTALL SOLC & TRUFFLE #
##########################
# SOLC instructions take from:
# https://solidity.readthedocs.io/en/v0.5.3/installing-solidity.html
# TRUFFLE Instructions from
# https://www.trufflesuite.com/docs/truffle/getting-started/installation
# To install on host:
# - No action necessary

# -q: silence detailed output
# -q: install globally
# emits warnings because we are root
RUN npm install -q -g \
		solc@0.5.10 \
		truffle@5.0.30 \
		ganache-cli@6.5.1

############
# ZOKRATES #
############
# Install zokrates
# - binaries were already compiled in the previous stage
# To install on host:
# - no action necessary

# libsnark (prerequisite)
# Instructions taken from:
# https://github.com/Zokrates/ZoKrates/blob/master/scripts/install_libsnark_prerequisites.sh
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential \
		cmake \
		libboost-dev \
		libboost-program-options-dev \
		libgmp3-dev \
		libprocps-dev \
		libssl-dev \
		pkg-config \
		python-markdown \
	&& rm -rf /var/lib/apt/lists/*

# copy relevant binaries
COPY --from=helper /ZoKrates $ZOKRATES_ROOT

RUN wget https://github.com/ethereum/solidity/releases/download/v0.5.12/solc-static-linux && mv solc-static-linux /usr/bin/solc && chmod +x /usr/bin/solc
