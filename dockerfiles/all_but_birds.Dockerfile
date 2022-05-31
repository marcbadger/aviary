# Build this docker using:
# export COMPOSE_DOCKER_CLI_BUILD=1
# export DOCKER_BUILDKIT=1
# DOCKER_BUILDKIT=1 docker build -t marcbadger/frame_exporting:all_but_birds -f all_but_birds.Dockerfile .

FROM marcbadger/frame_exporting:ffmpeg

WORKDIR /aviary

RUN apt-get update && apt-get install -q -y --no-install-recommends \
    python-catkin-tools \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libfftw3-dev

ENV ROS_DISTRO melodic

RUN echo "source /opt/ros/melodic/setup.bash" >> "/root/.bashrc"

RUN apt-get update && apt-get install -q -y --no-install-recommends \
	openssh-client