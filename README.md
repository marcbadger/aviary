# Guide for working with data from the UPenn Aviary

## Installation (skip this if using a pre-existing user)
Most export processes require only a conda environment, but a few will also require docker images.

### Setting up a conda environment for slicing
```
srun --partition compute --qos low --time=2:00:00 --pty bash
conda create --name slicing python=3.8
conda activate slicing
pip install --extra-index-url https://rospypi.github.io/simple/ rospy rosbag
pip install pytz
```

<!-- ### Setting up a conda environment for exporting
srun --partition compute --qos low --time=2:00:00 --pty bash
conda create --name exporting python=3.8
conda activate exporting -->

### Building docker images
For building docker images for the cluster, see the [this guide](dockerfiles/README.md).

## How to export video and audio from bags:
This code assumes you have already recorded a bag and transferred the bag to somewhere on the kostas server. You can extract audio and video out of the bag by following two steps.
1. Slice the bag into smaller, more manageable, chunks. See the [Slicing guide](bag_slicing/README.md).
2. Run the export script on all the sliced bags. See the [Export guide](exporting/README.md).

Look in the subfolders and their corresponding README documents for additional details.
