import os
import pickle
import matplotlib.pyplot as plt 
import numpy as np
root_dir = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
animals = os.listdir(root_dir)
stack_size = dict()

def folder_size(path='.'):
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += folder_size(entry.path)
    return total

def generate_stats():
    for animali in animals:
        print(animali)
        full_res_path = os.path.join(root_dir,animali,'preps/CH1/full')
        if os.path.exists(full_res_path):
            stack_size[animali] = folder_size(full_res_path)
    pickle.dump(stack_size,open('/home/zhw272/Desktop/stack_size_query.pkl','wb'))

stack_size = pickle.load(open('/home/zhw272/Desktop/stack_size_query.pkl','rb'))
sizes = np.array(list(stack_size.values()))*1e-9

ax = plt.hist(sizes)
plt.title('Distribution Of Stack Size')
plt.xlabel('size in Gb')
plt.axvline(sizes.mean())
plt.text(sizes.mean(),5, f"mean = {int(sizes.mean())} Gb", color="b", 
        ha="right", va="center")
plt.show()
print('done')