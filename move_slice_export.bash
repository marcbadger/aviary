#!/bin/bash

BIRD_DIR=$1 # /birds/aviary/data or /archive/birds/aviary/data
BIG_BAG=$2 # the bag basename without the path
DEST_DIR=$3 # /archive/birds/aviary/data2019/long_videos/tgia_dataset

BAG_YEAR=${BIG_BAG:7:4}

# Copy bag over and slice if bag is 2019
# Else just slice (since the large bag is accessible from a job)
if [ "$BAG_YEAR" = "2019" ]; then
	
	echo "Copying $BIG_BAG from $BIRD_DIR to $DEST_DIR"

	BAG_PATH=$BIRD_DIR/$BIG_BAG
	DEST_BAG=$DEST_DIR/$BIG_BAG

	MD5SUM=$(md5sum $BAG_PATH | cut -f1 -d' ')
	cp $BAG_PATH $DEST_BAG
	NEW_MD5SUM=$(md5sum $DEST_BAG | cut -f1 -d' ')
	if [ "$MD5SUM" = "$NEW_MD5SUM" ]; then
		echo "md5sum matched"
	else
		echo "md5sum failed to match investigate further"
		echo "Bag copying failed for $BIG_BAG" >> $DEST_BAG.log
		return
	fi

	# Launch a job to slice hours from bag
	echo "Launching slicing job for $BIG_BAG"
	cat ~/aviary/bag_handling/$BIG_BAG.slices

	# This launches a job and container, which runs the slice_bags_cluster.bash
	# script, which runs slice_bag_from_list.py with inputs:
	#  --timing file $BIG_BAG.slices (it is going to look for these in ~/aviary/bag_handling)
	#  --out_dir /archive/birds/aviary/data2019/long_videos/tgia_dataset
	#  --bag_name $DEST_DiR/$BIG_BAG
	sbatch --wait sbatch_slice_bags_cluster.bash $DEST_DIR $BIG_BAG $DEST_DIR

	rm $DEST_BAG

else

	# Launch a job to slice hours from bag
	echo "Launching slicing job for $BIG_BAG"
	cat ~/aviary/bag_handling/$BIG_BAG.slices

	# This launches a job and container, which runs the slice_bags_cluster.bash
	# script, which runs slice_bag_from_list.py with inputs:
	#  --timing file $BIG_BAG.slices (it is going to look for these in ~/aviary/bag_handling)
	#  --out_dir /archive/birds/aviary/data2019/long_videos/tgia_dataset
	#  --bag_name $DEST_DiR/$BIG_BAG
	sbatch --wait sbatch_slice_bags_cluster.bash $BIRD_DIR $BIG_BAG $DEST_DIR

fi

# Sleep for 1 min to allow the job to clear so resources will be available
sleep 1m

# Now that we have a bunch of bag slices, we launch a bunch of jobs to export images and audio

# srun --qos low --mem=32G --cpus-per-task=8 --container-mount-home --container-image=osrf/ros:melodic-desktop-full-bionic --container-mounts="/scratch/bird_packages:/bird_packages,/archive/birds/aviary/data2019:/archive/birds/aviary/data2019,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER" --no-container-remap-root --pty bash

# BAG_DIR=$DEST_DIR

# source /bird_packages/Documents/birds/devel/setup.bash
# source /bird_packages/catkin_build_ws/install/setup.bash --extend

# cd ~/aviary/bag_handling
# python slice_bag_from_list.py --timing_file $BIG_BAG.slices --out_dir /archive/birds/aviary/data2019/long_videos/tgia_dataset --chunk_threshold 10000000 $BAG_DIR/$BIG_BAG

# Launch a job to export images and audio for each slice
echo "Launching export job for $BIG_BAG"

TARGET_DIR=$DEST_DIR # /archive/birds/aviary/data2019/long_videos/tgia_dataset
TARGET_DATE=${BIG_BAG:7:10}

sbatch --wait sbatch_extract_everything_cluster.bash $TARGET_DIR $TARGET_DATE

echo "Finished"