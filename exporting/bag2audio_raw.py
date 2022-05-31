#!/usr/bin/env python
#
# grab raw audio from bag
#

import rosbag, rospy, numpy as np
import time
import argparse
import os

def write_aux_file(fname, t0, t1, fmt, n):
    with open(fname, 'w') as f:
        f.write('ros_start_time %s\n' % t0)
        f.write('ros_end_time %s\n' % t1)
        f.write('number_of_frames %d\n' % n)
        f.write('channels %d\n' % fmt.channels)
        f.write('depth %d\n' % fmt.depth)
        f.write('rate %f\n' % fmt.rate)
    print("wrote aux file to %s" % fname)

def export_audio_raw(bagfile, aux_file='audio.aux', output_file='audio.raw',
                            start=0, end=1e60):
    
    topics = '/audio/audio_stamped'
    outfile_name = output_file
    outfile = open(outfile_name, 'wb')
    print("writing to file %s" % outfile_name)
    fbag = open(bagfile, 'r')
    fsize = os.fstat(fbag.fileno()).st_size
    print("opening bag %s of size %.3fGb" % (bagfile, fsize / 1e9))
    measured_rate = 147440988782 / 115.0 # bytes/second
    print("this is estimated to take %.3f seconds = %.3f mins" % (
        fsize / measured_rate, fsize / (60.0 * measured_rate)))
    t0_bag_open = time.time()
    bag     = rosbag.Bag(bagfile, 'r')
    print( "opening bag took %.2f seconds" % (time.time() - t0_bag_open))

    # Check if the bag has an audio topic
    msgs_topics = bag.get_type_and_topic_info()
    if topics not in msgs_topics[1]:
        raise Exception('Selected bag contains no audio topic!', msgs_topics)

    t_start = bag.get_start_time()
    t_end   = bag.get_end_time()
    ## Get absolute start/end times based on input arguments (which are relative)
    true_start = start + bag.get_start_time()
    true_end = end + bag.get_start_time()
    start_time = rospy.Time(max(true_start, bag.get_start_time()))
    end_time   = rospy.Time(min(true_end, bag.get_end_time()))
    total_time = (end_time - start_time).to_sec()
    num_prints = 20
    next_print_time = start_time + rospy.Duration(total_time / num_prints)
    iterator = bag.read_messages(topics=topics, start_time=start_time,
                                 end_time=end_time)
    t0 = time.time()
    print("now fetching audio")
    tstamp_first = None
    num_samples = 0
    fmt = None
    num_msgs = 0

    for (topic, msg, t) in iterator:
        if msg._type == 'audio_common_msgs/AudioDataStamped':
            if not tstamp_first:
                tstamp_first = msg.header.stamp
            if not fmt:
                channels = msg.format.channels
                nbytes   = msg.format.depth / 8
                fmt      = msg.format
            tstamp_last = msg.header.stamp
            
            arr = np.frombuffer(msg.data, dtype='uint8')
            num_samples = num_samples + arr.shape[0] / (channels * nbytes)
            num_msgs = num_msgs + 1
            outfile.write(msg.data)
        if t > next_print_time:
            print("completed: %5.2f%% remaining: %5.2fs" % \
                ((next_print_time - start_time).to_sec() / total_time * 100,
                 (end_time - next_print_time).to_sec() * (time.time() - t0) /
                 (next_print_time - start_time).to_sec()))
            next_print_time = next_print_time + \
                              rospy.Duration(total_time / num_prints)
    outfile.close()
    write_aux_file(aux_file, tstamp_first, tstamp_last, fmt, num_samples)
    print("finished writing %d messages to file %s " % (num_msgs, outfile_name))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
                                     'Extract raw audio from bag files.')
    parser.add_argument('--aux_file', '-a', action='store',
                        default='audio.aux', help='output aux file name')
    parser.add_argument('--output_file', '-o', action='store',
                        default='audio.raw', help='output raw audio file name')
    parser.add_argument('--start', '-s', action='store', default=0, type=float,
                        help='Rostime (bag time, large number!) ' +
                        'representing where to start in the bag.')
    parser.add_argument('--end', '-e', action='store', default=1e60,
                        type=float, help='Rostime (bag time, large number!) ' +
                        'representing where to stop in the bag.')
    parser.add_argument('bagfile')

    args = parser.parse_args(rospy.myargv()[1:])

    export_audio_raw(args.bagfile, aux_file=args.aux_file, output_file=args.output_file,
                            start=args.start, end=args.end)

    
