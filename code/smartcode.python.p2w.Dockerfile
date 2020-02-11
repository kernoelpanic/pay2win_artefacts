# Dockerfile for smart contract development
# with web3 for python 3.7

# Docker file for python in ubuntu
# update the ubuntu development docker image first 
# $ docker pull ubuntu:devel  
#FROM ubuntu:devel
FROM ubuntu:eoan

WORKDIR /smartcode

COPY ./smartcode.python.p2w.requirements.txt /smartcode/requirements.txt

# Add a user given as build argument
ARG UNAME=smartcode
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID -o $UNAME
RUN useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME

# basic python3.7 setup
# Notes
# * python3-pip because dedicated python3.7-pip was not yet available
#		but you can install modules for 3.7 by invoking it like this
#   python3.7 -m pip --version    
RUN apt-get update \
  && apt-get install -y python3.7 python3.7-dev \
  && apt-get install -y python3-pip \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3.7 python \
  && python3.7 -m pip install --upgrade pip 

# requirements for building underlying packages
# e.g., secp256k1 
RUN apt-get install -y build-essential pkg-config autoconf libtool libssl-dev libffi-dev libgmp-dev libsecp256k1-0 libsecp256k1-dev

# Required system tools 
RUN apt-get install -y git wget
# Additional system tools 
RUN apt-get install -y vim iputils-ping netcat iproute2 sudo

# get recent solc version:
# https://github.com/ethereum/solidity/releases/
RUN cd /usr/local/bin \
  && wget -qO solc_4.25 https://github.com/ethereum/solidity/releases/download/v0.4.25/solc-static-linux \
  && wget -qO solc_5.4 https://github.com/ethereum/solidity/releases/download/v0.5.4/solc-static-linux \
  && wget -qO solc_5.9 https://github.com/ethereum/solidity/releases/download/v0.5.9/solc-static-linux \
	&& wget -qO solc_5.10 https://github.com/ethereum/solidity/releases/download/v0.5.10/solc-static-linux \
  && wget -qO solc_5.12 https://github.com/ethereum/solidity/releases/download/v0.5.12/solc-static-linux \
  && wget -qO solc_6.2 https://github.com/ethereum/solidity/releases/download/v0.6.2/solc-static-linux \
  && cp solc_6.2 solc \
  && chmod 755 solc*

# get current geth version from here for debug tools etc (not mandatory):
# https://geth.ethereum.org/downloads/#dl_stable_linux
RUN cd /tmp/ \
#  && wget -q https://gethstore.blob.core.windows.net/builds/geth-alltools-linux-amd64-1.8.19-dae82f09.tar.gz \
#  && tar -xzf /tmp/geth-alltools-linux-amd64-1.8.19-dae82f09.tar.gz \
#  && cp /tmp/geth-alltools-linux-amd64-1.8.19-dae82f09/* /usr/local/bin 
#  && wget -q https://gethstore.blob.core.windows.net/builds/geth-alltools-linux-amd64-1.8.27-4bcc0a37.tar.gz \
  && wget -q https://gethstore.blob.core.windows.net/builds/geth-alltools-linux-amd64-1.9.6-bd059680.tar.gz \
  && tar -xzf /tmp/geth-alltools-linux-amd64-1.9.6-bd059680.tar.gz \
  && cp /tmp/geth-alltools-linux-amd64-1.9.6-bd059680/* /usr/local/bin 

# install requirements which have been previously added to /smartcode
RUN python3.7 -m pip install -r requirements.txt

# port jupyter
EXPOSE 8887

# change final user
USER $UNAME

# Run jupyter per default:
CMD ["jupyter", "notebook", "--ip", "0.0.0.0", "--port", "8887"]

