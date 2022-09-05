import argparse
import os
import sys
import torch
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import cv2
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
from pathlib import Path

PIPELINE_ROOT = Path('./pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from lib.FileLocationManager import FileLocationManager
from utilities.utilities_mask import combine_dims, merge_mask


def get_model_instance_segmentation(num_classes):
    # load an instance segmentation model pre-trained pre-trained on COCO
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(weights="DEFAULT")
    # get number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # replace the pre-trained head with a new one
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    # now get the number of input features for the mask classifier
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    hidden_layer = 256
    # and replace the mask predictor with a new one
    model.roi_heads.mask_predictor = MaskRCNNPredictor(
        in_features_mask, hidden_layer, num_classes
    )
    return model


def load_machine_learning_model():
    """Load the CNN model used to generate image masks"""
    modelpath = os.path.join("/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks/tg/mask.model.pth" )
    loaded_model = get_model_instance_segmentation(num_classes=2)
    if os.path.exists(modelpath):
        loaded_model.load_state_dict(torch.load(modelpath, map_location=torch.device("cpu")))
        return loaded_model
    else:
        print("no model to load")
        sys.exit()



def predict_mask(animal):
    loaded_model = load_machine_learning_model()
    transform = torchvision.transforms.ToTensor()
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail_aligned')
    TG_MASKS = os.path.join(fileLocationManager.masks, 'tg')
    os.makedirs(TG_MASKS, exist_ok=True)

    files = os.listdir(INPUT)
    for file in files:
        filepath = os.path.join(INPUT, file)
        mask_dest_file = (
            os.path.splitext(file)[0] + ".tif"
        )  # colored mask images have .tif extension
        maskpath = os.path.join(TG_MASKS, mask_dest_file)

        if os.path.exists(maskpath):
            continue

        img = Image.open(filepath).convert("L")
        raw_img = np.array(img)
        torch_input = transform(img)
        torch_input = torch_input.unsqueeze(0)
        loaded_model.eval()
        with torch.no_grad():
            pred = loaded_model(torch_input)
        masks = [(pred[0]["masks"] > 0.5).squeeze().detach().cpu().numpy()]
        mask = masks[0]
        dims = mask.ndim
        if dims > 2:
            mask = combine_dims(mask)
        mask = mask.astype(np.uint8)
        mask[mask > 0] = 255
        merged_img = merge_mask(raw_img, mask)
        del mask
        cv2.imwrite(maskpath, merged_img)


if __name__ == "__main__":
    steps = """
    start=0, prep, normalized and masks=1, mask, clean and histograms=2, 
     elastix and alignment=3, neuroglancer=4
     """
    parser = argparse.ArgumentParser(description="Work on Animal")
    parser.add_argument("--animal", help="Enter the animal", required=True)
    args = parser.parse_args()
    animal = args.animal

    predict_mask(animal)
