import os
import sys
import glob
import time
import math

import argparse
import shlex

from multiprocessing import Process as multproc

try:
    from pathlib import Path
    from subprocess import Popen, PIPE, TimeoutExpired
except ImportError:
    from pathlib2 import Path # python 2 backport
    from subprocess32 import Popen, PIPE, TimeoutExpired

from signal import signal, SIGINT

from exporting.audio_raw2wavpack import raw_to_wavpack
from exporting.bag2audio_raw import export_audio_raw
from exporting.merge_video_audio import merge_audio_and_video, merge_audio_and_video_topbot
from exporting.export_spectrogram_localization import export_spectrogram_localization

def handler(signal_received, frame):
    global process
    # Handle cleanup
    print('Exiting gracefully')
    for k, p in process.items():
        if p:
            p.terminate()
    sys.stdout.flush()
    exit(0)


def run_command(command, key):
    global process
    print(command)
    sys.stdout.flush()

    process[key] = Popen(command, stdout=PIPE, universal_newlines=True, shell=True, stderr=PIPE)
    try:
        output, error = process[key].communicate(timeout=120)
    except TimeoutExpired:
        print('WARNING: killing process {}!'.format(key))
        process[key].kill()
        output, error = process[key].communicate()

    return output, error


def export_video(bagname, filesdir, basename):
    global process
    
    Path(os.path.join(filesdir,'frames')).mkdir(parents=True, exist_ok=True)

    if "2020" in basename:
        launch_file = 'rosbag2video_ns_ten.launch'
    else:
        launch_file = 'rosbag2video_ns.launch'

    video_command = (
        'roslaunch bird_recording {}'.format(launch_file)
        + ' bag:={} out_file_dir:={} write_frames:=false'.format(bagname, filesdir)
        + ' write_individual_frames:=false name_space:={}'.format(basename.replace("-","_").replace(".","_"))
        )

    output, error = run_command(video_command, "export_video")
    print(output)
    sys.stdout.flush()
    
    if error:
        text_file = open("{}.export_video.error".format(os.path.join(filesdir,basename)), "w")
        text_file.write(error)
        text_file.close()

def export_separate_videos(bagname, filesdir, basename):
    global process

    video_command = (
        'roslaunch ffmpeg_image_transport_tools split_bag_ns.launch'
        + ' bag:={} out_file_base:={}'.format(bagname, os.path.join(filesdir, basename+'_view'))
        + ' write_time_stamps:=true convert_to_mp4:=true name_space:={}'.format(basename.replace("-","_").replace(".","_"))
        )

    output, error = run_command(video_command, "separate")
    print(output)
    sys.stdout.flush()

    if error:
        text_file = open("{}.export_separate_video.error".format(os.path.join(filesdir,basename)), "w")
        text_file.write(error)
        text_file.close()

def export_frame(bagname, filesdir, basename):

    print("Creating path: {}".format(os.path.join(filesdir,'frames')))
    Path(os.path.join(filesdir,'frames')).mkdir(parents=True, exist_ok=True)

    command = 'roslaunch ffmpeg_image_transport_tools decode_frames.launch bag:={} out_file_dir:={} delta_time:=600'.format(bagname, basedir)

    output, error = run_command(command, "export_frame")

    # Now split the concatenated images into separate views
    command = '/bin/bash split_images.bash {}'.format(os.path.join(filesdir,'frames'))

    output, error = run_command(command, "split_frame")
    print(output)
    sys.stdout.flush()

    if error:
        text_file = open("{}.export_frame.error".format(os.path.join(filesdir,basename)), "w")
        text_file.write(error)
        text_file.close()

def extract_frames(bagname, filesdir, basename):

    print("Creating path: {}".format(os.path.join(filesdir,'frames')))
    Path(os.path.join(filesdir,'frames')).mkdir(parents=True, exist_ok=True)

    command = ('roslaunch ffmpeg_image_transport_tools decode_bag_ns.launch'
            + ' bag:={} out_file_dir:={}'.format(bagname, filesdir)
            + ' write_frames:=true write_individual_frames:=true write_video:=false'
            + ' name_space:={}'.format(basename.replace("-","_").replace(".","_")))

    output, error = run_command(command,"extract_frames")
    print(output)
    sys.stdout.flush()

    if error:
        text_file = open("{}.extract_frames.error".format(os.path.join(filesdir,basename)), "w")
        text_file.write(error)
        text_file.close()

    # Now split the concatenated images into separate views
    command = '/bin/bash split_images.bash {}'.format(os.path.join(filesdir,'frames'))

    output, error = run_command(command, "split_all_frame")
    print(output)
    sys.stdout.flush()

