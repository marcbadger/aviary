#!/usr/bin/env python
#
# merge raw video and audio into one playable file
#

#import rospy
import argparse
import subprocess

def read_aux(fname):
    print("reading aux file %s" % fname)
    d={}
    lines = [line.rstrip('\n') for line in open(fname)]
    for line in lines:
        a = line.split()
        v = a[1] # value
        if a[0] == 'ros_start_time' or a[0] == 'ros_end_time' or a[0] == 'number_of_frames':
            v = int(a[1]) #long(a[1])
        if a[0] == 'channels' or a[0] == 'depth':
            v = int(a[1])
        if a[0] == 'rate':
            v = float(a[1])
        d[a[0]] = v
    return d

def merge_audio_and_video(audio_file='audio.raw',video_file='video.raw',
                          audio_aux='audio.aux',video_aux='video_aux',
                          output_file='video.mp4',channels=[0,1],video_format='copy',
                          return_string=False):
    
    map_channel  = " ".join(['-map_channel 1.0.%d' % i for i in channels])
    out_aac      = " ".join(['-c:a:%d aac -strict -2' % i for i in range(0,len(channels))])
    if video_format != 'copy':
        video_format = 'libx264 -crf 30 -pix_fmt yuv420p'
        #video_format = 'h264_nvenc -b:v 8 -pix_fmt yuv420p'


    audio_aux = read_aux(audio_aux)
    video_aux = read_aux(video_aux)
    audio_duration = (audio_aux['ros_end_time'] - audio_aux['ros_start_time']) / 1.0e9
    audio_rate = audio_aux['number_of_frames'] / audio_duration
    print("audio samples:  %ld " % audio_aux['number_of_frames'])
    print("audio duration: %.2fs, rate: %.2f (%.2f)" % (audio_duration, audio_rate, audio_aux['rate']))
    print("video duration: %.2fs" % ((video_aux['ros_end_time'] - video_aux['ros_start_time'])/1e9))
    video_delay = (video_aux['ros_start_time'] - audio_aux['ros_start_time']) /1e9
    delay_video = ""
    delay_audio = ""
    if video_delay > 0: # video is delayed
        delay_video = "-itsoffset %.4f" % video_delay
    else:
        delay_audio = "-itsoffset %.4f" % video_delay
    print("first_video_time - fist_audio_time: %.4fs " % video_delay)
    # bashCommand = "ffmpeg -y -r %f %s -i %s -f %s -ar %f -ac %d %s -i %s %s -c:v copy %s %s" % (
    bashCommand = "ffmpeg -y -r %f %s -i %s -f %s -ar %f -ac %d %s -i %s %s -c:v %s %s %s" % (
        video_aux['rate'], delay_video, video_file, 's24le',
        audio_aux['rate'], audio_aux['channels'], delay_audio,
        audio_file, map_channel, video_format, out_aac, output_file)

    if return_string:
        return bashCommand
        
    else:
        print(bashCommand)
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        print("wrote output to file: %s" % output_file)

