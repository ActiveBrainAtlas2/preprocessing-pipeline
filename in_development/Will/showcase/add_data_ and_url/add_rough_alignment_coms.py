from notebooks.Will.toolbox.IOs.TransformCom import TransformCom
from notebooks.Will.toolbox.IOs.LoadComDatabase import LoadComDatabase
from abakit.lib.Controllers.SqlController import SqlController
getcom = LoadComDatabase()
gettc = TransformCom(getcom)
prep_list = getcom.get_prep_list_for_rough_alignment_test()
prepi = 'DK41'
prepi_com = getcom.get_prepi_com(prepi)
DK52_coms = getcom.get_dk52_com()
prepid = prep_list.index(prepi)
itk_transformed_coms = gettc.get_itk_affine_transformed_coms()
transformed_prepi_com = itk_transformed_coms[prepid]
controller = SqlController(prepi)

Zhongkai = 34
Aligned = 4
str_list = controller.get_structures_list()
for structure,coordinates in transformed_prepi_com.items():
    structure_id = str_list.index(structure)
    controller.add_layer_data_row(prepi,Zhongkai,Aligned,coordinates,structure_id,layer='Rough Alignment')
print('done')