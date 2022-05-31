#!/bin/bash

TARGET_DIR=$1 # /archive/birds/aviary/data2019/long_videos/tgia_dataset
TARGET_DATE=$2

eval "$(ssh-agent -s)"
ssh-add ~/.ssh/kostas_rsa

scp $( hostname ):/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.???.* /usr/lib/x86_64-linux-gnu/.
scp $( hostname ):/usr/lib/x86_64-linux-gnu/libnvcuvid.so.???.* /usr/lib/x86_64-linux-gnu/.

ln -s /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.???.* /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1
ln -s /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so

ln -s /usr/lib/x86_64-linux-gnu/libnvcuvid.so.???.* /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1
ln -s /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1 /usr/lib/x86_64-linux-gnu/libnvcuvid.so

# ln -s /bird_packages/libnvidia-encode.so.440.82 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1
# ln -s /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so

# ln -s /bird_packages/libnvcuvid.so.440.82 /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1
# ln -s /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1 /usr/lib/x86_64-linux-gnu/libnvcuvid.so

source /bird_packages/Documents/birds/devel/setup.bash
source /bird_packages/catkin_build_ws/install/setup.bash --extend

export PATH=$PATH:/aviary/ffmpeg/bin

cd ~/aviary/bag_handling

echo "exporting images and audio"

python export_images_and_audio.py --target_dir=$TARGET_DIR --target_date=$TARGET_DATE

# python export_images_and_audio.py --target_dir=$TARGET_DIR --target_bag=$TARGET_BAG


exit 0
