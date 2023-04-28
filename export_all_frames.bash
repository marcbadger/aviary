#!/bin/bash

export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

# Copy over a bunch of libraries that we need
# This is a hack because SLURM overwrites lib for some reason...
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/kostas_rsa

scp $( hostname ):/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.???.* /usr/lib/x86_64-linux-gnu/.
scp $( hostname ):/usr/lib/x86_64-linux-gnu/libnvcuvid.so.???.* /usr/lib/x86_64-linux-gnu/.

ln -sf /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.???.* /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1
ln -sf /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so

ln -sf /usr/lib/x86_64-linux-gnu/libnvcuvid.so.???.* /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1
ln -sf /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1 /usr/lib/x86_64-linux-gnu/libnvcuvid.so

# ln -s /bird_packages/libnvidia-encode.so.440.82 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1
# ln -s /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so

# ln -s /bird_packages/libnvcuvid.so.440.82 /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1
# ln -s /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1 /usr/lib/x86_64-linux-gnu/libnvcuvid.so

export PATH=$PATH:/aviary/ffmpeg/bin

source /opt/ros/melodic/setup.bash
source /aviary/birds/devel/setup.bash --extend
source /bird_packages/catkin_build_ws/install/setup.bash --extend

# These are our inputs:
TARGET_DIR=$1 #"/archive/birds/aviary/data2019/long_videos/female_annotations_dataset"
DEST_DIR=$2 #"/archive/birds/aviary/data2019/long_videos/female_annotations_dataset"

echo "Number of arguments: $#"

if [[ $# -eq 3 ]] ; then

	TARGET_BAG=$3

	cd ~/aviary/bag_handling
	echo "Exporting everything from target bag: $TARGET_BAG"
	python export_images_and_audio.py --target_dir=$TARGET_DIR --dest_dir=$DEST_DIR --target_bag=$TARGET_BAG --export allframes

else

	TID=$3
	TMAX=$4

	# We could split bags among tasks in bash, but it will be easier in python...
	cd ~/aviary/bag_handling
	echo "Exporting frames from bags with task ID: $TID/$TMAX"
	python export_images_and_audio.py --target_dir=$TARGET_DIR --dest_dir=$DEST_DIR --task_id=$TID --num_tasks=$TMAX --export allframes

fi

exit 0