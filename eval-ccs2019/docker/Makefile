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
_IMAGE := bpl-eval

############################
# SPECIFIC DOCKER COMMANDS #
############################

# build the docker image
.PHONY: image
image:
	make -C ../../install image
	sudo docker build -t $(_IMAGE) .
