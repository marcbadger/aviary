#!/bin/bash

#SBATCH --time=48:00:00
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute
#SBATCH --cpus-per-task=8

# collect the inputs
BAG_DIR=$1 # "/archive/birds/aviary/data" or "/archive/birds/aviary/data2019/whole_bags"
BAGS_LIST=$2 # "/home/marc/aviary/bag_handling/critical_bag_list_2020.txt" or "/home/marc/aviary/bag_handling/critical_bag_list_2019.txt"
BUCKET=$3 # kostas-group-neural-bases-of-song-2019-critical or kostas-group-neural-bases-of-song-2020-critical

BAG_NAME=$(cat $BAGS_LIST | head -$SLURM_ARRAY_TASK_ID | tail -1)
BAG_FILE=$BAG_DIR/$BAG_NAME

COMMAND="aws s3 cp ${BAG_FILE} s3://${BUCKET} --profile snowballEdge --endpoint http://192.168.123.55:8080 --region snow"

echo ${COMMAND}

srun --container-mount-home \
	 --container-name="awscli" \
	 --container-image="amazon/aws-cli:latest" \
	 --container-mounts="/archive/birds/aviary:/archive/birds/aviary,/archive/$USER:/archive/$USER" \
	 --no-container-remap-root \
	 ${COMMAND}