def export_all(bagname, args):
    global process
    process = dict()

    filesdir = bagname.replace("slice.bag","files")

    if args.dest_dir:
        filesdir = os.path.join(args.dest_dir, os.path.basename(filesdir))

    basename = os.path.basename(bagname.replace("_slice.bag",""))

    print("Base directory: {}".format(filesdir))
    print("Files basename: {}".format(basename))

    # ensure that the path exists
    print("Creating path: {}".format(filesdir))
    Path(filesdir).mkdir(parents=True, exist_ok=True)

    print("Starting export for {}".format(basename))
    sys.stdout.flush()

    try:
        if args.overwrite_existing:
            overwrite_existing = True
        else:
            overwrite_existing = False

    except:
        overwrite_existing = False

    ros_init = False

    if 'separate' in args.export:

        separate_files = glob.glob(os.path.join(filesdir,'*view*.mp4'))

        if (len(separate_files) < 8) or overwrite_existing:

            print("Exporting separate views for {}...".format(basename))

            export_separate_videos(bagname, filesdir, basename)

            # pause to wait for the ros port to get set up so we don't try
            # to create multiple ros's
            ros_init = True
            time.sleep(10)

        else:

            print("All separate videos already exist for {}. Skipping.".format(basename))

    if 'full' in args.export:

        full_files = glob.glob(os.path.join(filesdir,'video_full.aux'))

        if not full_files or overwrite_existing:

            print("Exporting full video for {}...".format(basename))
            export_video(bagname, filesdir, basename)

            if not ros_init:
                # pause to wait for the ros port to get set up so we don't try
                # to create multiple ros's
                ros_init = True
                time.sleep(10)

        else:

            print("Full video already exists for {}. Skipping.".format(basename))

    if 'audio' in args.export:

        audio_files = glob.glob(os.path.join(filesdir,'*_audio.wv'))

        if not audio_files or overwrite_existing:

            if not ros_init:
                # pause to wait for the ros port to get set up so we don't try
                # to create multiple ros's
                ros_init = True
                time.sleep(10)

            print("Exporting audio for {}...".format(basename))
            export_audio_raw(bagname, 
                aux_file=os.path.join(filesdir,'{}_audio.aux'.format(basename)), 
                output_file=os.path.join(filesdir,'{}_audio.raw'.format(basename)))

            # command = (f"python2 bag2audio_raw.py {bagname}"
            #            f" --aux_file {os.path.join(filesdir,'{}_audio.aux'.format(basename))}"
            #            f" --output_file {os.path.join(filesdir,'{}_audio.raw'.format(basename))}"
            #            )

            # output, error = run_command(command, "export_audio")
            # print(output)
            # sys.stdout.flush()

            if not ros_init:
                # pause to wait for the ros port to get set up so we don't try
                # to create multiple ros's
                ros_init = True
                time.sleep(10)

            raw_to_wavpack(os.path.join(filesdir,'{}_audio.raw'.format(basename)), 
                output_file=os.path.join(filesdir,'{}_audio.wv'.format(basename)))

        else:

            print("Audio already exists for {}. Skipping.".format(basename))

    if 'merge' in args.export:

        merged_video = glob.glob(os.path.join(filesdir,'*_all.mp4'))

        if not merged_video or overwrite_existing:

            print("Merging audio and video for {}...".format(basename))
            merge_audio_and_video(audio_file=os.path.join(filesdir,'{}_audio.raw'.format(basename)),
                                  video_file=os.path.join(filesdir,'video_full.h265'),
                                  audio_aux=os.path.join(filesdir,'{}_audio.aux'.format(basename)),
                                  video_aux=os.path.join(filesdir,'video_full.aux'),
                                  output_file=os.path.join(filesdir,'{}_all.mp4'.format(basename)),
                                  channels=[0,2], video_format='copy')

        else:

            print("Audio and video already merged for {}. Skipping.".format(basename))

    if 'mosaic' in args.export:

        mosaic_file = glob.glob(os.path.join(filesdir,'*_top.mp4'))

        if not mosaic_file or overwrite_existing:

            # Edit these channel numbers here if you want to use different channels for the top and bottom videos
            # The format is [left_channels, right_channels]
            top_channels = [[3,4,5,9,10,11], [15,16,17,21,22,23]]
            bot_channels = [[0,1,2,6,7,8], [12,13,14,18,19,20]]
            video_quality = 30

            print("Splitting into top and bottom {}...".format(basename))
            merge_audio_and_video_topbot(audio_file=os.path.join(filesdir,'{}_audio.raw'.format(basename)),
                                  video_file=os.path.join(filesdir,'video_full.h265'),
                                  audio_aux=os.path.join(filesdir,'{}_audio.aux'.format(basename)),
                                  video_aux=os.path.join(filesdir,'video_full.aux'),
                                  sequence_name=os.path.join(filesdir, basename),
                                  top_channels=top_channels, bot_channels=bot_channels, 
                                  video_quality=video_quality,
                                  video_format='libx264')

        else:

            print("Top view mosaic already created for {}. Skipping.".format(basename))

    if 'frame' in args.export:

        print("WARNING: Export frame not implemented yet.")
        #export_frame(short_bagname)
    
    if 'allframes' in args.export:

        # see if there are already images in the destination directory
        img_files = glob.glob(os.path.join(filesdir,'frames','frame*.jpg'))

        if not img_files or overwrite_existing:

            print("Extracting all frames for {}...".format(basename))
            extract_frames(bagname, filesdir, basename)

            if not ros_init:
                # pause to wait for the ros port to get set up so we don't try
                # to create multiple ros's
                ros_init = True
                time.sleep(10)

        else:
            
            print("Frames already extracted for {}. Skipping.".format(basename))

    if 'spectrogram' in args.export:

        spec_file = glob.glob(os.path.join(filesdir,'*_top_locspec.mp4'))

        if not spec_file or overwrite_existing:

            print("Exporting top spectrogram video for {}...".format(basename))
            sys.stdout.flush()
            export_spectrogram_localization(args.dest_dir, os.path.basename(filesdir).replace("_files", ""), view='top')

        else:

            print("Top sectrogram video already created for {}. Skipping.".format(basename))

        spec_file = glob.glob(os.path.join(filesdir,'*_bot_locspec.mp4'))

        if not spec_file or overwrite_existing:

            print("Exporting bot spectrogram video for {}...".format(basename))
            export_spectrogram_localization(args.dest_dir, os.path.basename(filesdir).replace("_files", ""), view='bot')

        else:

            print("Bottom spectrogram videos already created for {}. Skipping.".format(basename))


