import sys
import cv2
import numpy as np
import traceback


import torch
from matplotlib.pyplot import cm

import rospy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

from models import BirdDetector

def to_bayer(im):
    (height, width) = im.shape[:2]
    (B,G,R) = cv2.split(im)

    bayer = np.empty((height, width), np.uint8)

    # strided slicing for this pattern:
    #   R G
    #   G B
    bayer[0::2, 0::2] = R[0::2, 0::2] # top left
    bayer[0::2, 1::2] = G[0::2, 1::2] # top right
    bayer[1::2, 0::2] = G[1::2, 0::2] # bottom left
    bayer[1::2, 1::2] = B[1::2, 1::2] # bottom right

    return bayer

class detection_node:
    def __init__(self):

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # Load a maskRCNN finetuned on our birds
        self.bird_detector = BirdDetector(self.device)

        self.printed = False
        
        colors = cm.rainbow(np.linspace(0,1,16))
        self.show_colors = (colors[:,:3]*255).astype(int)

        self.start_node()



    def publish_image(self, msg, img):
        byr = to_bayer(img)
        msg.data = byr.tobytes()
        if not rospy.is_shutdown():
            self.pub.publish(msg)

    def annotate_image(self, img, detections):
        for i, (mask, bbox) in enumerate(zip(detections['masks'], detections['boxes'])):
            bb = bbox.astype(int)
            crop_mask = mask[bb[1]:bb[1]+bb[3],bb[0]:bb[0]+bb[2]]
            img[bb[1]:bb[1]+bb[3], bb[0]:bb[0]+bb[2]][crop_mask > 0] = self.show_colors[i % self.show_colors.shape[0]]

    def process_image(self, msg):
        try:
            if not self.printed:
                print(msg.header)
                print(msg.height, msg.width)
                print(msg.encoding)
                print(msg.is_bigendian)
                print(msg.step)
                self.printed = True

            orig = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, -1)
            bgrframe = cv2.cvtColor(orig, cv2.COLOR_BayerBG2BGR)

            detections = self.bird_detector(bgrframe[None,:,:,:])[0]

            self.annotate_image(bgrframe, detections)

            #bgrframe[600:800, 600:800, :] = 0

            self.publish_image(msg, bgrframe)

        except Exception as e:
            print(e)
            print(traceback.format_exc())


    def start_node(self):
        rospy.init_node('detection_node')
        rospy.loginfo('detection node started')

        self.pub = rospy.Publisher('/cam_sync/cam3/image_detections', Image, queue_size=10)

        rospy.Subscriber("/cam_sync/cam3/image_raw", Image, self.process_image)
        rospy.spin()

if __name__ == '__main__':
    try:
        detection_node()
    except rospy.ROSInterruptException:
        pass
