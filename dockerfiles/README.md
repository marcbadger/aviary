# Building Docker Images and Bird Exporting for the Cluster

## Building Images
Install docker and set up a docker hub account. Log in on the command line using ```docker login```.

Run in sequence:
```
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
docker build -t marcbadger/frame_exporting:base -f base.Dockerfile .
```
```
docker build -t marcbadger/frame_exporting:ffmpeg -f ffmpeg.Dockerfile .
```
```
docker build -t marcbadger/frame_exporting:all_but_birds -f all_but_birds.Dockerfile .
```
```
docker build -t marcbadger/frame_exporting:rclone -f rclone.Dockerfile .
```

Now that the images are done, push them to docker hub:
```
docker push marcbadger/frame_exporting:all_but_birds
docker push marcbadger/frame_exporting:rclone
```

You will probably run into trouble building because code installed in ffmpeg.Dockerfile has been updated since the docker that base.Dockerfile starts from was created. Probably best to start with ```~/aviary/dockerfiles-20.0.4``` and try to make it work with Ubuntu 20.0.4.

In that case, run in sequence:
```
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
docker build -t marcbadger/frame_exporting:base_20.04 -f base_20.04.Dockerfile .
```
```
docker build -t marcbadger/frame_exporting:all_but_birds_20.04 -f all_but_birds_20.04.Dockerfile .
```

Now that the images are done, push them to docker hub:
```
docker push marcbadger/frame_exporting:all_but_birds_20.04
```

## Installing bird_recording
The bird_recording package is installed in the /scratch/bird_packages directory on the kostas cluster.

Turn on your VPN, ssh into kostas-ap. If the birds package is not already built, make a directory for it to live in and clone the birds repository.
```
cd /scratch/bird_packages
mkdir Documents
cd Documents
git clone https://github.com/daniilidis-group/birds
```

