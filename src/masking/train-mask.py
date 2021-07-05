import argparse
import os, sys
import numpy as np
from numpy.core.defchararray import translate
import torch
import torch.utils.data
from PIL import Image
import pandas as pd
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor

from engine import train_one_epoch, evaluate
import utils
import transforms as T
import cv2

ROOT = '/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks'



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
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
    # get the number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # replace the pre-trained head with a new on
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    return model


def get_model_instance_segmentation(num_classes):
    # load an instance segmentation model pre-trained pre-trained on COCO
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=True)
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
   # converts the image, a PIL image, into a PyTorch Tensor
   transforms.append(T.ToTensor())
   if train:
      # during training, randomly flip the training images
      # and ground-truth for data augmentation
      transforms.append(T.RandomHorizontalFlip(0.5))
   return T.Compose(transforms)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='specify animal', required=False)
    parser.add_argument('--runmodel', help='run model', required=True)
    
    args = parser.parse_args()
    runmodel = bool({'true': True, 'false': False}[args.runmodel.lower()])
    animal = args.animal

    dataset = MaskDataset(ROOT, animal, transforms = get_transform(train=True))
    dataset_test = MaskDataset(ROOT, animal, transforms = get_transform(train=False))

    # split the dataset in train and test set
    torch.manual_seed(1)
    indices = torch.randperm(len(dataset)).tolist()
    test_cases = int(len(indices) * 0.01)
    test_cases = max(test_cases, 10)
    dataset = torch.utils.data.Subset(dataset, indices[:-test_cases])
    dataset_test = torch.utils.data.Subset(dataset_test, indices[-test_cases:])
    # define training and validation data loaders
    data_loader = torch.utils.data.DataLoader(
                dataset, batch_size=2, shuffle=True, num_workers=4,
                collate_fn=utils.collate_fn)
    data_loader_test = torch.utils.data.DataLoader(
            dataset_test, batch_size=1, shuffle=False, num_workers=0,
            collate_fn=utils.collate_fn)
    print("We have: {} examples, {} are training and {} testing".format(len(indices), len(dataset), len(dataset_test)))

    if torch.cuda.is_available(): 
        device = torch.device('cuda') 
        print('Using GPU')
    else:
        device = torch.device('cpu')
        print('Using CPU')
    # our dataset has two classs, tissue or 'not tissue'
    num_classes = 2
    modelpath = os.path.join(ROOT, 'mask.model.pth')
    if runmodel:
        # get the model using our helper function
        model = get_model_instance_segmentation(num_classes)
        # move model to the right device
        model.to(device)
        # construct an optimizer
        params = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.SGD(params, lr=0.005,
                                momentum=0.9, weight_decay=0.0005)
        # and a learning rate scheduler which decreases the learning rate by # 10x every 3 epochs
        lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

        # 1 epoch takes 8 minutes on muralis
        epochs = 30
        for epoch in range(epochs):
            # train for one epoch, printing every 10 iterations
            train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10)
            # update the learning rate
            lr_scheduler.step()
            # evaluate on the test dataset
            evaluate(model, data_loader_test, device=device)


        torch.save(model.state_dict(), modelpath)
        print('Finished with masks')
