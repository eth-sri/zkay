FROM debian:buster-slim

RUN mkdir -p /usr/share/man/man1

RUN apt-get update && apt-get install -y \
		python3-pip \
		python3-dev \
		build-essential \
		default-jdk-headless \
	&& apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
