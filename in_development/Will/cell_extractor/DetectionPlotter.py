import matplotlib.pyplot as plt
import numpy as np
class DetectionPlotter():

    def plot_examplei(self,examplei = 0):
        assert(hasattr(self, 'Examples'))
        examplei = self.Examples[examplei][0]
        ch1 = examplei['image_CH1']
        ch3 = examplei['image_CH3']
        plt.imshow(ch1)
        plt.show()
        plt.imshow(ch3)
        plt.show()
    
    def plot_examples(self,examples,channel = 3):
        i=1
        fig = plt.figure(figsize = [15,15])
        for examplei in examples:
            ax = plt.subplot(5,5,i)
            i+=1
            ax.imshow(examplei[f'image_CH{channel}'])
            ax.set_title('%d, %d'%(i,examplei['area']))
