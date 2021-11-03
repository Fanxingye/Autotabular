import itertools
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd
from autotabular.pipeline.components.base import AutotabularPreprocessingAlgorithm
from autotabular.pipeline.constants import DENSE, UNSIGNED_DATA
from ConfigSpace.configuration_space import ConfigurationSpace
from sklearn.metrics import log_loss
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier


class GoldenFeaturesTransformerClassification(AutotabularPreprocessingAlgorithm
                                              ):

    def __init__(self, features_count, random_state=None):
        self.features_count = features_count

        self.random_state = random_state

    def fit(self, X, Y=None):

        self.preprocessor = GoldenFeaturesTransformerOriginal(
            features_count=self.features_count)
        self.preprocessor.fit(X, Y)
        return self

    def transform(self, X):
        if self.preprocessor is None:
            raise NotImplementedError()
        return self.preprocessor.transform(X)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {
            'shortname': 'GoldenFeaturesTransformerClassification',
            'name': 'Golden Features Transformer To generate new features',
            'handles_regression': True,
            'handles_classification': True,
            'handles_multiclass': True,
            'handles_multilabel': True,
            'handles_multioutput': True,
            # TODO document that we have to be very careful
            'is_deterministic': False,
            'input': (DENSE, UNSIGNED_DATA),
            'output': (DENSE, UNSIGNED_DATA)
        }

    @staticmethod
    def get_hyperparameter_search_space(dataset_properties=None):
        cs = ConfigurationSpace()
        return cs


def get_logloss_score(X_train, y_train, X_test, y_test):
    clf = DecisionTreeClassifier(max_depth=3)
    clf.fit(X_train, y_train)
    pred = clf.predict_proba(X_test)
    ll = log_loss(y_test, pred)
    return ll


def get_score(item):
    col1 = item[0]
    col2 = item[1]
    X_train = item[2]
    y_train = item[3]
    X_test = item[4]
    y_test = item[5]
    scorer = item[6]

    try:
        x_train = np.array(X_train[col1] - X_train[col2]).reshape(-1, 1)
        x_test = np.array(X_test[col1] - X_test[col2]).reshape(-1, 1)
        diff_score = scorer(x_train, y_train, x_test, y_test)
    except Exception as e:
        diff_score = None
        print(str(e))

    try:
        a, b = (
            np.array(X_train[col1], dtype=float),
            np.array(X_train[col2], dtype=float),
        )
        x_train = np.divide(
            a, b, out=np.zeros_like(a), where=b != 0).reshape(-1, 1)
        a, b = np.array(
            X_test[col1], dtype=float), np.array(
                X_test[col2], dtype=float)
        x_test = np.divide(
            a, b, out=np.zeros_like(a), where=b != 0).reshape(-1, 1)
        ratio_1_score = scorer(x_train, y_train, x_test, y_test)
    except Exception as e:
        print(str(e))
        ratio_1_score = None

    try:
        b, a = (
            np.array(X_train[col1], dtype=float),
            np.array(X_train[col2], dtype=float),
        )
        x_train = np.divide(
            a, b, out=np.zeros_like(a), where=b != 0).reshape(-1, 1)
        b, a = np.array(
            X_test[col1], dtype=float), np.array(
                X_test[col2], dtype=float)
        x_test = np.divide(
            a, b, out=np.zeros_like(a), where=b != 0).reshape(-1, 1)
        ratio_2_score = scorer(x_train, y_train, x_test, y_test)
    except Exception as e:
        print(str(e))
        ratio_2_score = None

    try:
        x_train = np.array(X_train[col1] + X_train[col2]).reshape(-1, 1)
        x_test = np.array(X_test[col1] + X_test[col2]).reshape(-1, 1)
        sum_score = scorer(x_train, y_train, x_test, y_test)
    except Exception as e:
        sum_score = None
        print(str(e))

    try:
        x_train = np.array(X_train[col1] * X_train[col2]).reshape(-1, 1)
        x_test = np.array(X_test[col1] * X_test[col2]).reshape(-1, 1)
        multiply_score = scorer(x_train, y_train, x_test, y_test)
    except Exception as e:
        multiply_score = None
        print(str(e))

    return (diff_score, ratio_1_score, ratio_2_score, sum_score,
            multiply_score)


