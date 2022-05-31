SEQUENCE=$1

COMMAND="rclone -vv copy --config /home/marc/aviary/bag_handling/rclone.conf --include /*_top.mp4 --include /*_bot.mp4 --include /*_all.mp4 /archive/birds/aviary/data2019/long_videos/female_annotations_dataset/${SEQUENCE} aviary:datasets/social_network_dataset/${SEQUENCE}"
echo $COMMAND
srun -w node-2080ti-1 --partition kostas-compute --qos kostas-med --time 24:00:00 --container-mount-home --container-image=marcbadger/frame_exporting:rclone --container-mounts="/archive/birds/aviary:/archive/birds/aviary,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER" --no-container-remap-root --pty $COMMAND
