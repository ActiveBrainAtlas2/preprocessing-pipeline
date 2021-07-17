import sys
sys.path.append('/usr/lib/gimp/2.0/python')
from gimpfu import pdb

#creating the xcf
image1 = '/home/zhw272/Desktop/000n.tif'
image2 = '/home/zhw272/Desktop/000.tif'
sav =  '/home/zhw272/Desktop/000.xcf'
image=pdb.gimp_file_load(image1,image1)
layer = pdb.gimp_file_load_layer(image, image2)
pdb.gimp_layer_set_opacity(layer,37)
image.add_layer(layer,0)
pdb.gimp_xcf_save(0,image,layer,sav,sav)
mask = pdb.gimp_layer_create_mask(layer,mask)

pdb.gimp_xcf_load(sav)
gimp.Display(pdb.gimp_file_load(sav, sav))

#extracting and saving the masks
sav =  '/home/zhw272/Desktop/000.xcf'
modsav =  '/home/zhw272/Desktop/000s.tif'
image = pdb.gimp_xcf_load(0,sav,sav)
mask_layer = image.layers[0]
pdb.file_tiff_save(image,mask_layer,modsav,modsav,1)


gimp -idf --batch-interpreter python-fu-eval -b "import sys;sys.path.append('/home/zhw272/Desktop');import gimp_tools;gimp_tools.test_create_xcf()" -b "pdb.gimp_quit(1)"
gimp -idf --batch-interpreter python-fu-eval -b "import sys;sys.path.append('/home/zhw272/Desktop');import gimp_tools;gimp_tools.test_create_tif()" -b "pdb.gimp_quit(1)"