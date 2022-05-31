#!/bin/bash

#SBATCH --requeue
#SBATCH --gpus=rtx2080ti:1
#SBATCH --cpus-per-gpu=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --qos=low
#SBATCH --partition=compute
#SBATCH --array=0-7

# collect the inputs
TARGET_DIR=$1 # "/archive/birds/aviary/data2019/long_videos/female_annotations_dataset"

echo "Exporting wv for $SLURM_ARRAY_TASK_ID"

python re_export_wv.py $TARGET_DIR $SLURM_ARRAY_TASK_ID 8