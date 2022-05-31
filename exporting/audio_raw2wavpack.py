#!/usr/bin/env python
#
# convert raw audio to wavpack using ffmpeg
#


import argparse
import subprocess

def raw_to_wavpack(raw_audio_file, in_num_channels=24, out_channels=None, output_file='audio.wv', rate=48000, return_string=False):

    if out_channels:
        map_channel  = " ".join(['-map_channel 0.0.%d' % i for i in out_channels])
        out_wavepack = " ".join(['-c:a:%d wavpack'     % i for i in out_channels])
    else:
        map_channel = ""
        out_wavepack = "-c:a wavpack"
        
    bashCommand = "ffmpeg -y -f %s -ar %f -ac %d -i %s %s %s %s" % (
        's24le', rate, in_num_channels, raw_audio_file,
        map_channel, out_wavepack, output_file)

    if return_string:
        return bashCommand
        
    else:
        print(bashCommand)
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        print("wrote output to file: %s" % output_file)

    bashCommand = f"ffmpeg -y -i {output_file} {output_file.replace('_audio.wv', '_audio.wav')}"
    print(bashCommand)
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print("converted audio to file to wav: %s" % output_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='write audio to ffmpeg.',
                                     formatter_class =
                                     argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c','--channels', action='store',
                        help='list of output channels (start at 0,' +
                        '  maximum of 8!)',
                        default = None, required=False)
    parser.add_argument('--output_file', '-o', action='store',
                        default='audio.wv',
                        help='output file name')
    parser.add_argument('--rate', '-r', action='store', default=48000,
                        type=float, help='recording rate of raw input file')
    parser.add_argument('raw_audio_file')

    args = parser.parse_args()

    in_num_channels=24

    if args.channels:
        channels = [int(item) for item in args.channels.split(',')]
    else:
        channels = args.channels

    raw_to_wavpack(args.raw_audio_file, in_num_channels=in_num_channels, out_channels=channels, output_file=args.output_file, rate=args.rate)

    
