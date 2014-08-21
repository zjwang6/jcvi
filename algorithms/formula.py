#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Some math formula for various calculations
"""

import sys
import numpy as np

from math import log, exp, sqrt

from jcvi.utils.cbook import human_size


def erf(x):
    # save the sign of x
    sign = 1 if x >= 0 else -1
    x = abs(x)

    # constants
    a1 =  0.254829592
    a2 = -0.284496736
    a3 =  1.421413741
    a4 = -1.453152027
    a5 =  1.061405429
    p  =  0.3275911

    # A&S formula 7.1.26
    t = 1.0 / (1.0 + p*x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * exp(-x * x)
    return sign * y  # erf(-x) = -erf(x)


def gaussian_prob_le(mu, sigma, x):
    if sigma == 0:
        return 1 if mu <= x else 0
    z = (x - mu) / (sigma * sqrt(2))
    return .5 + .5 * erf(z)


def choose_insertsize(readlen=150, step=20, cutoff=.01):
    """
    Calculate ratio of overlap for a range of insert sizes. Idea borrowed from
    ALLPATHS code (`allpaths_cache/CacheToAllPathsInputs.pl`).
    """
    print >> sys.stderr, "Insert-size\tOverlap"
    for i in range(0, 3 * readlen, step):
        p = gaussian_prob_le(i, i / 5, 2 * readlen)
        if p < cutoff or p > 1 - cutoff:
            continue
        print >> sys.stderr, "{0}bp\t{1}%".format(i, int(round(100 * p)))


def spearmanr(x, y):
    """
    Michiel de Hoon's library (available in BioPython or standalone as
    PyCluster) returns Spearman rsb which does include a tie correction.

    >>> x = [5.05, 6.75, 3.21, 2.66]
    >>> y = [1.65, 26.5, -5.93, 7.96]
    >>> z = [1.65, 2.64, 2.64, 6.95]
    >>> round(spearmanr(x, y), 4)
    0.4
    >>> round(spearmanr(x, z), 4)
    -0.6325
    """
    from Bio.Cluster import distancematrix

    if not x or not y:
        return 0
    return 1 - distancematrix((x, y), dist="s")[1][0]


def reject_outliers(a, threshold=3.5):
    """
    Iglewicz and Hoaglin's robust test for multiple outliers (two sided test).
    <http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm>

    See also:
    <http://contchart.com/outliers.aspx>

    >>> a = [0, 1, 2, 4, 12, 58, 188, 189]
    >>> reject_outliers(a)
    array([False, False, False, False, False,  True,  True,  True], dtype=bool)
    """
    if len(a) < 3:
        return np.zeros(len(a), dtype=bool)

    A = np.array(a, dtype=float)
    lb, ub = outlier_cutoff(A, threshold=threshold)
    return np.logical_or(A > ub, A < lb)


def outlier_cutoff(a, threshold=3.5):
    """
    Iglewicz and Hoaglin's robust, returns the cutoff values - lower bound and
    upper bound.
    """
    A = np.array(a, dtype=float)
    M = np.median(A)
    D = np.absolute(A - M)
    MAD = np.median(D)
    C = threshold / .6745 * MAD
    return M - C, M + C


def recomb_probability(cM, method="kosambi"):
    """
    <http://statgen.ncsu.edu/qtlcart/manual/node46.html>

    >>> recomb_probability(1)
    0.009998666879965463
    >>> recomb_probability(100)
    0.48201379003790845
    >>> recomb_probability(10000)
    0.5
    """
    assert method in ("kosambi", "haldane")
    d = cM / 100.
    if method == "kosambi":
        e4d = exp(4 * d)
        return (e4d - 1) / (e4d + 1) / 2
    elif method == "haldane":
        return (1 - exp(-2 * d)) / 2


def jukesCantorD(p, L=100):
    """
    >>> jukesCantorD(.1)
    (0.10732563273050497, 0.001198224852071006)
    >>> jukesCantorD(.7)
    (2.0310376508266565, 0.47249999999999864)
    """
    assert 0 <= p < .75

    rD = 1 - 4. / 3 * p
    D = -.75 * log(rD)
    varD = p * (1 - p) / (rD ** 2 * L)

    return D, varD


def jukesCantorP(D):
    """
    >>> jukesCantorP(.1)
    0.09362001071778939
    >>> jukesCantorP(2)
    0.6978874115828988
    """
    rD = exp(-4. / 3 * D)
    p = .75 * (1 - rD)
    return p


def velvet(readsize, genomesize, numreads, K):
    """
    Calculate velvet memory requirement.
    <http://seqanswers.com/forums/showthread.php?t=2101>

    Ram required for velvetg = -109635 + 18977*ReadSize + 86326*GenomeSize +
    233353*NumReads - 51092*K

    Read size is in bases.
    Genome size is in millions of bases (Mb)
    Number of reads is in millions
    K is the kmer hash value used in velveth
    """
    ram = -109635 + 18977 * readsize + 86326 * genomesize + \
            233353 * numreads - 51092 * K
    print >> sys.stderr, "ReadSize: {0}".format(readsize)
    print >> sys.stderr, "GenomeSize: {0}Mb".format(genomesize)
    print >> sys.stderr, "NumReads: {0}M".format(numreads)
    print >> sys.stderr, "K: {0}".format(K)

    ram = human_size(ram * 1000, a_kilobyte_is_1024_bytes=True)
    print >> sys.stderr, "RAM usage: {0} (MAXKMERLENGTH=31)".format(ram)


if __name__ == '__main__':

    import doctest
    doctest.testmod()
