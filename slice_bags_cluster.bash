#!/bin/bash

BAG_DIR=$1
BIG_BAG=$2
DEST_DIR=$3

source /bird_packages/Documents/birds/devel/setup.bash
source /bird_packages/catkin_build_ws/install/setup.bash --extend

cd ~/aviary/bag_handling
python slice_bag_from_list.py --timing_file $BIG_BAG.slices --out_dir $DEST_DIR --chunk_threshold 10000000 $BAG_DIR/$BIG_BAG

exit 0