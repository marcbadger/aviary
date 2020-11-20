#!/bin/bash



# Copy over a bunch of libraries that we need
# This is a hack because SLURM overwrites lib for some reason...
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



# These are our inputs:

TARGET_DIR=$1 # /archive/birds/aviary/data2019/whole_bags
DEST_DIR=$2 # /archive/birds/aviary/data2019/frames_around_annotations
# these should already exist (maybe):
SLURM_ARRAY_TASK_ID=$3
SLURM_ARRAY_TASK_MAX=$4


# We could do this in bash, but it will be easier in python...

cd /bird_packages/aviary/bag_handling

echo "exporting frames from bags with task ID: $SLURM_ARRAY_TASK_ID"

python extract_frames_from_bags.py --target_dir=$TARGET_DIR --dest_dir=$DEST_DIR --task_id=$SLURM_ARRAY_TASK_ID --num_tasks=$SLURM_ARRAY_TASK_MAX

exit 0