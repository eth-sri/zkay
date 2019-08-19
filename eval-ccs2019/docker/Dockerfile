FROM bpl


################
# INSTALL CLOC #
################
# To install on host:
# - Install cloc (1.74)

# -L: follow redirects
RUN cd /scripts \
	&& curl -L -o cloc.tar.gz https://github.com/AlDanial/cloc/releases/download/1.74/cloc-1.74.tar.gz \
	&& tar -xzf cloc.tar.gz \
	&& cp cloc*/cloc /usr/bin

###########
# HELPERS #
###########
# Install helper tools (only needed for evaluation)
#
# To install on host:
# - Install git
# - Install textlive-full

# git
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		git \
		texlive-full \
	&& rm -rf /var/lib/apt/lists/*
