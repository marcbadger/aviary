import json
import numpy as np

class JSONProcessor:
    def __init__(self, in_file_path, out_file_path=None):
       self.in_file_path = in_file_path
       self.out_file_path = out_file_path
       self.in_json = None 
       self.img_ros_dict = dict()
       self.img_view_dict = dict()
       self.data_list = []

       self.read_in_file()
       self.make_img_ros_dict()
    
    def read_in_file(self):
        with open(self.in_file_path) as in_file:
            self.in_json = json.load(in_file)

    def process_images(self, mode = 0, write_data_list = False, date = None, delta = 0.4):
        """
        Functionality:
        Reads images from self.in_json and uses self.img_ros_dict to join on images[id] = annotations[img_id] 
        to make and update self.data_list, and potentially write this data to a json file

        In mode 0 (single frame mode), each item in self.data_list looks like {'date_captured', 'file_name', 'id', 'ros'}
        In mode 1 (three frame mode), the items contain (in addition to the ones above) {'after_file_name', 'before_file_name', 'ros_after', 'ros_before'}


        Arguments:
        mode -- 0 for single frame mode, 1 for 3 frame mode (default 0)
        write_data_list -- writes extracted json to self.out_file_path - the output file should be a .json file (default False)
        date -- builds and writes for only the specified date, if specifed (default None)
        delta -- for mode 1, adds 'ros_before' and 'ros_after' attributes with +/- delta respectively (default 0.4)
        
        Returns:
        self.data_list 
        """
        self.data_list = []
        for i in self.in_json["images"]:
            if i["id"] in self.img_ros_dict:
                if mode == 1:
                    self.data_list.append({'id': i["id"] ,'file_name': i["file_name"] ,'date_captured': i["date_captured"], 'after_file_name': self.get_after_file_name(i["file_name"]), 'before_file_name': self.get_before_file_name(i["file_name"]), 'ros': float(self.img_ros_dict[i["id"]]), 'ros_before': float(self.img_ros_dict[i["id"]]) - delta, 'ros_after': float(self.img_ros_dict[i["id"]]) + delta}) 
                elif mode == 0:
                    self.data_list.append({'id': i["id"] ,'file_name': i["file_name"] ,'date_captured': i["date_captured"], 'ros': float(self.img_ros_dict[i["id"]])})        
        if (date):
            self.data_list = list(filter(lambda x: x['date_captured'] == date, self.data_list))
        if (write_data_list):
            self.write_to_out(self.data_list)
        return self.data_list
    
    
    def make_img_ros_dict(self):
        for i in self.in_json["annotations"]:
            self.img_ros_dict[i["image_id"]] = i["ros"]
            self.img_view_dict[i["image_id"]] = i["frame"]
        
        # uncomment if want to check # of unique image_id's in annotations
        #print(len(np.unique([ann["image_id"] for ann in self.in_json["annotations"]])))
        return self.img_ros_dict, self.img_view_dict
        
    def get_ros_tuples(self, mode = 0, delta = 0.4):
        """
        Functionality:
        Reads data from self.data_list and uses delta to create a list of [ros_start, ros_end] 
        where ros_start = ros - delta and ros_end = ros + delta

        In mode 0 (single frame mode), ros is mapped to [ros_start, ros_end] adding one entry per json object
        In mode 1 (three frame mode), ros, ros_before, ros_after are mapped to [ros_start, ros_end] adding three entries per json object


        Arguments:
        mode -- 0 for single frame mode, 1 for 3 frame mode (default 0)
        delta -- the delta in: ros_start = ros - delta and ros_end = ros + delta for creating each [ros_start, ros_end] (default 0.4)
        
        Returns:
        ros_tuples, the list of [ros_start, ros_end] 
        """
        ros_tuples = set()
        for i in self.data_list:
            ros_tuples.add((i['ros'] - delta, i['ros'] + delta))
            if (mode == 1):
                ros_tuples.add((i['ros_before'] - delta, i['ros_before'] + delta))
                ros_tuples.add((i['ros_after'] - delta, i['ros_after'] + delta))
        return ros_tuples

   
        
    def get_after_file_name(self, file_name):
        return str(format(int(file_name.split('.')[0]) + 1, '08d'))+ '.jpg'

    def get_before_file_name(self, file_name):
        return str(format(int(file_name.split('.')[0]) - 1, '08d')) + '.jpg'

    def write_to_out(self, output_string):
        with open(self.out_file_path, "w") as write_file:
            json.dump(output_string, write_file, indent=4, sort_keys=True)

if __name__ == '__main__':

    processor = JSONProcessor(r"/data/aviary/data/cowbird/annotations/instance.json", r"/data/aviary/data/cowbird/annotations/out.json")
    processor.read_in_file()
    processor.make_img_ros_dict()
    #processor.process_images(write_data_list=True)
    processor.process_images(write_data_list=True, date="2019-04-09", mode=1)
    processor.get_ros_tuples(mode=1)

