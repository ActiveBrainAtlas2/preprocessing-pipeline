from abakit.lib.Controllers.TransformationController import TransformationController
import numpy as np
def test_transformation():
    '''Tests the transformation class used to store the Stack to Atlas or
     Atlas to Stack transforms. The test retrives one of the transformation 
     from the database, applies the forward and reverse transform to a group of 
     random points, and check if the same points are recovered.'''
    controller = TransformationController()
    transform = controller.get_transformation(source = 'DK39',destination = 'Atlas', transformation_type = 'Rigid')
    points = np.random.rand(30).reshape(10,3)
    transformed_points = transform.forward_transform_points(points)
    recovered_points = transform.inverse_transform_points(transformed_points)
    assert np.all(np.isclose(points,recovered_points))