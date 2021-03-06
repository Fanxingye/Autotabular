import os
from pathlib import Path

import pandas as pd
from autofe.get_feature import get_baseline_total_data, get_GBDT_total_data, get_groupby_total_data, train_and_evaluate
from sklearn.linear_model import LogisticRegression

SEED = 42


def generate_cross_cols(self, df: pd.DataFrame, crossed_cols):
    df_cc = df.copy()
    crossed_colnames = []
    for cols in crossed_cols:
        for c in cols:
            df_cc[c] = df_cc[c].astype('str')
        colname = '_'.join(cols)
        df_cc[colname] = df_cc[list(cols)].apply(lambda x: '-'.join(x), axis=1)

        crossed_colnames.append(colname)
    return df_cc[crossed_colnames]


if __name__ == '__main__':
    ROOTDIR = Path('./')
    PROCESSED_DATA_DIR = ROOTDIR / 'data/processed_data/bank_marketing/'
    RESULTS_DIR = ROOTDIR / 'results/bank_marketing/logistic_regression'
    if not RESULTS_DIR.is_dir():
        os.makedirs(RESULTS_DIR)

    train_datafile = PROCESSED_DATA_DIR / 'train_data.csv'
    test_datafile = PROCESSED_DATA_DIR / 'test_data.csv'

    train_data = pd.read_csv(PROCESSED_DATA_DIR / 'train_data.csv')
    test_data = pd.read_csv(PROCESSED_DATA_DIR / 'test_data.csv')

    len_train = len(train_data)
    total_data = pd.concat([train_data, test_data]).reset_index(drop=True)

    target_name = 'target'
    print(total_data.info())
    """lr baseline"""
    classfier = LogisticRegression(random_state=0)
    total_data_base = get_baseline_total_data(total_data)
    acc, auc = train_and_evaluate(total_data_base, target_name, len_train,
                                  classfier)
    """groupby + lr"""
    threshold = 0.9
    k = 5
    methods = ['min', 'max', 'sum', 'mean', 'std', 'count']
    total_data_groupby = get_groupby_total_data(total_data, target_name,
                                                threshold, k, methods)
    total_data_groupby = pd.get_dummies(total_data_groupby).fillna(0)
    total_data_groupby.to_csv(
        PROCESSED_DATA_DIR / 'adult_groupby.csv', index=False)
    acc, auc = train_and_evaluate(total_data_groupby, target_name, len_train,
                                  classfier)
    """GBDT + lr"""
    total_data_GBDT = get_GBDT_total_data(total_data, target_name)
    total_data_GBDT.to_csv(PROCESSED_DATA_DIR / 'adult_gbdt.csv', index=False)
    acc, auc = train_and_evaluate(total_data_GBDT, target_name, len_train,
                                  classfier)
