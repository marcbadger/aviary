#!/bin/bash

#SBATCH --time=48:00:00
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute

# collect the inputs
DATA_DIR=$1 # "/archive/birds/aviary/data"
BAGS_LIST=$2 # "/home/marc/aviary/bag_handling/critical_bag_list_2020.txt"

BIG_BAG=$(cat $BAGS_LIST | head -$SLURM_ARRAY_TASK_ID | tail -1)
DEST_BAG=$DATA_DIR/$BIG_BAG

echo "Checking $BIG_BAG"
MD5SUM=$(md5sum $DEST_BAG | cut -f1 -d' ')
echo "$MD5SUM" >> "$DEST_BAG.md5sum"