class GoldenFeaturesTransformerOriginal(object):

    def __init__(self, features_count=None):
        self._new_features = []
        self._new_columns = []
        self._features_count = features_count
        self._scorer = get_logloss_score
        self._error = None

    def fit(self, X, y):
        if self._new_features:
            return
        if self._error is not None and self._error:
            raise Exception(
                'Golden Features not created due to error (please check errors.md). '
                + self._error)
        if X.shape[1] == 0:
            self._error = f'Golden Features not created. No continous features. Input data shape: {X.shape}, {y.shape}'
            raise Exception(
                'Golden Features not created. No continous features.')

        start_time = time.time()
        combinations = itertools.combinations(X.columns, r=2)
        items = [i for i in combinations]
        if len(items) > 250000:
            si = np.random.choice(len(items), 250000, replace=False)
            items = [items[i] for i in si]

        X_train, X_test, y_train, y_test = self._subsample(X, y)

        for i in range(len(items)):
            items[i] += (X_train, y_train, X_test, y_test, self._scorer)

        scores = []
        # parallel version
        with Pool() as p:
            scores = p.map(get_score, items)
        # single process version
        # for item in items:
        #    scores += [get_score(item)]

        if not scores:
            self._error = f'Golden Features not created. Empty scores. Input data shape: {X.shape}, {y.shape}'
            raise Exception('Golden Features not created. Empty scores.')

        result = []
        for i in range(len(items)):
            if scores[i][0] is not None:
                result += [(items[i][0], items[i][1], 'diff', scores[i][0])]
            if scores[i][1] is not None:
                result += [(items[i][0], items[i][1], 'ratio', scores[i][1])]
            if scores[i][2] is not None:
                result += [(items[i][1], items[i][0], 'ratio', scores[i][2])]
            if scores[i][3] is not None:
                result += [(items[i][1], items[i][0], 'sum', scores[i][3])]
            if scores[i][4] is not None:
                result += [(items[i][1], items[i][0], 'multiply', scores[i][4])
                           ]

        df = pd.DataFrame(
            result, columns=['feature1', 'feature2', 'operation', 'score'])
        df.sort_values(by='score', inplace=True)

        new_cols_cnt = np.min([100, np.max([10, int(0.1 * X.shape[1])])])

        if (self._features_count is not None and self._features_count > 0
                and self._features_count < df.shape[0]):
            new_cols_cnt = self._features_count

        print(self._features_count, new_cols_cnt)
        self._new_features = df.head(new_cols_cnt)

        for new_feature in self._new_features:
            new_col = '_'.join([
                new_feature['feature1'],
                new_feature['operation'],
                new_feature['feature2'],
            ])
            self._new_columns += [new_col]
            print(f'Add Golden Feature: {new_col}')

        print(
            f'Created {len(self._new_features)} Golden Features in {np.round(time.time() - start_time,2)} seconds.'
        )

    def transform(self, X):
        for new_feature in self._new_features:
            new_col = '_'.join([
                new_feature['feature1'],
                new_feature['operation'],
                new_feature['feature2'],
            ])
            if new_feature['operation'] == 'diff':
                X[new_col] = X[new_feature['feature1']] - X[
                    new_feature['feature2']]
            elif new_feature['operation'] == 'ratio':
                a, b = (
                    np.array(X[new_feature['feature1']], dtype=float),
                    np.array(X[new_feature['feature2']], dtype=float),
                )
                X[new_col] = np.divide(
                    a, b, out=np.zeros_like(a), where=b != 0).reshape(-1, 1)
            elif new_feature['operation'] == 'sum':
                X[new_col] = X[new_feature['feature1']] + X[
                    new_feature['feature2']]
            elif new_feature['operation'] == 'multiply':
                X[new_col] = X[new_feature['feature1']] * X[
                    new_feature['feature2']]

        return X

    def _subsample(self, X, y):

        MAX_SIZE = 10000
        TRAIN_SIZE = 2500

        shuffle = True
        stratify = None

        if X.shape[0] > MAX_SIZE:
            stratify = y
            X_train, _, y_train, _ = train_test_split(
                X,
                y,
                train_size=MAX_SIZE,
                shuffle=shuffle,
                stratify=stratify,
                random_state=1,
            )
            stratify = y_train

            X_train, X_test, y_train, y_test = train_test_split(
                X_train,
                y_train,
                train_size=TRAIN_SIZE,
                shuffle=shuffle,
                stratify=stratify,
                random_state=1,
            )
        else:
            stratify = y
            train_size = X.shape[0] // 4
            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                train_size=train_size,
                shuffle=shuffle,
                stratify=stratify,
                random_state=1,
            )

        return X_train, X_test, y_train, y_test
