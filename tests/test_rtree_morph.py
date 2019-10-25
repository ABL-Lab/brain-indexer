"""
Python tests to the morphology spatial index.

It reuses tests from test_rthree_sphere
"""
import numpy as np
from spatial_index import MorphIndex
import os.path
import sys

# Add this dir to path so we can import the other tests
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import test_rtree_sphere  # NOQA
test_rtree_sphere.IndexClass = MorphIndex
from test_rtree_sphere import *  # NOQA  # Tests collected for pytest


def test_morphos_insert():
    c1 = test_rtree_sphere.arange_centroids(10)
    c2 = test_rtree_sphere.arange_centroids(10)
    c2[:, 1] += 2
    radii = np.full(10, 0.5, dtype=np.float32)

    t = MorphIndex()
    for i in range(len(c1)):
        t.insert(i//4, i % 4, c1[i], c2[i], radii[i])

    for i, c in enumerate(c1):
        idx = t.find_nearest(c, 1)[0]
        assert idx[0] == (i // 4) and idx[1] == (i % 4), "i={}, idx={} ".format(i, idx)


def test_bulk_neuron_add():
    """
    Adding a neuron alike:
    ( S ).=.=.=+=.=.=.=.=.
               +=.=.=.=.=.
      0  1 2 3 4 5 6 7 8 9  <- x coord
      0   1 2 3 4 5 6 7 8   <- segment_i
                9 0 1 2 3   <-    "
    """
    N = 10 + 6
    nrn_id = 1
    points = np.zeros([N, 3], dtype=np.float32)
    points[:, 0] = np.concatenate((np.arange(10), np.arange(4, 10)))
    points[10:, 1] = 1
    radius = np.ones(N, dtype=np.float32)

    rtree = MorphIndex()
    rtree.add_neuron(nrn_id, points, radius, [1, 10])

    idx = rtree.find_nearest([5, 0, 0], 4)
    assert sorted(idx['gid']) == [1, 1, 1, 1]
    assert sorted(idx['segment_i']) == [4, 5, 9, 10]


def test_add_neuron_with_soma_and_toString():
    points = [
        [1, 3, 5],
        [2, 4, 6],
        [2, 4, 6],
        [10, 10, 10]
    ]
    radius = [3, 2, 2, 1]
    offsets = [0, 2]
    rtree = MorphIndex()
    rtree.add_neuron(1, points, radius, offsets)
    str_expect = (
        'IndexTree([\n'
        '  Soma(id=(1, 0), centroid=[1 3 5], radius=3)\n'
        '  Segment(id=(1, 1), centroids=([1 3 5], [2 4 6]), radius=3)\n'
        '  Segment(id=(1, 2), centroids=([2 4 6], [10 10 10]), radius=2)\n'
        '])\n')
    str_result = str(rtree)
    assert str_result == str_expect


def test_add_neuron_without_soma_and_toString():
    points = [
        [1.123, 3, 5],
        [2, 4, 6],
        [2, 4, 6],
        [10, 10, 10]
    ]
    radius = [3, 2, 2, 1]
    offsets = [0, 2]
    rtree = MorphIndex()
    # add segments
    rtree.add_neuron(1, points, radius, offsets, has_Soma=False)
    str_expect = (
        'IndexTree([\n'
        '  Segment(id=(1, 1), centroids=([1.12 3 5], [2 4 6]), radius=3)\n'
        '  Segment(id=(1, 2), centroids=([2 4 6], [10 10 10]), radius=2)\n'
        '])\n')
    str_result = str(rtree)
    assert str_result == str_expect

    # add soma
    s_p = [1, 3, 5.135]
    s_r = 3136
    s_id = 1
    rtree.add_soma(s_id, s_p, s_r)
    str_expect = (
        'IndexTree([\n'
        '  Segment(id=(1, 1), centroids=([1.12 3 5], [2 4 6]), radius=3)\n'
        '  Segment(id=(1, 2), centroids=([2 4 6], [10 10 10]), radius=2)\n'
        '  Soma(id=(1, 0), centroid=[1 3 5.14], radius=3.14e+03)\n'
        '])\n')
    str_result = str(rtree)
    assert str_result == str_expect


if __name__ == "__main__":
    test_rtree_sphere.run_tests()

    test_morphos_insert()
    print("[PASSED] MTest test_morphos_insert")

    test_bulk_neuron_add()
    print("[PASSED] MTest test_bulk_neuron_add")

    test_add_neuron_with_soma_and_toString()
    print("[PASSED] MTest test_add_neuron_with_soma")

    test_add_neuron_without_soma_and_toString()
    print("[PASSED] MTest test_add_neuron_without_soma")
