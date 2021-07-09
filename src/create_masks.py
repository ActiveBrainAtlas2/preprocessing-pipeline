import argparse
import os, sys
import numpy as np
import torch
import torch.utils.data
from PIL import Image
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
import cv2
from tqdm import tqdm

def combine_dims(a):
    if a.shape[0] > 0:
        a1 = a[0,:,:]
        a2 = a[1,:,:]
        a3 = np.add(a1,a2)
    else:
        a3 = np.zeros([a.shape[1], a.shape[2]]) + 255
    return a3

def greenify_mask(image):
    r = np.zeros_like(image).astype(np.uint8)
    g = np.zeros_like(image).astype(np.uint8)
    b = np.zeros_like(image).astype(np.uint8)
    r[image == 1], g[image == 1], b[image == 1] = [0,255,0]
    coloured_mask = np.stack([r, g, b], axis=2)
    return coloured_mask


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

def create_mask(animal):

    modelpath = os.path.join(HOME, '/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks/mask.model.pth')
    loaded_model = get_model_instance_segmentation(num_classes=2)
    if os.path.exists(modelpath):
        loaded_model.load_state_dict(torch.load(modelpath,map_location=torch.device('cpu')))
    else:
        print('no model to load')

    transform = torchvision.transforms.ToTensor()

    DIR = f'/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{animal}/preps'
    INPUT = os.path.join(DIR, 'CH1/normalized')
    MASKS = os.path.join(DIR, 'thumbnail_masked')
    TESTS = os.path.join(DIR, 'thumbnail_green')

    os.makedirs(MASKS, exist_ok=True)
    os.makedirs(TESTS, exist_ok=True)

    files = sorted(os.listdir(INPUT))
    debug = False
    for file in tqdm(files):
        filepath = os.path.join(INPUT, file)
        outpath = os.path.join(MASKS, file)
        green_mask_path = os.path.join(TESTS, file)

        if os.path.exists(outpath) and os.path.exists(green_mask_path):
            continue

        img = Image.open(filepath)
        input = transform(img)
        input = input.unsqueeze(0)
        loaded_model.eval()
        with torch.no_grad():
            pred = loaded_model(input)
        pred_score = list(pred[0]['scores'].detach().numpy())
        if debug:
            print(file, pred_score[0])
        masks = [(pred[0]['masks']>0.5).squeeze().detach().cpu().numpy()]
        mask = masks[0]
        dims = mask.ndim
        if dims > 2:
            mask = combine_dims(mask)

        del img
        img = cv2.imread(filepath)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        green_mask = greenify_mask(mask)
        mask = mask.astype(np.uint8)
        mask[mask>0] = 255
        
        cv2.imwrite(outpath, mask)

        masked_img = cv2.addWeighted(img, 1, green_mask, 0.5, 0)
        cv2.imwrite(green_mask_path, masked_img)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)

    args = parser.parse_args()
    animal = args.animal

    create_mask(animal)


