FROM continuumio/miniconda3:4.7.12
# Image to be distributed
# - starts from image containing conda
# - conda allows to keep the installation within docker and on host consistent

RUN mkdir -p /usr/share/man/man1

RUN apt-get update && apt-get install -y build-essential default-jdk-headless

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

# ZKAY environment
ENV ZKAYDIR /zkay
ENV ZKAYSRC $ZKAYDIR/zkay
ENV PYTHONPATH $ZKAYDIR
