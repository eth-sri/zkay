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
# To run docker interactively (mounts the current directory):
# $ path/to/bpl-docker.sh
#
# To run a specific command withing docker (e.g.):
# $ path/to/bpl-docker.sh make test

############
# SETTINGS #
############

IMAGE=bpl
CONTAINERNAME=bpl-container

###############
# PREPARATION #
###############
# determine directory containing this script
BASEDIR="$(dirname "$(readlink -f "$0")")"

# create docker image (if it does not yet exist)
make -C "$BASEDIR/install" image

# remove existing container if one is there
sudo "$BASEDIR/install/scripts/cleanup-container.sh"

##############
# RUN DOCKER #
##############
# --rm: automatically clean up the container when the container exits
# --workdir: Working directory inside the container
# -v: Bind mount a volume from the host

if [ $# -eq 0 ]; then
	# no arguments supplied
	echo "Running docker interactively..."
	DIR="$(pwd)"
	WORKDIR="/$(basename "$DIR")_host"
	FLAGS="-v $DIR:$WORKDIR --workdir $WORKDIR"
else
	echo "Running in docker: $@"
	FLAGS="--workdir /bpl"
fi

sudo docker run \
	-it \
	--rm \
	-v "$BASEDIR":/bpl \
	$FLAGS \
	--name $CONTAINERNAME \
	$IMAGE \
	"$@"

