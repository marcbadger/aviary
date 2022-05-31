# Build this docker using:
# export COMPOSE_DOCKER_CLI_BUILD=1
# export DOCKER_BUILDKIT=1
# DOCKER_BUILDKIT=1 docker build -t marcbadger/frame_exporting:all_but_birds_20.04 -f all_but_birds_20.04.Dockerfile .

FROM marcbadger/frame_exporting:base_20.04

WORKDIR /aviary
# RUN sh \
#     -c 'echo "deb http://packages.ros.org/ros/ubuntu `lsb_release -sc` main" \
#         > /etc/apt/sources.list.d/ros-latest.list'

RUN apt-get update && apt-get install -y --no-install-recommends \
	software-properties-common

RUN add-apt-repository ppa:borglab/gtsam-release-4.0

# for building ffmpeg
RUN apt-get update && apt-add-repository ppa:bernd-pfrommer/gtsam
RUN apt-get update && apt-get install -y --no-install-recommends \
	autoconf \
	automake \
	build-essential \
	cmake \
	git-core \
	libgtsam-dev\
	libgtsam-unstable-dev \
	libass-dev \
	libfftw3-dev \
	libfreetype6-dev \
	libgstreamer1.0-dev \
	libgstreamer-plugins-base1.0-dev \
	libsdl2-dev \
	libtool \
	libva-dev \
	libvdpau-dev \
	libvorbis-dev \
	libx264-dev \
	libx265-dev \
	libxcb1-dev \
	libxcb-shm0-dev \
	libxcb-xfixes0-dev \
	pkg-config \
	python3-catkin-tools \
	texinfo \
	wget \
	zlib1g-dev

RUN apt-get update && apt-get install -q -y --no-install-recommends \
    python3-catkin-tools \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libfftw3-dev

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> "/root/.bashrc"

RUN apt-get update && apt-get install -q -y --no-install-recommends \
	openssh-client

RUN apt-get update && apt-get install -q -y --no-install-recommends \
	python2