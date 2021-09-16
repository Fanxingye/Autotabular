from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.feature_extraction.text import CountVectorizer

params = {
    'task': 'train',
    'boosting_type': 'gbdt',
    'objective': 'binary',
    'metric': {'binary_logloss'},
    'num_leaves': 64,
    'num_trees': 100,
    'learning_rate': 0.01,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': 0
}

gbm_reg_params = dict(
    objective='binary',
    subsample=0.8,
    min_child_weight=0.5,
    colsample_bytree=0.7,
    num_leaves=100,
    max_depth=12,
    learning_rate=0.05,
    n_estimators=10,
)


class GBDTFeatures(BaseEstimator, ClassifierMixin):

    def __init__(self,
                 gbdt=None,
                 gbdt_params=None,
                 vectorizer=CountVectorizer(
                     analyzer='word',
                     preprocessor=None,
                     ngram_range=(1, 1),
                     stop_words=None,
                     min_df=0,
                 )):
        self.gbdt = gbdt(**gbdt_params)
        self.vectorizer = vectorizer

    def fit(self, X, y):
        self.gbdt.fit(X, y)
        leaf = (self.gbdt.predict(X, pred_leaf=True)).astype(str).tolist()
        leaf = [' '.join(item) for item in leaf]
        self.result = self.vectorizer.fit_transform(leaf)
        return self

    def predict_proba(self, X):
        leaf = self.gbdt.predict(X, pred_leaf=True)
        leaf = (self.gbdt.predict(X, pred_leaf=True)).astype(str).tolist()
        if self.vectorizer is not None:
            leaf = [' '.join(item) for item in leaf]
            result = self.vectorizer.transform(leaf)
        return result


if __name__ == '__main__':
    from sklearn.datasets import load_iris
    import lightgbm as lgb
    X_train, y_train = load_iris(return_X_y=True)
    clf = GBDTFeatures(
        gbdt=lgb.LGBMClassifier, gbdt_params={'n_estimators': 500})
    clf.fit(X_train, y_train)
    result = clf.predict_proba(X_train)
