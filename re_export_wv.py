import os
import sys
import glob

import argparse
from pathlib import Path
from audio_raw2wavpack import raw_to_wavpack

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='export wv from a bunch of raw audio files')
    parser.add_argument(
        'target_dir', help='target directory containing bags to extract data from')
    parser.add_argument(
        'task_id', type=int, default=0, help='slurm array task id')
    parser.add_argument(
        'num_tasks', type=int, default=1, help='total number of slurm tasks')
    
    args = parser.parse_args()

    raw_names = glob.glob(os.path.join(args.target_dir,'*_files/aviary_*_audio.raw'))
    raw_names.sort()

    # split file list in to even chunks
    task_raws = [raw_names[i:i+args.num_tasks] for i in range(0, len(raw_names), args.num_tasks)]

    this_tasks_raws = [tb[args.task_id] for tb in task_raws if len(tb) > args.task_id]

    for rawname in this_tasks_raws:

        outname = rawname.replace("_audio.raw", "_audio.wv")
        print(outname)
        
        raw_to_wavpack(rawname, in_num_channels=24, out_channels=None, output_file=outname, rate=48000)


    

    
