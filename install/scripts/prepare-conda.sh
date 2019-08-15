#/bin/bash

###########
# PURPOSE #
###########
# Prepare conda environment
#
# Prerequisites:
# - install conda

#########
# USAGE #
#########
# Run this script by (no sudo):
# $ source ./prepare-conda.sh

###############
# PREPARATION #
###############

# navigate to directory containing this script
BASEDIR="$(dirname "$(readlink -f "$0")")"
cd "$BASEDIR"

######################
# CREATE ENVIRONMENT #
######################
# create conda environment

conda env create --force -f environment.yml

#########################
# ENVIRONMENT VARIABLES #
#########################

# activate (needed to load $CONDA_PREFIX)
conda activate bpl

# set up conda to automatically set/unset environment variables
ENVDIR=$CONDA_PREFIX/etc/conda
mkdir -p $ENVDIR/activate.d && mkdir -p $ENVDIR/deactivate.d
ACTIVATE="$ENVDIR/activate.d/set_environment_variables.sh"
cp set_environment_variables.sh "$ACTIVATE"
DEACTIVATE="$ENVDIR/deactivate.d/unset_environment_variables.sh"
cp unset_environment_variables.sh "$DEACTIVATE"

# update path of BASEDIR
PWD="$(pwd)"
sed -i "s|BASEDIR=.*|BASEDIR=\"$PWD\"|" "$ACTIVATE"

conda deactivate

################
# NPM packages #
################

# needed to run npm
conda activate bpl

# install npm packages
npm install -q -g \
	solc@0.5.10 \
	truffle@5.0.30 \
	ganache-cli@6.5.1

conda deactivate

# nagivate back
cd -