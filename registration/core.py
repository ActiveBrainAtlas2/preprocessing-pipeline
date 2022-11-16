"""Image registration methods."""
from functools import partial

import torch

from .similarity import MSESimilarity


class LandmarkRegistration:
    """Landmark registration method."""

    def __init__(self, fixed_landmark, moving_landmark):
        self._fixed_landmark = torch.tensor(fixed_landmark)
        self._moving_landmark = torch.tensor(moving_landmark)
        assert len(self._fixed_landmark.shape) == 2
        assert self._fixed_landmark.shape[1] == 3
        assert self._fixed_landmark.shape == self._moving_landmark.shape

        self._transform = None
        self._similarity = MSESimilarity()
        self._optimizer_class = torch.optim.Adam

    def set_transform(self, transform):
        """Set transform."""
        self._transform = transform

    def set_similarity(self, similarity):
        """Set similarity metric."""
        self._similarity = similarity

    def set_optimizer_class(self, optimizer_class, **kwargs):
        """Set optimizer class."""
        if kwargs:
            self._optimizer_class = partial(optimizer_class, **kwargs)
        else:
            self._optimizer_class = optimizer_class

    def run(self, max_iteration=1000):
        """Run registration."""
        self._transform.init_guess(
            self._fixed_landmark.numpy(), self._moving_landmark.numpy()
        )
        optimizer = self._optimizer_class(self._transform.parameters())
        for _ in range(max_iteration):

            def closure():
                # nonlocal optimizer
                optimizer.zero_grad()
                landmark1 = self._fixed_landmark
                landmark2 = self._transform(self._moving_landmark)
                loss = self._similarity.apply_to_landmark(landmark1, landmark2)
                loss.backward()
                return loss

            optimizer.step(closure)
