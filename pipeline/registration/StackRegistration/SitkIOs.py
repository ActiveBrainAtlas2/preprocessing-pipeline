import SimpleITK as sitk
import os
class SitkIOs:
    def array_to_image(self,array):
        sitk_image = sitk.GetImageFromArray(array)
        return  sitk.Cast(sitk_image, sitk.sitkFloat32)

    def load_image_from_directory(self,image_dir, spacing=None):
        """load_image [load all image files in a directory to a sitk image object]

        :param image_dir: [direction of tif files]
        :type image_dir: [str]
        :param spacing: [imaging resolution x,y,z], defaults to None
        :type spacing: [list or array of length 3], optional
        :return: [sikt image stack]
        :rtype: [sitk image object]
        """
        image_files = os.path.lsdir(image_dir)
        image_series = []
        for image_file in sorted(image_files):
            print(f'Loading image {image_file.name}', end='\r')
            image = sitk.ReadImage(image_file)
            image_series.append(image)
        sitk_image = sitk.JoinSeries(image_series)
        if spacing is not None:
            sitk_image.SetSpacing(spacing)
        sitk_image = sitk.Cast(sitk_image, sitk.sitkFloat32)
        return sitk_image