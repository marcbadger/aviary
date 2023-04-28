#!/bin/bash

# collect files that match $1 (BIG_BAG)

# then either start a job array with that many slots or
# work on parallelizing extract_everything_cluster_bash

#SBATCH --gpus=1
#SBATCH --cpus-per-gpu=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute

export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

CONTAINER_NAME="birds-complete"
CONTAINER_IMAGE="adarshmodh/birds:complete"
EXTRA_MOUNTS="/scratch/bird_packages:/bird_packages,/archive/birds/aviary/data2019:/archive/birds/aviary/data2019,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER"

TARGET_DIR=$1
TARGET_DATE=$2

# extract_everything_cluster.bash just calls export_images_and_audio.py with inputs:
#  --target_dir e.g. /archive/birds/aviary/data2019/long_videos/tgia_dataset
#  --target_date e.g. 2020-04-03

COMMAND="/bin/bash /home/marc/aviary/bag_handling/extract_everything_cluster.bash $TARGET_DIR $TARGET_DATE"

echo "Starting export jobs for $TARGET_DATE"

srun --container-mount-home\
     --container-mounts=${EXTRA_MOUNTS}\
     --container-name=${CONTAINER_NAME}\
     --container-image=${CONTAINER_IMAGE}\
     --no-container-remap-root\
     ${COMMAND}
