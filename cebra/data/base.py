"""Base classes for datasets and loaders."""

import abc
import collections
from typing import List

import literate_dataclasses as dataclasses
import numpy as np
import torch

import cebra.distributions
import cebra.io
from cebra.data.datatypes import Batch
from cebra.data.datatypes import BatchIndex
from cebra.data.datatypes import Offset

__all__ = ["Dataset", "Loader"]


class Dataset(abc.ABC, cebra.io.HasDevice):
    """Abstract base class for implementing a dataset.

    The class attributes provide information about the shape of the data when
    indexing this dataset.

    Attributes:
        input_dimension: The input dimension of the signal in this dataset.
            Models applied on this this dataset should match this dimensionality.
        offset: The offset determines the shape of the data obtained with the
            ``__getitem__`` and :py:meth:`expand_index` methods.
    """

    def __init__(self, device="cpu"):
        self.offset: Offset = cebra.data.Offset(0, 1)
        super().__init__(device)

    @property
    @abc.abstractmethod
    def input_dimension(self) -> int:
        raise NotImplementedError

    @property
    def continuous_index(self) -> torch.Tensor:
        """The continuous index, if available.

        The continuous index along with a similarity metric is used for drawing
        positive and/or negative samples.

        Returns:
            index for all ``N`` samples in the dataset.
        """
        return None

    @property
    def discrete_index(self) -> torch.Tensor:
        """The discrete index, if available.

        a variable for to restrict positive samples to share the same index variable.
        To implement more complicated indexing operations (such as modeling similiarities

        Returns:
            Tensor of shape ``(N,)``, representing the index
            for all ``N`` samples in the dataset.
        """
        return None

    def expand_index(self, index: torch.Tensor) -> torch.Tensor:
        """

        Args:
            index: A one-dimensional tensor of type long containing indices
                to select from the dataset.

        Returns:
            An expanded index of shape ``(len(index), len(self.offset))`` where
            the elements will be
            ``expanded_index[i,j] = index[i] + j - self.offset.left`` for all ``j``
            in ``range(0, len(self.offset))``.

        Note:
            Requires the :py:attr:`offset` to be set.
        """

        # using non_blocking copy operation.
        offset = torch.arange(-self.offset.left,
                              self.offset.right,
        index = torch.clamp(index, self.offset.left,
                            len(self) - self.offset.right)

        return index[:, None] + offset[None, :]

    def expand_index_in_trial(self, index, trial_ids, trial_borders):
        """When the neural/behavior is in discrete trial, e.g) Monkey Reaching Dataset

        Todo:
            - rewrite
        """

        # using non_blocking copy operation.
        offset = torch.arange(-self.offset.left,
        return index[:, None] + offset[None, :]

    @abc.abstractmethod
    def __getitem__(self, index: torch.Tensor) -> torch.Tensor:
        """Return samples at the given time indices.

        Args:
            index: An indexing tensor of type :py:attr:`torch.long`.

        Returns:
            Samples from the dataset matching the shape
            ``(len(index), self.input_dimension, len(self.offset))``
        """

        raise NotImplementedError

    @abc.abstractmethod
    def load_batch(self, index: BatchIndex) -> Batch:
        """Return the data at the specified index location.

        TODO: adapt signature to support Batches and List[Batch]
        """
        raise NotImplementedError()

    def configure_for(self, model: "cebra.models.Model"):
        """Configure the dataset offset for the provided model.

        Call this function before indexing the dataset. This sets the
        :py:attr:`offset` attribute of the dataset.

        Args:
            model: The model to configure the dataset for.
        """
        self.offset = model.get_offset()


@dataclasses.dataclass
class Loader(abc.ABC, cebra.io.HasDevice):
    """Base dataloader class.

    Args:
        See dataclass fields.
        Batches of the specified size from the given dataset object.

    Note:
        The ``__iter__`` method is non-deterministic, unless explicit seeding is implemented
        in derived classes. It is recommended to avoid global seeding in numpy
        and torch, and instead locally instantiate a ``Generator`` object for
        drawing samples.
    """

    )

    )


    def __post_init__(self):
        if self.num_steps is None or self.num_steps <= 0:
            raise ValueError(
                f"num_steps cannot be less than or equal to zero or None. Got {self.num_steps}"
            )
        if self.batch_size is not None and self.batch_size <= 0:
            raise ValueError(
                f"Batch size has to be None, or a non-negative value. Got {self.batch_size}."
            )
    def __len__(self):
        """The number of batches returned when calling as an iterator."""
        return self.num_steps

    def __iter__(self) -> Batch:
        for _ in range(len(self)):
            index = self.get_indices(num_samples=self.batch_size)
            yield self.dataset.load_batch(index)

    @abc.abstractmethod
    def get_indices(self, num_samples: int):
        """Sample and return the specified number of indices.

        The elements of the returned `BatchIndex` will be used to index the
        `dataset` of this data loader.
        Args:
            num_samples: The size of each of the reference, positive and
                negative samples.

        Returns:
            batch indices for the reference, positive and negative sample.
        """
        raise NotImplementedError()
