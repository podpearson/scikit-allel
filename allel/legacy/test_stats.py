# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division


import unittest
from allel.test.tools import assert_array_equal as aeq, assert_array_close
import numpy as np


from allel.model import GenotypeArray, HaplotypeArray, SortedIndex
from allel.stats import windowed_nnz, windowed_nnz_per_base, \
    mean_pairwise_difference, windowed_nucleotide_diversity


class TestWindowUtilities(unittest.TestCase):

    def test_windowed_nnz(self):
        f = windowed_nnz
        pos = [1, 12, 15, 27]

        # boolean array, all true
        b = [True, True, True, True]
        expected_counts = [1, 2, 1]
        expected_bin_edges = [1, 11, 21, 31]
        actual_counts, actual_bin_edges = f(pos, b, window=10)
        aeq(expected_counts, actual_counts)
        aeq(expected_bin_edges, actual_bin_edges)

        # boolean array, not all true
        b = [False, True, False, True]
        expected_counts = [0, 1, 1]
        expected_bin_edges = [1, 11, 21, 31]
        actual_counts, actual_bin_edges = f(pos, b, window=10)
        aeq(expected_bin_edges, actual_bin_edges)
        aeq(expected_counts, actual_counts)

        # explicit start and stop
        b = [False, True, False, True]
        expected_counts = [1, 0, 1]
        expected_bin_edges = [5, 15, 25, 27]
        actual_counts, actual_bin_edges = \
            f(pos, b, window=10, start=5, stop=27)
        aeq(expected_bin_edges, actual_bin_edges)
        aeq(expected_counts, actual_counts)

        # boolean array, bad length
        b = [False, True, False]
        with self.assertRaises(ValueError):
            f(pos, b, window=10)

        # 2D, 4 variants, 2 samples
        b = [[True, False],
             [True, True],
             [True, False],
             [True, True]]
        expected_counts = [[1, 0],
                           [2, 1],
                           [1, 1]]
        expected_bin_edges = [1, 11, 21, 31]
        actual_counts, actual_bin_edges = f(pos, b, window=10)
        aeq(expected_counts, actual_counts)
        aeq(expected_bin_edges, actual_bin_edges)

    def test_windowed_nnz_per_base(self):
        f = windowed_nnz_per_base
        pos = [1, 12, 15, 27]

        # boolean array, all true
        b = [True, True, True, True]
        # N.B., final bin includes right edge
        expected_densities = [1/10, 2/10, 1/11]
        expected_bin_edges = [1, 11, 21, 31]
        actual_densities, actual_bin_edges, _, _ = f(pos, b, window=10)
        aeq(expected_densities, actual_densities)
        aeq(expected_bin_edges, actual_bin_edges)

        # boolean array, not all true
        b = [False, True, False, True]
        expected_densities = [0/10, 1/10, 1/11]
        expected_bin_edges = [1, 11, 21, 31]
        actual_densities, actual_bin_edges, _, _ = f(pos, b, window=10)
        aeq(expected_bin_edges, actual_bin_edges)
        aeq(expected_densities, actual_densities)

        # explicit start and stop
        b = [False, True, False, True]
        expected_densities = [1/10, 0/10, 1/3]
        expected_bin_edges = [5, 15, 25, 27]
        actual_densities, actual_bin_edges, _, _ = \
            f(pos, b, window=10, start=5, stop=27)
        aeq(expected_bin_edges, actual_bin_edges)
        aeq(expected_densities, actual_densities)

        # boolean array, bad length
        b = [False, True, False]
        with self.assertRaises(ValueError):
            f(pos, b, window=10)

        # 2D, 4 variants, 2 samples
        b = [[True, False],
             [True, True],
             [True, False],
             [True, True]]
        expected_densities = [[1/10, 0/10],
                              [2/10, 1/10],
                              [1/11, 1/11]]
        expected_bin_edges = [1, 11, 21, 31]
        actual_densities, actual_bin_edges, _, _ = f(pos, b, window=10)
        aeq(expected_densities, actual_densities)
        aeq(expected_bin_edges, actual_bin_edges)

        # include is_accessible array option
        is_accessible = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                  1, 1, 1, 1, 0, 0, 1, 1, 0, 0,
                                  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=bool)
        b = [False, True, False, True]
        expected_densities = [-1, 1/6, 1/11]
        expected_bin_edges = [1, 11, 21, 31]
        actual_densities, actual_bin_edges, _, _ = \
            f(pos, b, window=10, is_accessible=is_accessible, fill=-1)
        aeq(expected_bin_edges, actual_bin_edges)
        aeq(expected_densities, actual_densities)


