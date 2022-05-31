#!/bin/bash

#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --qos=low
#SBATCH --partition=compute

# Specify folder containing large bags:
# Example: /archive/birds/aviary/data2019/whole_bags (2019) or /archive/birds/aviary/data (2020)
BIG_BAG_DIR=$1 

# Specify the bag name:
# Example: aviary_2019-05-15-04-59-08.bag
BIG_BAG=$2

# Specify where the sliced bags should be saved:
# Example: /archive/birds/aviary/data2019/example_dataset
DEST_DIR=$3

# Specify where the timing file is:
# Example: ${DEST_DIR}/${BIG_BAG}.slices
TIMING_FILE=$4

eval "$(conda shell.bash hook)"
conda activate slicing

echo "Starting slicing job for $BIG_BAG"
python bag_slicing/slice_bag_into_chunks.py ${BIG_BAG_DIR}/${BIG_BAG} --timing_file ${TIMING_FILE} --out_dir ${DEST_DIR}

