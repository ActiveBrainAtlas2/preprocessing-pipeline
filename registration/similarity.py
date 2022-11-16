"""Similarity metrics."""
import torch


class MSESimilarity:
    """Mean squared error similarity metric."""

    @staticmethod
    def apply_to_image(image1, image2):
        """Apply similarity metric to a pair of images."""
        raise NotImplementedError

    @staticmethod
    def apply_to_landmark(landmark1, landmark2):
        """Apply similarity metric to a pair of landmarks."""
        loss = torch.nn.MSELoss()
        return loss(landmark1, landmark2)
