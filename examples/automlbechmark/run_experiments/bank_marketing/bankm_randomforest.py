import os
from pathlib import Path

import pandas as pd
from autofe.deeptabular_utils import LabelEncoder
from autofe.feature_engineering.groupby import get_category_columns
from autofe.get_feature import (generate_cross_feature,
                                get_baseline_total_data, get_cross_columns,
                                get_groupby_GBDT_total_data,
                                get_groupby_total_data, train_and_evaluate)
from sklearn.ensemble import RandomForestClassifier

SEED = 42

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
    # random forest
    classfier = RandomForestClassifier(random_state=0)
    """RF baseline"""
    total_data_base = get_baseline_total_data(total_data)
    acc, auc = train_and_evaluate(total_data_base, target_name, len_train,
                                  classfier)
    """RF baseline_labelencoder"""
    cat_col_names = get_category_columns(total_data, target_name)
    label_encoder = LabelEncoder(cat_col_names)
    total_data_labelencoder = label_encoder.fit_transform(total_data)
    acc, auc = train_and_evaluate(total_data_labelencoder, target_name,
                                  len_train, classfier)

    # cross data
    cat_col_names = get_category_columns(total_data, target_name)
    crossed_cols = get_cross_columns(cat_col_names)
    total_cross_data = generate_cross_feature(
        total_data, crossed_cols=crossed_cols)
    cat_col_names = get_category_columns(total_cross_data, target_name)
    label_encoder = LabelEncoder(cat_col_names)
    total_cross_data = label_encoder.fit_transform(total_cross_data)
    acc, auc = train_and_evaluate(total_cross_data, target_name, len_train,
                                  classfier)
    """groupby + RF"""
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
    """GBDT + RF"""
    groupby_data = get_groupby_total_data(total_data, target_name, threshold,
                                          k, methods)
    total_data_GBDT = get_groupby_GBDT_total_data(groupby_data, target_name)
    acc, auc = train_and_evaluate(total_data_GBDT, target_name, len_train,
                                  classfier)

    # random forest
    param = {
        'criterion': 'gini',
        'min_samples_leaf': 2,
        'min_samples_split': 4,
        'max_depth': 8,
        'n_estimators': 1000
    }
    classfier = RandomForestClassifier(**param)
    """RF baseline"""
    total_data_base = get_baseline_total_data(total_data)
    acc, auc = train_and_evaluate(total_data_base, target_name, len_train,
                                  classfier)
