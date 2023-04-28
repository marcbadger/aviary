#!/bin/bash

#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

CONTAINER_NAME="python-ros"
CONTAINER_IMAGE="osrf/ros:melodic-desktop-full-bionic"
EXTRA_MOUNTS="/scratch/bird_packages:/bird_packages,/archive/birds/aviary:/archive/birds/aviary,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER"

COMMAND="/bin/bash echo 'I ran something!'"

srun --container-mount-home\
     --container-mounts=${EXTRA_MOUNTS}\
     --container-name=${CONTAINER_NAME}\
     --container-image=${CONTAINER_IMAGE}\
     --no-container-remap-root\
     ${COMMAND}