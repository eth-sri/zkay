###########
# PURPOSE #
###########
# Abbreviate common docker commands by simple `make` commands
#
# NOTE:
# all commands involving docker use sudo, which is typically required to use
# docker commands on Ubuntu

############
# SETTINGS #
############

# name of docker image
_IMAGE := zkay

############################
# SPECIFIC DOCKER COMMANDS #
############################

# build the docker image
.PHONY: image
image:
	sudo docker build -t $(_IMAGE) .
	sudo ./scripts/inspect-image.sh
