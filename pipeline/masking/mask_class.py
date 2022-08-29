import os
import numpy as np
import torch
from PIL import Image
import cv2
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor

import utils
import transforms as T


class MaskDataset(torch.utils.data.Dataset):
    def __init__(self, root, animal=None, transforms=None):
        self.root = root
        self.animal = animal
        self.transforms = transforms
        self.imgs = sorted(os.listdir(os.path.join(root, 'normalized')))
        self.masks = sorted(os.listdir(os.path.join(root, 'thumbnail_masked')))
        if self.animal is not None:
            self.imgs = sorted([img for img in self.imgs if img.startswith(animal)])
            self.masks = sorted([img for img in self.masks if img.startswith(animal)])

    def __getitem__(self, idx):
        # load images and bounding boxes
        img_path = os.path.join(self.root, 'normalized', self.imgs[idx])
        mask_path = os.path.join(self.root, 'thumbnail_masked', self.masks[idx])
        img = Image.open(img_path).convert("L")
        mask = Image.open(mask_path) # 
        mask = np.array(mask)
        mask[mask > 0] = 255
        ret, thresh = cv2.threshold(mask, 200, 255, 0)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for i, contour in enumerate(contours):
            x,y,w,h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            if area > 100:
                xmin = int(round(x))
                ymin = int(round(y))
                xmax = int(round(x+w))
                ymax = int(round(y+h))
                color = (i+10) * 10
                cv2.fillPoly(mask, [contour], color);
                boxes.append([xmin, ymin, xmax, ymax])
        obj_ids = np.unique(mask)
        obj_ids = obj_ids[1:]
        masks = mask == obj_ids[:, None, None]
        num_objs = len(obj_ids)



        # convert everything into a torch.Tensor
        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        # there is only one class
        labels = torch.ones((num_objs,), dtype=torch.int64)
        masks = torch.as_tensor(masks, dtype=torch.uint8)

        image_id = torch.tensor([idx])
        area = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0])        

        # suppose all instances are not crowd
        iscrowd = torch.zeros((num_objs,), dtype=torch.int64)
        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        target["image_id"] = image_id
        target["area"] = area
        target["iscrowd"] = iscrowd
        target["masks"] = masks

        if self.transforms is not None:
            img, target = self.transforms(img, target)
            return img, target

    def __len__(self):
        return len(self.imgs)

def get_model(num_classes):
    # load an object detection model pre-trained on COCO
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights="DEFAULT")
    #model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
    # get the number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # replace the pre-trained head with a new on
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    return model


def get_model_instance_segmentation(num_classes):
    # load an instance segmentation model pre-trained on COCO
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(weights="DEFAULT")
    #model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=True)
    # get number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # replace the pre-trained head with a new one
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    # now get the number of input features for the mask classifier
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    hidden_layer = 256
    # and replace the mask predictor with a new one
    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask, hidden_layer, num_classes)

    return model


def get_transform(train):
    transforms = []
    transforms.append(T.PILToTensor())
    transforms.append(T.ConvertImageDtype(torch.float))
    if train:
        transforms.append(T.RandomHorizontalFlip(0.5))
    return T.Compose(transforms)

def test_model(ROOT, animal):
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights="DEFAULT")
    dataset = MaskDataset(ROOT, animal, transforms = get_transform(train=True))
    data_loader = torch.utils.data.DataLoader(
    dataset, batch_size=1, shuffle=True, num_workers=1,
    collate_fn=utils.collate_fn)
    # For Training
    images,targets = next(iter(data_loader))
    images = list(image for image in images)
    targets = [{k: v for k, v in t.items()} for t in targets]
    output = model(images,targets)   # Returns losses and detections
    print('Output')
    print(output)
    # For inference
    model.eval()
    x = [torch.rand(3, 300, 400), torch.rand(3, 500, 400)]
    predictions = model(x)           # Returns predictions
    print()
    print('Predictions')
    print(predictions)
    print()


