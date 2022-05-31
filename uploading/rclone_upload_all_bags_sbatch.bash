#!/bin/bash

#SBATCH --time=48:00:00
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute
#SBATCH --cpus-per-task=4
#SBATCH --exclude=node-3090-3,node-v100-0

# collect the inputs
DATA_DIR=$1 # "/archive/birds/aviary/data2019/whole_bags"
AGENTS_LIST=$2 # "/home/marc/aviary/bag_handling/rclone_upload_agents.txt"
AGENT_NUM=$3 # "1-5"
NUM_AGENTS=$4 # "5"
BAGS_LIST=$5 # "/home/marc/aviary/bag_handling/rclone_all_bags.txt"

# we read every NUM_AGENTS line of BAG_LIST
# and create a SLURM array for that agent
AGENT=$(cat $AGENTS_LIST | head -$AGENT_NUM | tail -1)
BAGNAME=$(sed -n ${AGENT_NUM}~${NUM_AGENTS}p $BAGS_LIST | head -$SLURM_ARRAY_TASK_ID | tail -1)

#echo "+ $BAGNAME" > ${TMP_FILE}
#echo "+ $BAGNAME.md5sum" >> ${TMP_FILE}
#echo "- *" >> ${TMP_FILE}

#COMMAND="rclone -vv --dry-run copy --config ${AGENT} --filter-from ${TMP_FILE} ${DATA_DIR} aviary:BACKUP_BAGS"

COMMAND="rclone -vv copy --config ${AGENT} --include ${BAGNAME} --include ${BAGNAME}.md5sum ${DATA_DIR} aviary:BACKUP_BAGS"

echo ${COMMAND}

srun --container-mount-home \
	 --container-image="marcbadger/frame_exporting:rclone" \
     --container-mounts="/archive/birds/aviary:/archive/birds/aviary,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER" \
     --no-container-remap-root \
     ${COMMAND}
