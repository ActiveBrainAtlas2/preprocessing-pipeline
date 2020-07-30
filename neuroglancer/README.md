### Adding outside boundaries
1. Get the outside boundaries (masking) defined for each original uncropped foundation brain
using corrected dilation. (Ed)
1. Check feasibility for using full resolution images in CVAT. (Kui)
1. Mark on CVAT for each foundation brain the external mask and the internal structures for that brain. (Kui)
1. Combine outside masks with internal structures (Kui).
1. Beth/Litao/Kui will verify correct placement of internal structures and correct outside boundaries (for the 3 foundation brains)
### Generating an average brain
1. For average brain, there is an numpy array for each structure.
1. Take each of these structures into one numpy array for neuroglancer.
1. Get individual structures into CVAT
1. Find number of persons who annotated each structure from the HDF files
