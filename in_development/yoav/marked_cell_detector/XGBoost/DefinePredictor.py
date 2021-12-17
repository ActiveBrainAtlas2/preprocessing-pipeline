from numpy import *
from pylab import plot,legend

def points2line(p1,p2,i):
    x1,y1=p1
    x2,y2=p2
    a=(y1-y2)/(x1-x2)
    b=y1-a*x1
    plotline(a,b,i)
    return a,b

p=[[0,0.8],[2,2.5],[0,3.3],[-2,2.5],[-10,4],[10,4]]

def plotline(a,b,i):
    X=arange(-5,5,0.01)
    Y=a*X+b
    plot(X,Y,label=str(i))
    
def aboveline(p,l):
    return l[0]*p[0]+l[1] < p[1]

L=[]
L.append(points2line(p[0],p[1],0))
L.append(points2line(p[1],p[2],1))
L.append(points2line(p[2],p[3],2))
L.append(points2line(p[3],p[0],3))
L.append(points2line(p[1],p[5],4))
L.append(points2line(p[3],p[4],5))
legend()
L

def decision(x,y):
    p=[x,y]
    if aboveline(p,L[0]) and not aboveline(p,L[1])\
    and not aboveline(p,L[2]) and aboveline(p,L[3]):
        return 0
    if (x<0 and not aboveline(p,L[5])) or (x>0 and aboveline(p,L[4])):
        return -2
    if (x>0 and not aboveline(p,L[4])) or (x<0 and aboveline(p,L[5])):
        return 2
