import SimpleITK as sitk
import sys
import os

if len ( sys.argv ) < 2:
    print( "Usage: %s <input>" % ( sys.argv[0] ) )
    sys.exit ( 1 )


image = sitk.Cast( sitk.ReadImage( sys.argv[1] ), sitk.sitkFloat32 )

edges = sitk.CannyEdgeDetection( image, lowerThreshold=200, upperThreshold=400, variance=[4]*3 )

stats = sitk.StatisticsImageFilter()
stats.Execute( image )

if ( not "SITK_NOSHOW" in os.environ ):
    sitk.Show( sitk.Maximum( image*0.5, edges*stats.GetMaximum()*.5) )665
