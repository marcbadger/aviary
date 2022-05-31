#!/bin/bash

#SBATCH --time=48:00:00
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute

# collect the inputs
DATA_DIR=$1 # "/archive/birds/aviary/data2019/whole_bags"
AGENTS_LIST=$2 # "/home/marc/aviary/bag_handling/rclone_upload_agents.txt"
BAGS_LIST=$3 # "/home/marc/aviary/bag_handling/rclone_upload_bags_list_2021-11-23.txt"

AGENT=$(cat $AGENTS_LIST | head -$SLURM_ARRAY_TASK_ID | tail -1)
BAGNAME=$(cat $BAGS_LIST | head -$SLURM_ARRAY_TASK_ID | tail -1)
TMP_FILE="/home/marc/aviary/bag_handling/${BAGNAME}.rclone_backup.txt"

#echo "+ $BAGNAME" > ${TMP_FILE}
#echo "+ $BAGNAME.md5sum" >> ${TMP_FILE}
#echo "- *" >> ${TMP_FILE}

#COMMAND="rclone -vv --dry-run copy --config ${AGENT} --filter-from ${TMP_FILE} ${DATA_DIR} aviary:BACKUP_BAGS"

COMMAND="rclone -vv copy --config ${AGENT} --include ${BAGNAME} --include ${BAGNAME}.md5sum ${DATA_DIR} aviary:BACKUP_BAGS"

echo ${COMMAND}

srun --container-mount-home \
	 --container-name="rsync" \
	 --container-image="marcbadger/frame_exporting:rclone" \
	 --container-mounts="/scratch/bird_packages:/bird_packages,/archive/birds/aviary:/archive/birds/aviary,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER" \
	 --no-container-remap-root \
	 ${COMMAND}
