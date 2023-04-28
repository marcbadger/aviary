import os
import stat
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

from audio_raw2wavpack import raw_to_wavpack
from merge_video_audio import merge_audio_and_video

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


def export_video(bagname, filesdir, basename):
    
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

    record_output_command = ('if ' + video_command + ' ; then '
        + 'echo "export_video" >> {}_log.txt ; fi\n'.format(os.path.join(filesdir,basename)))

    return record_output_command

def export_separate_videos(bagname, filesdir, basename):

    video_command = (
        'roslaunch ffmpeg_image_transport_tools split_bag_ns.launch'
        + ' bag:={} out_file_base:={}'.format(bagname, os.path.join(filesdir, basename+'_view'))
        + ' write_time_stamps:=true convert_to_mp4:=true name_space:={}'.format(basename.replace("-","_").replace(".","_"))
        )

    record_output_command = ('if ' + video_command + ' ; then '
        + 'echo "export_separate_videos" >> {}_log.txt ; fi\n'.format(os.path.join(filesdir,basename)))

    return record_output_command

def export_frame(bagname, filesdir, basename):

    # os.makedirs(os.path.join(basedir,'frames'), exist_ok=True)
    Path(os.path.join(basedir,'frames')).mkdir(parents=True, exist_ok=True)

    command1 = 'roslaunch ffmpeg_image_transport_tools decode_frames.launch bag:={} out_file_dir:={} delta_time:=600\n'.format(bagname, basedir)

    # Now split the concatenated images into separate views
    command2 = '/bin/bash split_images.bash {}\n'.format(os.path.join(basedir,'frames'))

    return command1, command2

def create_mosaics(infile):

    command = (
        'ffmpeg -y -i {}'.format(infile)
        + ' -filter_complex "[0:v] crop=in_w/4:in_h/2:in_w*(0/4):0 [topupperleft]; [0:v] crop=in_w/4:in_h/2:in_w*(1/4):0 [topupperright]; [0:v] crop=in_w/4:in_h/2:in_w*(2/4):0 [toplowerleft]; [0:v] crop=in_w/4:in_h/2:in_w*(3/4):0 [toplowerright]; nullsrc=size=3840x2400 [topbase]; [topbase][topupperleft] overlay=shortest=1 [toptmp1]; [toptmp1][topupperright] overlay=shortest=1:x=1920 [toptmp2]; [toptmp2][toplowerleft] overlay=shortest=1:y=1200 [toptmp3]; [toptmp3][toplowerright] overlay=shortest=1:x=1920:y=1200 [topout]; [0:v] crop=in_w/4:in_h/2:in_w*(0/4):in_h/2 [botupperleft]; [0:v] crop=in_w/4:in_h/2:in_w*(1/4):in_h/2 [botupperright]; [0:v] crop=in_w/4:in_h/2:in_w*(2/4):in_h/2 [botlowerleft]; [0:v] crop=in_w/4:in_h/2:in_w*(3/4):in_h/2 [botlowerright]; nullsrc=size=3840x2400 [botbase]; [botbase][botupperleft] overlay=shortest=1 [bottmp1]; [bottmp1][botupperright] overlay=shortest=1:x=1920 [bottmp2]; [bottmp2][botlowerleft] overlay=shortest=1:y=1200 [bottmp3]; [bottmp3][botlowerright] overlay=shortest=1:x=1920:y=1200 [botout]"'
        + ' -map "[topout]" -map 0:a -c:v libx264 -crf 30 -pix_fmt yuv420p {}'.format(infile.replace('all.mp4','top.mp4'))
        + ' -map "[botout]" -map 0:a -c:v libx264 -crf 30 -pix_fmt yuv420p {}'.format(infile.replace('all.mp4','bot.mp4'))
        )

    record_output_command = ('if ' + command + ' ; then '
        + 'echo "create_mosaics" >> {}_log.txt ; fi\n'.format(os.path.join(filesdir,basename)))

    return record_output_command

def export_audio_raw(bagname, filesdir, basename):

    command = 'python bag2audio_raw.py --aux_file={} --output_file={} {}'.format(
        os.path.join(filesdir,'{}_audio.aux'.format(basename)),
        os.path.join(filesdir,'{}_audio.raw'.format(basename)),
        bagname)

    record_output_command = ('if ' + command + ' ; then '
        + 'echo "export_audio_raw" >> {}_log.txt ; fi\n'.format(os.path.join(filesdir,basename)))

    return record_output_command

def get_raw_to_wavpack(bagname, filesdir, basename):

    command = raw_to_wavpack(os.path.join(filesdir,'{}_audio.raw'.format(basename)), 
    output_file=os.path.join(filesdir,'{}_audio.wv'.format(basename)), return_string=True)

    record_output_command = ('if ' + command + ' ; then '
        + 'echo "raw_to_wavpack" >> {}_log.txt ; fi\n'.format(os.path.join(filesdir,basename)))

    return record_output_command

