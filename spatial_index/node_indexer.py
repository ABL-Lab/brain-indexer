#!/bin/env python
#
# This file is part of SpatialIndex, the new-gen spatial indexer for BBP
# Copyright Blue Brain Project 2020-2021. All rights reserved

"""
    Implementation of MvdMorphIndexer which, builds a MorphologyIndex
    and indexes all cells contained in an MVD/SONATA file
"""

import itertools
import warnings; warnings.simplefilter("ignore")  # NOQA
import logging
from collections import namedtuple
from os import path as ospath

import morphio
import mvdtool
import numpy as np
import quaternion as npq

from ._spatial_index import MorphIndex
from .util import ChunckedProcessingMixin

morphio.set_ignored_warning(morphio.Warning.only_child)
MorphInfo = namedtuple("MorphInfo", "soma, points, radius, branch_offsets")


class MorphologyLib:

    def __init__(self, pth):
        self._pth = pth
        self._morphologies = {}

    def _load(self, morph_name):
        if ospath.isfile(self._pth):
            morph = morphio.Morphology(self._pth)
        elif ospath.isdir(self._pth):
            morph = morphio.Morphology(ospath.join(self._pth, morph_name) + ".asc")
        else:
            raise Exception("Morphology path not found: " + self._pth)

        soma = morph.soma
        morph_infos = MorphInfo(
            (soma.center, soma.max_distance),
            morph.points,
            morph.diameters,
            morph.section_offsets,
        )
        self._morphologies[morph_name] = morph_infos
        return morph_infos

    def get(self, morph_name):
        return self._morphologies.get(morph_name) or self._load(morph_name)


class NodeMorphIndexer(ChunckedProcessingMixin, MorphIndex):

    def __init__(self, morphology_dir, mvd_file, gids=None):
        super().__init__()
        self.morph_lib = MorphologyLib(morphology_dir)
        self.mvd: mvdtool.MVD3.File = mvdtool.open(mvd_file)
        self._gids = range(0, len(self.mvd)) if gids is None else gids
        logging.info("Index count: %d cells", len(self._gids))

    def n_elements_to_import(self):
        return len(self._gids)

    def rototranslate(self, morph, position, rotation):
        morph = self.morph_lib.get(morph)

        # mvd files use (x, y, z, w) representation for quaternions. npq uses (w, x, y, z)
        rotation_vector = np.roll(rotation, 1)
        points = (npq.rotate_vectors(npq.quaternion(*rotation_vector).normalized(),
                                     morph.points)
                  if rotation is not None
                  else morph.points)

        points += position
        return points

    def process_cell(self, gid, morph, points, position):
        morph = self.morph_lib.get(morph)
        soma_center, soma_rad = morph.soma
        soma_center += position
        self.add_soma(gid, soma_center, soma_rad)
        self.add_neuron(
            gid, points, morph.radius, morph.branch_offsets[:-1], False
        )

    def process_range(self, range_=()):
        """Process a range of cells.

        :param: range_ (offset, count), or () [all]
        """
        if self._gids is None:
            # No need to translate to gids since ranges are valid gids
            index_args = range_
            cur_gids = itertools.count(range_[0] if range_ else 0)
        else:
            # Translate the current range to indexable gids
            cur_gids = self._gids
            if range_:
                cur_gids = self._gids[slice(range_[0], range_[0] + range_[1])]
            index_args = (cur_gids,)
        mvd = self.mvd
        morph_names = mvd.morphologies(*index_args)
        positions = mvd.positions(*index_args)
        rotations = mvd.rotations(*index_args) if mvd.rotated else itertools.repeat(None)

        for gid, morph, pos, rot in zip(cur_gids, morph_names, positions, rotations):
            # GIDs in files are zero-based, while they're typically 1-based in application
            gid += 1
            rotopoints = self.rototranslate(morph, pos, rot)
            self.process_cell(gid, morph, rotopoints, pos)

    @classmethod
    def load_dump(cls, filename):
        """Load the index from a dump file"""
        return MorphIndex(filename)
