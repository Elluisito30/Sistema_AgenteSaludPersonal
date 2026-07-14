"""
MLP model builder.

Constructs a Keras Sequential MLP given:
    - Hidden layer configuration (list of units)
    - Activation function (relu or leaky_relu)
    - Optimizer (adam or rmsprop)
    - Regularization (dropout or batch_norm)

All architecture decisions are parameterized here.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers

from config import (
    DROPOUT_RATE, OUTPUT_ACTIVATION, LOSS_FUNCTION,
)


def _get_activation_layer(name):
    """Return the activation layer by name."""
    if name == "relu":
        return layers.Activation("relu")
    elif name == "leaky_relu":
        return layers.LeakyReLU(negative_slope=0.1)
    else:
        raise ValueError(f"Unknown activation: {name}")


def _get_optimizer(name):
    """Return optimizer instance by name."""
    if name == "adam":
        return keras.optimizers.Adam(learning_rate=1e-3)
    elif name == "rmsprop":
        return keras.optimizers.RMSprop(learning_rate=1e-3)
    else:
        raise ValueError(f"Unknown optimizer: {name}")


def build_mlp(
    num_features,
    num_classes,
    hidden_units,
    activation="relu",
    optimizer_name="adam",
    regularization="dropout",
    dropout_rate=DROPOUT_RATE,
):
    """
    Build a Sequential MLP model.

    Args:
        num_features:   Input feature dimension (11).
        num_classes:    Number of output classes (7).
        hidden_units:   List of ints, e.g. [256, 128].
        activation:     'relu' or 'leaky_relu'.
        optimizer_name: 'adam' or 'rmsprop'.
        regularization: 'dropout' or 'batch_norm'.
        dropout_rate:   Dropout rate (only used if regularization='dropout').

    Returns:
        keras.Model: Compiled model.
    """
    model = keras.Sequential(name="MLP")

    model.add(layers.Input(shape=(num_features,)))

    for i, units in enumerate(hidden_units):
        model.add(layers.Dense(units, kernel_initializer="he_normal"))

        if regularization == "dropout":
            model.add(layers.Dropout(dropout_rate))
        elif regularization == "batch_norm":
            model.add(layers.BatchNormalization())

        model.add(_get_activation_layer(activation))

    model.add(layers.Dense(num_classes, activation=OUTPUT_ACTIVATION))

    model.compile(
        optimizer=_get_optimizer(optimizer_name),
        loss=LOSS_FUNCTION,
        metrics=["accuracy"],
    )

    return model


def build_model_from_config(num_features, num_classes, config):
    """
    Build model from a config dict.

    Args:
        num_features: Input dimension.
        num_classes:  Output classes.
        config: Dict with keys:
            - hidden_units (list[int])
            - activation (str)
            - optimizer (str)
            - regularization (str)

    Returns:
        keras.Model: Compiled model.
    """
    return build_mlp(
        num_features=num_features,
        num_classes=num_classes,
        hidden_units=config["hidden_units"],
        activation=config["activation"],
        optimizer_name=config["optimizer"],
        regularization=config["regularization"],
    )


def generate_grid_configs():
    """
    Generate all hyperparameter combinations for grid search.

    Returns:
        list[dict]: Each dict is a unique architecture config.
                    Total: 3 x 2 x 2 x 2 = 24 combinations.
    """
    from config import (
        HIDDEN_LAYER_CONFIGS, OPTIMIZERS, ACTIVATIONS, REGULARIZATIONS,
    )

    configs = []
    for layer_cfg in HIDDEN_LAYER_CONFIGS:
        for opt in OPTIMIZERS:
            for act in ACTIVATIONS:
                for reg in REGULARIZATIONS:
                    name = f"{layer_cfg['name']}_{opt}_{act}_{reg}"
                    configs.append({
                        "name": name,
                        "hidden_units": layer_cfg["units"],
                        "optimizer": opt,
                        "activation": act,
                        "regularization": reg,
                    })
    return configs


if __name__ == "__main__":
    configs = generate_grid_configs()
    print(f"Total configurations: {len(configs)}")
    for i, cfg in enumerate(configs, 1):
        print(f"  {i:2d}. {cfg['name']}")
