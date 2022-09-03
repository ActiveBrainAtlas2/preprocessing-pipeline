import argparse
from datetime import datetime
import os
import sys
from pathlib import Path
import torch
import torch.utils.data
from mask_class import MaskDataset, get_model_instance_segmentation, test_model, get_transform
PIPELINE_ROOT = Path('./pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())
import utils

from engine import train_one_epoch, evaluate

ROOT = '/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='specify animal', required=False)
    parser.add_argument('--runmodel', help='run model', required=True)
    parser.add_argument('--debug', help='test model', required=False, default='false')
    parser.add_argument('--tg', help='Use TG masks', required=False, default='false')
    parser.add_argument('--epochs', help='# of epochs', required=False, default=2)
    
    args = parser.parse_args()
    runmodel = bool({'true': True, 'false': False}[args.runmodel.lower()])
    tg = bool({'true': True, 'false': False}[args.tg.lower()])
    debug = bool({'true': True, 'false': False}[args.debug.lower()])

    if tg:
        ROOT = os.path.join(ROOT, 'tg')

    animal = args.animal
    epochs = int(args.epochs)
    dataset = MaskDataset(ROOT, animal, transforms = get_transform(train=True))
    dataset_test = MaskDataset(ROOT, animal, transforms = get_transform(train=False))

    # split the dataset in train and test set
    torch.manual_seed(1)
    if debug:
        indices = torch.randperm(len(dataset)).tolist()
        indices = indices[0:10]
        test_cases = int(len(indices) * 0.15)
        dataset = torch.utils.data.Subset(dataset, indices[:-test_cases])
        dataset_test = torch.utils.data.Subset(dataset_test, indices[-test_cases:])
    else:
        indices = torch.randperm(len(dataset)).tolist()
        test_cases = int(len(indices) * 0.15)
        dataset = torch.utils.data.Subset(dataset, indices[:-test_cases])
        dataset_test = torch.utils.data.Subset(dataset_test, indices[-test_cases:])


    # define training and validation data loaders
    # multiprocessing with something other than 0 workers doesn't work on current
    # version of python's multiprocessing. Using 0 turns it off
    workers = 0
    data_loader = torch.utils.data.DataLoader(
                dataset, batch_size=2, shuffle=True, num_workers=workers,
                collate_fn=utils.collate_fn)
    data_loader_test = torch.utils.data.DataLoader(
            dataset_test, batch_size=1, shuffle=False, num_workers=workers,
            collate_fn=utils.collate_fn)
    print(f"We have: {len(indices)} examples, {len(dataset)} are training and {len(dataset_test)} testing")

    if torch.cuda.is_available(): 
        device = torch.device('cuda') 
        print('Using Nvidia graphics card GPU')
    else:
        device = torch.device('cpu')
        print('Using CPU')
    # our dataset has two classs, tissue or 'not tissue'
    num_classes = 2
    modelpath = os.path.join(ROOT, 'mask.model.pth')
    if runmodel:
        # create logging file
        logpath = os.path.join(ROOT, "mask.logger.txt")
        logfile = open(logpath, "w")
        logheader = f"Masking {datetime.now()} with {epochs} epochs\n"
        logfile.write(logheader)
        # get the model using our helper function
        model = get_model_instance_segmentation(num_classes)
        # move model to the right device
        model.to(device)
        # construct an optimizer
        params = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.SGD(params, lr=0.005,momentum=0.9, weight_decay=0.0005)
        # and a learning rate scheduler which decreases the learning rate by # 10x every 3 epochs
        lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

        # 1 epoch takes 30 minutes on ratto
        for epoch in range(epochs):
            # train for one epoch, printing every 10 iterations
            mlogger = train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=100)
            smlogger = str(mlogger) + "\n"
            logfile.write(smlogger)
            # update the learning rate
            lr_scheduler.step()
            # evaluate on the test dataset
            evaluate(model, data_loader_test, device=device)
            if not debug:
                torch.save(model.state_dict(), modelpath)
        print('Finished with masks')
        logfile.close()