if __name__ == '__main__':

    signal(SIGINT, handler)

    parser = argparse.ArgumentParser(
        description='export things (images, audio, and video) from a bunch of bags')

    parser.add_argument(
        '--target_dir', help='target directory containing bags to extract data from')
    parser.add_argument(
        '--dest_dir', type=str, default=None, help='destination directory to save the frames')
    parser.add_argument(
        '--task_id', type=int, default=0, help='slurm array task id')
    parser.add_argument(
        '--num_tasks', type=int, default=1, help='total number of slurm tasks')
    parser.add_argument(
        '--target_bag', help='specific bag to target', default=None)
    parser.add_argument(
        '--overwrite_existing', dest='overwrite_existing', action='store_true', help='whether to re-do existing files')
    parser.add_argument(
        '--export', nargs='+', choices=['full','separate','audio','merge','mosaic','frame','allframes','spectrogram'],
        help='what to export: full, separate, audio, merge, mosaic, frame, allframes, spectrogram')
    
    args = parser.parse_args()

    if 'spectrogram' in args.export:
        args.export.extend(['mosaic'])

    # if we want a mosaic, we also need the full and audio
    if 'mosaic' in args.export:
        args.export.extend(['full','audio','merge'])

    if 'merge' in args.export:
        args.export.extend(['full','audio'])

    if args.target_bag:

        export_all(os.path.join(args.target_dir, args.target_bag), args)

    else:

        bag_names = glob.glob(os.path.join(args.target_dir,'aviary_*_slice.bag'))
        bag_names.sort()

        # split bag list in to even chunks
        task_bags = [bag_names[i:i+args.num_tasks] for i in range(0, len(bag_names), args.num_tasks)]

        this_tasks_bags = [tb[args.task_id] for tb in task_bags if len(tb) > args.task_id]

        for bag_num, bagname in enumerate(this_tasks_bags):

            export_all(bagname, args)

            # pause to wait for the ros port to get set up so we don't try
            # to create multiple ros's
            if bag_num == 0:
                time.sleep(10)

        #     # experimental (export is likely limited by transfer bandwidth, so this won't help much)
        #     # export bags in parallel
        #     procs = []
        #     for bagname in bag_names:
        #         p = multproc(target=export_all, args=(bagname, args.overwrite_existing))
        #         p.start()

        #         # pause to wait for the ros port to get set up so we don't try
        #         # to create multiple ros's
        #         time.sleep(10)

        #         procs.append(p)
        #         #export_all(bagname, args.overwrite_existing)

        #     for p in procs:
        #         p.join()

