#!/bin/bash


# TODO support command options
REMOVE_IMAGE="false"


echo_run() {
  cmd=$1
  echo "--- RUN $cmd"
  eval $cmd
}

new_section() {
  name=$1
  echo
  echo "========== SECTION: " $name "   =============="
}




new_section "Clear previous docker images & containers ..."
container_name="gocardless"
container_id=$(docker ps -a | grep "$container_name" | awk '{print $1}')
if [[ $container_id != "" ]]; then
  echo "[removing container]: $container_name"
  echo_run "docker rm -f $container_id"
fi

if [[ $REMOVE_IMAGE == "true" ]]; then
  image_name="gocardless"
  image_id=$(docker images | grep $image_name | awk '{print $3}')
  if [[ $image_id != "" ]]; then
    echo "[removing image]: $image_name"
    echo_run "docker rmi -f $image_id"
  fi
fi


new_section "Begin to run crawler ..."
echo_run "docker-compose up"
