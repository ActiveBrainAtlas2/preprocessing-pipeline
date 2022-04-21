import os, sys
from collections import Counter
from matplotlib import pyplot as plt
from skimage import io
import numpy as np
import cv2
from concurrent.futures.process import ProcessPoolExecutor
from abakit.lib.FileLocationManager import FileLocationManager
from lib.logger import get_logger
from abakit.lib.SqlController import SqlController
from abakit.lib.utilities_process import test_dir, get_cpus
COLORS = {1: 'b', 2: 'r', 3: 'g'}
from lib.PipelineUtilities import PipelineUtilities

class HistogramMaker(PipelineUtilities):
    def make_histogram(self):
        """
        This method creates an individual histogram for each tif file by channel.
        Args:
            animal: the prep id of the animal
            channel: the channel of the stack to process  {1,2,3}
        Returns:
            nothing
        """
        INPUT = self.fileLocationManager.get_thumbnail(self.channel)
        MASK_INPUT = self.fileLocationManager.thumbnail_masked
        files = self.sqlController.get_sections(self.animal, self.channel)
        test_dir(self.animal, INPUT, downsample=True, same_size=False)
        if len(files) == 0:
            error += " No sections in the database"
        OUTPUT = self.fileLocationManager.get_histogram(self.channel)
        os.makedirs(OUTPUT, exist_ok=True)
        self.sqlController.set_task_for_step(self.animal,True, self.channel, 'HISTOGRAM')
        file_keys = []
        for i, file in enumerate(files):
            filename = str(i).zfill(3) + '.tif'
            input_path = os.path.join(INPUT, filename)
            mask_path = os.path.join(MASK_INPUT, filename)
            output_path = os.path.join(OUTPUT, os.path.splitext(file.file_name)[0] + '.png')
            if not os.path.exists(input_path):
                print('Input tif does not exist', input_path)
                continue
            if os.path.exists(output_path):
                continue
            file_keys.append([input_path, mask_path, self.channel, file, output_path])
        workers = self.get_nworkers()
        self.run_commands_in_parallel_with_executor([file_keys],workers,self.make_single_histogram)    

    def make_single_histogram(self,file_key):
        input_path, mask_path, channel, file, output_path = file_key
        img = self.read_image(input_path)
        mask = self.read_image(mask_path)
        img = cv2.bitwise_and(img, img, mask=mask)
        if img.shape[0] * img.shape[1] > 1000000000:
            scale = 1 / float(2)
            img = img[::int(1. / scale), ::int(1. / scale)]
        try:
            flat = img.flatten()
        except:
            print(f'Could not flatten {input_path}')
            return
        del img
        del mask
        fig = plt.figure()
        plt.rcParams['figure.figsize'] = [10, 6]
        plt.hist(flat, flat.max(), [0, 10000], color=COLORS[channel])
        plt.style.use('ggplot')
        plt.yscale('log')
        plt.grid(axis='y', alpha=0.75)
        plt.xlabel('Value')
        plt.ylabel('Frequency')
        plt.title(f'{file.file_name} @16bit')
        plt.close()
        fig.savefig(output_path, bbox_inches='tight')
        return

    def make_combined_histogram(self):
        """
        This method takes all tif files by channel and creates a histogram of the combined image space.
        :param animal: the prep_id of the animal we are working with
        :param channel: the channel {1,2,3}
        :return: nothing
        """
        INPUT = self.fileLocationManager.get_thumbnail(self.channel)
        MASK_INPUT = self.fileLocationManager.thumbnail_masked
        OUTPUT = self.fileLocationManager.get_histogram(self.channel)
        os.makedirs(OUTPUT, exist_ok=True)
        files = os.listdir(INPUT)
        hist_dict = Counter({})
        outfile = f'{self.animal}.png'
        outpath = os.path.join(OUTPUT, outfile)
        if os.path.exists(outpath):
            return
        lfiles = len(files)
        midindex = lfiles // 2
        midfilepath = os.path.join(INPUT, files[midindex] )
        img = io.imread(midfilepath)
        bits = img.dtype
        del img
        for file in files:
            input_path = os.path.join(INPUT, file)
            mask_path = os.path.join(MASK_INPUT, file)
            try:
                img = io.imread(input_path)
            except:
                self.logger.error(f'Could not read {input_path}')
                lfiles -= 1
                continue
            try:
                mask = io.imread(mask_path)
            except:
                self.logger.error(f'Could not open {mask_path}')
                continue
            img = cv2.bitwise_and(img, img, mask=mask)
            try:
                flat = img.flatten()
                del img
            except:
                self.logger.error(f'Could not flatten file {input_path}')
                lfiles -= 1
                continue
            try:
                img_counts = np.bincount(flat)
            except:
                self.logger.error(f'Could not create counts {input_path}')
                lfiles -= 1
                continue
            try:
                img_dict = Counter(dict(zip(np.unique(flat), img_counts[img_counts.nonzero()])))
            except:
                self.logger.error(f'Could not create counter {input_path}')
                lfiles -= 1
                continue
            try:
                hist_dict = hist_dict + img_dict
            except:
                self.logger.error(f'Could not add files {input_path}')
                lfiles -= 1
                continue
        if lfiles > 10:
            hist_dict = dict(hist_dict)
            hist_values = [i/lfiles for i in hist_dict.values()]
            fig = plt.figure()
            plt.rcParams['figure.figsize'] = [10, 6]
            plt.bar(list(hist_dict.keys()), hist_values, color = COLORS[self.channel])
            plt.yscale('log')
            plt.grid(axis='y', alpha=0.75)
            plt.xlabel('Value')
            plt.ylabel('Frequency')
            plt.title(f'{self.animal} channel {self.channel} @{bits}bit with {lfiles} tif files')
            fig.savefig(outpath, bbox_inches='tight')