import argparse
from datetime import datetime
import os
import sys
from pathlib import Path
import torch
import torch.utils.data
from tqdm import tqdm
import numpy as np
from mask_class import MaskDataset, TrigeminalDataset, get_model_instance_segmentation, get_transform
PIPELINE_ROOT = Path('./pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())
import utils


from engine import train_one_epoch

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
    animal = args.animal
    epochs = int(args.epochs)

    if tg:
        ROOT = os.path.join(ROOT, 'tg')
        dataset = TrigeminalDataset(ROOT, transforms = get_transform(train=True))
    else:
        dataset = MaskDataset(ROOT, animal, transforms = get_transform(train=True))


    if debug:
        torch.manual_seed(1)
        indices = torch.randperm(len(dataset)).tolist()
        indices = indices[0:10]
        dataset = torch.utils.data.Subset(dataset, indices)


    # define training and validation data loaders
    # multiprocessing with something other than 0 workers doesn't work on current
    # version of python's multiprocessing. Using 0 turns it off
    workers = 1
    data_loader = torch.utils.data.DataLoader(
                dataset, batch_size=2, shuffle=True, num_workers=workers,
                collate_fn=utils.collate_fn)
    print(f"We have: {len(indices)} examples, {len(dataset)} are training")

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

        """
        for epoch in range(epochs):
            # train for one epoch, printing every 10 iterations
            mlogger = train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10)
            smlogger = str(mlogger) + "\n"
            logfile.write(smlogger)
            # update the learning rate
            lr_scheduler.step()
            if not debug:
                torch.save(model.state_dict(), modelpath)
        """

        # Perform training loop for n epochs
        loss_list = []
        model.train()
        for epoch in range(epochs):
            loss_epoch = []
            iteration=1
            for images,targets in tqdm(data_loader):
                images = list(image.to(device) for image in images)
                targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
                optimizer.zero_grad()
                model=model.double()
                loss_dict = model(images, targets)
                losses = sum(loss for loss in loss_dict.values())
                losses.backward()       
                optimizer.step()
                loss_epoch.append(losses.item())
                iteration+=1
            loss_epoch_mean = np.mean(loss_epoch) 
            loss_list.append(loss_epoch_mean) 
            smlogger = str(loss_epoch_mean) + ",\n"

            print("Average loss  = {:.4f} ".format(loss_epoch_mean))
            logfile.write(smlogger)
            torch.save(model.state_dict(), modelpath)
        print('Finished with masks')
        logfile.close()

