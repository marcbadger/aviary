#!/bin/bash

copy_bag () {

	local BIG_BAG=$1 # the bag basename without the path

	BIRD_DIR="/birds/aviary/data"
	DEST_DIR="/archive/birds/aviary/data2019/whole_bags"
	local CHECK_MD5=$2

	move_completed_list="/archive/birds/aviary/move_to_archive_completed_list.txt"

	echo "Copying $BIG_BAG from $BIRD_DIR to $DEST_DIR"

	local BAG_PATH=$BIRD_DIR/$BIG_BAG
	local DEST_BAG=$DEST_DIR/$BIG_BAG

	if test -f "$DEST_BAG"; then
		echo "$DEST_BAG already exists. Are you sure you want to do this?"
		echo "Maybe check md5sum instead?"
	else
		cp $BAG_PATH $DEST_BAG
		echo "Copying done"
	fi

	if [ "$CHECK_MD5" = true ]; then
		echo "Checking md5sum"
		local MD5SUM=$(md5sum $BAG_PATH | cut -f1 -d' ')
		local NEW_MD5SUM=$(md5sum $DEST_BAG | cut -f1 -d' ')
		if [ "$MD5SUM" = "$NEW_MD5SUM" ]; then
			echo "md5sum matched"
			mv $BAG_PATH "$BAG_PATH.back"
			echo "$NEW_MD5SUM" >> "$DEST_BAG.md5sum"
			echo "Bag copied to $DEST_BAG"
			echo "You can now delete $BAG_PATH.back"
			echo "$BIG_BAG" >> "$move_completed_list"
		else
			echo "md5sum failed to match investigate further"
			echo "Bag copying failed for $BIG_BAG" >> "$DEST_BAG.fail"
		fi

	else
		echo "bag copied without checking md5sum"
	fi
}

inputfile=$1
checkmd5=$2

copy_bag "$inputfile" "$checkmd5"
