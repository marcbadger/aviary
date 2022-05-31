#!/bin/bash

export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

# Copy over a bunch of libraries that we need
# This is a hack because SLURM overwrites lib for some reason...
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/kostas_rsa

ssh-keygen -f "/home/$USER/.ssh/known_hosts" -R "$( hostname )"

scp -oStrictHostKeyChecking=no $( hostname ):/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.???.* /usr/lib/x86_64-linux-gnu/.
scp -oStrictHostKeyChecking=no $( hostname ):/usr/lib/x86_64-linux-gnu/libnvcuvid.so.???.* /usr/lib/x86_64-linux-gnu/.

ln -sf /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.???.* /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1
ln -sf /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so

ln -sf /usr/lib/x86_64-linux-gnu/libnvcuvid.so.???.* /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1
ln -sf /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1 /usr/lib/x86_64-linux-gnu/libnvcuvid.so

# ln -s /bird_packages/libnvidia-encode.so.440.82 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1
# ln -s /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 /usr/lib/x86_64-linux-gnu/libnvidia-encode.so

# ln -s /bird_packages/libnvcuvid.so.440.82 /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1
# ln -s /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1 /usr/lib/x86_64-linux-gnu/libnvcuvid.so

export PATH=$PATH:/bird_packages/Documents/ffmpeg/bin

source /opt/ros/melodic/setup.bash
source /bird_packages/Documents/birds/devel/setup.bash --extend
source /bird_packages/catkin_build_ws/install/setup.bash --extend


# Specify folder containing sliced bags:
# Example: /archive/birds/aviary/data2019/example_dataset
TARGET_DIR=$1

# Specify where the sliced bags should be saved:
# Example: /archive/birds/aviary/data2019/example_dataset
DEST_DIR=$2

echo "Number of arguments: $#"

if [[ $# -eq 3 ]] ; then

	TARGET_BAG=$3

	cd ~/aviary/bag_handling
	echo "Exporting everything from target bag: $TARGET_BAG"
	python3 export_images_and_audio.py --target_dir=$TARGET_DIR --dest_dir=$DEST_DIR --target_bag=$TARGET_BAG --export separate mosaic spectrogram

else

	TID=$3
	TMAX=$4

	# We could split bags among tasks in bash, but it will be easier in python...
	cd ~/aviary/bag_handling
	echo "Exporting frames from bags with task ID: $TID/$TMAX"
	python3 export_images_and_audio.py --target_dir=$TARGET_DIR --dest_dir=$DEST_DIR --task_id=$TID --num_tasks=$TMAX --export separate mosaic

fi

exit 0