The requirements for the birds package have already been installed in the Docker image, but in case you need them, [they are here](https://github.com/daniilidis-group/birds).

First start up an interactive job on the kostas cluster:
```
IMAGE=marcbadger/frame_exporting:all_but_birds
EXTRA_MOUNTS="/scratch/bird_packages:/bird_packages,/archive/birds/aviary/data2019:/archive/birds/aviary/data2019,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER"

srun --gpus=rtx2080ti:1 --cpus-per-gpu=8 --mem=32G --time=01:00:00 --qos=kostas-high --partition=kostas-compute --container-mount-home --container-mounts=${EXTRA_MOUNTS} --container-image=${IMAGE} --no-container-remap-root --pty bash
```

Note if you are using the ubuntu20.04 images, then you should use ```IMAGE=marcbadger/frame_exporting:all_but_birds_20.04``` above.

Then once you are inside running job, link some libraries:
```
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/kostas_rsa

ssh-keygen -f "/home/marc/.ssh/known_hosts" -R "$( hostname )"

scp -oStrictHostKeyChecking=no $( hostname ):/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.???.* /usr/lib/x86_64-linux-gnu/.
scp -oStrictHostKeyChecking=no $( hostname ):/usr/lib/x86_64-linux-gnu/libnvcuvid.so.???.* /usr/lib/x86_64-linux-gnu/.

ln -sf /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.???.* /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1
ln -sf /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so

ln -sf /usr/lib/x86_64-linux-gnu/libnvcuvid.so.???.* /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1
ln -sf /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1 /usr/lib/x86_64-linux-gnu/libnvcuvid.so
```

Now build ffmpeg that can decode h265 with the gpu. Requirements are already inside the Docker, but in case you need the install directions, [here they are](https://github.com/daniilidis-group/ffmpeg_image_transport/blob/master/docs/compile_ffmpeg.md).
```
export PATH=$PATH:/bird_packages/Documents/ffmpeg/bin

source /opt/ros/melodic/setup.bash

ffmpeg_dir=/bird_packages/Documents/ffmpeg
mkdir -p $ffmpeg_dir/build $ffmpeg_dir/bin

cd $ffmpeg_dir
wget -O yasm-1.3.0.tar.gz https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz && \
tar xzvf yasm-1.3.0.tar.gz && \
cd yasm-1.3.0 && \
./configure --prefix="$ffmpeg_dir/build" --bindir="$ffmpeg_dir/bin" && \
make && \
make install

cd $ffmpeg_dir
wget https://www.nasm.us/pub/nasm/releasebuilds/2.13.03/nasm-2.13.03.tar.bz2 && \
tar xjvf nasm-2.13.03.tar.bz2 && \
cd nasm-2.13.03 && \
./autogen.sh && \
PATH="${ffmpeg_dir}/bin:$PATH" ./configure --prefix="${ffmpeg_dir}/build" --bindir="${ffmpeg_dir}/bin" && \
make && \
make install
```

If the ```nasm``` install gives an error (e.g. for ubuntu20.04), try ```nasm-2.15.0.5```.

Now build ffmpeg:
```
cd $ffmpeg_dir
git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git
cd nv-codec-headers
git checkout n9.1.23.3
tmp_var="${ffmpeg_dir//"/"/"\/"}"
sed "s/\/usr\/local/${tmp_var}\/build/g" Makefile > Makefile.tmp
make -f Makefile.tmp install

cd $ffmpeg_dir
git clone https://github.com/FFmpeg/FFmpeg.git	
cd $ffmpeg_dir/FFmpeg
git checkout 588114cea4ee434c9c61353ed91ffc817d2965f5
# n4.3-dev-3123-g588114cea4

PATH="$ffmpeg_dir/bin:$PATH" PKG_CONFIG_PATH="$ffmpeg_dir/build/lib/pkgconfig" ./configure --prefix=${ffmpeg_dir}/build --extra-cflags=-I${ffmpeg_dir}/build/include --extra-ldflags=-L${ffmpeg_dir}/build/lib --bindir=${ffmpeg_dir}/bin --enable-cuda-nvcc --enable-cuvid --enable-libnpp --extra-cflags=-I/usr/local/cuda/include/ --extra-ldflags=-L/usr/local/cuda/lib64/ --enable-gpl --enable-nvenc --enable-libx264 --enable-libx265 --enable-nonfree --enable-shared
PATH="$ffmpeg_dir/bin:${PATH}:/usr/local/cuda/bin" make && make install && hash -r
```

Alternative for Ubuntu20.04:
```
cd $ffmpeg_dir
git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git
cd nv-codec-headers
git checkout n9.1.23.3
tmp_var="${ffmpeg_dir//"/"/"\/"}"
sed "s/\/usr\/local/${tmp_var}\/build/g" Makefile > Makefile.tmp
make -f Makefile.tmp install

cd $ffmpeg_dir
git clone https://github.com/FFmpeg/FFmpeg.git	
cd $ffmpeg_dir/FFmpeg
git checkout 588114cea4ee434c9c61353ed91ffc817d2965f5

PATH="$ffmpeg_dir/bin:$PATH" PKG_CONFIG_PATH="$ffmpeg_dir/build/lib/pkgconfig" ./configure --prefix=${ffmpeg_dir}/build --extra-cflags=-I${ffmpeg_dir}/build/include --extra-ldflags=-L${ffmpeg_dir}/build/lib --bindir=${ffmpeg_dir}/bin --enable-cuda-nvcc --enable-cuvid --enable-libnpp --extra-cflags=-I/usr/local/cuda/include/ --extra-ldflags=-L/usr/local/cuda/lib64/ --enable-gpl --enable-nvenc --enable-libx264 --enable-libx265 --enable-nonfree --enable-shared
PATH="$ffmpeg_dir/bin:${PATH}:/usr/local/cuda/bin" make && make install && hash -r
```

Now build the bird recording package:
```
cd /bird_packages/Documents/birds
perl -i -p -e 's|https://(.*?)/|git@\1:|g' .gitmodules
git submodule sync
git submodule update --init
git submodule update --merge
./update_submodules.bash
```

Copy a patch for the ```ffmpeg_image_transport_tools``` and ```bird_recording``` packages:
```
cp ./birds_patch/src/ffmpeg_image_transport_tools/src/* /bird_packages/Documents/birds/src/ffmpeg_image_transport_tools/src/.
cp ./birds_patch/src/ffmpeg_image_transport_tools/launch/* /bird_packages/Documents/birds/src/ffmpeg_image_transport_tools/launch/.
cp ./birds_patch/src/bird_recording/launch/* /bird_packages/Documents/birds/src/bird_recording/launch/.
```

```
catkin config -DCMAKE_BUILD_TYPE=Release -DFFMPEG_LIB="${ffmpeg_dir}/build/lib" -DFFMPEG_INC="${ffmpeg_dir}/build/include"
catkin build -c
```

Download [this zip file](https://drive.google.com/file/d/1W1swUMkcBbTWIhB9AZDyzFrYcqF7t-j_/view?usp=sharing) and scp it into ```/scratch/bird_packages/Documents/birds/src/bird_recording/current.zip``` and unzip it:
```
cd /bird_packages/Documents/birds/src/bird_recording
unzip current.zip
```