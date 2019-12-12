FROM debian:10

#############
# LIBSNARKS #
#############
# the relevant dependencies to obtain and compile libsnarks
RUN apt-get update && apt-get install -y \
		git \
		build-essential \
		cmake \
		libgmp-dev \
		pkg-config \
		libssl-dev \
		libboost-dev \
		libboost-program-options-dev \
	&& apt-get clean && rm -rf /var/lib/apt/lists/*

########
# JAVA #
########
# required to install default-jdk-headless
RUN mkdir -p /usr/share/man/man1
RUN apt-get update && apt-get install -y \
		default-jdk-headless \
	&& apt-get clean && rm -rf /var/lib/apt/lists/*

##########
# PYTHON #
##########
RUN apt-get update && apt-get install -y \
		python3-pip \
	&& apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install virtualenv

#########
# ANTLR #
#########
# Recommended version: 4.7.2
RUN apt-get update && apt-get install -y \
		antlr4 \
	&& apt-get clean && rm -rf /var/lib/apt/lists/*