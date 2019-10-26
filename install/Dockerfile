FROM zokrates/zokrates:0.5.0 AS zok

FROM continuumio/miniconda3:4.7.12
# Image to be distributed
# - starts from image containing conda
# - conda allows to keep the installation within docker and on host consistent

RUN apt-get update && apt-get install -y build-essential

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

##########################
# INSTALL SOLCJS & TRUFFLE #
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
		solc@0.5.12 \
		truffle@5.0.30 \
		ganache-cli@6.5.1


##########################
# INSTALL SOLC
#########################

RUN wget https://github.com/ethereum/solidity/releases/download/v0.5.12/solc-static-linux && mv solc-static-linux /usr/bin/solc && chmod +x /usr/bin/solc

############
# ZOKRATES #
############

# Install dynamic lib dependency
RUN apt-get install -y --no-install-recommends libgmp3-dev && rm -rf /var/lib/apt/lists/*

# zokrates environment
ENV ZOKRATES_ROOT /zokrates
ENV ZOKRATES_HOME $ZOKRATES_ROOT/zokrates_home

# copy zokrates binaries from zokrates image
COPY --from=zok /home/zokrates $ZOKRATES_ROOT
RUN mv $ZOKRATES_ROOT/.zokrates $ZOKRATES_HOME

# ZKAY environment
ENV ZKAYDIR /zkay
ENV ZKAYSRC $ZKAYDIR/zkay
ENV PYTHONPATH $ZKAYDIR
