import SimpleITK as sitk
from rough_alignment.Registration import Registration

class AffineRegistration(Registration):

    def __init__(self):
        super().__init__()        

    def align_image_centers(self):
        """get_initial_transform_to_align_image_centers [finds an initial translation that alignes the mean of two stacks]
        :return: [translation for centering]
        :rtype: [sitk transformation]
        """
        self.transform = sitk.CenteredTransformInitializer(
            self.fixed_image, self.moving_image,
            sitk.AffineTransform(3),
            sitk.CenteredTransformInitializerFilter.GEOMETRY)

    def calculate_affine_transform(self):
        """get_affine_transform [using the registeration framework to find the best Affine transformation that alignes two sitk image ]

        :param transform: [initial transformation to roughly align the images]
        :type transform: [sitk transform]
        :return: [Affine transformation from fixed brain to the moving brain]
        :rtype: [sitk transform]
        """
        self.set_mutual_information_as_similarity_metrics()
        self.set_optimizer_as_gradient_descent()
        self.align_image_centers()
        self.set_initial_transformation(self.transform)
        self.set_multi_resolution_parameters()
        self.status_reporter.set_report_events()
        self.registration_method.Execute(self.fixed_image, self.moving_image)


