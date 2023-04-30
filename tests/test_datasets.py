import numpy as np
import pytest
import torch
import tqdm

import cebra.data
import cebra.datasets
import cebra.registry
from cebra.datasets import poisson


def test_registry():
    """Check the registry: Are all functions defined and is the
    docstring correctly adapted?"""
    assert cebra.registry.is_registry(cebra.datasets)
    assert cebra.registry.is_registry(cebra.datasets, check_docs=True)


def test_factory():
    """Register a new dataset"""
    import cebra.datasets

    @cebra.datasets.register("test-data")
    class TestDataset:
        pass

    assert "test-data" in cebra.datasets.get_options()
    instance = cebra.datasets.init("test-data")
    assert isinstance(instance, TestDataset)


def test_demo():
    dataset = cebra.datasets.init("demo-discrete")
    indices = torch.arange(0, 5)
    batch = dataset[indices]

    assert len(batch) == len(indices)


@pytest.mark.requires_dataset
def test_hippocampus():
    from cebra.datasets import hippocampus

    pytest.skip("Outdated")
    dataset = cebra.datasets.init("rat-hippocampus-single")
    loader = cebra.data.ContinuousDataLoader(
        dataset=dataset,
        num_steps=10,
        batch_size=8,
    )
    for batch in loader:
        break

    dataset = cebra.datasets.init("rats-hippocampus-multisubjects")
    loader = cebra.data.ContinuousMultiSessionDataLoader(
        dataset=dataset,
        num_steps=10,
        batch_size=8,
    )
    for batch in loader:
        for b in batch:
        break


@pytest.mark.requires_dataset
def test_monkey():
    from cebra.datasets import monkey_reaching
    dataset = cebra.datasets.init(
    indices = torch.randint(0, len(dataset), (10,))


@pytest.mark.requires_dataset
def test_allen():
    from cebra.datasets import allen
    pytest.skip("Test takes too long")

    ca_loader = cebra.data.ContinuousDataLoader(
        dataset=ca_dataset,
        num_steps=10,
        batch_size=8,
    )
    for batch in ca_loader:
        break
    joint_dataset = cebra.datasets.init(
    joint_loader = cebra.data.ContinuousMultiSessionDataLoader(
        dataset=joint_dataset,
        num_steps=10,
        batch_size=8,
    )
    for batch in joint_loader:
        for b in batch:
        break


try:
except:
    options = []


@pytest.mark.requires_dataset
                                                    expand_parametrized=False))
def test_options(options):
    assert len(options) > 0


@pytest.mark.requires_dataset
def test_all(dataset):
    import cebra.datasets
    data = cebra.datasets.init(dataset)
    assert isinstance(data, cebra.data.base.Dataset)


def _assert_histograms_close(values, histogram):
    max_counts = max(max(values), len(histogram))

    value_mean = values.mean()
    histogram_mean = (histogram *
                      np.arange(len(histogram))).sum() / histogram.sum()
    assert np.isclose(value_mean, histogram_mean, rtol=0.05)

    value_histogram = np.bincount(values, minlength=max_counts)
    # NOTE(stes) normalize the histograms to be able to use the same atol values in the histogram
    # test below
    value_histogram = value_histogram / float(value_histogram.sum())
    histogram = histogram / float(histogram.sum())
    if len(histogram) < len(value_histogram):

    assert value_histogram.shape == histogram.shape
    # NOTE(stes) while the relative tolerance here is quite high (20%), this is a tradeoff vs. speed.


def test_poisson_reference_implementation():
    spike_rate = 40
    num_repeats = 500

    neuron_model = poisson.PoissonNeuron(
        spike_rate=spike_rate,
        num_repeats=num_repeats,
    )

    def _check_histogram(bins, hist):
        assert len(bins) == len(hist)
        assert (hist >= 0).all()

    bins, hist = neuron_model.sample_spikes()
    _check_histogram(bins, hist)
    assert hist.sum() == num_repeats

    bins, hist = neuron_model.sample_poisson_estimate()
    _check_histogram(bins, hist)

    bins, hist = neuron_model.sample_poisson()
    _check_histogram(bins, hist)


def test_homogeneous_poisson_sampling(spike_rate):
    torch.manual_seed(0)
    np.random.seed(0)
    spike_rates = spike_rate * torch.ones((10, 2000, 1))
    spike_counts = poisson._sample_batch(spike_rates)
    assert spike_counts.shape == spike_rates.shape

    neuron_model = poisson.PoissonNeuron(spike_rate=spike_rate,
                                         num_repeats=spike_counts.numel())
    _, reference_counts = neuron_model.sample_poisson(
        range_=(0, spike_counts.max() + 1))

    _assert_histograms_close(spike_counts.flatten().numpy(), reference_counts)


def test_poisson_sampling(spike_rate, refractory_period):
    torch.manual_seed(0)
    np.random.seed(0)
    spike_rates = spike_rate * torch.ones((10, 2000, 1))
    spike_counts = poisson._sample_batch(spike_rates,
                                         refractory_period=refractory_period)
    transform = poisson.PoissonNeuronTransform(
        num_neurons=10, refractory_period=refractory_period)
    spike_counts = transform(spike_rates)
    assert spike_counts.shape == spike_rates.shape

    neuron_model = poisson.PoissonNeuron(spike_rate=spike_rate,
                                         num_repeats=spike_counts.numel())

    _, reference_counts = neuron_model.sample_spikes(
        refractory_period=refractory_period)

    _assert_histograms_close(spike_counts.flatten().numpy(), reference_counts)
