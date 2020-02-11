#!/bin/bash

docker run \
  -p 127.0.0.1:8887:8887 \
  --mount type=bind,source=$(pwd),target=/smartcode \
  --net smartnet \
  --hostname smartcode \
  --ip 172.18.0.7 \
  -it smartcode:p2w
