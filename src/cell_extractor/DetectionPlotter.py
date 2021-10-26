from cell_extractor.CellDetectorBase import CellDetectorBase
import matplotlib.pyplot as plt
import numpy as np
class DetectionPlotter(CellDetectorBase):
    def __init__(self,animal,section):
        super().__init__(animal,section)

    def plot_examples(self,examplei = 0):
        assert(hasattr(self, 'Examples'))
        examplei = self.Examples[examplei][0]
        ch1 = examplei['image_CH1']
        ch3 = examplei['image_CH3']
        plt.imshow(ch1)
        plt.show()
        plt.imshow(ch3)
        plt.show()
