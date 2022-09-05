import argparse
from datetime import datetime
import os
import sys
from pathlib import Path
import torch
import torch.utils.data
from tqdm import tqdm
import numpy as np
from mask_class import MaskDataset, TrigeminalDataset, get_model_instance_segmentation, get_transform, train_an_epoch
PIPELINE_ROOT = Path('./pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())
import utils


from engine import train_one_epoch

ROOT = '/net/birdstore/Active_Atlas_Data/data_root/brains_info/masks'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='specify animal', required=False)
    parser.add_argument('--debug', help='test model', required=False, default='false')
    parser.add_argument('--tg', help='Use TG masks', required=False, default='false')
    parser.add_argument('--epochs', help='# of epochs', required=False, default=2)
    
    args = parser.parse_args()
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

    workers = 1
    batch_size = 1
    if torch.cuda.is_available(): 
        device = torch.device('cuda') 
        print(f'Using Nvidia graphics card GPU with {workers} workers at a batch size of {batch_size}')
    else:
        device = torch.device('cpu')
        print(f'Using CPU with {workers} workers at a batch size of {batch_size}')

    # define training and validation data loaders
    # multiprocessing with something other than 0 workers doesn't work on current
    # version of python's multiprocessing. Using 0 turns it off
    data_loader = torch.utils.data.DataLoader(
                dataset, batch_size=batch_size, shuffle=True, num_workers=workers,
                collate_fn=utils.collate_fn)
    print(f"We have: {len(dataset)} images to train.")

    # our dataset has two classs, tissue or 'not tissue'
    num_classes = 2
    modelpath = os.path.join(ROOT, 'mask.model.pth')
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
    epoch_losses = []
    """

    for epoch in range(epochs):
        # train for one epoch, printing every 10 iterations model, optimizer, data_loader, device, epoch,
        epoch_loss = train_an_epoch(model, optimizer, data_loader, device, epoch)
        print(epoch, epoch_loss)
        #x = txt.split()
        #loss1 = float(x[0])
        #sx2 = x[1]
        #sx2 = sx2.replace("(","").replace(")","")
        #x2 = float(sx2)
        epoch_losses.append(epoch_loss)
        # update the learning rate
        lr_scheduler.step()
        if not debug:
            torch.save(model.state_dict(), modelpath)
    logfile.write(str(epoch_losses))
    logfile.write("\n")

    for epoch in range(epochs):
        # train for one epoch, printing every 10 iterations
        mlogger = train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10)
        txt = str(mlogger.loss)
        x = txt.split()
        loss1 = float(x[0])
        #sx2 = x[1]
        #sx2 = sx2.replace("(","").replace(")","")
        #x2 = float(sx2)
        losses.append(loss1)
        # update the learning rate
        lr_scheduler.step()
        if not debug:
            torch.save(model.state_dict(), modelpath)
    logfile.write(str(losses))
    logfile.write("\n")
    """

    # Perform training loop for n epochs
    loss_list = []
    model.train()
    for epoch in range(epochs):
        loss_epoch = []
        iteration=1
        for images,targets in data_loader:
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
        print("Epoch: {} average loss  = {:.4f} ".format(epoch, loss_epoch_mean))
        torch.save(model.state_dict(), modelpath) # save each epoch

    logfile.write(str(loss_list))
    logfile.write("\n")


    print('Finished with masks')
    logfile.close()

