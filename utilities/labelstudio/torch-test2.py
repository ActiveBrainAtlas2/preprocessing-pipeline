import argparse
import os, sys
import numpy as np
import torch
import torch.utils.data
from PIL import Image
import pandas as pd
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from engine import train_one_epoch, evaluate
import utils
import transforms as T


def create_box_df(animal, prep, dfpath):
    data = []
    INPUT = os.path.join(prep, 'thumbnail_masked')
    masks = sorted(os.listdir(INPUT))
    for file in masks:
        maskfile = os.path.join(INPUT, file)
        mask = Image.open(maskfile)
        mask = np.expand_dims(mask, axis=0)

        pos = np.where(np.array(mask)[0, :, :])
        xmin = np.min(pos[1])
        xmax = np.max(pos[1])
        ymin = np.min(pos[0])
        ymax = np.max(pos[0])
        data.append([file, xmin, ymin, xmax, ymax])
        #data[maskfile] = [xmin, ymin, xmax, ymax]

    df = pd.DataFrame(data, columns = ['filename', 'xmin', 'ymin', 'xmax', 'ymax'])
    df['xmin'] = pd.to_numeric(df['xmin'])
    df['ymin'] = pd.to_numeric(df['ymin'])
    df['xmax'] = pd.to_numeric(df['xmax'])
    df['ymax'] = pd.to_numeric(df['ymax'])
    df.to_csv(dfpath)

def parse_one_annot(dfpath, filename):
   data = pd.read_csv(dfpath)
   boxes_array = data[data["filename"] == filename][["xmin", "ymin", "xmax", "ymax"]].values
   return boxes_array


class MaskDataset(torch.utils.data.Dataset):
    def __init__(self, root, data_file, transforms=None):
        self.root = root
        self.transforms = transforms
        self.input_path = 'CH1/normalized'
        self.imgs = sorted(os.listdir(os.path.join(root, self.input_path)))
        self.path_to_data_file = data_file

    def __getitem__(self, idx):
        # load images and bounding boxes
        img_path = os.path.join(self.root, self.input_path, self.imgs[idx])
        img = Image.open(img_path).convert("L")
        box_list = parse_one_annot(self.path_to_data_file, 
        self.imgs[idx])
        boxes = torch.as_tensor(box_list, dtype=torch.float32)

        num_objs = len(box_list)
        # there is only one class
        labels = torch.ones((num_objs,), dtype=torch.int64)
        image_id = torch.tensor([idx])
        area = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:,0])
        # suppose all instances are not crowd
        iscrowd = torch.zeros((num_objs,), dtype=torch.int64)
        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        target["image_id"] = image_id
        target["area"] = area
        target["iscrowd"] = iscrowd

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
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--create', help='create volume', required=False, default='false')
    
    args = parser.parse_args()
    animal = args.animal
    create = bool({'true': True, 'false': False}[args.create.lower()])
    PREP = os.path.join(f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps')
    dfpath = os.path.join(PREP, 'boxes.csv')
    if not os.path.exists(dfpath):
        print(f'Creating bounding box csv file {dfpath}')
        data = create_box_df(animal, PREP, dfpath)

    dataset = MaskDataset(root= PREP, data_file= dfpath, transforms = get_transform(train=True))
    dataset_test = MaskDataset(root= PREP, data_file= dfpath, transforms = get_transform(train=False))

    # split the dataset in train and test set
    torch.manual_seed(1)
    indices = torch.randperm(len(dataset)).tolist()
    test_cases = int(len(indices) * 0.15)
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
        torch.device('cpu')
        print('Using CPU')
    # our dataset has two classes only - mask and not mask
    num_classes = 2
    modelpath = os.path.join(PREP, 'model.pth')
    datatestpath = os.path.join(PREP, 'data_loader_test.pth')
    torch.save(data_loader_test, datatestpath)
    if create:
        # get the model using our helper function
        model = get_model(num_classes)
        # move model to the right device
        model.to(device)
        # construct an optimizer
        params = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.SGD(params, lr=0.005,
                                momentum=0.9, weight_decay=0.0005)
        # and a learning rate scheduler which decreases the learning rate by # 10x every 3 epochs
        lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

        # let's train it for 10 epochs
        num_epochs = 10
        for epoch in range(num_epochs):
            # train for one epoch, printing every 10 iterations
            train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=5)
            # update the learning rate
            lr_scheduler.step()
        # evaluate on the test dataset
        evaluate(model, data_loader_test, device=device)


        torch.save(model.state_dict(), modelpath)
