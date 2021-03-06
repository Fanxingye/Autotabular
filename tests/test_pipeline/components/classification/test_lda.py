import sklearn.discriminant_analysis
from autotabular.pipeline.components.classification.lda import LDA

from .test_base import BaseClassificationComponentTest


class LDAComponentTest(BaseClassificationComponentTest):

    __test__ = True

    res = dict()
    res['default_iris'] = 1.0
    res['default_iris_iterative'] = -1
    res['default_iris_proba'] = 0.5614481896257509
    res['default_iris_sparse'] = -1
    res['default_digits'] = 0.88585306618093507
    res['default_digits_iterative'] = -1
    res['default_digits_binary'] = 0.9811778992106861
    res['default_digits_multilabel'] = 0.82204896441795205
    res['default_digits_multilabel_proba'] = 0.9833070018235553

    sk_mod = sklearn.discriminant_analysis.LinearDiscriminantAnalysis
    module = LDA
