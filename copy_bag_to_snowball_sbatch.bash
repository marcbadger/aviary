#!/bin/bash

#SBATCH --time=48:00:00
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute
#SBATCH --spread-job
#SBATCH --exclude=node-1080ti-[0-2],node-2080ti-0,node-3090-3,node-v100-0

# collect the inputs
BAG_DIR=$1 # "/archive/birds/aviary/data" or "/archive/birds/aviary/data2019/whole_bags"
BAGS_LIST=$2 # "/home/marc/aviary/bag_handling/critical_bag_list_2020.txt" or "/home/marc/aviary/bag_handling/critical_bag_list_2019.txt"
BUCKET=$3 # kostas-group-neural-bases-of-song-2019-critical or kostas-group-neural-bases-of-song-2020-critical

BAG_NAME=$(cat $BAGS_LIST | head -$SLURM_ARRAY_TASK_ID | tail -1)
BAG_FILE=$BAG_DIR/$BAG_NAME
MD5_FILE="$BAG_FILE.md5sum"
if test -f "$MD5_FILE";
then
    MD5_VAL="$(cat "$MD5_FILE")" 
    MD5_B64="$( (echo 0:; echo -n $(echo $MD5_VAL)) | xxd -rp -l 16 | base64 )"
    COMMAND="aws s3api put-object --profile snowballEdge --endpoint http://192.168.123.72:8080 --region snow --bucket ${BUCKET} --key ${BAG_NAME} --body ${BAG_FILE} --content-md5 $MD5_B64"
else
    COMMAND="aws s3api put-object --profile snowballEdge --endpoint http://192.168.123.72:8080 --region snow --bucket ${BUCKET} --key ${BAG_NAME} --body ${BAG_FILE}"
fi

echo ${COMMAND}

srun --container-mount-home \
	 --container-name="awscli" \
	 --container-image="amazon/aws-cli:latest" \
	 --container-mounts="/archive/birds/aviary:/archive/birds/aviary,/archive/$USER:/archive/$USER" \
	 --no-container-remap-root \
	 ${COMMAND}
