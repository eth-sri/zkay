FROM debian:10
ARG INSTALL_ZKAY=0
ARG PYTHON_VERSION=3.8.7

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

########
# RUST #
########
# required to build babygiant-lib
RUN apt-get update && apt-get install -y curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

##########
# PYTHON #
##########
# recent python versions need to be built from source
RUN apt-get update && apt-get install -y \
		wget \
        zlib1g-dev \
		libffi-dev \
	&& apt-get clean && rm -rf /var/lib/apt/lists/*
RUN wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz \
    && tar xzf Python-$PYTHON_VERSION.tgz \
    && cd Python-$PYTHON_VERSION \
    && ./configure --enable-optimizations \
    && make install
RUN pip3 install virtualenv

###################
# ZKAY (OPTIONAL) #
###################
RUN if [ "$INSTALL_ZKAY" = "1" ]; then \
		git clone https://github.com/eth-sri/zkay.git && \
		    sh ./babygiant-lib/install.sh && \
			cd zkay && \
			pip install --no-binary zkay .; \
	fi
