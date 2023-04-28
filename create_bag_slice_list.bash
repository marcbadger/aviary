#!/bin/bash

# inputs:
# bag name
BAG_NAME=$1
# ros time of SUNRISE
ROS_TIME=$2

# OLD EXPORT SUMMER 2020
# Will export 4 x 15 minute chunks
# sunrise + 1 hour
#echo "$(( ROS_TIME + 1*3600 + 0*60)), $(( ROS_TIME + 1*3600 + 0*60 + 15*60))" >> $BAG_NAME.slices

# sunrise + 2.5 hours
#echo "$(( ROS_TIME + 2*3600 + 30*60)), $(( ROS_TIME + 2*3600 + 30*60 + 15*60))" >> $BAG_NAME.slices

# sunrise + 5.5 hours
#echo "$(( ROS_TIME + 5*3600 + 30*60)), $(( ROS_TIME + 5*3600 + 30*60 + 15*60))" >> $BAG_NAME.slices

# sunrise + 8.5 hours
#echo "$(( ROS_TIME + 8*3600 + 30*60)), $(( ROS_TIME + 8*3600 + 30*60 + 15*60))" >> $BAG_NAME.slices

# NEW EXPORT FALL 2020
# Will export 4 x 15 minute chunks
# sunrise + 1 hour
echo "$(( ROS_TIME + 1*3600 + 0*60)), $(( ROS_TIME + 1*3600 + 0*60 + 15*60))" >> $BAG_NAME.slices

# sunrise + 1 hour 15 min
echo "$(( ROS_TIME + 1*3600 + 15*60)), $(( ROS_TIME + 1*3600 + 15*60 + 15*60))" >> $BAG_NAME.slices

# sunrise + 5 hours
echo "$(( ROS_TIME + 5*3600 + 0*60)), $(( ROS_TIME + 5*3600 + 0*60 + 15*60))" >> $BAG_NAME.slices

# sunrise + 5 hours 15 min
echo "$(( ROS_TIME + 5*3600 + 15*60)), $(( ROS_TIME + 5*3600 + 15*60 + 15*60))" >> $BAG_NAME.slices