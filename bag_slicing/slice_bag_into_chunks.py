#!/usr/bin/env python

# Modified from a pervious version by Bernd Pfrommer, 2019, to support multiple segments
# https://github.com/daniilidis-group/bird_recording/blob/master/src/slice_bag.py

import os
import sys
import time

import rosbag
import rospy
import numpy as np

import argparse
import datetime
import time
import pytz
import csv

from pathlib import Path

from bag_slicing import SlicedBag

tz = pytz.timezone('US/Eastern')

def utc_to_local(utc_dt):
    """Convert datetime timezone"""
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(tz)
    return tz.normalize(local_dt)

def to_datetime(utc_sec):
    """Convert utc seconds to local timezone datetime"""
    dt = utc_to_local(
        datetime.datetime(1970,1,1,tzinfo=pytz.utc) +
        datetime.timedelta(seconds=utc_sec))
    return (dt)

def utc_time_since_epoch(dt):
    """Convert local timezone datetime to utc since epoch"""
    return ((dt - datetime.datetime(1970,1,1,tzinfo=pytz.utc)).total_seconds())

def find_start_end_times(in_bag, args):
    """Get ROS start and end times from a bag.

    Args:
        in_bag (rosbag.Bag): a bag
        args.timing_file: a csv file with one row (start, stop) for each slice to produce
        args.start_ros: if no timing file is present, start at this rostime
        args.start_time_of_day: if no start rostime is present, start at this time of day
        args.end_ros: end at this rostime
        args.duration: if no end rostime is present, export for this duration
        args.chunk_duration: (unit: MINUTES) optionally slice the bag into shorter segments

    Returns:
        chunks: a list of tuples of rospy.Time objects like [(start0, end0), (start1, end1)]

    """
    t_bag_start = in_bag.get_start_time()
    t_bag_end   = in_bag.get_end_time()
    print('start bag time:   %15.2f' % t_bag_start, \
        ' = ', to_datetime(t_bag_start))
    print('end bag   time:   %15.2f' % t_bag_end, \
        ' = ', to_datetime(t_bag_end))

    # if a timing file is present, we use that
    if args.timing_file:
        with open(args.timing_file, 'r') as infile:
            inlist = csv.reader(infile, delimiter=',')

            # for each line in the timing file, convert elements 0 and 1 to rospy.Time objects and add them to a list
            # (note this is a list comprehension: https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)
            start_stops = [(
                rospy.Time(float(ll[0])),
                rospy.Time(float(ll[1])))
                 for ll in inlist] # if ll[1] == "song"]
        return start_stops

    # otherwise we will check for other input arguemnts
    else:
        t_start = args.start

        # if args.start is None (i.e. no flag was given and the parser assigned None)
        if not args.start:

            # check if there is a start_time_of_day
            if args.start_time_of_day:

                # retrieve the date and time the input bag started
                t_0 = to_datetime(t_bag_start)

                # split into hours, minutes, seconds using ":" (input was "HH:MM:SS")
                hms = args.start_time_of_day.split(':')

                # keep the date, but make new hour, minute, and second info
                t_00 = t_0.replace(hour=int(hms[0]), minute=int(hms[1]),
                                   second=int(hms[2]), microsecond=0)

                # convert it to a rostime
                t_start = utc_time_since_epoch(t_00)

            # otherwise, start at the beginning of the bag
            else:
                t_start = int(np.ceil(t_bag_start))
        
        t_end = args.end
        # if args.end is None (i.e. no flag was given and the parser assigned None)
        if not args.end:

            # use the duration argument (args.duration is in seconds)
            if args.duration:
                t_end = t_start + args.duration

            # or stop at the end of the bag if no stop or duration was given
            else:
                t_end = int(np.floor(t_bag_end))
                
        print("start slice time: %15.2f" % t_start, " = ", str(to_datetime(t_start)))
        print("end   slice time: %15.2f" % t_end,   " = ", str(to_datetime(t_end)))

        # Optionally split the time range into a list of several time ranges 
        if args.chunk_duration:
            print(f"Splitting into {args.chunk_duration} minute chunks")
            cd_seconds = int(args.chunk_duration*60)
            starts = [t_start + ss for ss in range(0, int(t_end-t_start), cd_seconds)]
            ends = [min(t_end, ss + cd_seconds + args.chunk_overlap) for ss in starts]
            chunks = [(rospy.Time(ss), rospy.Time(ee)) for ss, ee in zip(starts, ends)]
        
        # Form start and end rostimes into a list of touples, since this is the same format
        # returned by the timing file block
        else:
            chunks = [(rospy.Time(t_start), rospy.Time(t_end))]

        return chunks

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Cut one or more time slices from a ROS bag.',
        formatter_class =
        argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('bagfile')
    parser.add_argument(
        '--out_dir', default='/archive/birds/aviary/data2022/tutorial/', type=str,
        help='Location of saved bags')

    timingfile = parser.add_argument_group('timing file')
    timingfile.add_argument(
        '--timing_file', default=None, type=str,
        help='Filename of file containing rostime start and end of events to slice.')
    
    manual_timing = parser.add_argument_group('manual timing')
    start_group = manual_timing.add_mutually_exclusive_group()
    start_group.add_argument(
        '--start', default=None, type=float,
        help='Rostime representing where to start in the bag.')
    start_group.add_argument(
        '--start_time_of_day', default=None,
        help='What time of the day to start, i.e. \'08:00:10\'.')

    end_group = manual_timing.add_mutually_exclusive_group()
    end_group.add_argument(
        '--end', type=float,
        help='Rostime representing where to stop in the bag.')
    end_group.add_argument(
        '--duration', default=None, type=float,
        help='How many seconds to slice.')
    
    chunking_behavior = parser.add_argument_group('chunking behavior')
    chunking_behavior.add_argument(
        '--chunk_duration', default=None, type=float,
        help='Split the bag into separate chunks, each of length chunk_duration (in minutes).')
    chunking_behavior.add_argument(
        '--chunk_overlap', default=0.5, type=float,
        help='Overlap of chunks in seconds. Video exported from bags begins only once all video ' +
             'streams have encountered a keyframe. If overlap is less than ~0.5 seconds, frames ' +
             'might be missing between chunks.')
    
    parser.add_argument(
        '--chunk_threshold', default=10000000, type=int,
        help='Chunk threshold in bytes.')
    

    # Parse input arguments and make a rosbag.Bag object
    args    = parser.parse_args(rospy.myargv()[1:])
    print("opening bag ", args.bagfile)
    in_bag  = rosbag.Bag(args.bagfile, mode = 'r')
    cthresh = args.chunk_threshold if args.chunk_threshold else \
              in_bag.chunk_threshold
    print("using chunk threshold of ", cthresh)
    
    # get a list of start and end rostimes for each (or maybe just one) chunk
    start_stops = find_start_end_times(in_bag, args)

    out_dir = args.out_dir

    # make the directory where bag slices will be saved
    print("output directory:{}".format(out_dir))
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # split bag chunks will be saved as aviary_<date>_<start_rostime>-<end_rostime>_slice.bag
    # see SlicedBag in bag_slicing.py
    
    # create a list of SlicedBag objects that we will write messages to as we step through
    # the original bag messages
    out_bags = [SlicedBag(out_dir, event_start, event_stop,
                  mode='w', chunk_threshold=cthresh) for event_start, event_stop in start_stops]

    if not out_bags:
        sys.exit("No bags to export!")

    # Find the earliest start time and latest end time of all output bags
    t_start_all = min([ob.time_start for ob in out_bags])
    t_stop_all = max([ob.time_stop for ob in out_bags])

    print("Out bag rostimes:")
    for bag in out_bags:
        print("{}: {:06f}-{:06f}".format('slice', bag.time_start.to_sec(), bag.time_stop.to_sec()))

    # This iterator steps through each message stored in the bag
    iterator = in_bag.read_messages(start_time=t_start_all, end_time=t_stop_all)
    
    # Save a time for deciding when to print saving information
    t0 = time.time()
    num_prints = 20
    
    # Total time range we have to scan through in the original bag
    total_time = (t_stop_all - t_start_all).to_sec()

    # Record the next time to print saving information
    next_print_time = t_start_all + rospy.Duration(total_time / num_prints)

    # Now step through the messages in the bag (each message has a topic, message, and rostime)
    for (topic, msg, t) in iterator:

        # Keep track of finished bag indices
        finished_bags = []

        # For each output bag in out_bags (non-finished bags)
        for bag in out_bags:

            # If the current message is within the time range for the bag, write the message to the bag
            if bag.should_write_message(t):
                #print("writing message to {}.".format(bag.out_bag_name))
                bag.write(topic, msg, t)

            # If the current message is past the end time for the bag, stop writing and close the bag
            if bag.done_writing(t):
                #print("finished bag {}.".format(bag.out_bag_name))
                bag.close()

                # and remove the bag from the out_bag list
                finished_bags.append(bag.out_bag_name)

        # keep only the bags that have not finished
        out_bags = [bag for bag in out_bags if bag.out_bag_name not in finished_bags]

        # If it is time to print saving information
        if t > next_print_time:
            print("completed: %5.2f%% remaining: %5.2fs" % \
                ((next_print_time - t_start_all).to_sec() / total_time * 100,
                 (t_stop_all - next_print_time).to_sec() * (time.time() - t0) /
                 (next_print_time - t_start_all).to_sec()))
            next_print_time = next_print_time + \
                              rospy.Duration(total_time / num_prints)

    # Close any leftover bags if we are out of messages in the source bag
    for bag in out_bags:
        bag.close()

    print("finished processing in ", time.time() - t0)