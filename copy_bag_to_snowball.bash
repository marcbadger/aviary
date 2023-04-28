#!/bin/bash

BAG_DIR=$1
BAG_NAME=$2
MD5_FILE="$BAG_DIR/$BAG_NAME.md5sum"
if test -f "$MD5_FILE";
then
    MD5_VAL="$(cat "$BAG_DIR/$BAG_NAME.md5sum")" 
    MD5_B64="$((echo 0:; echo -n $(echo $MD5_VAL)) | xxd -rp -l 16 | base64 )"
else
    MD5SUM=$(md5sum "$BAG_DIR/$BAG_NAME" | cut -f1 -d' ')
	echo "$MD5SUM" >> "$BAG_DIR/$BAG_NAME.md5sum"
	MD5_VAL="$(cat "$BAG_DIR/$BAG_NAME.md5sum")" 
    MD5_B64="$((echo 0:; echo -n $(echo $MD5_VAL)) | xxd -rp -l 16 | base64 )"
fi

echo aws s3api put-object --bucket kostas-group-neural-bases-of-song-test --key $BAG_NAME --body "${BAG_DIR}/${BAG_NAME}" --content-md5 "$MD5_B64"
