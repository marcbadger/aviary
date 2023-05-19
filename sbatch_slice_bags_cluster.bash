#!/bin/bash

#SBATCH --output=log.out
#SBATCH --job-name=any_name_you_want
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --qos=normal
#SBATCH --partition=batch

# 06:00:00
# kostas-med
# kostas-compute

unset NVIDIA_VISIBLE_DEVICES
unset NVIDIA_DRIVER_CAPABILITIES

CONTAINER_NAME="python-ros"
CONTAINER_IMAGE="osrf/ros:melodic-desktop-full-bionic"
EXTRA_MOUNTS="/scratch/bird_packages:/bird_packages,/archive/birds/aviary:/archive/birds/aviary,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER"

BAG_DIR=$1 # /archive/birds/aviary/data2019/long_videos (2019) or /archive/birds/aviary/data (2020)
BIG_BAG=$2
DEST_DIR=$3 # /archive/birds/aviary/data2019/long_videos/tgia_dataset

# slice_bags_cluster.bash just calls slice_bag_from_list.py with inputs:
#  --timing file $BIG_BAG.slices
#  --out_dir $DEST_DIR
#  --bag_name $BAG_DIR/$BIG_BAG

COMMAND="/bin/bash /home/marc/aviary/bag_handling/slice_bags_cluster.bash $BAG_DIR $BIG_BAG $DEST_DIR"

echo "Starting slicing job for $BIG_BAG"

srun --container-mount-home\
     --container-mounts=${EXTRA_MOUNTS}\
     --container-name=${CONTAINER_NAME}\
     --container-image=${CONTAINER_IMAGE}\
     --no-container-remap-root\
     ${COMMAND}
