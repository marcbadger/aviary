import os
import sys
import time

import rosbag
import rospy

class SlicedBag(rosbag.Bag):
    '''methods for adding messages to a bag only within a specified time range'''

    def __init__(self, out_dir, event_start, event_stop, **kwargs):

        # each bag object will keep track of its own target start and stop times 
        # so we can check with each bag whether we should write to it
        self.time_start=event_start
        self.time_stop=event_stop

        self.date = time.localtime(self.time_start.to_sec())
        self.date = time.strftime("%Y-%m-%d", self.date)

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