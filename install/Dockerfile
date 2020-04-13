FROM debian:10
ARG INSTALL_ZKAY=0

#############
# LIBSNARK #
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


###################
# ZKAY (OPTIONAL) #
###################
RUN if [ "$INSTALL_ZKAY" = "1" ]; then \
		git clone https://github.com/eth-sri/zkay.git && \
			cd zkay && \
			python3 setup.py sdist && \
			pip3 install --no-binary zkay dist/zkay-*.tar.gz; \
	fi