def get_merge_command(bagname, filesdir, basename):

    command = (
        'python merge_video_audio.py'
        + ' audio_file={}'.format(os.path.join(filesdir,'{}_audio.raw'.format(basename)))
        + ' video_file={}'.format(os.path.join(filesdir,'video_full.h265'))
        + ' audio_aux={}'.format(os.path.join(filesdir,'{}_audio.aux'.format(basename)))
        + ' video_aux={}'.format(os.path.join(filesdir,'video_full.aux'))
        + ' output_file={}'.format(os.path.join(filesdir,'{}_all.mp4'.format(basename)))
        + ' channels={} video_format={}'.format('0,2', 'copy')
        )

    record_output_command = ('if ' + command + ' ; then '
        + 'echo "merge_audio_and_video" >> {}_log.txt ; fi\n'.format(os.path.join(filesdir,basename)))

    return record_output_command

def export_all(bagname, overwrite_existing):

    # This creates a bash script and then runs it
    
    filesdir = bagname.replace("slice.bag","files")
    basename = os.path.basename(bagname.replace("_slice.bag",""))
    basename_w_path = os.path.join(filesdir, basename)

    print("Base directory: {}".format(filesdir))
    print("Files basename: {}".format(basename))

    # ensure that the path exists
    Path(filesdir).mkdir(parents=True, exist_ok=True)

    # Open a log file that keeps track of which processes have completed successfully
    
    if os.path.exists("{}_log.txt".format(basename_w_path)):
        with open("{}_log.txt".format(basename_w_path)) as file:
            finished_log = [line.rstrip('\n') for line in file]
    else:
        finished_log = []

    # Open the bash script
    print("Exporting command_file: {}_export_command.bash".format(basename_w_path))
    command_file = open("{}_export_command.bash".format(basename_w_path), "w")
    command_file.write('#!/bin/bash\n')
    
    # Export separate views
    command_file.write('echo "'
        + 'Exporting separate views for {}..."\n'.format(basename))

    if 'export_separate_videos' not in finished_log:
        command_file.write(export_separate_videos(bagname, filesdir, basename))

    # pause to wait for the ros port to get set up so we don't try
    # to create multiple ros's
    command_file.write('sleep 10\n')

    # Export full video
    command_file.write('echo "'
        + 'Exporting full video for {}..."\n'.format(basename))

    if 'export_video' not in finished_log:
        command_file.write(export_video(bagname, filesdir, basename))

    # Export audio
    command_file.write('echo "'
        + 'Exporting audio for {}..."\n'.format(basename))

    if 'export_audio_raw' not in finished_log:
        command_file.write(export_audio_raw(bagname, filesdir, basename))

    if 'raw_to_wavpack' not in finished_log:
        command_file.write(get_raw_to_wavpack(bagname, filesdir, basename))

    command_file.write('echo "'
        + 'Merging audio and video for {}..."\n'.format(basename))

    if 'merge_audio_and_video' not in finished_log:
        command_file.write(get_merge_command(bagname, filesdir, basename))


    # command_file.write('echo "'
    #     + 'Splitting into top and bottom {}..."'.format(basename))

    # if 'create_mosaics' not in finished_log:
    #     command_file.write(create_mosaics(os.path.join(filesdir, '{}_all.mp4'.format(basename))))

    # export_frame(short_bagname)

    command_file.close()

if __name__ == '__main__':

    signal(SIGINT, handler)

    parser = argparse.ArgumentParser(
        description='export images, audio, and video from a bunch of bags')

    parser.add_argument(
        '--target_dir', help='target directory containing bags to extract data from.')
    parser.add_argument(
        '--target_date', help='target date of the bags to extract data from.')
    parser.add_argument(
        '--target_bag', help='specific bag to target', default=None)
    parser.add_argument(
        '--overwrite_existing', default=True, help='whether to re-do existing files.')
    
    args = parser.parse_args()

    if args.target_bag:
        export_all(os.path.join(args.target_dir, args.target_bag), args.overwrite_existing)

    else:

        bag_names = glob.glob(os.path.join(args.target_dir,'aviary_{}*_slice.bag'.format(args.target_date)))

        if True:
            for bagname in bag_names:
                
                export_all(bagname, args.overwrite_existing)

                # pause to wait for the ros port to get set up so we don't try
                # to create multiple ros's
                time.sleep(10)

        else:
            # bag_names = [bag_names[0]]
            # print(bag_names)

            # export bags in parallel
            procs = []
            for bagname in bag_names:
                p = multproc(target=export_all, args=(bagname, args.overwrite_existing))
                p.start()

                # pause to wait for the ros port to get set up so we don't try
                # to create multiple ros's
                time.sleep(10)

                procs.append(p)
                #export_all(bagname, args.overwrite_existing)

            for p in procs:
                p.join()

