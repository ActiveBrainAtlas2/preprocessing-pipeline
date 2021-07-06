import matplotlib.pyplot as plt
def get_common_point_set(com1_dict,com2_dict):
    key1 = com1_dict.keys()
    key2 = com2_dict.keys()
    shared_keys = [keyi for keyi in key1 if keyi in key2]
    com1 = []
    com2 = []
    for key in shared_keys:
        com1.append(com1_dict[key])
        com2.append(com2_dict[key])
    com1 = np.array(com1)
    com2 = np.array(com2)
    return com1,com2

def print_two_point_set(pointset1,pointset2):
    assert len(pointset1)==len(pointset2)
    for pointi in range(len(pointset1)):
        print(pointset1[pointi],pointset2[pointi])

def scatter_two_com_array(com1,com2):
    plt.scatter(com1[:,0],com1[:,1])
    plt.scatter(com2[:,0],com2[:,1])

def scatter_two_com_dict(com1_dict,com2_dict):
    com1,com2 = get_common_point_set(com1_dict,com2_dict)
    print((com1.shape,com2.shape))
    plt.scatter(com1[:,0],com1[:,1])
    plt.scatter(com2[:,0],com2[:,1])