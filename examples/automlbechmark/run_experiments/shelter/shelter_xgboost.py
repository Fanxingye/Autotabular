from pathlib import Path

import pandas as pd
from autofe.deeptabular_utils import LabelEncoder
from autofe.get_feature import get_baseline_total_data, get_category_columns, train_and_evaluate
from xgboost import XGBClassifier

if __name__ == '__main__':
    ROOTDIR = Path('./')
    PROCESSED_DATA_DIR = ROOTDIR / 'data/processed_data/shelter/'

    train_datafile = PROCESSED_DATA_DIR / 'train_data.csv'
    test_datafile = PROCESSED_DATA_DIR / 'test_data.csv'

    train_data = pd.read_csv(PROCESSED_DATA_DIR / 'train_data.csv')
    test_data = pd.read_csv(PROCESSED_DATA_DIR / 'test_data.csv')
    total_data = pd.concat([train_data, test_data]).reset_index(drop=True)
    len_train = len(train_data)

    target_name = 'OutcomeType'
    classfier = XGBClassifier(objective='multi:softprob')
    """XGBClassifier baseline"""
    total_data_base = get_baseline_total_data(total_data)
    cat_col_names = get_category_columns(total_data, target_name)
    label_encoder = LabelEncoder(cat_col_names)
    total_data_base = label_encoder.fit_transform(total_data)
    print('XGBClassifier baseline: ')
    acc = train_and_evaluate(
        total_data_base,
        target_name,
        len_train,
        classfier,
        task_type='multiclass')

    param = {
        'subsample': 0.9691896314686848,
        'colsample_bytree': 0.6605496959185819,
        'learning_rate': 0.012217164333137215,
        'max_depth': 27,
        'n_estimators': 900
    }
    classfier = XGBClassifier(**param)
    acc = train_and_evaluate(
        total_data_base,
        target_name,
        len_train,
        classfier,
        task_type='multiclass')
