import numpy as np
import cv2

import torch

from torchvision import transforms as T
from torchvision.models.detection.backbone_utils import resnet_fpn_backbone
from torchvision.models.detection.transform import GeneralizedRCNNTransform
from torchvision.models.detection.mask_rcnn import MaskRCNN

class BirdDetectionNet(MaskRCNN):
    """Class for building a bird detecctor model.

    Uses a finetuned Mask R-CNN to detect cowbirds.

    Args:
        device (str): 'cuda' or 'cpu'
        model_weights (str): path to model weights

    Attributes:
        model: the MaskRCNN model

    """

    def __init__(self, device='cuda', model_weights='models/detector.pth'):
        print("Loading detection network")

        # Load a maskRCNN finetuned on our birds
        network_transform = GeneralizedRCNNTransform(800, 1333, (0,0,0), (1,1,1))
        backbone = resnet_fpn_backbone(backbone_name='resnet101', pretrained=False)

        super().__init__(backbone, num_classes=2)
        self.transform = network_transform
        self.eval()
        self.load_state_dict(torch.load(model_weights))
        self.to(device)

class BirdDetector:
    def __init__(self, device='cuda', model_weights='models/detector.pth', detection_threshold=0.7, mask_threshold=0.75):
        self.device = device
        self.detection_threshold = 0.7
        self.mask_threshold = 0.75
        self.bird_net = BirdDetectionNet(device = device, model_weights = model_weights)
        self.input_transform = T.Compose([
            T.ToTensor(),
            T.Normalize(mean=[102.9801, 115.9465, 122.7717], std=[1., 1., 1.])
            ])

    def get_detection_outputs(self, output):
        confident = (output['scores'] > self.detection_threshold)
        bird = (output['labels'] == 1) # for class birds
        select = confident * bird
        conf = output['scores'][select].cpu().numpy()
        boxes = output['boxes'][select].cpu().numpy()
        masks = output['masks'][select].squeeze(1) > self.mask_threshold
        masks = masks.cpu().numpy()

        centroids = self.find_centroids(masks)

        return boxes, centroids, masks, conf

    def find_centroids(self, binary_image_batch):
        """Find the centroids for a batch of binary images (i.e. masks).

        TODO: Probably can speed this up by cropping to the bboxes first

        """
        centroids = []
        for bi in binary_image_batch:
            moments = cv2.moments(bi.astype(np.uint8), binaryImage=True)
            if moments['m00'] == 0:
                centroids.append([None,None])
            else:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])
                centroids.append([cx, cy])

        return centroids

    def __call__(self, image_batch):
        """Run detector on an image_batch."""
        # prep frames for Mask R-CNN input

        frames = image_batch[:,:,:,[2,1,0]].astype(np.float32)
        frames = torch.stack([self.input_transform(f) for f in frames], axis = 0).float()

        # Detection output
        with torch.no_grad():
            batch_outputs = self.bird_net(frames.to(self.device))

        outputs = [{
            'boxes':None,
            'masks':None,
            'centroids':None
            } for i in range(image_batch.shape[0])]

        for view_num, out in enumerate(batch_outputs):

            boxes, centroids, masks, conf = self.get_detection_outputs(out)

            outputs[view_num]['boxes'] = np.array(boxes)
            outputs[view_num]['centroids'] = np.array(centroids)
            outputs[view_num]['masks'] = np.array(masks)
            outputs[view_num]['confidences'] = np.array(conf)

        return outputs


def test_model():

    import os
    import cv2
    import numpy as np

    def create_color_mask(mask):
        color = ((np.random.random((1, 3))*0.6+0.4)*255).astype(int).tolist()[0]
        color_mask = np.zeros([mask.shape[0], mask.shape[1], 3]).astype(int)
        color_mask[mask==1] = color
        return color_mask

    img_file = os.path.join(
        "/data/aviary/tracking",
        "aviary_2019-04-01_1554119100.000-1554120000.000_files/frames",
        "aviary_2019-04-01_1554119100.000-1554120000.000_view2.png")

    # Fake frame_num, rostime
    frame_num = 13
    rostime = 1554119100.000
    rostime_idx = 16

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = BirdDetectionNet(device=device, model_weights='models/detector.pth')

    normalize = T.Normalize(
        mean=[102.9801, 115.9465, 122.7717], std=[1., 1., 1.]
        )

    img = cv2.imread(img_file)
    img = normalize(torch.tensor(img).float().permute(2,0,1))

    # Run detector
    with torch.no_grad():
        output = model([img.to(device)])[0]

    # MOT format detection output
    confident = (output['scores'] > 0.7)  #confidence of 80%
    bird = (output['labels'] == 1)       #for class birds
    select = confident * bird
    conf = output['scores'][select].cpu().numpy()
    boxes = output['boxes'][select].cpu().numpy()
    masks = output['masks'][select].cpu().numpy()

    boxes = [[box[0], box[1], box[2]-box[0], box[3]-box[1]] for box in boxes]
    box_strings = [', '.join([str(i) for i in box]) for box in boxes]

    # Output files will be of the format:
    # <frame>, <id>, <bb_left>, <bb_top>, <bb_width>, <bb_height>, <conf>, <rostime>, <video_loader_idx>

    # This is how to write them to a file:
    # box_filename = vid_file.replace('.mp4', '_boxes.txt')
    # file = open(box_filename, "w")

    file_lines = [f"{frame_num}, -1, {bs}, {cf}, {rostime}, {rostime_idx}\n" 
                                    for bs, cf in zip(box_strings, conf)]

    # file.writelines(file_lines)
    # file.close()

    # We will just print them instead
    print(f"Detected {len(file_lines)} birds:")                                
    for line in file_lines:
        print(line)


    # Visualization
    confident = (output['scores'] > 0.80)
    bird = (output['labels'] == 1)
    select = confident * bird
    masks = output['masks'][select].squeeze(1) > 0.75
    masks = masks.cpu()
    valid_mask = masks.sum(dim=0)>0

    color_masks = []
    for mask in masks:
        color_mask = create_color_mask(mask)
        color_masks.append(color_mask)
    color_masks = np.stack(color_masks, axis=0).sum(axis=0)

    img = cv2.imread(img_file)[:,:,[2,1,0]]
    img[valid_mask] = 0.4*img[valid_mask] + 0.6*color_masks[valid_mask]
    img = img[:,:,[2,1,0]]

    cv2.imshow('output masks', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    test_model()