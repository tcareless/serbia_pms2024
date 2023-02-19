#! /bin/bash
RELEASE_VERSION=0.1.6
set -e

echo "Building new release container"
docker build -t pms:$RELEASE_VERSION .

if [ $( docker ps -a | grep pms_temp | wc -l ) -gt 0 ]; then
  echo "Removing existing pms_temp container"
  docker container stop pms_temp
  docker container rm pms_temp
fi

# 1 container
echo "starting new pms_temp container"
docker run -d --restart=always\
    -e VIRTUAL_HOST=pmdsdata12 \
    -e VIRTUAL_PROTO=uwsgi \
    -e VIRTUAL_PORT=8000 \
    --name pms_temp \
    pms:$RELEASE_VERSION

# wait until pms_temp is up
sleep 15

if [ $( docker ps -a | grep pms | wc -l ) -gt 0 ]; then
  echo "Removing existing pms container"
  docker container stop pms
  docker container rm pms
fi

# 1 container
echo "Starting new pms container"
docker run -d --restart=always\
    -e VIRTUAL_HOST=pmdsdata12 \
    -e VIRTUAL_PROTO=uwsgi \
    -e VIRTUAL_PORT=8000 \
    --name pms \
    pms:$RELEASE_VERSION

# wait until pms_temp is up
sleep 15

if [ $( docker ps -a | grep pms_temp | wc -l ) -gt 0 ]; then
  echo "Removing existing pms_temp container"
  docker container stop pms_temp
  docker container rm pms_temp
fi
