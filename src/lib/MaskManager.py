import os, sys
import numpy as np
import torch
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import cv2
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
from abakit.lib.utilities_mask import combine_dims, merge_mask
from abakit.lib.utilities_process import test_dir
import warnings
warnings.filterwarnings("ignore")
from lib.pipeline_utilities import get_image_size

class MaskManager:
    def apply_user_mask_edits(self):
        """Apply the edits made on the image masks to extract the tissue from the surround debre to create the final
        masks used to clean the images"""
        COLORED = self.fileLocationManager.thumbnail_colored
        MASKS = self.fileLocationManager.thumbnail_masked
        test_dir(self.animal, COLORED, True, same_size=False)
        os.makedirs(MASKS, exist_ok=True)
        files = sorted(os.listdir(COLORED))
        for file in files:
            filepath = os.path.join(COLORED, file)
            maskpath = os.path.join(MASKS, file)
            if os.path.exists(maskpath):
                continue
            mask = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
            mask = mask[:,:,2]
            mask[mask>0] = 255
            mask[mask<=0]=255
            cv2.imwrite(maskpath, mask.astype(np.uint8))

    def get_model_instance_segmentation(self, num_classes):
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
        model.roi_heads.mask_predictor = MaskRCNNPredictor(
            in_features_mask, hidden_layer, num_classes
        )
        return model

    def create_mask(self):
        """Create the images masks for extracting the tissue from the surrounding debres using a CNN based machine learning algorithm"""
        if not self.downsample:
            self.create_full_resolution_mask()
        else:
            self.create_downsampled_mask()

    def load_machine_learning_model(self):
        """Load the CNN model used to generate image masks"""
        modelpath = os.path.join(
            "/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks/mask.model.pth"
        )
        self.loaded_model = self.get_model_instance_segmentation(num_classes=2)
        if os.path.exists(modelpath):
            self.loaded_model.load_state_dict(
                torch.load(modelpath, map_location=torch.device("cpu"))
            )
        else:
            print("no model to load")
            return

    def create_full_resolution_mask(self):
        """Upsample the masks created for the downsampled images to the full resolution"""
        self.sqlController.set_task(
            self.animal, self.progress_lookup.CREATE_FULL_RES_MASKS
        )
        FULLRES = self.fileLocationManager.get_full(self.channel)
        THUMBNAIL = self.fileLocationManager.thumbnail_masked
        MASKED = self.fileLocationManager.full_masked
        test_dir(self.animal, FULLRES, self.downsample, same_size=False)
        os.makedirs(MASKED, exist_ok=True)
        files = sorted(os.listdir(FULLRES))
        file_keys = []
        for file in files:
            infile = os.path.join(FULLRES, file)
            thumbfile = os.path.join(THUMBNAIL, file)
            outpath = os.path.join(MASKED, file)
            if os.path.exists(outpath):
                continue
            try:
                width, height = get_image_size(infile)
            except:
                print(f"Could not open {infile}")
            size = int(width), int(height)
            file_keys.append([thumbfile, outpath, size])
        workers = self.get_nworkers()
        self.run_commands_in_parallel_with_executor([file_keys], workers, resize_tif)

    def create_downsampled_mask(self):
        """Create masks for the downsampled images using a machine learning algorism"""
        self.load_machine_learning_model()
        transform = torchvision.transforms.ToTensor()
        FULLRES = self.fileLocationManager.get_normalized()
        COLORED = self.fileLocationManager.thumbnail_colored
        test_dir(self.animal, FULLRES, self.downsample, same_size=False)
        os.makedirs(COLORED, exist_ok=True)
        files = sorted(os.listdir(FULLRES))
        for file in files:
            filepath = os.path.join(FULLRES, file)
            maskpath = os.path.join(COLORED, file)
            if os.path.exists(maskpath):
                continue
            img = Image.open(filepath)
            torch_input = transform(img)
            torch_input = torch_input.unsqueeze(0)
            self.loaded_model.eval()
            with torch.no_grad():
                pred = self.loaded_model(torch_input)
            masks = [(pred[0]["masks"] > 0.5).squeeze().detach().cpu().numpy()]
            mask = masks[0]
            dims = mask.ndim
            if dims > 2:
                mask = combine_dims(mask)
            raw_img = np.array(img)
            mask = mask.astype(np.uint8)
            mask[mask > 0] = 255
            merged_img = merge_mask(raw_img, mask)
            del mask
            cv2.imwrite(maskpath, merged_img)


def resize_tif(file_key):
    """Function to upsample mask images

    Args:
        file_key (list): list of inputs to the upsampling program including:
        1. path to thumbnail file
        2. The output directory of upsampled image
        3. resulting size after upsampling
    """
    thumbfile, outpath, size = file_key
    try:
        im = Image.open(thumbfile)
        im = im.resize(size, Image.LANCZOS)
        im.save(outpath)
    except IOError:
        print("cannot resize", thumbfile)
