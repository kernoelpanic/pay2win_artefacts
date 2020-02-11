#!/bin/bash
# Setup docker environment for tutorial

docker pull trufflesuite/ganache-cli:latest
docker build --build-arg UID=1000 --build-arg GID=1000 -f smartcode.python.p2w.Dockerfile -t smartcode:p2w .
docker network create --subnet=172.18.0.0/16 --driver bridge smartnet
docker network ls
docker images 
