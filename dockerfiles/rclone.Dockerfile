# build this docker using:
# export COMPOSE_DOCKER_CLI_BUILD=1
# export DOCKER_BUILDKIT=1
# DOCKER_BUILDKIT=1 docker build -t marcbadger/frame_exporting:rclone -f rclone.Dockerfile .

FROM osrf/ros:melodic-desktop-full-bionic

RUN apt-get update && apt-get install -y --no-install-recommends \
	software-properties-common \
	vim

RUN curl https://rclone.org/install.sh | bash

