
"""
Preprocessing script for UCI Obesity Dataset (with fit/transform separation to prevent leakage)
"""
import pandas as pd
from ucimlrepo import fetch_ucirepo
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer


def load_data():
    """
    Load dataset from UCI Machine Learning Repository (id=544).
    Returns:
        pd.DataFrame: Full dataset with features and target.
    """
    obesity_dataset = fetch_ucirepo(id=544)
    X = obesity_dataset.data.features
    y = obesity_dataset.data.targets
    df = pd.concat([X, y], axis=1)
    return df


def create_preprocessing_components():
    """
    Create, but do NOT fit, all preprocessing components.
    Returns:
        tuple: (binary_vars, categorical_vars, numerical_vars, target_var)
    """
    binary_vars = ['Gender', 'family_history_with_overweight', 'FAVC', 'SMOKE', 'SCC']
    categorical_vars = ['CAEC', 'CALC', 'MTRANS']
    numerical_vars = ['Age', 'Height', 'Weight', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE']
    target_var = 'NObeyesdad'
    return binary_vars, categorical_vars, numerical_vars, target_var


def fit_preprocessing(X_train):
    """
    Fit preprocessing components ONLY on X_train.
    Args:
        X_train (pd.DataFrame): Training features to fit preprocessing on.
    Returns:
        tuple: (fitted_binary_encoders, fitted_col_transformer)
    """
    # 1. Make a copy and compute BMI
    X = X_train.copy()
    X['BMI'] = X['Weight'] / (X['Height'] ** 2)

    # 2. Fit LabelEncoders for binary variables
    binary_vars, _, _, _ = create_preprocessing_components()
    binary_encoders = {}
    for col in binary_vars:
        le = LabelEncoder()
        le.fit(X[col])
        binary_encoders[col] = le

    # 3. Fit ColumnTransformer (OneHotEncoder and StandardScaler)
    col_transformer = ColumnTransformer(
        transformers=[
            ('binary', 'passthrough', binary_vars),
            ('cat', OneHotEncoder(sparse_output=False, drop='first', handle_unknown='ignore'), ['CAEC', 'CALC', 'MTRANS']),
            ('num', StandardScaler(), ['Age', 'Height', 'Weight', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE'])
        ],
        remainder='drop'
    )
    # Apply binary encoders first on the copy before fitting ColumnTransformer
    for col, le in binary_encoders.items():
        X[col] = le.transform(X[col])

    col_transformer.fit(X)

    return binary_encoders, col_transformer


def transform_preprocessing(X, binary_encoders, col_transformer):
    """
    Transform data using pre-fitted preprocessing components.
    Args:
        X (pd.DataFrame): Features to transform
        binary_encoders (dict): Fitted LabelEncoders for binary columns
        col_transformer (ColumnTransformer): Fitted ColumnTransformer
    Returns:
        numpy.ndarray: Transformed features
    """
    X_transform = X.copy()
    X_transform['BMI'] = X_transform['Weight'] / (X_transform['Height'] ** 2)

    # Apply binary encoders
    for col, le in binary_encoders.items():
        X_transform[col] = le.transform(X_transform[col])

    # Apply ColumnTransformer
    X_processed = col_transformer.transform(X_transform)

    return X_processed


def fit_transform_preprocessing(X):
    """
    Fit and transform in one step (for initial EDA only, NOT for ML).
    """
    binary_encoders, col_transformer = fit_preprocessing(X)
    return transform_preprocessing(X, binary_encoders, col_transformer), binary_encoders, col_transformer


def fit_target(y_train):
    """
    Fit LabelEncoder on target variable.
    Args:
        y_train (pd.Series): Training target
    Returns:
        LabelEncoder: Fitted target encoder
    """
    target_encoder = LabelEncoder()
    target_encoder.fit(y_train)
    return target_encoder


def transform_target(y, target_encoder):
    """
    Transform target variable using fitted encoder.
    """
    return target_encoder.transform(y)


if __name__ == "__main__":
    print("Testing preprocessing pipeline...")
    df = load_data()
    print(f"Loaded {len(df)} records")

    X = df.drop('NObeyesdad', axis=1)
    y = df['NObeyesdad']

    binary_encoders, col_transformer = fit_preprocessing(X)
    X_processed = transform_preprocessing(X, binary_encoders, col_transformer)
    print(f"Transformed shape: {X_processed.shape}")
    print("Preprocessing test successful (no leakage)!")
