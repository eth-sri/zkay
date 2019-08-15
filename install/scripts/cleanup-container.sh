#!/bin/bash

###########
# PURPOSE #
###########
# Remove bpl-container (cleanup)

#########
# USAGE #
#########
# Run this script by
# $ sudo ./cleanup-container.sh

CONTAINER=$(docker ps -aqf "name=bpl-container")

if [ ! -z "$CONTAINER" ]; then
	echo "Removing existing container..."
	docker rm -f $CONTAINER
fi
