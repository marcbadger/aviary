#!/bin/bash

write_md5sum () {

	local BIG_BAG=$1 # the bag basename without the path
	DEST_DIR="/archive/birds/aviary/data2019/whole_bags"
	local DEST_BAG=$DEST_DIR/$BIG_BAG

	echo "Checking $BIG_BAG"
	local MD5SUM=$(md5sum $DEST_BAG | cut -f1 -d' ')
	echo "$MD5SUM" >> "$DEST_BAG.md5sum"

}

inputfile=$1

while IFS= read -r line
do
	write_md5sum "$line"
done < "$inputfile"