def merge_audio_and_video_topbot(audio_file='audio.raw',video_file='video.raw',
                          audio_aux='audio.aux',video_aux='video_aux',
                          sequence_name='video',channels=[0,1],video_format='copy',
                          return_string=False):
    
    if video_format != 'copy':
        video_format = 'libx264 -crf 30 -pix_fmt yuv420p'
        #video_format = 'h264_nvenc -b:v 8 -pix_fmt yuv420p'


    audio_aux = read_aux(audio_aux)
    video_aux = read_aux(video_aux)
    audio_duration = (audio_aux['ros_end_time'] - audio_aux['ros_start_time']) / 1.0e9
    audio_rate = audio_aux['number_of_frames'] / audio_duration
    
    video_delay = (video_aux['ros_start_time'] - audio_aux['ros_start_time']) /1e9
    delay_video = ""
    delay_audio = ""
    if video_delay > 0: # video is delayed
        delay_video = "-itsoffset %.4f" % video_delay
    else:
        delay_audio = "-itsoffset %.4f" % video_delay
    
    top_out = sequence_name + "_top.mp4"
    bot_out = sequence_name + "_bot.mp4"

    audio_filter = (f"[1:a:0] pan=stereo|"
                    f"c0<0.166*c3+0.166*c4+0.166*c5+0.166*c9+0.166*c10+0.166*c11|"
                    f"c1<0.166*c15+0.166*c16+0.166*c17+0.166*c21+0.166*c22+0.166*c23 [topaout]; "
                    f"[1:a:0] pan=stereo|"
                    f"c0<0.166*c0+0.166*c1+0.166*c2+0.166*c6+0.166*c7+0.166*c8|"
                    f"c1<0.166*c12+0.166*c13+0.166*c14+0.166*c18+0.166*c19+0.166*c20 [botaout]"
                   )

    filter_complex = (f"[0:v] crop=in_w/4:in_h/2:in_w*(0/4):0 [topupperleft]; "
                      f"[0:v] crop=in_w/4:in_h/2:in_w*(1/4):0 [topupperright]; "
                      f"[0:v] crop=in_w/4:in_h/2:in_w*(2/4):0 [toplowerleft]; "
                      f"[0:v] crop=in_w/4:in_h/2:in_w*(3/4):0 [toplowerright]; "
                      f"[topupperleft][topupperright][toplowerleft][toplowerright] xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0 [topout]; "
                      f"[0:v] crop=in_w/4:in_h/2:in_w*(0/4):in_h/2 [botupperleft]; "
                      f"[0:v] crop=in_w/4:in_h/2:in_w*(1/4):in_h/2 [botupperright]; "
                      f"[0:v] crop=in_w/4:in_h/2:in_w*(2/4):in_h/2 [botlowerleft]; "
                      f"[0:v] crop=in_w/4:in_h/2:in_w*(3/4):in_h/2 [botlowerright]; "
                      f"[botupperleft][botupperright][botlowerleft][botlowerright] xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0 [botout]; "
                      f"{audio_filter}"
                     )

    # audio_filter = (f"[1:a:0]pan=stereo|"
    #                 f"c0<0.166*c3+0.166*c4+0.166*c5+0.166*c9+0.166*c10+0.166*c11|"
    #                 f"c1<0.166*c15+0.166*c16+0.166*c17+0.166*c21+0.166*c22+0.166*c23[topaout]; "
    #                 f"[1:a:0]pan=stereo|"
    #                 f"c0<0.166*c0+0.166*c1+0.166*c2+0.166*c6+0.166*c7+0.166*c8|"
    #                 f"c1<0.166*c12+0.166*c13+0.166*c14+0.166*c18+0.166*c19+0.166*c20[botaout]"
    #                )

    # filter_complex = (f"[0:v]crop=in_w/4:in_h/2:in_w*(0/4):0[topupperleft];"
    #                   f"[0:v]crop=in_w/4:in_h/2:in_w*(1/4):0[topupperright];"
    #                   f"[0:v]crop=in_w/4:in_h/2:in_w*(2/4):0[toplowerleft];"
    #                   f"[0:v]crop=in_w/4:in_h/2:in_w*(3/4):0[toplowerright];"
    #                   f"[topupperleft][topupperright][toplowerleft][toplowerright]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[topout];"
    #                   f"[0:v]crop=in_w/4:in_h/2:in_w*(0/4):in_h/2[botupperleft];"
    #                   f"[0:v]crop=in_w/4:in_h/2:in_w*(1/4):in_h/2[botupperright];"
    #                   f"[0:v]crop=in_w/4:in_h/2:in_w*(2/4):in_h/2[botlowerleft];"
    #                   f"[0:v]crop=in_w/4:in_h/2:in_w*(3/4):in_h/2[botlowerright];"
    #                   f"[botupperleft][botupperright][botlowerleft][botlowerright]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[botout];"
    #                   f"{audio_filter}"
    #                  )

    bashCommand = (f'ffmpeg -y '
                   f'-r {video_aux["rate"]:.06f} {delay_video} -i {video_file} '
                   f'-f s24le -ar {audio_aux["rate"]:.06f} -ac {audio_aux["channels"]} {delay_audio} -i {audio_file} '
                   f'-filter_complex "{filter_complex}" '
                   f'-map "[topout]" -c:v {video_format} -map "[topaout]" -c:a aac -strict -2 {top_out} '
                   f'-map "[botout]" -c:v {video_format} -map "[botaout]" -c:a aac -strict -2 {bot_out}'
                  )

    print(bashCommand)

    if return_string:
        return bashCommand
        
    else:
        print(bashCommand)
        process = subprocess.Popen(bashCommand, universal_newlines=True, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()
        print("wrote output to file: %s" % top_out)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='merge video and audio.',
                                     formatter_class =
                                     argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--audio_file', '-a', action='store',
                        default='audio.raw',
                        help='raw audio input file')
    parser.add_argument('--video_file', '-v', action='store',
                        default='video.raw',
                        help='raw video input file')
    parser.add_argument('--audio_aux', '-x', action='store',
                        default='audio.aux',
                        help='audio aux file')
    parser.add_argument('--video_aux', '-y', action='store',
                        default='video.aux',
                        help='video aux file')
    parser.add_argument('--output_file', '-o', action='store',
                        default='video.mp4',
                        help='output file name (if using topbot, this is the sequence_name)')
    parser.add_argument('-c','--channels', action='store',
                        help='list of output channels (start at 0,' +
                        '  maximum of 8!)',
                        default = None, required=False)
    parser.add_argument('--video_format', '-f', action='store',
                        default='libx264',
                        help='audio format (if not "copy" will be libx264)')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--topbot', action='store_true')
    #args = parser.parse_args(rospy.myargv()[1:])

    if not args.channels:
        args.channels = '0,1'
    channels = [int(item) for item in args.channels.split(',')]

    if args.all:
        merge_audio_and_video(audio_file=args.audio_file,video_file=args.video_file,
                          audio_aux=args.audio_aux,video_aux=args.video_aux,
                          output_file=args.output_file,channels=channels,video_format=args.video_format)
    else:
        print("Skipping full mosaic export.")

    if args.topbot:
        merge_audio_and_video_topbot(audio_file=args.audio_file,video_file=args.video_file,
                          audio_aux=args.audio_aux,video_aux=args.video_aux,
                          sequence_name=args.output_file,channels=channels,video_format=args.video_format)

    else:
        print("Skipping top and bottom mosaic exports.")