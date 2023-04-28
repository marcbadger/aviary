#!/bin/bash

#SBATCH --gpus=rtx2080ti:1
#SBATCH --cpus-per-gpu=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --array=0-12
#SBATCH --qos=normal
#SBATCH --partition=batch

# collect the inputs
TARGET_DIR=$1 # this should be /archive/birds/aviary/data2019/frames_around_annotations
DEST_DIR=$2 # this should be /archive/birds/aviary/data2019/frames_around_annotations

# set some enviornment variables
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

# this script just calls extract_frames_from_bags.[bash/py] with inputs:
#   --TARGET_DIR the directory containing the small bags
#	--DEST_DIR the destination for the extracted images
# 	--SLURM_ARRAY_TASK_ID the id of the task within the task array
#	--SLURM_ARRAY_TASK_MAX the max task array

# extract_frames_from_bags.py will:
#  - collect a list of bag files in TARGET_DIR
#  - select the files that correspond to 
#    $SLURM_ARRAY_TASK_ID out of $SLURM_ARRAY_TASK_MAX
#  - check which bags have already been completed
#  - call ffmpeg_image_transport_tools decode_bag on this list

# set the docker container parameters
CONTAINER_NAME="birds-frame-exporting"
CONTAINER_IMAGE="marcbadger/frame_exporting:birds"
EXTRA_MOUNTS="/scratch/bird_packages:/bird_packages,/archive/birds/aviary/data2019:/archive/birds/aviary/data2019,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER"

COMMAND="/bin/bash /home/marc/aviary/bag_handling/export_images_and_audio.bash $TARGET_DIR $DEST_DIR $SLURM_ARRAY_TASK_ID $SLURM_ARRAY_TASK_MAX"

srun --container-mount-home\
     --container-mounts=${EXTRA_MOUNTS}\
     --container-name=${CONTAINER_NAME}\
     --container-image=${CONTAINER_IMAGE}\
     --no-container-remap-root\
     ${COMMAND}
