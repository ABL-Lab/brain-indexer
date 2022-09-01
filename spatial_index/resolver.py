from spatial_index import core

from .morphology_builder import MorphIndexBuilder, MorphMultiIndexBuilder
from .morphology_builder import MorphIndexMemDiskBuilder

from .synapse_builder import SynapseIndexBuilder, SynapseMultiIndexBuilder
from .synapse_builder import SynapseIndexMemDiskBuilder

from .index import MorphIndex, MorphIndexMemDisk, MorphMultiIndex
from .index import SynapseIndex, SynapseIndexMemDisk, SynapseMultiIndex

from .io import MetaData


class _SingleKindIndexResolverBase:
    @classmethod
    def _resolve(cls, index_variant, classes):
        if index_variant not in classes:
            raise ValueError(f"Invalid variant: {index_variant}")

        return classes[index_variant]

    @classmethod
    def core_class(cls, index_variant):
        """The low-level C++ wrapper."""
        return cls._resolve(index_variant, classes=cls._core_classes)

    @classmethod
    def index_class(cls, index_variant):
        """The high-level user facing class."""
        return cls._resolve(index_variant, classes=cls._index_classes)

    @classmethod
    def builder_class(cls, index_variant):
        """The builder required to build the index."""
        return cls._resolve(index_variant, classes=cls._builder_classes)


class SynapseIndexResolver(_SingleKindIndexResolverBase):
    """Provides string to class mapping.

    This class is for all classes related to indexes of synapses.
    """
    _core_classes = {
        core._MetaDataConstants.in_memory_key: core.SynapseIndex,
        core._MetaDataConstants.memory_mapped_key: core.SynapseIndexMemDisk,
        core._MetaDataConstants.multi_index_key: core.SynapseMultiIndex,
    }

    _index_classes = {
        core._MetaDataConstants.in_memory_key: SynapseIndex,
        core._MetaDataConstants.memory_mapped_key: SynapseIndexMemDisk,
        core._MetaDataConstants.multi_index_key: SynapseMultiIndex,
    }

    _builder_classes = {
        core._MetaDataConstants.in_memory_key: SynapseIndexBuilder,
        core._MetaDataConstants.memory_mapped_key: SynapseIndexMemDiskBuilder,
        core._MetaDataConstants.multi_index_key: SynapseMultiIndexBuilder,
    }


class MorphIndexResolver(_SingleKindIndexResolverBase):
    """Provides string to class mapping.

    This class is for all classes related to indexes of morphologies.
    """
    _core_classes = {
        core._MetaDataConstants.in_memory_key: core.MorphIndex,
        core._MetaDataConstants.memory_mapped_key: core.MorphIndexMemDisk,
        core._MetaDataConstants.multi_index_key: core.MorphMultiIndex,
    }

    _index_classes = {
        core._MetaDataConstants.in_memory_key: MorphIndex,
        core._MetaDataConstants.memory_mapped_key: MorphIndexMemDisk,
        core._MetaDataConstants.multi_index_key: MorphMultiIndex,
    }

    _builder_classes = {
        core._MetaDataConstants.in_memory_key: MorphIndexBuilder,
        core._MetaDataConstants.memory_mapped_key: MorphIndexMemDiskBuilder,
        core._MetaDataConstants.multi_index_key: MorphMultiIndexBuilder,
    }


class IndexResolver:
    """Provides string to class mapping.

    This resolver generalizes also over the type of index elements. Therefore,
    its used to cover both synapse and morphology indexes.
    """
    _resolver_classes = {
        "morpho_entry": MorphIndexResolver,
        "synapse": SynapseIndexResolver
    }

    @staticmethod
    def from_meta_data(meta_data):
        """The high-level class specified by the `MetaData`."""
        return IndexResolver.index_class(
            element_type=meta_data.element_type,
            index_variant=meta_data.index_variant,
        )

    @staticmethod
    def index_class(element_type, index_variant):
        """The high-level user facing class."""
        return IndexResolver._resolve(element_type, index_variant, "index_class")

    @staticmethod
    def builder_class(element_type, index_variant):
        """The builder required to build the index."""
        return IndexResolver._resolve(element_type, index_variant, "builder_class")

    @staticmethod
    def core_class(element_type, index_variant):
        """The low-level C++ wrapper."""
        return IndexResolver._resolve(element_type, index_variant, "core_class")

    @staticmethod
    def _resolve(element_type, index_variant, method):
        Resolver = IndexResolver._resolver_classes[element_type]
        return getattr(Resolver, method)(index_variant)


def _open_single_population_index(meta_data, **kwargs):
    Index = IndexResolver.from_meta_data(meta_data)
    return Index.from_meta_data(meta_data, **kwargs)


def open_index(path, max_cache_size_mb=None):
    """Open an index.

    Indexes are stored in folders, these folders contain the actual index and
    a meta data file, typically called ``meta_data.json``. The ``path`` is
    either the file name of the meta data file; or the path of the directory
    containing the meta data file.

    When opening multi-indexes one must specify the amount of memory the index
    is allowed to consume. This is done through ``max_cache_size_mb`` which is
    the size maximum amount of memory all loaded indexed elements may consume,
    in MB. Note that this does not include the space required for the tree
    structure itself. The User Guide contains more information about how a
    multi-index works and how the cache size affects performance. Regular,
    in-memory indexes will ignore this flag.
    """

    meta_data = MetaData(path)
    return _open_single_population_index(
        meta_data,
        max_cache_size_mb=max_cache_size_mb
    )
