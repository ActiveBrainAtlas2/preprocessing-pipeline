#!/usr/bin/env python
import json
import time
from argparse import ArgumentParser
from pathlib import Path

import SimpleITK as sitk
import airlab as al
import matplotlib.pyplot as plt
import numpy as np
import torch

from toolbox.airlab import dump_al_affine_transform
from toolbox.airlab import load_al_affine_transform

ROOT = Path(__file__).resolve().parent.parent

def load_and_prep_images(
    mov_img_dir, mov_img_thumb_dir,
    fix_img_dir, fix_img_thumb_dir,
    downsample_factor=(1, 1, 1)
):
    mov_img_size = get_tif_size(mov_img_dir / '000.tif')
    mov_img_thumb_size = get_tif_size(mov_img_thumb_dir / '000.tif')
    fix_img_size = get_tif_size(fix_img_dir / '000.tif')
    fix_img_thumb_size = get_tif_size(fix_img_thumb_dir / '000.tif')
    print('Moving image size:', mov_img_size)
    print('Moving image thumbnail size:', mov_img_thumb_size)
    print('Fixed image size:', fix_img_size)
    print('Fixed image thumbnail size:', fix_img_thumb_size)

    print('Loading moving image stack')
    mov_img_stack = load_image_stack(mov_img_thumb_dir)
    print('Loading fixed image stack')
    fix_img_stack = load_image_stack(fix_img_thumb_dir)

    print('Normalizing image intensity')
    mov_img_stack = normalize_intensity(mov_img_stack)
    fix_img_stack = normalize_intensity(fix_img_stack)

    print('Padding image')
    mov_img_stack, fix_img_stack = pad([mov_img_stack, fix_img_stack])

    print('Downsampling image')
    dx, dy, dz = downsample_factor
    mov_img_stack = mov_img_stack[::dx, ::dy, ::dz]
    fix_img_stack = fix_img_stack[::dx, ::dy, ::dz]
    
    print('Converting to AirLab image')
    dtype = torch.float32
    device = torch.device('cpu')
    origin = (0, 0, 0)
    downsample_factor = np.array(downsample_factor)

    def prep_al_img(img, size, thumb_size):
        spacing = np.append(size / thumb_size, 1) * downsample_factor
        img = torch.tensor(img, dtype=dtype).to(device)
        img = al.Image(img, img.shape, spacing, origin)
        return img

    mov_img = prep_al_img(mov_img_stack, mov_img_size, mov_img_thumb_size)
    fix_img = prep_al_img(fix_img_stack, fix_img_size, fix_img_thumb_size)
    return mov_img, fix_img

def get_tif_size(tif_file):
    file_reader = sitk.ImageFileReader()
    file_reader.SetFileName(tif_file.as_posix())
    file_reader.ReadImageInformation()
    return np.array(file_reader.GetSize())

def load_image_stack(image_dir):
    image_dir = Path(image_dir).resolve()
    image_stack = []
    for image_file in sorted(image_dir.iterdir()):
        print(f'Loading image {image_file.name}', end='\r')
        image = sitk.ReadImage(image_file.as_posix())
        image_arr = sitk.GetArrayViewFromImage(image).copy()
        image_stack.append(image_arr.T)
    print(f'Finished loading {len(image_stack)} images')
    image_stack = np.stack(image_stack, axis=-1)
    return image_stack

def normalize_intensity(image):
    v_min, v_max = image.min(), image.max()
    image = (image - v_min) / (v_max - v_min)
    return image

def pad(images):
    shape = np.array(list(map(lambda image: image.shape, images))).max(axis=0)

    def put_in_corner(canvas, image):
        dx, dy, dz = image.shape
        canvas[0:dx,0:dy,0:dz] = image
        
    padded_images = []
    for image in images:
        canvas = np.zeros(shape, dtype=image.dtype)
        put_in_corner(canvas, image)
        padded_images.append(canvas)
    return padded_images

def affine_registrate(
    mov_img, fix_img,
    lr=None, niter=None 
):
    registration = al.PairwiseRegistration(verbose=True)

    transformation = al.transformation.pairwise.AffineTransformation(mov_img)
    registration.set_transformation(transformation)

    image_loss = al.loss.pairwise.MSE(fix_img, mov_img)
    registration.set_image_loss([image_loss])

    optimizer = torch.optim.Adam(transformation.parameters(), lr=lr)
    registration.set_optimizer(optimizer)

    registration.set_number_of_iterations(niter)
    registration.start()

    end = time.time()
    return transformation

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('brain')
    parser.add_argument('--base_brain', default='DK52')
    parser.add_argument('--workdir', type=Path)
    parser.add_argument('--dx', help='downsampling factor in x',
        type=int, default=8)
    parser.add_argument('--dy', help='downsampling factor in x',
        type=int, default=8)
    parser.add_argument('--dz', help='downsampling factor in x',
        type=int, default=2)
    parser.add_argument('--lr', help='learning rate',
        type=float, default=1e-2)
    parser.add_argument('--niter', help='number of optimization iterations',
        type=int, default=64)
    args = parser.parse_args()

    data_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data')
    work_dir = ROOT / 'data/rough-alignment' / args.brain
    work_dir.mkdir(parents=True, exist_ok=True)

    mov_brain = args.base_brain
    fix_brain = args.brain
    print(f'Aligning {mov_brain} (moving image) to {fix_brain} (fixed image)')

    mov_img_dir = data_dir / mov_brain / 'preps/CH1/full_aligned'
    mov_img_thumb_dir = data_dir / mov_brain / 'preps/CH1/thumbnail_aligned'

    fix_img_dir = data_dir / fix_brain / 'preps/CH1/full_aligned'
    fix_img_thumb_dir = data_dir / fix_brain / 'preps/CH1/thumbnail_aligned'

    mov_img, fix_img = load_and_prep_images(
        mov_img_dir, mov_img_thumb_dir,
        fix_img_dir, fix_img_thumb_dir,
        downsample_factor=(args.dx, args.dy, args.dz)
    )

    transform = affine_registrate(
        mov_img, fix_img,
        lr=args.lr, niter=args.niter
    )

    print('Warping moving image')
    displacement = transform.get_displacement()
    wrp_img = al.transformation.utils.warp_image(mov_img, displacement)

    print('Saving results')

    np.save(work_dir / 'img-mov.npy', mov_img.image[0,0].numpy())
    np.save(work_dir / 'img-fix.npy', fix_img.image[0,0].numpy())
    np.save(work_dir / 'img-wrp.npy', wrp_img.image[0,0].numpy())

    transform_param_file = work_dir / 'transform-affine-al.json'
    dump_al_affine_transform(mov_img, fix_img, transform, transform_param_file)
    transform = load_al_affine_transform(transform_param_file)

    coms_file = work_dir / f'coms-rough.json'
    with open(ROOT / 'data/DK52_coms_kui_detected.json', 'r') as f:
        mov_coms = json.load(f)
    fix_coms = {}
    for name, com in mov_coms.items():
        com = np.array(com, dtype=float)
        fix_coms[name] = transform.forward_point(com).tolist()
    with open(coms_file, 'w') as f:
        json.dump(fix_coms, f, sort_keys=True, indent=4)
