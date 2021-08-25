__author__ = 'Zhongkai Wu'
from GimpInterface import GimpInterface
if __name__ == '__main__':
    gimp_tool_path = '"/home/zhw272/programming/pipeline_utility/src"'
    tif_path = '"/home/zhw272/Desktop/000n.tif"'
    mask_path = '"/home/zhw272/Desktop/000.tif"'
    xcf_path =  '"/home/zhw272/Desktop/000.xcf"'
    modsav =  '"/home/zhw272/Desktop/000s.tif"'
    interface = GimpInterface()
    interface.import_custome_library(gimp_tool_path,'gimp_tools')
    interface.create_xcf(tif_path,mask_path,xcf_path)
    interface.save_mask(modsav,xcf_path)
    interface.add_batch_script()
    interface.execute()