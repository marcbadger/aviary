#!/bin/bash

#SBATCH --gpus=rtx2080ti:1
#SBATCH --cpus-per-gpu=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --nodelist=node-2080ti-3
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute

# collect the inputs
TARGET_DIR=$1 # this should be /archive/birds/aviary/data2019/frames_around_annotations
DEST_DIR=$2 # this should be /archive/birds/aviary/data2019/frames_around_annotations
TARGET_BAG=$3

# set some enviornment variables
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

# this script just calls export_images_and_audio.[bash/py] with inputs:
#   --TARGET_DIR the directory containing the small bags
#	--DEST_DIR the destination for the extracted images
# 	--TARGET_BAG the target bag

# set the docker container parameters
CONTAINER_NAME="birds-frame-exporting"
CONTAINER_IMAGE="marcbadger/frame_exporting:birds"
EXTRA_MOUNTS="/scratch/bird_packages:/bird_packages,/archive/birds/aviary/data2019:/archive/birds/aviary/data2019,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER"

COMMAND="/bin/bash /home/marc/aviary/bag_handling/export_all_frames.bash $TARGET_DIR $DEST_DIR $TARGET_BAG"

srun --container-mount-home\
     --container-mounts=${EXTRA_MOUNTS}\
     --container-name=${CONTAINER_NAME}\
     --container-image=${CONTAINER_IMAGE}\
     --no-container-remap-root\
     ${COMMAND}
