#!/usr/bin/env python3
"""
Fast TensorFlow GPU training for vowel recognition.
Optimized for maximum speed with GPU acceleration.
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import time
import argparse
from datetime import datetime

# Set TensorFlow for optimal GPU performance
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress verbose logs

# Enable mixed precision for faster training on compatible GPUs
try:
    policy = keras.mixed_precision.Policy('mixed_float16')
    keras.mixed_precision.set_global_policy(policy)
    print("Mixed precision enabled for faster training")
except:
    print("Mixed precision not available, using default precision")

def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config

def load_features():
    """Load features from features.json"""
    features_path = 'dataset/features.json'
    with open(features_path, 'r') as f:
        data = json.load(f)
    
    features = np.array(data['features'], dtype=np.float32)
    labels = np.array(data['labels'], dtype=np.int32)
    label_names = data['labelNames']
    
    print(f"Loaded {len(features)} samples")
    print(f"Feature shape: {features[0].shape}")
    print(f"Labels: {label_names}")
    
    return features, labels, label_names

def reshape_features(features, input_shape):
    """Reshape features to match model input shape"""
    height, width, channels = input_shape
    total_elements = height * width * channels
    
    reshaped = []
    for feature in features:
        # Ensure feature has correct length
        if len(feature) != total_elements:
            # Pad or truncate
            if len(feature) < total_elements:
                padded = np.pad(feature, (0, total_elements - len(feature)), 'constant')
            else:
                padded = feature[:total_elements]
        else:
            padded = feature
        
        # Reshape to 2D and add channel dimension
        reshaped_feature = padded.reshape(height, width, channels)
        reshaped.append(reshaped_feature)
    
    return np.array(reshaped, dtype=np.float32)

def create_fast_cnn_model(input_shape, num_classes):
    """
    Create optimized CNN model for fast GPU training.
    Uses depthwise separable convolutions and batch normalization for speed.
    """
    inputs = keras.Input(shape=input_shape)
    
    # First block - optimized for speed
    x = layers.Conv2D(16, (3, 3), padding='same', activation='relu')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    
    # Second block - depthwise separable convolution for efficiency
    x = layers.SeparableConv2D(32, (3, 3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    
    # Third block
    x = layers.SeparableConv2D(64, (3, 3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    
    # Global pooling instead of flatten for better performance
    x = layers.GlobalAveragePooling2D()(x)
    
    # Dense layers with dropout
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    
    # Output layer
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = keras.Model(inputs=inputs, outputs=outputs)
    return model

def create_lightning_model(input_shape, num_classes):
    """
    Even faster model with fewer parameters for maximum speed.
    """
    model = keras.Sequential([
        layers.Conv2D(8, (2, 8), padding='same', activation='relu', input_shape=input_shape),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        
        layers.Conv2D(16, (2, 4), padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(32, activation='relu'),
        layers.Dense(num_classes, activation='softmax')
    ])
    return model

def train_model(config, use_fast_model=True):
    """Main training function optimized for GPU speed"""
    
    print("=" * 60)
    print("FAST TENSORFLOW GPU TRAINING")
    print("=" * 60)
    
    # Check GPU availability
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print(f"GPU detected: {len(gpus)} device(s)")
        for gpu in gpus:
            print(f"  - {gpu}")
        
        # Enable memory growth
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    else:
        print("WARNING: No GPU detected. Training will be slower on CPU.")
    
    # Load data
    print("\nLoading data...")
    features, labels, label_names = load_features()
    
    # Reshape features
    input_shape = tuple(config['model']['inputShape'])
    print(f"Input shape: {input_shape}")
    
    X = reshape_features(features, input_shape)
    y = keras.utils.to_categorical(labels, config['model']['outputClasses'])
    
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    
    # Create model
    print("\nCreating optimized model...")
    if use_fast_model:
        model = create_fast_cnn_model(input_shape, config['model']['outputClasses'])
        print("Using fast CNN model with batch normalization")
    else:
        model = create_lightning_model(input_shape, config['model']['outputClasses'])
        print("Using lightning-fast minimal model")
    
    # Compile with optimized settings
    print("\nCompiling model...")
    model.compile(
        optimizer=keras.optimizers.Adam(
            learning_rate=config['training']['learningRate'],
            beta_1=0.9,
            beta_2=0.999,
            epsilon=1e-07
        ),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    model.summary()
    
    # Prepare callbacks for fast training
    callbacks = [
        # Early stopping to prevent overfitting
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=config['training']['earlyStoppingPatience'],
            restore_best_weights=True,
            verbose=1
        ),
        # Reduce learning rate on plateau
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1
        ),
        # TensorBoard for monitoring
        keras.callbacks.TensorBoard(
            log_dir='logs/tensorboard/fast_gpu',
            histogram_freq=1,
            write_graph=True,
            write_images=True,
            update_freq='epoch'
        )
    ]
    
    # Train with optimized settings
    print("\n" + "=" * 60)
    print("STARTING FAST GPU TRAINING")
    print("=" * 60)
    
    batch_size = config['training']['batchSize']
    epochs = config['training']['epochs']
    validation_split = config['training']['validationSplit']
    
    print(f"Batch size: {batch_size}")
    print(f"Epochs: {epochs}")
    print(f"Validation split: {validation_split}")
    
    start_time = time.time()
    
    history = model.fit(
        X, y,
        batch_size=batch_size,
        epochs=epochs,
        validation_split=validation_split,
        callbacks=callbacks,
        verbose=1,
        shuffle=True
    )
    
    training_time = time.time() - start_time
    print(f"\nTraining completed in {training_time:.2f} seconds")
    print(f"Average time per epoch: {training_time/len(history.history['loss']):.2f} seconds")
    
    # Evaluate model
    print("\nEvaluating model...")
    val_loss, val_accuracy = model.evaluate(X, y, verbose=0)
    print(f"Final validation loss: {val_loss:.4f}")
    print(f"Final validation accuracy: {val_accuracy:.4f}")
    
    # Save model
    print("\nSaving model...")
    save_dir = 'trained_python_fast'
    os.makedirs(save_dir, exist_ok=True)
    
    # Save in multiple formats
    model.save(os.path.join(save_dir, 'model.keras'))
    model.save(os.path.join(save_dir, 'saved_model'))
    
    # Save TensorFlow.js format (with error handling)
    try:
        import tensorflowjs as tfjs
        tfjs.converters.save_keras_model(model, os.path.join(save_dir, 'tfjs_model'))
        print("  - tfjs_model/ (TensorFlow.js format)")
    except Exception as e:
        print(f"  - TensorFlow.js export skipped: {e}")
    
    # Save training history
    history_data = {
        'training_time': training_time,
        'epochs_trained': len(history.history['loss']),
        'final_loss': float(history.history['loss'][-1]),
        'final_accuracy': float(history.history['accuracy'][-1]),
        'final_val_loss': float(history.history['val_loss'][-1]),
        'final_val_accuracy': float(history.history['val_accuracy'][-1]),
        'config': config['training'],
        'timestamp': datetime.now().isoformat(),
        'gpu_used': len(gpus) > 0
    }
    
    with open(os.path.join(save_dir, 'training_history.json'), 'w') as f:
        json.dump(history_data, f, indent=2)
    
    print(f"\nModel saved to: {save_dir}")
    print("Formats saved:")
    print("  - model.keras (Keras native format)")
    print("  - saved_model/ (TensorFlow SavedModel)")
    print(f"  - training_history.json")
    
    return model, history

def main():
    parser = argparse.ArgumentParser(description='Fast TensorFlow GPU Training')
    parser.add_argument('--fast', action='store_true', 
                       help='Use fast CNN model (default)')
    parser.add_argument('--lightning', action='store_true',
                       help='Use lightning-fast minimal model')
    parser.add_argument('--benchmark', action='store_true',
                       help='Run benchmark mode with different batch sizes')
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    # Determine which model to use
    use_fast_model = True
    if args.lightning:
        use_fast_model = False
    
    # Train model
    model, history = train_model(config, use_fast_model=use_fast_model)
    
    # Benchmark if requested
    if args.benchmark:
        run_benchmark(model, config)
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

def run_benchmark(model, config):
    """Run performance benchmark with different batch sizes"""
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    # Load data
    features, labels, _ = load_features()
    input_shape = tuple(config['model']['inputShape'])
    X = reshape_features(features, input_shape)
    y = keras.utils.to_categorical(labels, config['model']['outputClasses'])
    
    batch_sizes = [16, 32, 64, 128, 256]
    
    for batch_size in batch_sizes:
        print(f"\nBenchmarking with batch size: {batch_size}")
        
        start_time = time.time()
        model.evaluate(X, y, batch_size=batch_size, verbose=0)
        eval_time = time.time() - start_time
        
        # Predict benchmark
        start_time = time.time()
        model.predict(X[:100], batch_size=batch_size, verbose=0)
        predict_time = time.time() - start_time
        
        print(f"  Evaluation time: {eval_time:.3f}s")
        print(f"  Prediction time (100 samples): {predict_time:.3f}s")
        print(f"  Samples per second: {100/predict_time:.0f}")

if __name__ == '__main__':
    main()