class TestHardyWeinberg(unittest.TestCase):

    def test_heterozygosity_observed(self):

        # diploid
        g = GenotypeArray([[[0, 0], [0, 0]],
                           [[1, 1], [1, 1]],
                           [[1, 1], [2, 2]],
                           [[0, 0], [0, 1]],
                           [[0, 0], [0, 2]],
                           [[1, 1], [1, 2]],
                           [[0, 1], [0, 1]],
                           [[0, 1], [1, 2]],
                           [[0, 0], [-1, -1]],
                           [[0, 1], [-1, -1]],
                           [[-1, -1], [-1, -1]]], dtype='i1')
        expect = [0, 0, 0, .5, .5, .5, 1, 1, 0, 1, -1]
        actual = heterozygosity_observed(g, fill=-1)
        aeq(expect, actual)

        # polyploid
        g = GenotypeArray([[[0, 0, 0], [0, 0, 0]],
                           [[1, 1, 1], [1, 1, 1]],
                           [[1, 1, 1], [2, 2, 2]],
                           [[0, 0, 0], [0, 0, 1]],
                           [[0, 0, 0], [0, 0, 2]],
                           [[1, 1, 1], [0, 1, 2]],
                           [[0, 0, 1], [0, 1, 1]],
                           [[0, 1, 1], [0, 1, 2]],
                           [[0, 0, 0], [-1, -1, -1]],
                           [[0, 0, 1], [-1, -1, -1]],
                           [[-1, -1, -1], [-1, -1, -1]]], dtype='i1')
        expect = [0, 0, 0, .5, .5, .5, 1, 1, 0, 1, -1]
        actual = heterozygosity_observed(g, fill=-1)
        aeq(expect, actual)

    def test_heterozygosity_expected(self):

        def refimpl(g, fill=0):
            """Limited reference implementation for testing purposes."""

            ploidy = g.ploidy

            # calculate allele frequencies
            af, _, an = g.allele_frequencies()

            # assume three alleles
            p = af[:, 0]
            q = af[:, 1]
            r = af[:, 2]

            out = 1 - p**ploidy - q**ploidy - r**ploidy
            out[an == 0] = fill

            return out

        # diploid
        g = GenotypeArray([[[0, 0], [0, 0]],
                           [[1, 1], [1, 1]],
                           [[1, 1], [2, 2]],
                           [[0, 0], [0, 1]],
                           [[0, 0], [0, 2]],
                           [[1, 1], [1, 2]],
                           [[0, 1], [0, 1]],
                           [[0, 1], [1, 2]],
                           [[0, 0], [-1, -1]],
                           [[0, 1], [-1, -1]],
                           [[-1, -1], [-1, -1]]], dtype='i1')
        expect1 = [0, 0, 0.5, .375, .375, .375, .5, .625, 0, .5, -1]
        expect2 = refimpl(g, fill=-1)
        actual = heterozygosity_expected(g, fill=-1)
        assert_array_close(expect1, actual)
        assert_array_close(expect2, actual)
        expect3 = [0, 0, 0.5, .375, .375, .375, .5, .625, 0, .5, 0]
        actual = heterozygosity_expected(g, fill=0)
        assert_array_close(expect3, actual)

        # polyploid
        g = GenotypeArray([[[0, 0, 0], [0, 0, 0]],
                           [[1, 1, 1], [1, 1, 1]],
                           [[1, 1, 1], [2, 2, 2]],
                           [[0, 0, 0], [0, 0, 1]],
                           [[0, 0, 0], [0, 0, 2]],
                           [[1, 1, 1], [0, 1, 2]],
                           [[0, 0, 1], [0, 1, 1]],
                           [[0, 1, 1], [0, 1, 2]],
                           [[0, 0, 0], [-1, -1, -1]],
                           [[0, 0, 1], [-1, -1, -1]],
                           [[-1, -1, -1], [-1, -1, -1]]], dtype='i1')
        expect = refimpl(g, fill=-1)
        actual = heterozygosity_expected(g, fill=-1)
        assert_array_close(expect, actual)

    def test_inbreeding_coefficient(self):

        # diploid
        g = GenotypeArray([[[0, 0], [0, 0]],
                           [[1, 1], [1, 1]],
                           [[1, 1], [2, 2]],
                           [[0, 0], [0, 1]],
                           [[0, 0], [0, 2]],
                           [[1, 1], [1, 2]],
                           [[0, 1], [0, 1]],
                           [[0, 1], [1, 2]],
                           [[0, 0], [-1, -1]],
                           [[0, 1], [-1, -1]],
                           [[-1, -1], [-1, -1]]], dtype='i1')
        # ho = np.array([0, 0, 0, .5, .5, .5, 1, 1, 0, 1, -1])
        # he = np.array([0, 0, 0.5, .375, .375, .375, .5, .625, 0, .5, -1])
        # expect = 1 - (ho/he)
        # expect[he == 0] = -1
        expect = [-1, -1, 1-0, 1-(.5/.375), 1-(.5/.375), 1-(.5/.375),
                  1-(1/.5), 1-(1/.625), -1, 1-(1/.5), -1]
        actual = inbreeding_coefficient(g, fill=-1)
        assert_array_close(expect, actual)


