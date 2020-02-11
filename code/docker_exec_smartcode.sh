#!/bin/bash



CONTAINER_ID=$(docker ps | grep "smartcode:p2w" | cut -d" " -f1)

if [ -z "${1}" ] && [ -z "${CUID+x}" ];
then 
	export CUID=1000 # start shell as normal user with UID = 1000
elif [ ! -z "${1}" ];
then
	export CUID="${1}" # start shell as root with UID = 0
fi

docker exec \
  --user ${CUID} \
  -it ${CONTAINER_ID} \
  /bin/bash
