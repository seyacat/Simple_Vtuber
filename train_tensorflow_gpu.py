#!/usr/bin/env python3
import os
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import time
from datetime import datetime

os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Mixed precision
try:
    policy = keras.mixed_precision.Policy('mixed_float16')
    keras.mixed_precision.set_global_policy(policy)
    print("Mixed precision enabled")
except:
    print("Mixed precision not available")

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def load_features():
    path = 'dataset/features.json'

    with open(path, 'r') as f:
        data = json.load(f)

    features = data['features']
    labels = np.array(data['labels'], dtype=np.int32)
    label_names = data['labelNames']

    print(f"Loaded samples: {len(features)}")

    # Convert to numpy
    features = [np.array(f, dtype=np.float32) for f in features]

    print("Example feature shape:", features[0].shape)

    return features, labels, label_names


def reshape_features(features):
    """
    Convert spectrograms to CNN input format
    Expected input: [melBands, frames]
    Output: [melBands, frames, 1]
    """

    processed = []

    for mel in features:

        if len(mel.shape) == 1:
            raise ValueError(
                "Feature appears flattened. Spectrogram structure lost."
            )

        mel = np.expand_dims(mel, axis=-1)

        processed.append(mel)

    X = np.array(processed, dtype=np.float32)

    print("Final tensor shape:", X.shape)

    return X


def create_model(input_shape, num_classes):

    inputs = keras.Input(shape=input_shape)

    x = layers.Conv2D(32, (3,3), padding='same', activation='relu')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2,2))(x)

    x = layers.Conv2D(64, (3,3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2,2))(x)

    x = layers.Conv2D(128, (3,3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)

    x = layers.GlobalAveragePooling2D()(x)

    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.5)(x)

    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model = keras.Model(inputs, outputs)

    return model


def train_model(config):

    print("="*60)
    print("TRAINING START")
    print("="*60)

    gpus = tf.config.list_physical_devices('GPU')
    print("GPU devices:", gpus)

    features, labels, label_names = load_features()

    X = reshape_features(features)

    num_classes = config['model']['outputClasses']

    y = keras.utils.to_categorical(labels, num_classes)

    # shuffle dataset
    idx = np.arange(len(X))
    np.random.shuffle(idx)

    X = X[idx]
    y = y[idx]

    input_shape = X.shape[1:]

    print("Input shape detected:", input_shape)

    model = create_model(input_shape, num_classes)

    model.compile(
        optimizer=keras.optimizers.Adam(
            learning_rate=config['training']['learningRate']
        ),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    model.summary()

    callbacks = [

        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=config['training']['earlyStoppingPatience'],
            restore_best_weights=True
        ),

        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6
        )
    ]

    start = time.time()

    history = model.fit(
        X,
        y,
        batch_size=config['training']['batchSize'],
        epochs=config['training']['epochs'],
        validation_split=config['training']['validationSplit'],
        callbacks=callbacks,
        shuffle=True
    )

    training_time = time.time() - start

    print("Training time:", training_time)

    save_dir = "trained_python_fast"
    os.makedirs(save_dir, exist_ok=True)

    model.save(os.path.join(save_dir, "model.keras"))

    try:
        import tensorflowjs as tfjs
        tfjs.converters.save_keras_model(
            model,
            os.path.join(save_dir, "tfjs_model")
        )
    except:
        print("TensorFlow.js export skipped")

    history_data = {
        "training_time": training_time,
        "epochs_trained": len(history.history['loss']),
        "final_loss": float(history.history['loss'][-1]),
        "final_accuracy": float(history.history['accuracy'][-1]),
        "final_val_loss": float(history.history['val_loss'][-1]),
        "final_val_accuracy": float(history.history['val_accuracy'][-1]),
        "timestamp": datetime.now().isoformat()
    }

    with open(os.path.join(save_dir, "training_history.json"), "w") as f:
        json.dump(history_data, f, indent=2)

    print("Model saved.")


def main():

    config = load_config()

    train_model(config)

    print("="*60)
    print("TRAINING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()