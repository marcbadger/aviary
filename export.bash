#!/bin/bash

TARGET_DIR=$1 # /archive/birds/aviary/data2019/long_videos/tgia_dataset
TARGET_DATE=$2 # the target date 2020-05-01 e.g.

# Launch a job to export images and audio for each slice
echo "Launching export job for $TARGET_DATE"

sbatch --wait sbatch_extract_everything_cluster.bash $TARGET_DIR $TARGET_DATE

echo "Finished"