
"""
Test script for model integration (NO DATA LEAKAGE)
"""
import joblib
import pandas as pd
import tensorflow as tf
from preprocessing import transform_preprocessing


def test_model():
    """
    Test loading and using trained models and preprocessors.
    """
    print("Testing integration...")

    # Load everything from disk
    model = tf.keras.models.load_model('eda/models/obesity_mlp.h5')
    col_transformer = joblib.load('eda/models/preprocessor.pkl')
    binary_encoders = joblib.load('eda/models/binary_encoders.pkl')
    target_encoder = joblib.load('eda/models/le_target.pkl')

    # Create a sample user DataFrame
    sample_user = pd.DataFrame([{
        'Age': 25,
        'Gender': 'Male',
        'Height': 1.75,
        'Weight': 80,
        'family_history_with_overweight': 'yes',
        'FAVC': 'yes',
        'FCVC': 2.0,
        'NCP': 3.0,
        'CAEC': 'Sometimes',
        'SMOKE': 'no',
        'CH2O': 2.0,
        'SCC': 'no',
        'FAF': 2.0,
        'TUE': 1.0,
        'CALC': 'Sometimes',
        'MTRANS': 'Public_Transportation'
    }])

    # Preprocess with the loaded components ONLY (no fitting!)
    X_processed = transform_preprocessing(sample_user, binary_encoders, col_transformer)

    # Predict!
    y_pred_proba = model.predict(X_processed, verbose=0)
    predicted_class_idx = y_pred_proba.argmax(axis=-1)[0]
    predicted_class = target_encoder.inverse_transform([predicted_class_idx])[0]
    confidence = y_pred_proba[0][predicted_class_idx] * 100

    print("\n--- Prediction Results ---")
    print(f"Predicted Obesity Level: {predicted_class}")
    print(f"Confidence: {confidence:.2f}%")
    return predicted_class, confidence


if __name__ == "__main__":
    test_model()
