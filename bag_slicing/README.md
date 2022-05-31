# Step 1: Bag Slicing
Large bags need to be split up so that we can actually work with them.

## Cluster information
Recordings from the aviary are in a few places:
| Year | Location on kostas-ap.seas.upenn.edu |
| --- | --- |
| 2019 | ```/archive/birds/aviary/data2019``` |
| 2020 | ```/archive/birds/aviary/data``` |
| 2022 | ```/archive/birds/aviary/data2022``` |

To work with the bags, you will need to start a 'job' on the cluster, which will allocate computational resources to you.

## How to start a job
The bash scripts below contain example scripts for launching jobs with appropriate docker images, but if you want to modify them or learn more about how it works, refer to the cluster tutorials for [how to launch interactive and batch jobs](https://github.com/daniilidis-group/cluster_tutorials/tree/master/slurm_intro) and [how to launch jobs that require a docker image](https://github.com/daniilidis-group/cluster_tutorials/tree/master/pyxis).

## How to slice bags
To slice bags, you will use the ```exporting``` conda environment. You do not need a GPU, so you do not need to ask for one. The bash script [slice_bag_into_chunks_sbatch.bash](slice_bags_cluster_sbatch.bash) tells sbatch to launch a job with 8 cpus, 16G of memory, that will last for 4 hours.
```
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --qos=low
#SBATCH --partition=compute
```
and then runs a python script [slice_bag_into_chunks.py](slice_bag_into_chunks.py).

Note that videos are stored using h.265 encoding and the image messages in the rosbag are not the raw images.  They are instead "keyframes" (i.e. an entire image) and "differences". As we read image messages and decode them we won’t get any "real" images until a keyframe is encountered. Thus the first complete set of images for a given slice will not occur until about 0.3 seconds (12 frames) after the start rostime. To ensure we are not skipping frames between back-to-back chunks, we extend the end time of each chunk past the next chunk's start time by some small duration. Default is 0.5 seconds or 20 frames, and is specified in [slice_bag_into_chunks.py](slice_bag_into_chunks.py).

Finally, we can launch the job by running the following on ```kostas-ap```:
```
CHUNK_DUR=5
BIG_BAG_DIR=/archive/birds/aviary/data2019/whole_bags
BIG_BAG=aviary_2019-05-15-04-59-08.bag
DEST_DIR=/archive/birds/aviary/data2019/example_dataset
sbatch slice_bag_into_chunks_sbatch.bash $BIG_DIR $BIG_BAG $DEST_DIR $CHUNK_DUR
```
where ```BIG_DIR``` is the folder containing the large bag ```BIG_BAG``` that you copied over from aviary-1 previously, ```DEST_DIR``` is the folder where the bag slices will get saved, and ```CHUNK_DUR``` is the chunk duration in **MINUTES**.

If you are exporing slices from the afternoon, it might take longer than 4 hours to step through all the messages in order to get to the ones you want to save. In that case you can modify the command you use when you run the sbatch script below to this:
```
sbatch --time=8:00:00 --qos=kostas-med --partition=kostas-compute slice_bag_into_chunks_sbatch.bash $BIG_BAG_DIR $BIG_BAG $DEST_DIR $CHUNK_DUR
```

If you have a timing file like [example_timing_files/aviary_2019-04-22_slices.csv](example_timing_files/aviary_2019-04-22_slices.csv):
```
1555927200,1555930800
1555930800,1555934400
1555934400,1555938000
...
```
saved as
```
/archive/birds/aviary/data2019/example_dataset/aviary_2019-05-15-04-59-08.bag.slices
```
then you can export a sliced bag for each line in the file using:
```
BIG_BAG_DIR=/archive/birds/aviary/data2019/whole_bags
BIG_BAG=aviary_2019-05-15-04-59-08.bag
DEST_DIR=/archive/birds/aviary/data2019/example_dataset
TIMING_FILE=${DEST_DIR}/${BIG_BAG}.slices
sbatch slice_bag_using_timingfile_sbatch.bash $BIG_BAG_DIR $BIG_BAG $DEST_DIR $TIMING_FILE
```

