#!/usr/bin/env python

# WARNING: this file is in Python 2 because rosbag and rospy
#       are needed for reading ROS bags and they work 
#       much better with Python 2.

# Modified from a pervious version by Bernd Pfrommer, 2019, to support multiple segments
# https://github.com/daniilidis-group/bird_recording/blob/master/src/slice_bag.py

import rosbag, rospy
import sys, os, time
import argparse
import datetime
import time
import pytz
import csv

from pathlib2 import Path

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

def find_start_end_time(in_bag, args):
    """Get ROS start and end times.

    Keyword arguments:
    in_bag -- a bag of rosbag.Bag class
    args.timing_file -- a csv file with one row (start, stop) for each slice to produce

    If no timing file is present:
        args.start -- start at this rostime
        args.start_time_of_day -- if no start rostime is present, start at this time of day
        args.end -- end at this rostime
        args.duration -- if no end rostime is present, export for this duration
    """
    t_bag_start = in_bag.get_start_time()
    t_bag_end   = in_bag.get_end_time()
    print 'start bag time:   %15.2f' % t_bag_start, \
        ' = ', to_datetime(t_bag_start)
    print 'end bag   time:   %15.2f' % t_bag_end, \
        ' = ', to_datetime(t_bag_end)

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
                t_start = 0.0
        t_end = args.end

        # if args.end is None (i.e. no flag was given and the parser assigned None)
        if not args.end:

            # use the duration argument (args.duration is in seconds)
            if args.duration:
                t_end = t_start + args.duration

            # or stop at the end of the bag if no stop or duration was given
            else:
                t_end = float(sys.maxint)
                
        print "start slice time: %15.2f" % t_start, " = ", str(to_datetime(t_start))
        print "end   slice time: %15.2f" % t_end,   " = ", str(to_datetime(t_end))

        # If you wanted to implement a "chunks" feature where you could add an num_chunks arguemnt that would
        # split the start and stop range into num_chunks separate bags during exporting, this is where you would do it!
        # if args.num_chunks:
        #   # split the time range into a list of several time ranges 

        # Form start and end rostimes into a list of one touple, since this is the same format
        # returned by the timing file block
        return [(rospy.Time(t_start), rospy.Time(t_end))]

class SlicedBag(rosbag.Bag):
    '''methods for adding messages to a bag only within a specified time range'''

    def __init__(self, out_dir, event_start, event_stop, custom_name=None, **kwargs):

        # each bag object will keep track of its own target start and stop times 
        # so we can check with each bag whether we should write to it
        self.time_start=event_start
        self.time_stop=event_stop

        self.date = time.localtime(self.time_start.to_sec())
        self.date = time.strftime("%Y-%m-%d", self.date)

        if custom_name:
            self.out_bag_name = os.path.join(
                out_dir, custom_name)
        else:
            self.out_bag_name = os.path.join(
                out_dir, 'aviary_{}_{:.03f}-{:.03f}_slice.bag'.format(
                    self.date, 
                    self.time_start.to_sec(),
                    self.time_stop.to_sec()))

        # initialize the rest of the rosbag.Bag object
        super(SlicedBag, self).__init__(self.out_bag_name, **kwargs)

    def should_write_message(self, t):
        """Check by rostime if a message should be written"""
        return t >= self.time_start and t <= self.time_stop

    def done_writing(self, t):
        """Check if a bag is finished writing messages"""
        return t >= self.time_stop


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Cut one or more time slices from a ROS bag.',
        formatter_class =
        argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        '--out_bag', '-o', action='store', default=None,
        help='name of the sliced output bag (currently not used because slices are autonamed with rostime)')
    timingfile = parser.add_argument_group('timing file')
    timingfile.add_argument(
        '--timing_file', '-f', action='store', default=None, type=str,
        help='Filename of file containing relative timing of events to slice.')
    timingfile.add_argument(
        '--out_dir', action='store', default='/archive/birds/aviary/data2019/long_videos/', type=str,
        help='location of saved bags')
    parser.add_argument(
        '--start', '-s', action='store', default=None, type=float,
        help='Rostime representing where to start in the bag.')
    parser.add_argument(
        '--start_time_of_day', '-t', action='store', default=None,
        help='what time of the day to start, i.e. \'08:00:10\'.')
    parser.add_argument(
        '--duration', '-d', action='store', default=None, type=float,
        help='how many seconds to slice.')
    parser.add_argument(
        '--end', '-e', action='store', type=float,
        help='Rostime representing where to stop in the bag.')
    parser.add_argument(
        '--chunk_threshold', '-c', action='store', default=None, type=int,
        help='chunk threshold in bytes.')
    parser.add_argument('bagfile')

    # Parse input arguments and make a rosbag.Bag object
    args    = parser.parse_args(rospy.myargv()[1:])
    print "opening bag ", args.bagfile
    in_bag  = rosbag.Bag(args.bagfile, mode = 'r')
    cthresh = args.chunk_threshold if args.chunk_threshold else \
              in_bag.chunk_threshold
    print "using chunk threshold of ", cthresh
    
    # get a list of start and end rostimes for each (or maybe just one) chunk
    start_stops = find_start_end_time(in_bag, args)

    out_dir = args.out_dir

    # make the directory where bag slices will be saved
    print("output directory:{}".format(out_dir))
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # If out_bag is set, the bag will be set with that name. Otherwise
    # split bag chunks will be saved as aviary_<date>_<start_rostime>-<end_rostime>_slice.bag
    
    # create a list of SlicedBag objects that we will write messages to as we step through
    # the original bag messages
    out_bags = [SlicedBag(out_dir, event_start, event_stop, args.out_bag,
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
        for i, bag in enumerate(out_bags):

            # If the current message is within the time range for the bag, write the message to the bag
            if bag.should_write_message(t):
                #print("writing message to {}.".format(bag.out_bag_name))
                bag.write(topic, msg, t)

            # If the current message is past the end time for the bag, stop writing and close the bag
            if bag.done_writing(t):
                #print("finished bag {}.".format(bag.out_bag_name))
                bag.close()

                # and remove the bag from the out_bag list
                finished_bags.append(i)

        # keep only the bags that have not finished
        out_bags = [bag for i, bag in enumerate(out_bags) if i not in finished_bags]

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

    print "finished processing in ", time.time() - t0