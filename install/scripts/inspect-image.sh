#!/bin/bash

###########
# PURPOSE #
###########
# show details of each layer of the docker image

#########
# USAGE #
#########
# Run this script by
# $ sudo ./inspect-image.sh

ID=$(docker images --filter=reference=bpl --format "{{.ID}}")

echo $ID
docker history --format "table {{printf \"%.150s\" .CreatedBy}}\t{{.Size}}" --no-trunc $ID