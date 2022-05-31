# Build this docker with:
# export COMPOSE_DOCKER_CLI_BUILD=1
# export DOCKER_BUILDKIT=1
# DOCKER_BUILDKIT=1 docker build -t marcbadger/frame_exporting:watcher -f watcher.Dockerfile .
# docker push marcbadger/frame_exporting:watcher

FROM ubuntu:20.04

RUN apt-get update && apt-get install -y --no-install-recommends \
	software-properties-common \
	vim \
	inotify-tools