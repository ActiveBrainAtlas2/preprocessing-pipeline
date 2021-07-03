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
HOME = os.path.expanduser("~")
import cv2

def create_box_df(dfpath):
    data = []
    INPUT = os.path.join(HOME, 'programming/brains/thumbnail_masked')
    masks = sorted(os.listdir(INPUT))
    for file in masks:
        maskfile = os.path.join(INPUT, file)
        mask = Image.open(maskfile)
        mask = np.expand_dims(mask, axis=0)

        pos = np.where(np.array(mask)[0, :, :])
        limit = 2
        xmin = np.min(pos[1]) - limit
        xmax = np.max(pos[1]) + limit
        ymin = np.min(pos[0]) - limit
        ymax = np.max(pos[0]) + limit
        data.append([file, xmin, ymin, xmax, ymax])

    df = pd.DataFrame(data, columns = ['filename', 'xmin', 'ymin', 'xmax', 'ymax'])
    df['xmin'] = pd.to_numeric(df['xmin'])
    df['ymin'] = pd.to_numeric(df['ymin'])
    df['xmax'] = pd.to_numeric(df['xmax'])
    df['ymax'] = pd.to_numeric(df['ymax'])
    df.to_csv(dfpath, index=False, header=True)


def list_contours():
    INPUT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK41/preps/thumbnail_masked'
    OUTPUT = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK41/preps/thumbnail_contour'
    os.makedirs(OUTPUT, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    for file in files:
        infile = os.path.join(INPUT, file)
        outfile = os.path.join(OUTPUT, file)
        img = cv2.imread(infile, -1)
        img[img > 0] = 255
        ret, thresh = cv2.threshold(img, 127, 255, 0)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) != 1:
            print('unique values', np.unique(img))
            # Find the index of the largest contour
            areas = [cv2.contourArea(c) for c in contours]
            max_index = np.argmax(areas)
            print(f'{file} biggest contour is {max_index}', end="\t")
            del contours[max_index]
            cv2.fillPoly(img, contours, 100);
            print('unique values', np.unique(img))
            print()
        cv2.imwrite(outfile, img)


def parse_one_annot(dfpath, filename):
   data = pd.read_csv(dfpath)
   boxes_array = data[data["filename"] == filename][["xmin", "ymin", "xmax", "ymax"]].values
   return boxes_array


class MaskDataset(torch.utils.data.Dataset):
    def __init__(self, root, data_file, transforms=None):
        self.root = root
        self.transforms = transforms
        self.imgs = sorted(os.listdir(os.path.join(root, 'programming/brains/normalized')))
        self.masks = sorted(os.listdir(os.path.join(root, 'programming/brains/thumbnail_masked')))
        self.path_to_data_file = data_file

    def __getitem__(self, idx):
        # load images and bounding boxes
        img_path = os.path.join(self.root, 'programming/brains/normalized', self.imgs[idx])
        img = Image.open(img_path).convert("L")
        
        #box_list = parse_one_annot(self.path_to_data_file, 
        #self.imgs[idx])
        #boxes = torch.as_tensor(box_list, dtype=torch.float32)

        num_objs = len(box_list)
        # there is only one class
        labels = torch.ones((num_objs,), dtype=torch.int64)
        image_id = torch.tensor([idx])
        #area = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:,0])
        ## masks
        mask_path = os.path.join(self.root, 'programming/brains/thumbnail_masked', self.masks[idx])
        mask = Image.open(mask_path) # 
        mask = np.array(mask)
        mask[mask > 0] = 255
        obj_ids = np.unique(mask)
        # print('1',obj_ids) = 0 or 255
        obj_ids = obj_ids[1:] 
        masks = mask == obj_ids[:, None, None]
        masks = torch.as_tensor(masks, dtype=torch.uint8)

        # suppose all instances are not crowd
        iscrowd = torch.zeros((num_objs,), dtype=torch.int64)
        target = {}
        #target["boxes"] = boxes
        target["labels"] = labels
        target["image_id"] = image_id
        #target["area"] = area
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
    parser.add_argument('--create', help='create volume', required=False, default='false')
    
    args = parser.parse_args()
    create = bool({'true': True, 'false': False}[args.create.lower()])
    dfpath = os.path.join(HOME, 'programming/brains/boxes.csv')
    if not os.path.exists(dfpath):
        print(f'Creating bounding box csv file {dfpath}')
        data = create_box_df(dfpath)

    dataset = MaskDataset(HOME, data_file= dfpath, transforms = get_transform(train=True))
    dataset_test = MaskDataset(HOME, data_file= dfpath, transforms = get_transform(train=False))

    # split the dataset in train and test set
    torch.manual_seed(1)
    indices = torch.randperm(len(dataset)).tolist()
    test_cases = int(len(indices) * 0.05)
    dataset = torch.utils.data.Subset(dataset, indices[:-test_cases])
    dataset_test = torch.utils.data.Subset(dataset_test, indices[-test_cases:])
    # define training and validation data loaders
    data_loader = torch.utils.data.DataLoader(
                dataset, batch_size=2, shuffle=True, num_workers=4,
                collate_fn=utils.collate_fn)
    data_loader_test = torch.utils.data.DataLoader(
            dataset_test, batch_size=1, shuffle=False, num_workers=4,
            collate_fn=utils.collate_fn)
    print("We have: {} examples, {} are training and {} testing".format(len(indices), len(dataset), len(dataset_test)))

    if torch.cuda.is_available(): 
        device = torch.device('cuda') 
        print('Using GPU')
    else:
        device = torch.device('cpu')
        print('Using CPU')
    # our dataset has three classs, brain, tissue, nothing
    num_classes = 3
    modelpath = os.path.join(HOME, 'programming/brains/mask.model.pth')
    if create:
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
        epochs = 10
        for epoch in range(epochs):
            # train for one epoch, printing every 10 iterations
            train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10)
            # update the learning rate
            lr_scheduler.step()
        # evaluate on the test dataset
        evaluate(model, data_loader_test, device=device)


        torch.save(model.state_dict(), modelpath)
        print('Finished with masks')
    else:
        list_contours()