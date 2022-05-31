# Live Demos on the Aviary

## Setup
VPN into the aviary
```
sudo openvpn --config ~/Documents/carol-desk.ovpn
```

Log onto aviary-1
```
ssh <user: ask Marc or look in the google doc>@aviary-1.sas.upenn.edu
```

Create/start a tmux session
```
tmux new -s demo
```

Clone the repository:
```
git clone https://github.com/marcbadger/aviary.git
cd aviary/demo
```

Download the [bird detector weights](https://drive.google.com/file/d/1YrDNJNEdbMgHjmiA2go6yOB3hEiXxw8V/view) and save it under ```models/detector.pth```:
```
# assuming you downloaded the weights to Downloads on your own machine
scp ~/Downloads/detector.pth <user>@aviary-1.sas.upenn.edu:~/aviary/models/detector.pth
```

Create the conda environment:
```
conda env create -f demo_environment.yml
```

## Showing Mask R-CNN detections
VPN into the aviary
```
sudo openvpn --config ~/Documents/carol-desk.ovpn
```

Log onto aviary-1
```
ssh <user>@aviary-1.sas.upenn.edu
```

Create/start a tmux session
```
tmux new -s demo
```
OR
```
tmux a -t demo
```

Activate a conda environment
```
conda activate exporting
```

Start the detection node (currently set to process cam3)
```
cd ~/aviary/demo
python3 detection_node.py
```

Note ```detection_node.py``` is an example of how to use python to set up ROS nodes that subscribe, process, and publish data.

On your own computer:
```
sudo openvpn --config ~/Documents/carol-desk.ovpn
export PATH=$PATH:/usr/local/cuda/bin
source /opt/ros/melodic/setup.bash
export ROS_IP=192.168.0.4
source ~/Documents/birds/devel/setup.bash --extend
export LD_LIBRARY_PATH=$HOME/Documents/birds/ffmpeg/build/lib:$LD_LIBRARY_PATH
export ROS_MASTER_URI=http://192.168.0.4:11311/
rqt_image_view 
```
Pick the topic ```/cam_sync/cam3/image_detections``` to see the live view.