class TestDiversity(unittest.TestCase):

    def test_mean_pairwise_difference(self):

        # start with simplest case, two haplotypes, one pairwise comparison
        h = HaplotypeArray([[0, 0],
                            [1, 1],
                            [0, 1],
                            [1, 2],
                            [0, -1],
                            [-1, -1]])
        expect = [0, 0, 1, 1, -1, -1]
        actual = mean_pairwise_difference(h, fill=-1)
        aeq(expect, actual)

        # four haplotypes, 6 pairwise comparison
        h = HaplotypeArray([[0, 0, 0, 0],
                            [0, 0, 0, 1],
                            [0, 0, 1, 1],
                            [0, 1, 1, 1],
                            [1, 1, 1, 1],
                            [0, 0, 1, 2],
                            [0, 1, 1, 2],
                            [0, 1, -1, -1],
                            [-1, -1, -1, -1]])
        expect = [0, 3/6, 4/6, 3/6, 0, 5/6, 5/6, 1, -1]
        actual = mean_pairwise_difference(h, fill=-1)
        assert_array_close(expect, actual)

        # should also work for genotypes
        g = h.view_genotypes(ploidy=2)
        expect = [0, 3/6, 4/6, 3/6, 0, 5/6, 5/6, 1, -1]
        actual = mean_pairwise_difference(g, fill=-1)
        assert_array_close(expect, actual)

    def test_windowed_nucleotide_diversity(self):

        g = GenotypeArray([[[0, 0], [0, 0]],
                           [[0, 0], [0, 1]],
                           [[0, 0], [1, 1]],
                           [[0, 1], [1, 1]],
                           [[1, 1], [1, 1]],
                           [[0, 0], [1, 2]],
                           [[0, 1], [1, 2]],
                           [[0, 1], [-1, -1]],
                           [[-1, -1], [-1, -1]]])
        pos = SortedIndex([2, 4, 7, 14, 15, 18, 19, 25, 27])
        # mean pairwise differences
        # expect = [0, 3/6, 4/6, 3/6, 0, 5/6, 5/6, 1, -1]
        expect = [(7/6)/10, (13/6)/10, 1/11]
        actual, _, _ = windowed_nucleotide_diversity(g, pos, window=10)
        assert_array_close(expect, actual)

        # should also work with haplotypes as input
        h = g.view_haplotypes()
        actual, _, _ = windowed_nucleotide_diversity(h, pos, window=10)
        assert_array_close(expect, actual)