library(rjson)

f <- file('~/programming/pipeline_utility/contours/MD589.C1.json', 'r')
h <- rjson::fromJSON(file = f)
close(f)

## grab voxel size of current navigation settings
voxelSize <- h$navigation$pose$positio$voxelSize

## grab current voxel coordinates
voxelCoordinates <- h$navigation$pose$positio$voxelCoordinates

## Create a new list for the new layer
MyAnnotations <- list(type = "annotation",
                      tool = "annotateSphere",
                      annotationColor = "#ff9900", # orange
                      voxelSize = as.numeric(voxelSize)
)

## Example of the structure for 2 ellipsoid annotations ##
##annotations <- list(list(center = c(6963, 7296.5, 23.5), 
##                         radii = c(68.2422180175781, 68.2422180175781, 4.09453296661377), 
##                         type = "ellipsoid", 
##                         id = "1", 
##                         description = "1"),
##                    list(center = c(6968, 7298, 23.5), 
##                         radii = c(80, 80, 8), 
##                         type = "ellipsoid", 
##                         id = "2", 
##                         description = "2"))