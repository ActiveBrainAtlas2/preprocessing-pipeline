"""Transformations."""
import torch
from pytorch3d.transforms import RotateAxisAngle
from pytorch3d.transforms import Scale
from pytorch3d.transforms import Translate
from torch.nn import Module
from torch.nn import Parameter
from .algorithm import umeyama

class Transform(Module):
    def transform_numpy(self, moving):
        """Apply transform to the moving object and get numpy result."""
        return self.forward(torch.tensor(moving)).detach().numpy()

class LinearTransform(Transform):
    def get_linear_matrix(self):
        """Get the linear transform matrix."""
        affine_matrix = self._transform.get_matrix()
        return affine_matrix[0, :3, :3].numpy()

    def get_translation(self):
        """Get the translation vector."""
        affine_matrix = self._transform.get_matrix()
        return affine_matrix[0, 3, :3].numpy()

class LandmarkRigidTransform(LinearTransform):
    """Rigid transform for landmark."""

    def __init__(self):
        super().__init__()
        self._set_rotation(0, 0, 0)
        self._set_translation(0, 0, 0)
        self._transform = self._get_transform()

    def _set_rotation(self, phi_x, phi_y, phi_z):
        self._phi_x = Parameter(torch.tensor(phi_x))
        self._phi_y = Parameter(torch.tensor(phi_y))
        self._phi_z = Parameter(torch.tensor(phi_z))

    def _set_translation(self, x, y, z):
        self._x = Parameter(torch.tensor(x))
        self._y = Parameter(torch.tensor(y))
        self._z = Parameter(torch.tensor(z))

    def _get_transform(self):
        rot_x = RotateAxisAngle(self._phi_x, "X")
        rot_y = RotateAxisAngle(self._phi_y, "Y")
        rot_z = RotateAxisAngle(self._phi_z, "Z")
        rotation = rot_x.compose(rot_y).compose(rot_z)
        translation = Translate(self._x, self._y, self._z)
        return rotation.compose(translation)

    def get_linear_matrix(self):
        """Get the linear transform matrix."""
        affine_matrix = self._transform.get_matrix()
        return affine_matrix[0, :3, :3].numpy()

    def get_translation(self):
        """Get the translation vector."""
        affine_matrix = self._transform.get_matrix()
        return affine_matrix[0, 3, :3].numpy()

    def forward(self, moving_landmark):
        return self._transform.transform_points(moving_landmark)

class LandmarkSimilarTransform(LandmarkRigidTransform):
    """Similar transform for landmark."""

    def __init__(self):
        super().__init__()
        self._set_scale(1, 1, 1)
        self._transform = self._get_transform()

    def _set_scale(self, scale_x, scale_y, scale_z):
        self._scale_x = Parameter(torch.tensor(scale_x))
        self._scale_y = Parameter(torch.tensor(scale_y))
        self._scale_z = Parameter(torch.tensor(scale_z))

    def _get_transform(self):
        rigid = super()._get_transform()
        scale = Scale(self._scale_x, self._scale_y, self._scale_z)
        return scale.compose(rigid)

    def transform(self):
        return self.scale().compse(super().transform())

class LandmarkAffineTransform(LinearTransform):
    """Affine transform for landmark."""

    def __init__(self):
        super().__init__()
        self._linear_matrix = Parameter(torch.eye(3))
        self._translation = Parameter(torch.zeros(3))

    def init_guess(self, fixed_landmark, moving_landmark):
        """Make an initial guess of parameters."""
        r, t = umeyama(moving_landmark.T, fixed_landmark.T)
        print(r, t)
        self._linear_matrix = Parameter(torch.tensor(r.T))
        self._translation = Parameter(torch.tensor(t.T[0]))

    def get_linear_matrix(self):
        """Get the linear transform matrix."""
        return self._linear_matrix.detach().numpy()

    def get_translation(self):
        """Get the translation vector."""
        return self._translation.detach().numpy()

    def forward(self, moving_landmark):
        """Forward the model."""
        return moving_landmark @ self._linear_matrix + self._translation
