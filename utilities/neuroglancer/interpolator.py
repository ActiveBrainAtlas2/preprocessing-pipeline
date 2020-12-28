from scipy.interpolate import UnivariateSpline
import numpy as np

def interpolate(input, fi):
    i, f = int(fi // 1), fi % 1  # Split floating-point index into whole & fractional parts.
    j = i+1 if f > 0 else i  # Avoid index error.
    x = (1-f) * input[i][0] + f * input[j][0]
    y = (1-f) * input[i][1] + f * input[j][1]
    return [round(x,4), round(y,4)]


v1 = [[1,2], [4,5], [7,8], [4.4, 5.5], [3.33,4.44]]
v2 = [[11,22], [44,55], [77,88], [99,110], [4,4], [5,5]]


new_len = max(len(v1),len(v2))
print('new_len',new_len)


delta = (len(v1)-1) / (new_len-1)
print('delta', delta)
outp = [interpolate(v1, i*delta) for i in range(new_len)]

print('v1',(v1))
print('lin out',outp)
x = [v[0] for v in v1]
y = [v[1] for v in v1]


vx = np.array(x)
vy = np.array(y)
indices = np.arange(0,len(vx))
new_length = new_len
new_indices = np.linspace(0,len(v1)-1,new_length)

splx = UnivariateSpline(indices,vx,k=3,s=0)
x_array = splx(new_indices)
sply = UnivariateSpline(indices,vy,k=3,s=1)
y_array = sply(new_indices)
print(x_array, y_array)

points = np.array([])

x = np.array([v[0] for v in points])
y = np.array([v[1] for v in points])
old_len = points.shape[0]
new_len = old_len * 2
indexes = np.arange(0, old_len)
new_indexes = np.linspace(0,old_len-1, new_len)
splx = UnivariateSpline(indexes,x,k=3,s=0)
x_smooth = splx(new_indexes)
sply = UnivariateSpline(indexes,y,k=3,s=0)
y_smooth = sply(new_indexes)
points = np.column_stack((x_smooth, y_smooth)).astype(np.int32)
print('points, type,shape, dtype', type(points), points.shape, points.dtype)
print('smooth points, type,shape, dtype', type(points), points.shape, points.dtype)
