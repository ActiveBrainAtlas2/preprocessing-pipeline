from vtkplotter import *

s = load('SC.stl')

cols, als = [], []
for i in range(s.NCells()):
    cols.append(i) # i-th color
    als.append(i/s.NCells()) #opacity

s.colorCellsByArray(cols, als).lw(1).show()
