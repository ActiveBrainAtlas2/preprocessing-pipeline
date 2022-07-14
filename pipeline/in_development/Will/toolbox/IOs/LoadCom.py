import numpy as np

class LoadCom:
    def get_prep_list_for_rough_alignment_test(self):
        """list of brains for that we have for plotting at 6.12.2021"""
        return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']

    def get_prep_list(self):
        """list of brains for that we have for image to image alignmen at June 2021.  DK52 was excluded as all transformation goes from DK52 to DKX"""
        return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55','DK52']

    def _atlas_to_physical(self,com):
        """convets the atlas units to physical(1um,1um,1um) this is necessary as the save is before all units in database is turn into physical"""
        com_physical = (np.array(com)*10/np.array([10,10,20])+np.array([500,500,150]))*np.array([10,10,20])
        return com_physical

    def _image_to_physical(self,com,imaging_resolution = np.array([0.325,0.325,20])):
        """convets the pixel units to physical(1um,1um,1um) this is necessary as the save is before all units in database is turn into physical"""
        com_physical = np.array(com)*imaging_resolution
        return com_physical
    
    def _physical_to_image(self,com,imaging_resolution = np.array([0.325,0.325,20])):
        """convets the pixel units to physical(1um,1um,1um) this is necessary as the save is before all units in database is turn into physical"""
        com_image = np.array(com)/imaging_resolution
        return com_image

    def _neuroglancer_atlas_to_physical(self,com):
        """convets the neuroglancer units(10,10,20)um to physical(1um,1um,1um) this is necessary as the save is before all units in database is turn into physical"""
        com_physical = np.array(com)*np.array([10,10,20])
        return com_physical

    def _convert_com_dict_units(self,com_dict,conversion_function):
        """_convert_com_dict_units [Perform unit conversions for the entire com dictionary]

        :param com_dict: [com dictionaries, keys are structure names and values are tuple or np array of len 3]
        :type com_dict: [dict]
        :param conversion_function: [the function that converts the unit for one com]
        :type conversion_function: [function]
        :return: [converted com dictionary]
        :rtype: [dict]
        """
        com_dict_converted = {}
        for landmark,com in com_dict.items():
            com_dict_converted[landmark] = conversion_function(com)
        return com_dict_converted