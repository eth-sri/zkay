#/bin/bash

###########
# PURPOSE #
###########
# Run the docker image
#
# Prerequisites:
# - docker

#########
# USAGE #
#########
# $ ./bpl-eval-docker.sh

############
# SETTINGS #
############

IMAGE=bpl-eval

###############
# PREPARATION #
###############
# determine directory containing this script
BASEDIR="$(dirname "$(readlink -f "$0")")"

# create docker image (if it does not yet exist)
make -C "$BASEDIR/docker" image

##############
# RUN DOCKER #
##############
# --rm: automatically clean up the container when the container exits
# --workdir: Working directory inside the container
# -v: Bind mount a volume from the host

sudo docker run \
	-it \
	--rm \
	-v "$BASEDIR/..":/bpl-implementation \
	--workdir /bpl-implementation/eval-ccs2019 \
	$IMAGE \
	make eval

