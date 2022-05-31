# Step 2: Exporting Audio and Video
## TLDR:
To export audio and video for all bag slices in a target directory:
```
TARGET_DIR=/archive/birds/aviary/data2019/long_videos/tutorial # change this directory to where your bag slices are
DEST_DIR=/archive/birds/aviary/data2019/long_videos/tutorial # change this directory to where you want your aviary_*_files folders to be saved
sbatch export_images_and_audio_sbatch_all.bash $TARGET_DIR $DEST_DIR
```

To export audio and video only for a target sliced bag:
```
TARGET_BAG_DIR=/archive/birds/aviary/data2019/long_videos/single_bird_dataset
DEST_DIR=/archive/birds/aviary/data2019/long_videos/single_bird_dataset
TARGET_BAG=aviary_2021-11-12_1636727340.000-1636727400.000_slice.bag
sbatch export_images_and_audio_sbatch_target.bash $TARGET_BAG_DIR $DEST_DIR $TARGET_BAG
```

To look at the progress of a running job:
```
squeue -u marc # view the currently running jobs
```

Find the job id 178750 (or 178750_1 if it is from a job array) from the list above. Then run:
```
tail -f slurm-178750.out 
```

I usually start typing tail -f slurm-178… and hit tab to complete it.

You can cancel a job with:
```
scancel 178750
```

If you want to modify what things get exported, look at the ```--export``` argument of [export_images_and_audio.py](export_images_and_audio.py). Current options are [full, separate, audio, merge, mosaic, frame, allframes, spectrogram]. Some of the choices depend on other exports, but these will be added to the export list automatically. To change what gets exported (e.g. also export a spectrogram/sound localization video) add them to the end of lines 51 and 61 in [export_images_and_audio.bash](export_images_and_audio.bash). To modify the file, or create a new copy to modify, use vim on kostas-ap:

```
cp ~/aviary/exporting/export_images_and_audio.bash ~/aviary/exporting/export_images_and_audio.bash.original
vim ~/aviary/exporting/export_images_and_audio.bash
``` 

If you want to modify _how_ things get exported (quality, microphones used, etc), look at lines 277-279 of [export_images_and_audio.py](export_images_and_audio.py).

## How it works
To export video from the sliced bags, you need ROS, a custom package called [```ffmpeg_image_transport_tools```](https://github.com/daniilidis-group/ffmpeg_image_transport_tools), and a custom build of ```ffmpeg```. So we need to start a job that runs inside a docker image that contains these packages. The bash script [export_images_and_audio_sbatch_all.bash](export_images_and_audio_sbatch_all.bash) tells sbatch to launch an array of 12 tasks (```#SBATCH --array=0-12```), each of which will get 1 GPU, 8 cpus, and 32G of memory and will last for 1 hour:
```
#SBATCH --gpus=1
#SBATCH --cpus-per-gpu=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --array=0-12
#SBATCH --qos=low
#SBATCH --partition=compute
```
Each task in the array will process one of the 5-15 minute bags and will take about 30 minutes to process. The python code will use ```$SLURM_ARRAY_TASK_ID``` to decide which bags this task should process and then check if each bag has already been exported before running the export command.

The docker image is on [docker_hub](https://hub.docker.com/r/marcbadger/frame_exporting/tags) and the system will automatically download it.  We also mount a bunch of directories that we will need to access within the job:
```
CONTAINER_IMAGE="marcbadger/frame_exporting:all_but_birds"
EXTRA_MOUNTS="/scratch/bird_packages:/bird_packages,/archive/birds/aviary:/archive/birds/aviary,/archive/$USER:/archive/$USER,/scratch/$USER:/scratch/$USER"
```

Finally, we provide a command that we want to run once we are inside the running job and run it with ```srun```:
```
COMMAND="/bin/bash /home/marc/aviary/bag_handling/export_images_and_audio.bash $TARGET_DIR $DEST_DIR $SLURM_ARRAY_TASK_ID $SLURM_ARRAY_TASK_MAX"

srun --container-mount-home\
     --container-mounts=${EXTRA_MOUNTS}\
     --container-image=${CONTAINER_IMAGE}\
     --no-container-remap-root\
     ${COMMAND}
```

This command will run [export_images_and_audio.bash](export_images_and_audio.bash) which will:
1. Import some extra libraries and copy some library files
1. Call export_images_and_audio.py

Finally, [export_images_and_audio.py](export_images_and_audio.py) will:
1. Collect a list of bags in the target directory
1. Split them into $SLURM_ARRAY_TASK_MAX lists
1. Take the bags list corresponding to $SLURM_ARRAY_TASK_ID
1. Then for each bag:
     - Check if the bag has already been exported by looking for outputs from that bag in the destination directory
     	  - WARNING: if the outputs for a bag are not right (incomplete, won't open, etc), you need to delete the files inside the corresponding ```aviary_*_files``` directory.
     - If the audio/video is not yet exported:
          - Run the export scripts contained in [bag2audio_raw.py](bag2audio_raw.py), [audio_raw2wavpack.py](audio_raw2wavpack.py), and [merge_video_audio.py](merge_video_audio.py).
1. Once all bags for that task are finished, return with exit code 0 so that SLURM will know the task is finished.