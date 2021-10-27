import SimpleITK as sitk
import matplotlib.pyplot as plt
import numpy as np

class AlignmentTools:

    def create_neighborhood(Dict2d,N):
        neighborhoods=[]  # each element is a segment we would like to draw, points to the relevant row in fixed/moving/moved.
        for i in range(N):
            for j in range(N):
                for k in range(N):
                    if(i<N-1):
                        neighborhoods.append((Dict2d[(i,j,k)],Dict2d[(i+1,j,k)],'green'))
                    if(j<N-1):
                        neighborhoods.append((Dict2d[(i,j,k)],Dict2d[(i,j+1,k)],'red'))
                    if(k<N-1):
                        neighborhoods.append((Dict2d[(i,j,k)],Dict2d[(i,j,k+1)],'blue'))
        return neighborhoods

    def transformPoints(transform,points):
        """Transform a set of points according to a given transformation
            transform: and instance of SimpleITK.SimpleITK.Transform
            points: a numpy array of shape (number of points) X (number of dimensions)
            
            return moved: a numpy array of the same shape as points"""
        n,m=points.shape
        moved=np.zeros(points.shape)
        for i in range(n):
            moved[i]=transform.TransformPoint(points[i,:])
        return moved

    def errors(fixed,moving):
        diff=(fixed-moving)
        plt.hist(diff.flatten(),bins=100);
        plt.grid()
        
    def find_and_eval_transform(transform,fixed,moving):
        transform = sitk.LandmarkBasedTransformInitializer(transform,
                                                        list(fixed.flatten()),
                                                        list(moving.flatten()))
        inv_transform=transform.GetInverse()
        moved=transformPoints(transform,fixed)
        plt.figure(figsize=[8,4])
        plt.subplot(1,2,1)
        errors(fixed,moving)
        plt.title('errors of fixed vs. moving');
        plt.subplot(1,2,2)
        errors(moved,moving)
        # "moved" is the name I give to the thransformed fixed points
        plt.title('errors of moved versus moving');
        return moved,transform,inv_transform

    def dplt(ax,a,N,nbrs,m='o',**linestyle):
        """ plot a 3d rendinring of a grid of points"""
        x=a[:,0]
        y=a[:,1]
        z=a[:,2]
        ax.scatter(x, y, z, marker=m)

        _coor=np.zeros([2,3])
        for i,j,color in nbrs:
            _coor[0,:]=a[i,:]
            _coor[1,:]=a[j,:]
            x=list(_coor[:,0])
            y=list(_coor[:,1])
            z=list(_coor[:,2])
            #print(i,j,a[i,:],a[j,:],color,x,y,z)
            ax.plot(x,y,z,color,**linestyle)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')

        xline=np.zeros([N])
        yline=np.zeros([N])
        zline=np.zeros([N])
        plt.show()
        
