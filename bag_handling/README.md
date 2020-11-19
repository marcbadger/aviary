# Aviary data and processing overview

## Cluster information
Recordings from the aviary are in two places:
| Year | Location | What to do |
| --- | --- | --- |
| 2019 | ```/birds/aviary/data``` | first copy to ```/archive/birds/aviary/data2019/whole_bags``` then access from a running job |
| 2020 | ```/archive/birds/aviary/data``` | access from a running job |

To work with the bags, you will need to start a 'job' on the cluster, which will allocate computational resources to you. The ```/birds``` directory **cannot** be accessed from a running job, so for 2019 recordings, you will first need to copy the bag over to ```/archive/birds/aviary/data2019/whole_bags```. The bash script [copy_bag.bash](copy_bag.bash) takes in one input, the bag name (e.g. ```aviary_2019-04-01-04-59-09.bag```) and will do the copying for you.

## How to start a job
The basch scripts below contain example scripts for launching jobs with appropriate docker images, but if you want to modify them or learn more about how it works, refer to the cluster tutorials for [how to launch interactive and batch jobs](https://github.com/daniilidis-group/cluster_tutorials/tree/master/slurm_intro) and [how to launch jobs that require a docker image](https://github.com/daniilidis-group/cluster_tutorials/tree/master/pyxis).

## How to slice bags
To slice bags, you need ROS, which means you need to start a job that runs inside a docker image that contains ROS. To slice bags, you do not need a GPU, so you do not need to ask for one. The bash script [sbatch_slice_bags_cluster.bash](sbatch_slice_bags_cluster.bash) tells sbatch to launch a job with 8 cpus, 32G of memory, that will last for 6 hours.
```
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute
```

The docker image is from [docker_hub](https://hub.docker.com/r/osrf/ros/tags?page=1&name=melodic-desktop-full-bionic) and we will name it "python-ros" so that the system will keep the image around and we won't have to re-download it every time.  We also mount a bunch of directories that we will need to access within the job:
```
CONTAINER_NAME="python-ros"
CONTAINER_IMAGE="osrf/ros:melodic-desktop-full-bionic"
EXTRA_MOUNTS="/scratch/bird_packages:/bird_packages,/archive/birds/aviary:/archive/birds/aviary,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER"
```

Finally, we provide a command that we want to run once we are inside the running job and run it with ```srun```:
```COMMAND="/bin/bash /bird_packages/aviary/bag_handling/slice_bags_cluster.bash $BAG_DIR $BIG_BAG $DEST_DIR"

srun --container-mount-home\
     --container-mounts=${EXTRA_MOUNTS}\
     --container-name=${CONTAINER_NAME}\
     --container-image=${CONTAINER_IMAGE}\
     --no-container-remap-root\
     ${COMMAND}
```

This will run [slice_bags_cluster.bash](slice_bags_cluster.bash) which imports some extra libraries and runs a python script, [slice_bag_from_list.py](slice_bag_from_list.py).

We will need to make some modifications to ```slice_bag_from_list.py```. It will need to:
1. load the JSONProcessor from [processing.py](processing.py)
1. extract the date from the ```args.bagfile``` input[^1]
1. write a new function that takes in the date and returns a list of [(start_i, stop_i),...] times where each start/stop is a ```rospy.Time()``` object
     - use the JSONProcessor[^2] to obtain a list of bag slice rostime ranges for the input date
     - turn each input rostime into a ```rospy.Time``` object using ```rospy.Time(float(<rostime>))```
     - return this list
1. Assign the list returned by the above function to ```start_stops```.
  1. The rest of the script will create ```out_bags```, a list of SlicedBag objects, run through the input bag and write messages that satisfy a bag's time range to that bag.

[^1]: You probably want to add an input argument ```--from_annotations``` that, if supplied, calls the function above and sets ```start_stops```. Otherwise, ```start_stops``` should be assigned using ```find_start_end_times(in_bag, args)```.

[^2]: Videos are stored using h.265 encoding and the image messages in the rosbag are not the raw images.  They are instead "keyframes" (i.e. an entire image) and "differences". As we read image messages and decode them we won’t get any "real" images until a keyframe is encountered, which means we need to start the actual bag slice 0.3 seconds (~12 frames) before the first rostime for which we actually want to have an image. We also need to extend the stop time by 0.075 seconds (~3 frames). So to get images +- 0.4 around 1553361312.000 (which should return about 32 frames from 1553361311.600 to 1553361312.400), we want to set the bag slice range to [1553361312.000 - 0.4 - 0.3, 1553361312.000 + 0.4 + 0.075] = [1553361311.300, 1553361312.475].

Finally, we can launch the job by running the following on ```kostas-ap```:
```
sbatch sbatch_slice_bags_cluster.bash $BIG_DIR $BIG_BAG $DEST_DIR
```
where ```BIG_DIR=/archive/birds/aviary/data2019/whole_bags``` is where the large bag ```BIG_BAG``` is, and ```DEST_DIR``` is the place where the bag slices will get saved[^3].

[^3]: We will need to make sure the next step matches with where we save the bag slices.

## How to export bags
To export images from the sliced bags, you need ROS, a custom package called ```ffmpeg_image_transport_tools```, and a custom build of ```ffmpeg```. So we need to start a job that runs inside yet another docker image. The bash script [sbatch_extract_everything_cluster.bash](sbatch_extract_everything_cluster.bash) tells sbatch to launch a job with 1 GPU, 8 cpus, 32G of memory, that will last for 4 hours{^4]:
```
#SBATCH --gpus=1
#SBATCH --cpus-per-gpu=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute
```
[^4]: We will actually have a bunch of tiny bags, each of which will only take about 30 seconds or so to process, so the best thing to do is probably to launch a bunch of low priority jobs [as a batch](https://github.com/daniilidis-group/cluster_tutorials/tree/master/slurm_intro#batches) and processes the small bags in parallel. When each job launches it gets assigned a ```$SLURM_ARRAY_TASK_ID```, which it can use to look up in a dictionary which bags it should export.  Then it should check which of its assigned bags have already been completed and only export the ones that haven't been finished yet.

Our the docker container we want now is:
```
CONTAINER_NAME="birds-complete"
CONTAINER_IMAGE="adarshmodh/birds:complete"
```

And the command we will run is:
```
/bin/bash /bin/bash /bird_packages/aviary/bag_handling/extract_everything_cluster.bash $TARGET_DIR $TARGET_DATE
```
which will run [extract_everything_cluster.bash](extract_everything_cluster.bash) which imports some extra libraries, copies some library files, and call ```ffmpeg_image_transport_tools decode_bag_ns.launch``` for each bag that satisfies ```TARGET_DATE``` in ```TARGET_DIR```.
