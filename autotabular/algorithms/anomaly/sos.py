"""Stochastic Outlier Selection (SOS).

Part of the codes are adapted from https://github.com/jeroenjanssens/scikit-sos
"""
# Author: Winston Li <jk_zhengli@hotmail.com>
# License: BSD 2 clause

from __future__ import division, print_function

import numpy as np
from numba import njit
from sklearn.utils import check_array
from sklearn.utils.validation import check_is_fitted

from .base import BaseDetector


@njit
def _get_perplexity(D, beta):
    """Compute the perplexity and the A-row for a specific value of the
    precision of a Gaussian distribution.

    Parameters
    ----------
    D : array, shape (n_samples, )
        The dissimilarity matrix of the training samples.
    """

    A = np.exp(-D * beta)
    sumA = np.sum(A)
    H = np.log(sumA) + beta * np.sum(D * A) / sumA
    return H, A


class SOS(BaseDetector):
    """Stochastic Outlier Selection.

    SOS employs the concept of affinity to quantify
    the relationship from one data point to another data point. Affinity is
    proportional to the similarity between two data points. So, a data point
    has little affinity with a dissimilar data point. A data point is
    selected as an outlier when all the other data points have insufficient
    affinity with it.
    Read more in the :cite:`janssens2012stochastic`.

    Parameters
    ----------
    contamination : float in (0., 0.5), optional (default=0.1)
        The amount of contamination of the data set, i.e.
        the proportion of outliers in the data set. Used when fitting to
        define the threshold on the decision function.

    perplexity : float, optional (default=4.5)
        A smooth measure of the effective number of neighbours. The perplexity
        parameter is similar to the parameter `k` in kNN algorithm (the number
        of nearest neighbors). The range of perplexity can be any real number
        between 1 and n-1, where `n` is the number of samples.

    metric: str, default 'euclidean'
        Metric used for the distance computation. Any metric from
        scipy.spatial.distance can be used.

        Valid values for metric are:

        - 'euclidean'
        - from scipy.spatial.distance: ['braycurtis', 'canberra',
          'chebyshev', 'correlation', 'dice', 'hamming', 'jaccard',
          'kulsinski', 'mahalanobis', 'matching', 'minkowski',
          'rogerstanimoto', 'russellrao', 'seuclidean', 'sokalmichener',
          'sokalsneath', 'sqeuclidean', 'yule']

        See the documentation for scipy.spatial.distance for details on these
        metrics:
        http://docs.scipy.org/doc/scipy/reference/spatial.distance.html

    eps : float, optional (default = 1e-5)
        Tolerance threshold for floating point errors.

    Attributes
    ----------
    decision_scores_ : numpy array of shape (n_samples,)
        The outlier scores of the training data.
        The higher, the more abnormal. Outliers tend to have higher
        scores. This value is available once the detector is fitted.

    threshold_ : float
        The threshold is based on ``contamination``. It is the
        ``n_samples * contamination`` most abnormal samples in
        ``decision_scores_``. The threshold is calculated for generating
        binary outlier labels.

    labels_ : int, either 0 or 1
        The binary labels of the training data. 0 stands for inliers
        and 1 for outliers/anomalies. It is generated by applying
        ``threshold_`` on ``decision_scores_``.


    Examples
    --------
    >>> from pyod.models.sos import SOS
    >>> from pyod.utils.data import generate_data
    >>> n_train = 50
    >>> n_test = 50
    >>> contamination = 0.1
    >>> X_train, y_train, X_test, y_test = generate_data(
    ...     n_train=n_train, n_test=n_test,
    ...     contamination=contamination, random_state=42)
    >>>
    >>> clf = SOS()
    >>> clf.fit(X_train)
    SOS(contamination=0.1, eps=1e-05, metric='euclidean', perplexity=4.5)
    """

    def __init__(self,
                 contamination=0.1,
                 perplexity=4.5,
                 metric='euclidean',
                 eps=1e-5):
        super(SOS, self).__init__(contamination=contamination)
        self.perplexity = perplexity
        self.metric = metric.lower()
        self.eps = eps

    def _x2d(self, X):
        """Computes the dissimilarity matrix of a given dataset.

        Parameters
        ----------
        X : array-like, shape (n_samples, n_features)
            The query sample or samples to compute the dissimilarity matrix
            w.r.t. to the training samples.

        Returns
        -------
        D : array, shape (n_samples, )
            Returns the dissimilarity matrix.
        """

        (n, d) = X.shape
        if self.metric == 'none':
            if n != d:
                raise ValueError(
                    "If you specify 'none' as the metric, the data set "
                    'should be a square dissimilarity matrix')
            else:
                D = X
        elif self.metric == 'euclidean':
            sumX = np.sum(np.square(X), 1)

            # np.abs protects against extremely small negative values
            # that may arise due to floating point arithmetic errors
            D = np.sqrt(
                np.abs(np.add(np.add(-2 * np.dot(X, X.T), sumX).T, sumX)))
        else:
            try:
                from scipy.spatial import distance
            except ImportError as e:
                raise ImportError(
                    'Please install scipy if you wish to use a metric '
                    "other than 'euclidean' or 'none'")
            else:
                D = distance.squareform(distance.pdist(X, self.metric))
        return D

    def _d2a(self, D):
        """Performs a binary search to get affinities in such a way that each
        conditional Gaussian has the same perplexity. Then returns the
        affinities matrix.

        Parameters
        ----------
        D : array, shape (n_samples, )
            The dissimilarity matrix of the training samples.

        Returns
        -------
        A : array, shape (n_samples, )
            Returns the affinity matrix.
        """

        (n, _) = D.shape
        A = np.zeros((n, n))
        beta = np.ones((n, 1))
        logU = np.log(self.perplexity)

        for i in range(n):
            # Compute the Gaussian kernel and entropy for the current precision
            betamin = -np.inf
            betamax = np.inf
            Di = D[i, np.concatenate((np.r_[0:i], np.r_[i + 1:n]))]
            (H, thisA) = _get_perplexity(Di, beta[i])

            # Evaluate whether the perplexity is within tolerance
            Hdiff = H - logU
            tries = 0
            while (np.isnan(Hdiff)
                   or np.abs(Hdiff) > self.eps) and tries < 5000:
                if np.isnan(Hdiff):
                    beta[i] = beta[i] / 10.0
                # If not, increase or decrease precision
                elif Hdiff > 0:
                    betamin = beta[i].copy()
                    if betamax == np.inf or betamax == -np.inf:
                        beta[i] = beta[i] * 2.0
                    else:
                        beta[i] = (beta[i] + betamax) / 2.0
                else:
                    betamax = beta[i].copy()
                    if betamin == np.inf or betamin == -np.inf:
                        beta[i] = beta[i] / 2.0
                    else:
                        beta[i] = (beta[i] + betamin) / 2.0
                # Recompute the values
                (H, thisA) = _get_perplexity(Di, beta[i])
                Hdiff = H - logU
                tries += 1

            # Set the final row of A
            A[i, np.concatenate((np.r_[0:i], np.r_[i + 1:n]))] = thisA

        return A

    def _a2b(self, A):
        """Computes the binding probabilities of a given affinity matrix.

        Parameters
        ----------
        A : array, shape (n_samples, )
            The affinities matrix.

        Returns
        -------
        B : array, shape (n_samples, )
            Returns the matrix of binding probabilities.
        """

        B = A / A.sum(axis=1)[:, np.newaxis]
        return B

    def _b2o(self, B):
        """Computes the binding probabilities of a given affinity matrix.

        Parameters
        ----------
        A : array, shape (n_samples, )
            The affinities matrix.

        Returns
        -------
        B : array, shape (n_samples, )
            Returns the matrix of binding probabilities.
        """
        O = np.prod(1 - B, 0)
        return O

    def fit(self, X, y=None):
        """Fit detector. y is ignored in unsupervised methods.

        Parameters
        ----------
        X : numpy array of shape (n_samples, n_features)
            The input samples.

        y : Ignored
            Not used, present for API consistency by convention.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        X = check_array(X)
        self._set_n_classes(y)
        D = self._x2d(X)
        A = self._d2a(D)
        B = self._a2b(A)
        O = self._b2o(B)
        # Invert decision_scores_. Outliers comes with higher outlier scores
        self.decision_scores_ = O
        self._process_decision_scores()
        return self

    def decision_function(self, X):
        """Predict raw anomaly score of X using the fitted detector.

        The anomaly score of an input sample is computed based on different
        detector algorithms. For consistency, outliers are assigned with
        larger anomaly scores.

        Parameters
        ----------
        X : numpy array of shape (n_samples, n_features)
            The training input samples. Sparse matrices are accepted only
            if they are supported by the base estimator.

        Returns
        -------
        anomaly_scores : numpy array of shape (n_samples,)
            The anomaly score of the input samples.
        """
        check_is_fitted(self, ['decision_scores_', 'threshold_', 'labels_'])
        X = check_array(X)
        D = self._x2d(X)
        A = self._d2a(D)
        B = self._a2b(A)
        O = self._b2o(B)
        return O
