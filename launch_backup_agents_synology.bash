DATA_DIR=/mnt/birds/aviary/data
AGENTS_LIST=/home/marc/aviary/bag_handling/rclone_upload_agents_2.txt
BAGS_LIST=/home/marc/aviary/bag_handling/rclone_bags_to_do_synology.txt
NUM_AGENTS=$(cat $AGENTS_LIST | wc -l)

for AGENT_NUM in $(eval echo "{1..${NUM_AGENTS}}")
do
	NUM_TO_DO=$(sed -n ${AGENT_NUM}~${NUM_AGENTS}p rclone_bags_to_do.txt | wc -l)
	sbatch --array 1-${NUM_TO_DO}%1 -w node-2080ti-1 rclone_upload_all_bags_sbatch_synology.bash $DATA_DIR $AGENTS_LIST $AGENT_NUM $NUM_AGENTS $BAGS_LIST
done