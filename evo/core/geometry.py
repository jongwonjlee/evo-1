"""
Provides generic geometry algorithms.
author: Michael Grupp

This file is part of evo (github.com/MichaelGrupp/evo).

evo is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

evo is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with evo.  If not, see <http://www.gnu.org/licenses/>.
"""

import typing

import numpy as np

from evo import EvoException


class GeometryException(EvoException):
    pass


UmeyamaResult = typing.Tuple[np.ndarray, np.ndarray, float]


def umeyama_alignment(x: np.ndarray, y: np.ndarray,
                      with_scale: bool = False) -> UmeyamaResult:
    """
    Computes the least squares solution parameters of an Sim(m) matrix
    that minimizes the distance between a set of registered points.
    Umeyama, Shinji: Least-squares estimation of transformation parameters
                     between two point patterns. IEEE PAMI, 1991
    :param x: mxn matrix of points, m = dimension, n = nr. of data points
    :param y: mxn matrix of points, m = dimension, n = nr. of data points
    :param with_scale: set to True to align also the scale (default: 1.0 scale)
    :return: r, t, c - rotation matrix, translation vector and scale factor
    """
    if x.shape != y.shape:
        raise GeometryException("data matrices must have the same shape")

    # m = dimension, n = nr. of data points
    m, n = x.shape

    # set tolerance for near-zero values
    tolerance = 1e-6

    # identify the near-zero columns in reference data (y)
    zero_cols = np.max(np.abs(y), axis=0) < tolerance
    num_zero_cols = np.sum(zero_cols)
    # print(f"# OF ZERO COLS: {num_zero_cols}")

    # means, eq. 34 and 35
    mean_x = np.mean(x[:, ~zero_cols], axis=1)
    mean_y = np.mean(y[:, ~zero_cols], axis=1)

    # variance, eq. 36
    # "transpose" for column subtraction
    sigma_x = 1.0 / n * (np.linalg.norm(x - mean_x[:, np.newaxis])**2)

    # covariance matrix, eq. 38
    outer_sum = np.zeros((m, m))
    for i in range(n):
        if not zero_cols[i] == True:
            outer_sum += np.outer((y[:, i] - mean_y), (x[:, i] - mean_x))
    cov_xy = np.multiply(1.0 / (n-num_zero_cols), outer_sum)

    # SVD (text betw. eq. 38 and 39)
    u, d, v = np.linalg.svd(cov_xy)
    if np.count_nonzero(d > np.finfo(d.dtype).eps) < m - 1:
        raise GeometryException("Degenerate covariance rank, "
                                "Umeyama alignment is not possible")

    # S matrix, eq. 43
    s = np.eye(m)
    if np.linalg.det(u) * np.linalg.det(v) < 0.0:
        # Ensure a RHS coordinate system (Kabsch algorithm).
        s[m - 1, m - 1] = -1

    # rotation, eq. 40
    r = u.dot(s).dot(v)

    # scale & translation, eq. 42 and 41
    c = 1 / sigma_x * np.trace(np.diag(d).dot(s)) if with_scale else 1.0
    t = mean_y - np.multiply(c, r.dot(mean_x))

    return r, t, c


def arc_len(x: np.ndarray) -> float:
    """
    :param x: nxm array of points, m=dimension
    :return: the (discrete approximated) arc-length of the point sequence
    """
    return np.sum(np.linalg.norm(x[:-1] - x[1:], axis=1))


def accumulated_distances(x: np.ndarray) -> np.ndarray:
    """
    :param x: nxm array of points, m=dimension
    :return: the accumulated distances along the point sequence
    """
    return np.concatenate(
        (np.array([0]), np.cumsum(np.linalg.norm(x[:-1] - x[1:], axis=1))))
