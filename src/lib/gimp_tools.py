from gimpfu import pdb

def test_create_xcf(tif_path,mask_path,xcf_path):
    image=pdb.gimp_file_load(tif_path,tif_path)
    layer = pdb.gimp_file_load_layer(image, mask_path)
    pdb.gimp_layer_set_opacity(layer,37)
    image.add_layer(layer,0)
    pdb.gimp_xcf_save(0,image,layer,xcf_path,xcf_path)

def test_create_tif(mask_path,xcf_path):
    image = pdb.gimp_xcf_load(0,xcf_path,xcf_path)
    mask_layer = image.layers[0]
    pdb.file_tiff_save(image,mask_layer,mask_path,mask_path,1)
