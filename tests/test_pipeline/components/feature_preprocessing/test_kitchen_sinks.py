import unittest

from autotabular.pipeline.components.feature_preprocessing.kitchen_sinks import RandomKitchenSinks
from autotabular.pipeline.util import PreprocessingTestCase, _test_preprocessing


class KitchenSinkComponent(PreprocessingTestCase):

    def test_default_configuration(self):
        transformation, original = _test_preprocessing(RandomKitchenSinks)
        self.assertEqual(transformation.shape[0], original.shape[0])
        self.assertEqual(transformation.shape[1], 100)
        self.assertFalse((transformation == 0).all())

    @unittest.skip('Right now, the RBFSampler returns a float64 array!')
    def test_preprocessing_dtype(self):
        super(KitchenSinkComponent,
              self)._test_preprocessing_dtype(RandomKitchenSinks)
