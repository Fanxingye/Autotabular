import warnings
from typing import Dict, Optional, Tuple, Union

import numpy as np
from autotabular.pipeline.base import DATASET_PROPERTIES_TYPE, PIPELINE_DATA_DTYPE
from autotabular.pipeline.components.base import AutotabularPreprocessingAlgorithm
from autotabular.pipeline.constants import DENSE, INPUT, SPARSE, UNSIGNED_DATA
from category_encoders import CountEncoder
from ConfigSpace.configuration_space import ConfigurationSpace


class CountEncoderTransformer(AutotabularPreprocessingAlgorithm):

    def __init__(
        self,
        cols=None,
        random_state: Optional[np.random.RandomState] = None,
    ):
        self.cols = cols
        self.random_state = random_state

    def fit(self,
            X: PIPELINE_DATA_DTYPE,
            y: Optional[PIPELINE_DATA_DTYPE] = None
            ) -> 'CountEncoderTransformer':

        self.preprocessor = CtEncoder(cols=self.cols)
        self.preprocessor.fit(X)
        return self

    def transform(self, X: PIPELINE_DATA_DTYPE) -> PIPELINE_DATA_DTYPE:
        if self.preprocessor is None:
            raise NotImplementedError()

        return self.preprocessor.transform(X)

    @staticmethod
    def get_properties(
        dataset_properties: Optional[DATASET_PROPERTIES_TYPE] = None
    ) -> Dict[str, Optional[Union[str, int, bool, Tuple]]]:
        return {
            'shortname': 'CountEncoderTransformer',
            'name': 'CountEncoder Transformer',
            'handles_regression': False,
            'handles_classification': True,
            'handles_multiclass': True,
            'handles_multilabel': True,
            'handles_multioutput': True,
            # TODO find out of this is right!
            'handles_sparse': True,
            'handles_dense': True,
            'input': (DENSE, SPARSE, UNSIGNED_DATA),
            'output': (INPUT, ),
        }

    @staticmethod
    def get_hyperparameter_search_space(
        dataset_properties: Optional[DATASET_PROPERTIES_TYPE] = None,
    ) -> ConfigurationSpace:
        return ConfigurationSpace()


class CtEncoder(object):

    def __init__(self, cols=None):
        self.enc = CountEncoder(
            cols=cols,
            verbose=1,
            drop_invariant=False,
            return_df=True,
            handle_unknown='value',
            handle_missing='value',
            min_group_size=None,
            combine_min_nan_groups=None,
            min_group_name=None,
            normalize=False)

    def fit(self, X):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.enc.fit(X)

    def transform(self, X):
        return self.enc.transform(X)
