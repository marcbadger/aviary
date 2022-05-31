#!/bin/bash

BIRD_DIR=$1 # /birds/aviary/data or /archive/birds/aviary/data
BIG_BAG=$2 # the bag basename without the path
DEST_DIR=$3 # /archive/birds/aviary/data2019/whole_bags
SLICES_DIR=$DEST_DIR/../long_videos/female_annotations_dataset
CHECK_MD5=false

BAG_YEAR=${BIG_BAG:7:4}

# Copy bag over and slice if bag is 2019
# Else just slice (since the large bag is accessible from a job)
if [ "$BAG_YEAR" = "2019" ]; then
	
	BAG_PATH=$BIRD_DIR/$BIG_BAG
	DEST_BAG=$DEST_DIR/$BIG_BAG

	if test -f "$DEST_BAG"; then
		echo "$DEST_BAG already exists. Skipping to slicing."
	else
		echo "Copying $BIG_BAG from $BIRD_DIR to $DEST_DIR"

		cp $BAG_PATH $DEST_BAG

		if [ "$CHECK_MD5" == true ]; then
			echo "Checking md5sum"
			MD5SUM=$(md5sum $BAG_PATH | cut -f1 -d' ')
			NEW_MD5SUM=$(md5sum $DEST_BAG | cut -f1 -d' ')
			if [ "$MD5SUM" = "$NEW_MD5SUM" ]; then
				echo "md5sum matched"
				echo "$NEW_MD5SUM" >> "$DEST_BAG.md5sum"
			else
				echo "md5sum failed to match investigate further"
				echo "Bag copying failed for $BIG_BAG" >> $DEST_BAG.fail
				return
			fi
		fi
	fi

	# Launch a job to slice hours from bag
	echo "Launching slicing job for $BIG_BAG"
	cat ~/aviary/bag_handling/$BIG_BAG.slices

	# This launches a job and container, which runs the slice_bags_cluster.bash
	# script, which runs slice_bag_from_list.py with inputs:
	#  --timing file $BIG_BAG.slices (it is going to look for these in ~/aviary/bag_handling)
	#  --out_dir /archive/birds/aviary/data2019/long_videos/female_annotations_dataset
	#  --bag_name $DEST_DiR/$BIG_BAG
	sbatch --wait sbatch_slice_bags_for_tgia_cluster.bash $DEST_DIR $BIG_BAG $SLICES_DIR

	# rm $DEST_BAG

else

	# Launch a job to slice hours from bag
	echo "Launching slicing job for $BIG_BAG"
	cat ~/aviary/bag_handling/$BIG_BAG.slices

	# This launches a job and container, which runs the slice_bags_cluster.bash
	# script, which runs slice_bag_from_list.py with inputs:
	#  --timing file $BIG_BAG.slices (it is going to look for these in ~/aviary/bag_handling)
	#  --out_dir /archive/birds/aviary/data2019/long_videos/tgia_dataset
	#  --bag_name $DEST_DIR/$BIG_BAG
	sbatch --wait sbatch_slice_bags_for_tgia_cluster.bash $BIRD_DIR $BIG_BAG $SLICES_DIR

fi
