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
To slice bags, you need ROS, which means you need to start a job that runs inside a docker image contining ROS. To slice bags, you do not need a GPU, so you do not need to ask for one. The bash script [sbatch_slice_bags_cluster.bash](sbatch_slice_bags_cluster.bash) tells sbatch to launch a job with 8 cpus, 32G of memory, that will last for 6 hours:
```
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --qos=kostas-med
#SBATCH --partition=kostas-compute
```

The docker image is from [docker_hub](https://hub.docker.com/r/osrf/ros/tags?page=1&name=melodic-desktop-full-bionic) and we will name it "python-ros" so that the system will keep the image around and we won't have to re-download it every time.  We also mount a bunch of directories we will need to access within the job:
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

Inside ```slice_bag_from_list.py```, we will need to make some modifications:
1. load the JSONProcessor from [processing.py](processing.py)
1. extract the date from the ```args.bagfile``` input arg
1. write a new function that takes in the date and returns a list of [(start_i, stop_i),...] times where each start/stop is a ```rospy.Time()``` object.
  1. use the JSONProcessor to obtain a list of bag slice rostime ranges for the input date
  1. turn each input rostime into a ```rospy.Time``` object using ```rospy.Time(float(<rostime>))```
  1. return this list
1. Assign the list returned by the above function to ```start_stops```.
  1. The rest of the script will create ```out_bags```, a list of SlicedBag objects, run through the input bag and write messages that satisfy a bag's time range to that bag.

You probably want to add an input argument ```--from_annotations``` that, if supplied, calls the function above and sets ```start_stops```.

## How to export bags

## Connecting it all with bash scripts
