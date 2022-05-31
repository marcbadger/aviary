# build this file using:
# export COMPOSE_DOCKER_CLI_BUILD=1
# export DOCKER_BUILDKIT=1
# DOCKER_BUILDKIT=1 docker build -t marcbadger/frame_exporting:ffmpeg -f ffmpeg.Dockerfile .

# syntax=docker/dockerfile:experimental
FROM marcbadger/frame_exporting:base

RUN apt-get update && apt-get install -y --no-install-recommends \
	software-properties-common

# for building ffmpeg
RUN apt-get update && apt-add-repository ppa:bernd-pfrommer/gtsam
RUN apt-get update && apt-get install -y --no-install-recommends \
	autoconf \
	automake \
	build-essential \
	cmake \
	git-core \
	gtsam \
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
	python-catkin-tools \
	texinfo \
	wget \
	zlib1g-dev

ENV ffmpeg_dir /aviary/ffmpeg

RUN mkdir -p /aviary $ffmpeg_dir $ffmpeg_dir/build $ffmpeg_dir/bin
WORKDIR $ffmpeg_dir

RUN wget -O yasm-1.3.0.tar.gz https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz && \
	tar xzvf yasm-1.3.0.tar.gz && \
	cd yasm-1.3.0 && \
	./configure --prefix="$ffmpeg_dir/build" --bindir="$ffmpeg_dir/bin" && \
	make && \
	make install

RUN wget https://www.nasm.us/pub/nasm/releasebuilds/2.13.03/nasm-2.13.03.tar.bz2 && \
	tar xjvf nasm-2.13.03.tar.bz2 && \
	cd nasm-2.13.03 && \
	./autogen.sh && \
	PATH="${ffmpeg_dir}/bin:$PATH" ./configure --prefix="${ffmpeg_dir}/build" --bindir="${ffmpeg_dir}/bin" && \
	make && \
	make install

RUN git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git && \
	cd nv-codec-headers && \
	git checkout n9.1.23.2 && \
	tmp_var="PREFIX = ${ffmpeg_dir}/build" && \
	sed -i "1c${tmp_var}" Makefile && \
	make -f Makefile install

RUN git clone https://github.com/FFmpeg/FFmpeg.git && \
	cd $ffmpeg_dir/FFmpeg

RUN cd $ffmpeg_dir/FFmpeg && \
	PATH="$ffmpeg_dir/bin:$PATH" PKG_CONFIG_PATH="$ffmpeg_dir/build/lib/pkgconfig" ./configure \
		--prefix=${ffmpeg_dir}/build \
		--extra-cflags=-I${ffmpeg_dir}/build/include \
		--extra-ldflags=-L${ffmpeg_dir}/build/lib \
		--bindir=${ffmpeg_dir}/bin \
		--enable-cuda-nvcc \
		--enable-cuvid \
		--enable-libnpp \
		--extra-cflags=-I/usr/local/cuda/include/ \
		--extra-ldflags=-L/usr/local/cuda/lib64/ \
		--enable-gpl \
		--enable-nvenc \
		--enable-libx264 \
		--enable-libx265 \
		--enable-nonfree \
		--enable-shared

RUN cd $ffmpeg_dir/FFmpeg && \
	PATH="$ffmpeg_dir/bin:${PATH}:/usr/local/cuda/bin" make && make install && hash -r

RUN echo "$ffmpeg_dir/build/lib" >> "/etc/ld.so.conf" && \
	ldconfig




# From oscf:ros-desktop