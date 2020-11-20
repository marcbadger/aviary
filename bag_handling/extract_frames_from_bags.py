import os
import sys
import glob
import time

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


def handler(signal_received, frame):
    global process
    # Handle cleanup
    print('Exiting gracefully')
    if process:
        process.terminate()
    exit(0)


def run_command(command):
    global process
    print(command)

    process = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE)
    try:
        output, error = process.communicate(timeout=120)
    except TimeoutExpired:
        process.kill()
        output, error = process.communicate()

    return output, error


def extract_frames(bagname, filesdir, basename):

    Path(os.path.join(filesdir,'frames')).mkdir(parents=True, exist_ok=True)

    command = 'roslaunch ffmpeg_image_transport_tools decode_bag_ns.launch'
            + ' bag:={} out_file_dir:={}'.format(bagname, filesdir)
            + ' write_frames:=true write_individual_frames:=true write_video:=false'
            + ' name_space:={}'.format(basename.replace("-","_").replace(".","_"))

    output, error = run_command(command)

    if error:
        text_file = open("{}.extract_frames.error".format(os.path.join(filesdir,basename)), "w")
        text_file.write(error)
        text_file.close()


if __name__ == '__main__':

    signal(SIGINT, handler)

    parser = argparse.ArgumentParser(
        description='extract all frames from a bunch of bags')

    parser.add_argument(
        '--target_dir', help='target directory containing bags to extract data from')
    parser.add_argument(
        '--dest_dir', help='destination directory to save the frames')
    parser.add_argument(
        '--task_id', type=int, help='slurm array task id')
    parser.add_argument(
        '--num_tasks', type=int, help='total number of slurm tasks')
    
    args = parser.parse_args()

    bag_names = glob.glob(os.path.join(args.target_dir,'aviary_{}*_slice.bag'.format(args.target_date)))
    bag_names.sort()

    # split bag list in to even chunks
    task_bags = [bag_names[i:i+num_tasks] for i in range(0, len(bag_names), num_tasks)]

    this_tasks_bags = task_bags[task_id]

    for bag_num, bagname in enumerate(this_tasks_bags):

        filesdir = bagname.replace("slice.bag","files")
        basename = os.path.basename(bagname.replace("_slice.bag",""))

        print("Base directory: {}".format(filesdir))
        print("Files basename: {}".format(basename))

        # ensure that the path exists
        Path(filesdir).mkdir(parents=True, exist_ok=True)

        # see if there are already images in the destination directory
        img_files = glob.glob(os.path.join(filesdir,'frame*.jpg'))

        if img_files:
            print("Frames already extracted for {}. Skipping.".format(basename))

        else:

            print("Extracting all frames for {}...".format(basename))
            extract_frames(bagname, filesdir, basename)

            # pause to wait for the ros port to get set up so we don't try
            # to create multiple ros's
            if bag_num == 0:
                time.sleep(10)